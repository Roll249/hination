"""
Hination Disaster Prediction Model Training
Train 1 hour, predict 1 hour ahead
"""

import os
import sys
import json
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

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
    'weather_data_path': Path(__file__).parent.parent / 'data',
}


# ============================================================
# Dataset Classes
# ============================================================

class DisasterDataset(Dataset):
    """
    Dataset for disaster prediction
    
    Each sample contains:
    - Spatial features: Weather grid (rainfall, temp, humidity, wind)
    - Temporal features: Sequence of weather observations
    - Labels: Flood, landslide, cold wave occurrence
    """
    
    def __init__(
        self,
        weather_data: List[Dict],
        disaster_labels: List[Dict],
        sequence_length: int = 24,
        grid_size: int = 64,
        transform=None
    ):
        self.weather_data = weather_data
        self.disaster_labels = disaster_labels
        self.sequence_length = sequence_length
        self.grid_size = grid_size
        self.transform = transform
        
        # Create spatial grids from weather data
        self._create_spatial_grids()
        
    def _create_spatial_grids(self):
        """Convert weather data to spatial grids"""
        # Grid dimensions: [channels, height, width]
        # Channels: rainfall, temperature, humidity, wind
        self.spatial_grids = []
        self.temporal_sequences = []
        self.labels = []
        
        for i in range(len(self.weather_data)):
            weather = self.weather_data[i]
            
            # Create 2D grid from point observations
            grid = self._interpolate_to_grid(weather)
            self.spatial_grids.append(grid)
            
            # Create temporal sequence
            seq = self._create_temporal_sequence(weather)
            self.temporal_sequences.append(seq)
            
            # Get labels
            if i < len(self.disaster_labels):
                self.labels.append(self.disaster_labels[i])
            else:
                self.labels.append({
                    'flood': 0.0,
                    'landslide': 0.0,
                    'cold_wave': 0.0
                })
                
    def _interpolate_to_grid(self, weather: Dict) -> np.ndarray:
        """Interpolate point observations to grid"""
        # Simple nearest-neighbor interpolation for demo
        # In production, use kriging or IDW
        grid = np.zeros((4, self.grid_size, self.grid_size))
        
        # Rainfall channel (normalized 0-100mm -> 0-1)
        grid[0] = min(weather.get('rainfall', 0) / 100.0, 1.0)
        
        # Temperature channel (normalized -10 to 45C -> 0-1)
        temp = weather.get('temperature', 20)
        grid[1] = max(0, min((temp + 10) / 55.0, 1.0))
        
        # Humidity channel (0-100% -> 0-1)
        grid[2] = weather.get('humidity', 50) / 100.0
        
        # Wind channel (0-100 km/h -> 0-1)
        grid[3] = min(weather.get('wind_speed', 0) / 100.0, 1.0)
        
        return grid
        
    def _create_temporal_sequence(self, weather: Dict) -> np.ndarray:
        """Create temporal feature sequence"""
        # Features: rainfall, temperature, humidity, wind, pressure, cloud, 
        #           hours_of_rain, consecutive_rain_hours
        seq = np.zeros((self.sequence_length, 8))
        
        for i in range(min(self.sequence_length, len(weather.get('history', [weather])))):
            hist = weather.get('history', [weather])[i]
            seq[i, 0] = min(hist.get('rainfall', 0) / 100.0, 1.0)
            seq[i, 1] = max(0, min((hist.get('temperature', 20) + 10) / 55.0, 1.0))
            seq[i, 2] = hist.get('humidity', 50) / 100.0
            seq[i, 3] = min(hist.get('wind_speed', 0) / 100.0, 1.0)
            seq[i, 4] = hist.get('pressure', 1013) / 1050.0
            seq[i, 5] = hist.get('cloud_cover', 0) / 100.0
            seq[i, 6] = min(hist.get('hours_of_rain', 0) / 24.0, 1.0)
            seq[i, 7] = min(hist.get('consecutive_rain_hours', 0) / 48.0, 1.0)
            
        return seq
        
    def __len__(self) -> int:
        return len(self.spatial_grids)
        
    def __getitem__(self, idx: int) -> Tuple:
        spatial = torch.FloatTensor(self.spatial_grids[idx])
        temporal = torch.FloatTensor(self.temporal_sequences[idx])
        
        label = self.labels[idx]
        labels = torch.FloatTensor([
            label.get('flood', 0.0),
            label.get('landslide', 0.0),
            label.get('cold_wave', 0.0)
        ])
        
        return spatial, temporal, labels


class SyntheticDisasterGenerator:
    """
    Generate synthetic disaster data for training
    Based on Hawkes process temporal clustering
    """
    
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
        start_humidity: float = 70.0
    ) -> List[Dict]:
        """Generate synthetic weather sequence"""
        weather_seq = []
        current_temp = start_temp
        current_humidity = start_humidity
        consecutive_rain = 0
        
        for hour in range(length):
            # Random walk for temperature
            temp_change = np.random.normal(0, 2)
            current_temp = np.clip(current_temp + temp_change, 5, 40)
            
            # Humidity with rain tendency
            rain_prob = 0.3 + 0.1 * (current_humidity - 50) / 50
            is_raining = np.random.random() < rain_prob
            
            if is_raining:
                rainfall = np.random.exponential(5)
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
                'temperature': current_temp,
                'humidity': current_humidity,
                'rainfall': rainfall,
                'wind_speed': np.random.exponential(10),
                'pressure': 1013 + np.random.normal(0, 5),
                'cloud_cover': min(100, 30 + rainfall * 3 + np.random.normal(0, 10)),
                'hours_of_rain': weather_seq[-24]['hours_of_rain'] + 1 if is_raining and hour > 0 else (1 if is_raining else 0),
                'consecutive_rain_hours': consecutive_rain
            })
            
        return weather_seq
        
    def generate_disaster_label(
        self,
        weather: List[Dict]
    ) -> Dict[str, float]:
        """
        Generate disaster labels based on weather conditions
        Using Hawkes-like intensity function
        """
        # Check recent weather (last 6 hours)
        recent = weather[-6:]
        
        # Calculate risk factors
        total_rainfall = sum(w['rainfall'] for w in recent)
        max_consecutive_rain = max(w['consecutive_rain_hours'] for w in recent)
        avg_humidity = np.mean([w['humidity'] for w in recent])
        min_temp = min(w['temperature'] for w in recent)
        
        # Flood risk: high rainfall + high humidity
        flood_risk = min(1.0, total_rainfall / 50.0) * (avg_humidity / 100.0)
        
        # Landslide risk: sustained rain + steep slopes (simulated)
        landslide_risk = min(1.0, max_consecutive_rain / 24.0) * (total_rainfall / 30.0)
        
        # Cold wave risk: low temperature
        cold_wave_risk = max(0, (15 - min_temp) / 15.0) if min_temp < 15 else 0
        
        # Add some random noise
        noise = np.random.normal(0, 0.1, 3)
        
        return {
            'flood': min(1.0, max(0, flood_risk + noise[0])),
            'landslide': min(1.0, max(0, landslide_risk + noise[1])),
            'cold_wave': min(1.0, max(0, cold_wave_risk + noise[2]))
        }
        
    def generate_dataset(self, num_samples: int) -> Tuple[List[Dict], List[Dict]]:
        """Generate full dataset"""
        weather_data = []
        labels = []
        
        for _ in range(num_samples):
            weather = self.generate_weather_sequence(
                length=CONFIG['sequence_length'] + 1
            )
            label = self.generate_disaster_label(weather)
            
            weather_data.append({
                **weather[-1],
                'history': weather[:-1]
            })
            labels.append(label)
            
        return weather_data, labels


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
        
        # Forward pass
        optimizer.zero_grad()
        predictions = model(spatial, temporal)
        
        # Create zonation targets (simplified: based on labels)
        batch_size = spatial.size(0)
        zonation_targets = labels.unsqueeze(-1).unsqueeze(-1).repeat(1, 1, 64, 64) * 0.5
        
        # Compute loss
        loss_dict = criterion(predictions, 
                           (labels[:, 0], labels[:, 1], labels[:, 2]),
                           zonation_targets)
        
        # Backward pass
        loss_dict['total'].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        # Accumulate losses
        total_loss += loss_dict['total'].item()
        for key in losses:
            losses[key] += loss_dict[key].item()
            
        if batch_idx % 10 == 0:
            print(f"  Batch {batch_idx}/{len(dataloader)} - Loss: {loss_dict['total'].item():.4f}")
    
    # Average losses
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
            
            # Forward pass
            predictions = model(spatial, temporal)
            
            # Create zonation targets
            batch_size = spatial.size(0)
            zonation_targets = labels.unsqueeze(-1).unsqueeze(-1).repeat(1, 1, 64, 64) * 0.5
            
            # Compute loss
            loss_dict = criterion(predictions,
                               (labels[:, 0], labels[:, 1], labels[:, 2]),
                               zonation_targets)
            
            total_loss += loss_dict['total'].item()
            
            # Collect predictions for metrics
            flood_pred, landslide_pred, cold_wave_pred, _ = predictions
            all_predictions.append(torch.cat([flood_pred, landslide_pred, cold_wave_pred], dim=1).cpu())
            all_labels.append(labels.cpu())
    
    # Calculate metrics
    predictions = torch.cat(all_predictions)
    labels = torch.cat(all_labels)
    
    # AUC-ROC approximation
    metrics = calculate_metrics(predictions.numpy(), labels.numpy())
    metrics['loss'] = total_loss / len(dataloader)
    
    return metrics


def calculate_metrics(predictions: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    """Calculate evaluation metrics"""
    metrics = {}
    
    for i, name in enumerate(['flood', 'landslide', 'cold_wave']):
        pred = predictions[:, i]
        true = labels[:, i]
        
        # Binary accuracy
        pred_binary = (pred > 0.5).astype(float)
        accuracy = (pred_binary == true).mean()
        
        # Precision, Recall, F1
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
    
    # Also save as latest
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
    model_size: str = 'small'
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
    print()
    
    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    
    # Create model
    model_config = MODEL_CONFIGS[model_size]
    model = get_model(model_config)
    model = model.to(device)
    
    # Count parameters
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {num_params:,}")
    
    # Generate synthetic dataset
    print("\nGenerating synthetic training data...")
    generator = SyntheticDisasterGenerator()
    weather_data, labels = generator.generate_dataset(num_samples)
    
    # Split train/val
    split_idx = int(num_samples * 0.8)
    train_weather = weather_data[:split_idx]
    train_labels = labels[:split_idx]
    val_weather = weather_data[split_idx:]
    val_labels = labels[split_idx:]
    
    print(f"Training samples: {len(train_weather)}")
    print(f"Validation samples: {len(val_weather)}")
    
    # Create datasets
    train_dataset = DisasterDataset(
        train_weather, train_labels,
        sequence_length=CONFIG['sequence_length'],
        grid_size=model_config['grid_size']
    )
    val_dataset = DisasterDataset(
        val_weather, val_labels,
        sequence_length=CONFIG['sequence_length'],
        grid_size=model_config['grid_size']
    )
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=CONFIG['num_workers'],
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=CONFIG['num_workers'],
        pin_memory=True
    )
    
    # Loss and optimizer
    criterion = HawkesProcessLoss()
    optimizer = optim.AdamW(
        model.parameters(),
        lr=CONFIG['learning_rate'],
        weight_decay=CONFIG['weight_decay']
    )
    scheduler = CosineAnnealingWarmRestarts(
        optimizer, T_0=10, T_mult=2
    )
    
    # Training loop
    best_val_loss = float('inf')
    patience_counter = 0
    
    print("\nStarting training...")
    print("-" * 60)
    
    for epoch in range(epochs):
        print(f"\nEpoch {epoch + 1}/{epochs}")
        print("-" * 40)
        
        # Train
        train_losses = train_epoch(model, train_loader, criterion, optimizer, device, epoch)
        scheduler.step()
        
        # Evaluate
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
        
        # Save checkpoint
        checkpoint_dir = Path(CONFIG['checkpoint_dir'])
        save_checkpoint(model, optimizer, epoch, val_metrics, checkpoint_dir)
        
        # Early stopping
        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            patience_counter = 0
            print("  -> New best model!")
        else:
            patience_counter += 1
            if patience_counter >= CONFIG['early_stopping_patience']:
                print(f"\nEarly stopping triggered after {epoch + 1} epochs")
                break
        
        # Training time check
        elapsed = epoch * 0.5  # Approximate seconds per epoch
        if elapsed >= 3600:  # 1 hour limit
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
    
    args = parser.parse_args()
    
    model = train(
        num_samples=args.samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        model_size=args.model_size
    )
