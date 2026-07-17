"""
Hination ML Training - Sử dụng dữ liệu thực từ Open-Meteo
Train model dự đoán thiên tai cho Điện Biên
"""

import os
import sys
import json
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts

# Add model to path
sys.path.insert(0, str(Path(__file__).parent))
from model import DisasterPredictionModel, HawkesProcessLoss, get_model, MODEL_CONFIGS


# ============================================================
# Configuration
# ============================================================

CONFIG = {
    # Model
    'model_size': 'small',  # small, medium, large
    'checkpoint_dir': Path(__file__).parent / 'checkpoints',
    
    # Training
    'epochs': 50,
    'batch_size': 16,
    'learning_rate': 1e-4,
    'weight_decay': 1e-5,
    'early_stopping_patience': 10,
    
    # Data
    'sequence_length': 24,  # 24 hours of history
    'prediction_horizon': 1,  # Predict 1 hour ahead
    'grid_resolution': 0.01,  # ~1km grid cells
    'num_workers': 4,
    
    # Paths
    'data_dir': Path(__file__).parent.parent / 'data',
    'historical_dir': Path(__file__).parent.parent / 'data' / 'historical',
    'cache_dir': Path(__file__).parent.parent / 'data' / 'cache',
}


# ============================================================
# Điện Biên Districts
# ============================================================

DIEN_BIEN_DISTRICTS = {
    'dien_bien_phu': {'name': 'TP Điện Biên Phủ', 'lat': 21.3869, 'lon': 103.0228, 'elev': 483},
    'tuan_giao': {'name': 'Huyện Tuần Giáo', 'lat': 21.6167, 'lon': 103.25, 'elev': 1047},
    'tua_chua': {'name': 'Huyện Tủa Chùa', 'lat': 21.4667, 'lon': 103.4333, 'elev': 1565},
    'muong_cha': {'name': 'Huyện Mường Chà', 'lat': 22.0833, 'lon': 102.4333, 'elev': 500},
    'muong_nhe': {'name': 'Huyện Mường Nhé', 'lat': 22.4167, 'lon': 102.3, 'elev': 600},
    'dien_bien_dong': {'name': 'Huyện Điện Biên Đông', 'lat': 21.1833, 'lon': 103.55, 'elev': 800},
    'nam_po': {'name': 'Huyện Nậm Pồ', 'lat': 21.65, 'lon': 103.1167, 'elev': 700},
    'muong_ang': {'name': 'Huyện Mường Ảng', 'lat': 21.8167, 'lon': 103.0833, 'elev': 650},
    'muong_lay': {'name': 'Thị xã Mường Lay', 'lat': 22.5, 'lon': 102.6833, 'elev': 450},
}


# ============================================================
# Open-Meteo API Client
# ============================================================

class OpenMeteoClient:
    """Client để fetch dữ liệu từ Open-Meteo API"""
    
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    def __init__(self):
        self.cache_dir = CONFIG['cache_dir']
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_forecast(self, lat: float, lon: float, days: int = 7) -> Dict:
        """Fetch forecast data cho một location"""
        params = {
            'latitude': lat,
            'longitude': lon,
            'hourly': 'temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl,cloud_cover',
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,wind_speed_10m_max',
            'timezone': 'Asia/Ho_Chi_Minh',
            'forecast_days': days
        }
        
        url = f"{self.FORECAST_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data
        except Exception as e:
            print(f"Error fetching forecast: {e}")
            return None
    
    def fetch_historical(self, lat: float, lon: float, start_date: str, end_date: str) -> Dict:
        """Fetch historical data từ Open-Meteo Archive"""
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': end_date,
            'hourly': 'temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl,cloud_cover',
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,wind_speed_10m_max',
            'timezone': 'Asia/Ho_Chi_Minh'
        }
        
        url = f"{self.ARCHIVE_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode())
                return data
        except Exception as e:
            print(f"Error fetching historical: {e}")
            return None


# ============================================================
# Data Preprocessor
# ============================================================

class WeatherDataPreprocessor:
    """Preprocess dữ liệu thời tiết cho training"""
    
    # WMO Weather Code mapping
    WEATHER_CODES = {
        0: {'vi': 'Trời quang', 'risk_level': 0},
        1: {'vi': 'Ít mây', 'risk_level': 0},
        2: {'vi': 'Nhiều mây', 'risk_level': 1},
        3: {'vi': 'U ám', 'risk_level': 1},
        45: {'vi': 'Sương mù', 'risk_level': 2},
        51: {'vi': 'Mưa phùn nhẹ', 'risk_level': 1},
        53: {'vi': 'Mưa phùn vừa', 'risk_level': 2},
        55: {'vi': 'Mưa phùn nặng', 'risk_level': 2},
        61: {'vi': 'Mưa nhẹ', 'risk_level': 2},
        63: {'vi': 'Mưa vừa', 'risk_level': 3},
        65: {'vi': 'Mưa to', 'risk_level': 4},
        80: {'vi': 'Mưa rào nhẹ', 'risk_level': 2},
        81: {'vi': 'Mưa rào vừa', 'risk_level': 3},
        82: {'vi': 'Mưa rào nặng', 'risk_level': 4},
        95: {'vi': 'Giông', 'risk_level': 4},
        96: {'vi': 'Giông mưa đá', 'risk_level': 5},
        99: {'vi': 'Giông mưa đá nặng', 'risk_level': 5},
    }
    
    def __init__(self, sequence_length: int = 24, grid_size: int = 64):
        self.sequence_length = sequence_length
        self.grid_size = grid_size
    
    def normalize_rainfall(self, value: float) -> float:
        """Normalize rainfall: 0-100mm -> 0-1"""
        return min(max(value / 100.0, 0), 1)
    
    def normalize_temperature(self, value: float) -> float:
        """Normalize temperature: -10 to 45°C -> 0-1"""
        return max(0, min((value + 10) / 55.0, 1))
    
    def normalize_humidity(self, value: float) -> float:
        """Normalize humidity: 0-100% -> 0-1"""
        return value / 100.0
    
    def normalize_wind(self, value: float) -> float:
        """Normalize wind: 0-100 km/h -> 0-1"""
        return min(value / 100.0, 1)
    
    def normalize_pressure(self, value: float) -> float:
        """Normalize pressure: typical range 980-1040 hPa"""
        return (value - 980) / 60.0
    
    def create_spatial_grid(self, weather_data: Dict) -> np.ndarray:
        """Create spatial grid từ weather data"""
        grid = np.zeros((4, self.grid_size, self.grid_size))
        
        # Rainfall channel
        grid[0] = self.normalize_rainfall(weather_data.get('precipitation', 0))
        
        # Temperature channel
        grid[1] = self.normalize_temperature(weather_data.get('temperature_2m', 25))
        
        # Humidity channel
        grid[2] = self.normalize_humidity(weather_data.get('humidity', 70))
        
        # Wind channel
        grid[3] = self.normalize_wind(weather_data.get('wind_speed', 10))
        
        return grid
    
    def create_temporal_sequence(self, hourly_data: List[Dict]) -> np.ndarray:
        """Create temporal feature sequence từ hourly data"""
        seq = np.zeros((self.sequence_length, 8))
        
        # Take last N hours
        data = hourly_data[-self.sequence_length:]
        
        for i, hour_data in enumerate(data):
            seq[i, 0] = self.normalize_rainfall(hour_data.get('precipitation', 0))
            seq[i, 1] = self.normalize_temperature(hour_data.get('temperature_2m', 25))
            seq[i, 2] = self.normalize_humidity(hour_data.get('humidity', 70))
            seq[i, 3] = self.normalize_wind(hour_data.get('wind_speed', 10))
            seq[i, 4] = self.normalize_pressure(hour_data.get('pressure', 1013))
            seq[i, 5] = hour_data.get('cloud_cover', 0) / 100.0
            seq[i, 6] = min(hour_data.get('hours_of_rain', 0) / 24.0, 1)
            seq[i, 7] = min(hour_data.get('consecutive_rain_hours', 0) / 48.0, 1)
        
        return seq
    
    def generate_labels(self, weather_data: List[Dict]) -> Dict[str, float]:
        """
        Generate disaster labels từ weather conditions
        Dựa trên VNDMS thresholds
        """
        # Check recent weather (last 6 hours)
        recent = weather_data[-6:]
        
        total_rainfall = sum(w.get('precipitation', 0) for w in recent)
        max_consecutive_rain = max(w.get('consecutive_rain_hours', 0) for w in recent)
        avg_humidity = np.mean([w.get('humidity', 70) for w in recent])
        min_temp = min(w.get('temperature_2m', 25) for w in recent)
        
        # Flood risk: high rainfall + high humidity
        flood_risk = min(1.0, total_rainfall / 50.0) * (avg_humidity / 100.0)
        
        # Landslide risk: sustained rain
        landslide_risk = min(1.0, max_consecutive_rain / 24.0) * (total_rainfall / 30.0)
        
        # Cold wave risk: low temperature
        if min_temp < 10:
            cold_wave_risk = max(0, (10 - min_temp) / 10.0)
        else:
            cold_wave_risk = 0
        
        return {
            'flood': min(1.0, max(0, flood_risk)),
            'landslide': min(1.0, max(0, landslide_risk)),
            'cold_wave': min(1.0, max(0, cold_wave_risk))
        }


# ============================================================
# Dataset Classes
# ============================================================

def collate_fn(batch):
    """Custom collate function for variable length sequences"""
    spatial, temporal, labels = zip(*batch)
    return (
        torch.stack(spatial),
        torch.stack(temporal),
        torch.stack(labels)
    )


class RealWeatherDataset(Dataset):
    """
    Dataset sử dụng dữ liệu thực từ Open-Meteo
    """
    
    def __init__(
        self,
        weather_sequences: List[Dict],
        labels: List[Dict],
        preprocessor: WeatherDataPreprocessor
    ):
        self.sequences = weather_sequences
        self.labels = labels
        self.preprocessor = preprocessor
        
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> Tuple:
        seq_data = self.sequences[idx]
        
        # Create spatial grid
        spatial = self.preprocessor.create_spatial_grid(seq_data)
        
        # Create temporal sequence
        temporal = self.preprocessor.create_temporal_sequence(seq_data.get('hourly', [seq_data]))
        
        # Get labels
        label = self.labels[idx]
        labels = torch.FloatTensor([
            label.get('flood', 0.0),
            label.get('landslide', 0.0),
            label.get('cold_wave', 0.0)
        ])
        
        return (
            torch.FloatTensor(spatial),
            torch.FloatTensor(temporal),
            labels
        )


class SyntheticDisasterGenerator:
    """Generate synthetic disaster data cho augmentation"""
    
    def __init__(
        self,
        base_intensity: float = 0.01,
        trigger_alpha: float = 0.5,
        decay_beta: float = 0.1
    ):
        self.base_intensity = base_intensity
        self.trigger_alpha = trigger_alpha
        self.decay_beta = decay_beta
    
    def generate_weather_sequence(
        self,
        length: int,
        start_temp: float = 25.0,
        start_humidity: float = 70.0,
        monsoon_mode: bool = False
    ) -> List[Dict]:
        """Generate synthetic weather sequence"""
        weather_seq = []
        current_temp = start_temp
        current_humidity = start_humidity
        consecutive_rain = 0
        
        # Higher rain probability during monsoon
        base_rain_prob = 0.6 if monsoon_mode else 0.3
        
        for hour in range(length):
            # Random walk for temperature
            temp_change = np.random.normal(0, 2)
            current_temp = np.clip(current_temp + temp_change, 5, 40)
            
            # Humidity with rain tendency
            rain_prob = base_rain_prob + 0.1 * (current_humidity - 50) / 50
            is_raining = np.random.random() < rain_prob
            
            if is_raining:
                rainfall = np.random.exponential(5) * (2 if monsoon_mode else 1)
                consecutive_rain += 1
            else:
                rainfall = 0
                consecutive_rain = max(0, consecutive_rain - 1)
            
            current_humidity = np.clip(
                current_humidity + np.random.normal(0, 5) + (50 if is_raining else -10),
                30, 100
            )
            
            weather_seq.append({
                'hour': hour,
                'temperature_2m': current_temp,
                'humidity': current_humidity,
                'precipitation': rainfall,
                'wind_speed': np.random.exponential(10),
                'pressure': 1013 + np.random.normal(0, 5),
                'cloud_cover': min(100, 30 + rainfall * 3 + np.random.normal(0, 10)),
                'weather_code': 95 if rainfall > 10 and np.random.random() < 0.3 else (61 if rainfall > 0 else 0),
                'hours_of_rain': 1 if is_raining else 0,
                'consecutive_rain_hours': consecutive_rain
            })
        
        # Second pass: calculate hours_of_rain
        running_hours = 0
        for h in weather_seq:
            if h['hours_of_rain'] == 1:
                running_hours += 1
                h['hours_of_rain'] = running_hours
            else:
                running_hours = 0
        
        return weather_seq
    
    def generate_dataset(self, num_samples: int, monsoon_ratio: float = 0.5) -> Tuple[List[Dict], List[Dict]]:
        """Generate full synthetic dataset"""
        weather_data = []
        labels = []
        preprocessor = WeatherDataPreprocessor()
        
        for i in range(num_samples):
            monsoon_mode = np.random.random() < monsoon_ratio
            
            weather = self.generate_weather_sequence(
                length=CONFIG['sequence_length'] + 1,
                monsoon_mode=monsoon_mode
            )
            
            label_dict = preprocessor.generate_labels(weather)
            
            weather_data.append({
                **weather[-1],
                'history': weather[:-1],
                'hourly': weather[:-1]
            })
            labels.append(label_dict)
        
        return weather_data, labels


# ============================================================
# Data Collection Functions
# ============================================================

def load_existing_data(data_dir: Path) -> Tuple[List[Dict], List[Dict]]:
    """Load existing data từ JSON files"""
    weather_data = []
    labels = []
    preprocessor = WeatherDataPreprocessor()
    
    # Load from weather_latest.json
    latest_file = data_dir / 'weather_latest.json'
    if latest_file.exists():
        with open(latest_file) as f:
            data = json.load(f)
            for district_id, district_data in data.get('districts', {}).items():
                # Create hourly sequence from daily forecast
                hourly_seq = []
                for day in district_data.get('daily_forecast', []):
                    # Simulate hourly data from daily
                    for hour in range(24):
                        hourly_seq.append({
                            'temperature_2m': (day.get('temp_max', 30) + day.get('temp_min', 25)) / 2,
                            'humidity': 80,
                            'precipitation': day.get('precipitation_sum', 0) / 24,
                            'wind_speed': 10,
                            'pressure': 1013,
                            'cloud_cover': 50,
                            'weather_code': day.get('weather_code', 0),
                            'hours_of_rain': 1 if day.get('precipitation_sum', 0) > 0 else 0,
                            'consecutive_rain_hours': 1
                        })
                
                if hourly_seq:
                    weather_data.append({
                        'district_id': district_id,
                        'hourly': hourly_seq
                    })
                    labels.append(preprocessor.generate_labels(hourly_seq))
    
    return weather_data, labels


def fetch_all_districts_weather(client: OpenMeteoClient) -> List[Dict]:
    """Fetch weather data cho tất cả huyện"""
    all_data = []
    
    for district_id, info in DIEN_BIEN_DISTRICTS.items():
        print(f"Fetching {info['name']}...")
        data = client.fetch_forecast(info['lat'], info['lon'])
        
        if data:
            # Parse hourly data
            hourly = data.get('hourly', {})
            hourly_data = []
            
            for i in range(min(len(hourly.get('time', [])), 24 * 7)):
                hourly_data.append({
                    'time': hourly['time'][i] if i < len(hourly.get('time', [])) else None,
                    'temperature_2m': hourly['temperature_2m'][i] if i < len(hourly.get('temperature_2m', [])) else 25,
                    'humidity': hourly['relative_humidity_2m'][i] if i < len(hourly.get('relative_humidity_2m', [])) else 70,
                    'precipitation': hourly['precipitation'][i] if i < len(hourly.get('precipitation', [])) else 0,
                    'wind_speed': hourly['wind_speed_10m'][i] if i < len(hourly.get('wind_speed_10m', [])) else 10,
                    'pressure': hourly['pressure_msl'][i] if i < len(hourly.get('pressure_msl', [])) else 1013,
                    'cloud_cover': hourly['cloud_cover'][i] if i < len(hourly.get('cloud_cover', [])) else 0,
                    'weather_code': hourly['weather_code'][i] if i < len(hourly.get('weather_code', [])) else 0,
                })
            
            # Add computed features
            consecutive_rain = 0
            hours_of_rain = 0
            for h in hourly_data:
                if h['precipitation'] > 0.1:
                    consecutive_rain += 1
                    hours_of_rain += 1
                else:
                    consecutive_rain = 0
                h['consecutive_rain_hours'] = consecutive_rain
                h['hours_of_rain'] = hours_of_rain
            
            all_data.append({
                'district_id': district_id,
                'district_name': info['name'],
                'coordinates': {'lat': info['lat'], 'lon': info['lon']},
                'hourly': hourly_data
            })
            
            print(f"  -> {len(hourly_data)} hours of data")
    
    return all_data


# ============================================================
# Training Functions
# ============================================================

def train_epoch(
    model: DisasterPredictionModel,
    dataloader: DataLoader,
    criterion: HawkesProcessLoss,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int
) -> Dict[str, float]:
    """Train for one epoch"""
    model.train()
    total_loss = 0
    losses = {'total': 0, 'flood': 0, 'landslide': 0, 'cold_wave': 0, 'zonation': 0}
    
    for batch_idx, (spatial, temporal, labels) in enumerate(dataloader):
        spatial = spatial.to(device)
        temporal = temporal.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        predictions = model(spatial, temporal)
        
        # Create zonation targets
        batch_size = spatial.size(0)
        zonation_targets = labels.unsqueeze(-1).unsqueeze(-1).repeat(1, 1, 64, 64) * 0.5
        
        loss_dict = criterion(
            predictions,
            (labels[:, 0], labels[:, 1], labels[:, 2]),
            zonation_targets
        )
        
        loss_dict['total'].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss_dict['total'].item()
        for key in losses:
            losses[key] += loss_dict[key].item()
        
        if batch_idx % 10 == 0:
            print(f"  Batch {batch_idx}/{len(dataloader)} - Loss: {loss_dict['total'].item():.4f}")
    
    num_batches = len(dataloader)
    for key in losses:
        losses[key] /= num_batches
    
    return losses


def evaluate(
    model: DisasterPredictionModel,
    dataloader: DataLoader,
    criterion: HawkesProcessLoss,
    device: torch.device
) -> Dict[str, float]:
    """Evaluate model"""
    model.eval()
    total_loss = 0
    all_predictions = []
    all_labels = []
    
    with torch.no_grad():
        for spatial, temporal, labels in dataloader:
            spatial = spatial.to(device)
            temporal = temporal.to(device)
            labels = labels.to(device)
            
            predictions = model(spatial, temporal)
            
            batch_size = spatial.size(0)
            zonation_targets = labels.unsqueeze(-1).unsqueeze(-1).repeat(1, 1, 64, 64) * 0.5
            
            loss_dict = criterion(
                predictions,
                (labels[:, 0], labels[:, 1], labels[:, 2]),
                zonation_targets
            )
            
            total_loss += loss_dict['total'].item()
            
            flood_pred, landslide_pred, cold_wave_pred, _ = predictions
            all_predictions.append(torch.cat([flood_pred, landslide_pred, cold_wave_pred], dim=1).cpu())
            all_labels.append(labels.cpu())
    
    predictions = torch.cat(all_predictions)
    labels = torch.cat(all_labels)
    
    metrics = calculate_metrics(predictions.numpy(), labels.numpy())
    metrics['loss'] = total_loss / len(dataloader)
    
    return metrics


def calculate_metrics(predictions: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    """Calculate evaluation metrics"""
    metrics = {}
    
    for i, name in enumerate(['flood', 'landslide', 'cold_wave']):
        pred = predictions[:, i]
        true = labels[:, i]
        
        pred_binary = (pred > 0.5).astype(float)
        accuracy = (pred_binary == true).mean()
        
        tp = ((pred_binary == 1) & (true == 1)).sum()
        fp = ((pred_binary == 1) & (true == 0)).sum()
        fn = ((pred_binary == 0) & (true == 1)).sum()
        
        precision = tp / (tp + fp + 1e-6)
        recall = tp / (tp + fn + 1e-6)
        f1 = 2 * precision * recall / (precision + recall + 1e-6)
        
        metrics[f'{name}_accuracy'] = accuracy
        metrics[f'{name}_precision'] = precision
        metrics[f'{name}_recall'] = recall
        metrics[f'{name}_f1'] = f1
    
    return metrics


def save_checkpoint(
    model: DisasterPredictionModel,
    optimizer: optim.Optimizer,
    epoch: int,
    metrics: Dict,
    checkpoint_dir: Path
):
    """Save model checkpoint"""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'metrics': metrics,
        'timestamp': datetime.now().isoformat()
    }
    
    path = checkpoint_dir / f'checkpoint_epoch_{epoch}.pt'
    torch.save(checkpoint, path)
    
    latest_path = checkpoint_dir / 'latest.pt'
    torch.save(checkpoint, latest_path)
    
    print(f"Checkpoint saved: {path}")


# ============================================================
# Main Training Loop
# ============================================================

def train(
    num_samples: int = 10000,
    epochs: int = 50,
    batch_size: int = 32,
    model_size: str = 'small',
    use_real_data: bool = True,
    fetch_new_data: bool = False
):
    """Main training function"""
    print("=" * 60)
    print("HINATION DISASTER PREDICTION MODEL TRAINING")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  - Samples: {num_samples}")
    print(f"  - Epochs: {epochs}")
    print(f"  - Batch Size: {batch_size}")
    print(f"  - Model Size: {model_size}")
    print(f"  - Use Real Data: {use_real_data}")
    print()
    
    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    
    # Create model
    model_config = MODEL_CONFIGS[model_size]
    model = get_model(model_config)
    model = model.to(device)
    
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {num_params:,}")
    
    # Collect data
    weather_data = []
    labels = []
    
    if use_real_data:
        print("\n=== Loading real weather data ===")
        
        if fetch_new_data:
            print("Fetching new data from Open-Meteo API...")
            client = OpenMeteoClient()
            weather_data = fetch_all_districts_weather(client)
        else:
            # Load existing data
            weather_data, labels = load_existing_data(CONFIG['data_dir'])
        
        print(f"Loaded {len(weather_data)} real samples")
        
        if len(weather_data) > 0:
            preprocessor = WeatherDataPreprocessor()
            
            # Expand real data with synthetic augmentation
            remaining = num_samples - len(weather_data)
            if remaining > 0:
                print(f"\nGenerating {remaining} synthetic samples for augmentation...")
                generator = SyntheticDisasterGenerator()
                synthetic_data, synthetic_labels = generator.generate_dataset(remaining)
                
                # Combine
                weather_data.extend(synthetic_data)
                labels.extend(synthetic_labels)
    
    if len(weather_data) == 0:
        print("\nGenerating synthetic training data...")
        generator = SyntheticDisasterGenerator()
        weather_data, labels = generator.generate_dataset(num_samples)
    
    # Split train/val
    split_idx = int(len(weather_data) * 0.8)
    train_weather = weather_data[:split_idx]
    train_labels = labels[:split_idx]
    val_weather = weather_data[split_idx:]
    val_labels = labels[split_idx:]
    
    print(f"\nTraining samples: {len(train_weather)}")
    print(f"Validation samples: {len(val_weather)}")
    
    # Create datasets
    preprocessor = WeatherDataPreprocessor()
    train_dataset = RealWeatherDataset(train_weather, train_labels, preprocessor)
    val_dataset = RealWeatherDataset(val_weather, val_labels, preprocessor)
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=CONFIG['num_workers'],
        collate_fn=collate_fn
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=CONFIG['num_workers'],
        collate_fn=collate_fn
    )
    
    # Loss and optimizer
    criterion = HawkesProcessLoss()
    optimizer = optim.AdamW(
        model.parameters(),
        lr=CONFIG['learning_rate'],
        weight_decay=CONFIG['weight_decay']
    )
    scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)
    
    # Training loop
    best_val_loss = float('inf')
    patience_counter = 0
    
    print("\nStarting training...")
    print("-" * 60)
    
    for epoch in range(epochs):
        print(f"\nEpoch {epoch + 1}/{epochs}")
        print("-" * 40)
        
        train_losses = train_epoch(model, train_loader, criterion, optimizer, device, epoch)
        scheduler.step()
        
        val_metrics = evaluate(model, val_loader, criterion, device)
        
        print(f"\nTrain Loss: {train_losses['total']:.4f}")
        print(f"  - Flood: {train_losses['flood']:.4f}")
        print(f"  - Landslide: {train_losses['landslide']:.4f}")
        print(f"  - Cold Wave: {train_losses['cold_wave']:.4f}")
        print(f"\nVal Metrics:")
        print(f"  - Loss: {val_metrics['loss']:.4f}")
        print(f"  - Flood F1: {val_metrics['flood_f1']:.4f}")
        print(f"  - Landslide F1: {val_metrics['landslide_f1']:.4f}")
        print(f"  - Cold Wave F1: {val_metrics['cold_wave_f1']:.4f}")
        
        checkpoint_dir = Path(CONFIG['checkpoint_dir'])
        save_checkpoint(model, optimizer, epoch, val_metrics, checkpoint_dir)
        
        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            patience_counter = 0
            print("  -> New best model!")
        else:
            patience_counter += 1
            if patience_counter >= CONFIG['early_stopping_patience']:
                print(f"\nEarly stopping triggered after {epoch + 1} epochs")
                break
        
        elapsed = epoch * 0.5
        if elapsed >= 3600:
            print(f"\n1-hour training limit reached after {epoch + 1} epochs")
            break
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    
    return model


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=10000, help='Number of training samples')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--model-size', type=str, default='small', choices=['small', 'medium', 'large'])
    parser.add_argument('--synthetic', action='store_true', help='Use only synthetic data')
    parser.add_argument('--fetch', action='store_true', help='Fetch new data from Open-Meteo')
    
    args = parser.parse_args()
    
    model = train(
        num_samples=args.samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        model_size=args.model_size,
        use_real_data=not args.synthetic,
        fetch_new_data=args.fetch
    )
