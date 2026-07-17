"""
Hination Model Inference API
Dự đoán thiên tai sử dụng trained model
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn.functional as F

# Add model to path
model_path = Path(__file__).parent.parent / 'model'
sys.path.insert(0, str(model_path))
from model import DisasterPredictionModel, get_model, MODEL_CONFIGS


# ============================================================
# Model Inference Class
# ============================================================

class DisasterPredictor:
    """Dự đoán thiên tai sử dụng trained model"""
    
    def __init__(self, checkpoint_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
        # Load model
        if checkpoint_path is None:
            checkpoint_path = Path(__file__).parent.parent / 'model' / 'checkpoints' / 'latest.pt'
        
        self.checkpoint_path = Path(checkpoint_path)
        self.model = self._load_model()
        
        # Preprocessor
        self.preprocessor = WeatherPreprocessor()
        
        print("Model loaded successfully!")
    
    def _load_model(self) -> DisasterPredictionModel:
        """Load trained model from checkpoint"""
        checkpoint = torch.load(self.checkpoint_path, map_location=self.device, weights_only=False)
        
        # Create model with default config
        model = get_model(MODEL_CONFIGS['small'])
        model.load_state_dict(checkpoint['model_state_dict'])
        model = model.to(self.device)
        model.eval()
        
        print(f"Loaded checkpoint from epoch {checkpoint['epoch']}")
        print(f"Metrics: {checkpoint.get('metrics', {})}")
        
        return model
    
    def preprocess_weather(self, weather_data: Dict) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Convert weather data to model input format
        
        Args:
            weather_data: Dict with weather information
            
        Returns:
            spatial: (1, 4, 64, 64) tensor
            temporal: (1, 24, 8) tensor
        """
        # Create spatial grid
        spatial = np.zeros((4, 64, 64))
        
        # Get current weather values
        if 'current' in weather_data:
            current = weather_data['current']
            rainfall = current.get('precipitation_mm', 0)
            temp = current.get('temperature_c', 25)
            humidity = current.get('humidity_percent', 70)
            wind = current.get('wind_speed_kmh', 10)
        else:
            rainfall = weather_data.get('precipitation', 0)
            temp = weather_data.get('temperature_2m', 25)
            humidity = weather_data.get('humidity', 70)
            wind = weather_data.get('wind_speed', 10)
        
        spatial[0] = self.preprocessor.normalize_rainfall(rainfall)
        spatial[1] = self.preprocessor.normalize_temperature(temp)
        spatial[2] = self.preprocessor.normalize_humidity(humidity)
        spatial[3] = self.preprocessor.normalize_wind(wind)
        
        # Create temporal sequence
        temporal = np.zeros((24, 8))
        
        # Use forecast or current values to create sequence
        hourly_data = weather_data.get('hourly', [weather_data] * 24)
        
        for i in range(min(24, len(hourly_data))):
            h = hourly_data[i] if i < len(hourly_data) else hourly_data[-1]
            
            temporal[i, 0] = self.preprocessor.normalize_rainfall(h.get('precipitation', 0))
            temporal[i, 1] = self.preprocessor.normalize_temperature(h.get('temperature_2m', temp))
            temporal[i, 2] = self.preprocessor.normalize_humidity(h.get('humidity', humidity))
            temporal[i, 3] = self.preprocessor.normalize_wind(h.get('wind_speed', wind))
            temporal[i, 4] = self.preprocessor.normalize_pressure(h.get('pressure', 1013))
            temporal[i, 5] = h.get('cloud_cover', 50) / 100.0
            temporal[i, 6] = min(h.get('hours_of_rain', 0) / 24.0, 1)
            temporal[i, 7] = min(h.get('consecutive_rain_hours', 0) / 48.0, 1)
        
        return (
            torch.FloatTensor(spatial).unsqueeze(0),
            torch.FloatTensor(temporal).unsqueeze(0)
        )
    
    def predict(self, weather_data: Dict) -> Dict:
        """
        Dự đoán rủi ro thiên tai
        
        Args:
            weather_data: Weather information dictionary
            
        Returns:
            Prediction results with risk levels
        """
        # Preprocess
        spatial, temporal = self.preprocess_weather(weather_data)
        spatial = spatial.to(self.device)
        temporal = temporal.to(self.device)
        
        # Predict
        with torch.no_grad():
            flood_prob, landslide_prob, cold_wave_prob, zonation_map = self.model(spatial, temporal)
        
        # Convert to numpy
        flood = flood_prob.item()
        landslide = landslide_prob.item()
        cold_wave = cold_wave_prob.item()
        
        # Calculate risk levels (1-5 scale like VNDMS)
        risk_levels = {
            'flood': self._prob_to_level(flood),
            'landslide': self._prob_to_level(landslide),
            'cold_wave': self._prob_to_level(cold_wave)
        }
        
        # Get overall risk level
        overall_risk = max(risk_levels.values())
        
        # Generate warnings based on risk
        warnings = self._generate_warnings(risk_levels, weather_data)
        
        # Get zonation map as heatmap data
        zonation_data = zonation_map.squeeze(0).cpu().numpy()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'model_version': 'v1.0',
            'overall_risk': overall_risk,
            'overall_risk_text': self._level_to_text(overall_risk),
            'risks': {
                'flood': {
                    'probability': round(flood, 4),
                    'level': risk_levels['flood'],
                    'level_text': self._level_to_text(risk_levels['flood'])
                },
                'landslide': {
                    'probability': round(landslide, 4),
                    'level': risk_levels['landslide'],
                    'level_text': self._level_to_text(risk_levels['landslide'])
                },
                'cold_wave': {
                    'probability': round(cold_wave, 4),
                    'level': risk_levels['cold_wave'],
                    'level_text': self._level_to_text(risk_levels['cold_wave'])
                }
            },
            'warnings': warnings,
            'zonation_heatmap': zonation_data.tolist(),
            'action_required': overall_risk >= 3
        }
    
    def predict_districts(self, districts_data: Dict) -> Dict:
        """
        Dự đoán cho nhiều huyện
        
        Args:
            districts_data: Dictionary of district weather data
            
        Returns:
            Predictions for all districts
        """
        results = {}
        
        for district_id, weather_data in districts_data.items():
            try:
                prediction = self.predict(weather_data)
                results[district_id] = {
                    'name': weather_data.get('name', district_id),
                    'prediction': prediction
                }
            except Exception as e:
                print(f"Error predicting for {district_id}: {e}")
                results[district_id] = {
                    'name': weather_data.get('name', district_id),
                    'error': str(e)
                }
        
        return results
    
    def _prob_to_level(self, prob: float) -> int:
        """Convert probability to VNDMS risk level (1-5)"""
        if prob < 0.2:
            return 1
        elif prob < 0.4:
            return 2
        elif prob < 0.6:
            return 3
        elif prob < 0.8:
            return 4
        else:
            return 5
    
    def _level_to_text(self, level: int) -> str:
        """Convert risk level to Vietnamese text"""
        texts = {
            1: 'AN TOÀN',
            2: 'CHÚ Ý',
            3: 'CẢNH BÁO',
            4: 'NGUY HIỂM',
            5: 'CẢNH BÁO CAO'
        }
        return texts.get(level, 'UNKNOWN')
    
    def _generate_warnings(self, risk_levels: Dict, weather_data: Dict) -> List[str]:
        """Generate warning messages based on risk levels"""
        warnings = []
        
        if risk_levels['flood'] >= 3:
            warnings.append("⚠️ CẢNH BÁO: Nguy cơ ngập lụt cao. Hạn chế di chuyển.")
        
        if risk_levels['landslide'] >= 3:
            warnings.append("⚠️ CẢNH BÁO: Nguy cơ sạt lở đất. Cẩn trọng vùng đồi núi.")
        
        if risk_levels['cold_wave'] >= 3:
            warnings.append("❄️ CẢNH BÁO: Sóng lạnh. Cần giữ ấm và bảo vệ cây trồng.")
        
        # Add weather-specific warnings
        if 'current' in weather_data:
            current = weather_data['current']
            if current.get('precipitation_mm', 0) > 15:
                warnings.append(f"🌧️ Mưa to: {current['precipitation_mm']:.1f}mm")
            if current.get('wind_speed_kmh', 0) > 40:
                warnings.append(f"💨 Gió mạnh: {current['wind_speed_kmh']:.1f}km/h")
            if current.get('temperature_c', 25) < 10:
                warnings.append(f"🌡️ Nhiệt độ thấp: {current['temperature_c']:.1f}°C")
        
        return warnings


class WeatherPreprocessor:
    """Preprocess weather data for model input"""
    
    def normalize_rainfall(self, value: float) -> float:
        return min(max(value / 100.0, 0), 1)
    
    def normalize_temperature(self, value: float) -> float:
        return max(0, min((value + 10) / 55.0, 1))
    
    def normalize_humidity(self, value: float) -> float:
        return value / 100.0
    
    def normalize_wind(self, value: float) -> float:
        return min(value / 100.0, 1)
    
    def normalize_pressure(self, value: float) -> float:
        return (value - 980) / 60.0


# ============================================================
# CLI Interface
# ============================================================

if __name__ == '__main__':
    import argparse
    import urllib.request
    
    parser = argparse.ArgumentParser(description='Hination Disaster Prediction')
    parser.add_argument('--lat', type=float, default=21.3869, help='Latitude')
    parser.add_argument('--lon', type=float, default=103.0228, help='Longitude')
    parser.add_argument('--checkpoint', type=str, help='Path to checkpoint')
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = DisasterPredictor(args.checkpoint)
    
    # Fetch weather data from Open-Meteo
    url = f"https://api.open-meteo.com/v1/forecast?latitude={args.lat}&longitude={args.lon}&hourly=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,pressure_msl,cloud_cover&timezone=Asia/Ho_Chi_Minh&forecast_days=1"
    
    try:
        print(f"Fetching weather data for ({args.lat}, {args.lon})...")
        with urllib.request.urlopen(url, timeout=10) as response:
            weather_data = json.loads(response.read().decode())
        
        # Extract hourly data
        hourly = weather_data.get('hourly', {})
        hourly_list = []
        for i in range(min(24, len(hourly.get('time', [])))):
            hourly_list.append({
                'time': hourly['time'][i],
                'temperature_2m': hourly['temperature_2m'][i],
                'humidity': hourly['relative_humidity_2m'][i],
                'precipitation': hourly['precipitation'][i],
                'wind_speed': hourly['wind_speed_10m'][i],
                'pressure': hourly['pressure_msl'][i],
                'cloud_cover': hourly['cloud_cover'][i],
                'weather_code': hourly['weather_code'][i]
            })
        
        # Create input data
        input_data = {
            'current': {
                'temperature_c': hourly_list[0]['temperature_2m'],
                'humidity_percent': hourly_list[0]['humidity'],
                'precipitation_mm': hourly_list[0]['precipitation'],
                'wind_speed_kmh': hourly_list[0]['wind_speed'],
            },
            'hourly': hourly_list
        }
        
        # Predict
        result = predictor.predict(input_data)
        
        print("\n" + "=" * 50)
        print("HINATION DISASTER PREDICTION RESULTS")
        print("=" * 50)
        print(f"Location: ({args.lat}, {args.lon})")
        print(f"Timestamp: {result['timestamp']}")
        print(f"\nOverall Risk: {result['overall_risk_text']} (Level {result['overall_risk']})")
        print("\nRisk Details:")
        for risk_type, data in result['risks'].items():
            emoji = {'flood': '🌊', 'landslide': '⛰️', 'cold_wave': '❄️'}[risk_type]
            print(f"  {emoji} {risk_type.capitalize()}: {data['level_text']} ({data['probability']:.2%})")
        
        if result['warnings']:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        print("\n" + "=" * 50)
        
        # Save result to file
        output_path = Path(__file__).parent.parent / 'data' / 'ml_predictions.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
