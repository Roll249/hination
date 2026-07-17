"""
Hination FastAPI Server
集成 ML Model Inference với API endpoints
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Add model path
sys.path.insert(0, str(Path(__file__).parent.parent / 'model'))
from model import get_model, MODEL_CONFIGS

# Lazy load model to avoid slow startup
_model = None
_predictor = None


def get_predictor():
    """Lazy load predictor"""
    global _predictor
    if _predictor is None:
        from api.model_inference import DisasterPredictor
        _predictor = DisasterPredictor()
    return _predictor


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="HINATION API",
    description="Hệ thống Cảnh Báo Thiên Tai Điện Biên",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request/Response Models
# ============================================================

class WeatherInput(BaseModel):
    temperature_c: float
    humidity_percent: float
    precipitation_mm: float
    wind_speed_kmh: float
    pressure_hpa: Optional[float] = 1013
    cloud_cover_percent: Optional[float] = 50


class DistrictInput(BaseModel):
    district_id: str
    name: str
    lat: float
    lon: float
    weather: WeatherInput


# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "service": "HINATION API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.post("/api/ml/predict")
async def predict_disaster(weather: WeatherInput):
    """
    Dự đoán thiên tai dựa trên thời tiết
    
    Returns:
        - overall_risk: Mức rủi ro tổng hợp (1-5)
        - risks: Chi tiết từng loại rủi ro
        - warnings: Cảnh báo
    """
    try:
        predictor = get_predictor()
        
        # Convert to dict
        weather_data = {
            'current': {
                'temperature_c': weather.temperature_c,
                'humidity_percent': weather.humidity_percent,
                'precipitation_mm': weather.precipitation_mm,
                'wind_speed_kmh': weather.wind_speed_kmh,
            }
        }
        
        result = predictor.predict(weather_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/predict-districts")
async def predict_districts(districts: List[DistrictInput]):
    """
    Dự đoán cho nhiều huyện
    
    Args:
        districts: List of districts with weather data
        
    Returns:
        Predictions for all districts
    """
    try:
        predictor = get_predictor()
        
        districts_data = {}
        for d in districts:
            districts_data[d.district_id] = {
                'name': d.name,
                'lat': d.lat,
                'lon': d.lon,
                'current': {
                    'temperature_c': d.weather.temperature_c,
                    'humidity_percent': d.weather.humidity_percent,
                    'precipitation_mm': d.weather.precipitation_mm,
                    'wind_speed_kmh': d.weather.wind_speed_kmh,
                }
            }
        
        results = predictor.predict_districts(districts_data)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'num_districts': len(results),
            'predictions': results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/status")
async def model_status():
    """Get ML model status"""
    try:
        predictor = get_predictor()
        checkpoint = predictor.checkpoint_path
        
        return {
            'model_loaded': True,
            'checkpoint': str(checkpoint),
            'device': str(predictor.device),
            'model_size': 'small',
            'config': MODEL_CONFIGS['small']
        }
    except Exception as e:
        return {
            'model_loaded': False,
            'error': str(e)
        }


@app.get("/api/districts")
async def get_districts():
    """Get list of districts in Điện Biên"""
    return {
        'districts': [
            {'id': 'dien_bien_phu', 'name': 'TP Điện Biên Phủ', 'lat': 21.3869, 'lon': 103.0228},
            {'id': 'tuan_giao', 'name': 'Huyện Tuần Giáo', 'lat': 21.6167, 'lon': 103.25},
            {'id': 'tua_chua', 'name': 'Huyện Tủa Chùa', 'lat': 21.4667, 'lon': 103.4333},
            {'id': 'muong_cha', 'name': 'Huyện Mường Chà', 'lat': 22.0833, 'lon': 102.4333},
            {'id': 'muong_nhe', 'name': 'Huyện Mường Nhé', 'lat': 22.4167, 'lon': 102.3},
            {'id': 'dien_bien_dong', 'name': 'Huyện Điện Biên Đông', 'lat': 21.1833, 'lon': 103.55},
            {'id': 'nam_po', 'name': 'Huyện Nậm Pồ', 'lat': 21.65, 'lon': 103.1167},
            {'id': 'muong_ang', 'name': 'Huyện Mường Ảng', 'lat': 21.8167, 'lon': 103.0833},
            {'id': 'muong_lay', 'name': 'Thị xã Mường Lay', 'lat': 22.5, 'lon': 102.6833},
        ]
    }


@app.get("/api/weather/{district_id}")
async def get_weather(district_id: str):
    """Get current weather for a district"""
    import urllib.request
    
    districts = {
        'dien_bien_phu': (21.3869, 103.0228),
        'tuan_giao': (21.6167, 103.25),
        'tua_chua': (21.4667, 103.4333),
        'muong_cha': (22.0833, 102.4333),
        'muong_nhe': (22.4167, 102.3),
        'dien_bien_dong': (21.1833, 103.55),
        'nam_po': (21.65, 103.1167),
        'muong_ang': (21.8167, 103.0833),
        'muong_lay': (22.5, 102.6833),
    }
    
    if district_id not in districts:
        raise HTTPException(status_code=404, detail="District not found")
    
    lat, lon = districts[district_id]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&hourly=temperature_2m,precipitation&timezone=Asia/Ho_Chi_Minh&forecast_days=1"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        current = data.get('current', {})
        current_units = data.get('current_units', {})
        
        return {
            'district_id': district_id,
            'timestamp': data.get('current_time'),
            'temperature_c': current.get('temperature_2m'),
            'humidity_percent': current.get('relative_humidity_2m'),
            'precipitation_mm': current.get('precipitation'),
            'wind_speed_kmh': current.get('wind_speed_10m'),
            'weather_code': current.get('weather_code'),
            'units': {
                'temperature': current_units.get('temperature_2m'),
                'humidity': '%',
                'precipitation': current_units.get('precipitation'),
                'wind': current_units.get('wind_speed_10m')
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/full")
async def get_full_risk_assessment():
    """Get full risk assessment for all districts with ML predictions"""
    import urllib.request
    
    districts = {
        'dien_bien_phu': {'name': 'TP Điện Biên Phủ', 'lat': 21.3869, 'lon': 103.0228},
        'tuan_giao': {'name': 'Huyện Tuần Giáo', 'lat': 21.6167, 'lon': 103.25},
        'tua_chua': {'name': 'Huyện Tủa Chùa', 'lat': 21.4667, 'lon': 103.4333},
        'muong_cha': {'name': 'Huyện Mường Chà', 'lat': 22.0833, 'lon': 102.4333},
        'muong_nhe': {'name': 'Huyện Mường Nhé', 'lat': 22.4167, 'lon': 102.3},
        'dien_bien_dong': {'name': 'Huyện Điện Biên Đông', 'lat': 21.1833, 'lon': 103.55},
        'nam_po': {'name': 'Huyện Nậm Pồ', 'lat': 21.65, 'lon': 103.1167},
        'muong_ang': {'name': 'Huyện Mường Ảng', 'lat': 21.8167, 'lon': 103.0833},
        'muong_lay': {'name': 'Thị xã Mường Lay', 'lat': 22.5, 'lon': 102.6833},
    }
    
    results = {}
    predictor = get_predictor()
    
    for district_id, info in districts.items():
        try:
            lat, lon = info['lat'], info['lon']
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,precipitation&timezone=Asia/Ho_Chi_Minh&forecast_days=1"
            
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            current = data.get('current', {})
            hourly = data.get('hourly', {})
            
            # Create weather data
            hourly_list = []
            for i in range(min(24, len(hourly.get('time', [])))):
                hourly_list.append({
                    'temperature_2m': hourly['temperature_2m'][i] if i < len(hourly.get('temperature_2m', [])) else 25,
                    'humidity': hourly['relative_humidity_2m'][i] if i < len(hourly.get('relative_humidity_2m', [])) else 70,
                    'precipitation': hourly['precipitation'][i] if i < len(hourly.get('precipitation', [])) else 0,
                    'wind_speed': current.get('wind_speed_10m', 10),
                    'pressure': 1013,
                    'cloud_cover': 50,
                })
            
            weather_data = {
                'name': info['name'],
                'current': {
                    'temperature_c': current.get('temperature_2m', 25),
                    'humidity_percent': current.get('relative_humidity_2f', 70),
                    'precipitation_mm': current.get('precipitation', 0),
                    'wind_speed_kmh': current.get('wind_speed_10m', 10),
                },
                'hourly': hourly_list
            }
            
            # Predict
            prediction = predictor.predict(weather_data)
            
            results[district_id] = {
                'name': info['name'],
                'coordinates': {'lat': lat, 'lon': lon},
                'weather': weather_data['current'],
                'prediction': prediction
            }
            
        except Exception as e:
            results[district_id] = {
                'name': info['name'],
                'error': str(e)
            }
    
    return {
        'timestamp': datetime.now().isoformat(),
        'province': 'Điện Biên',
        'num_districts': len(results),
        'districts': results
    }


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print("=" * 50)
    print("HINATION API Server")
    print("Starting on http://localhost:8000")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        reload=False
    )
