#!/usr/bin/env python3
"""
GFS-based Weather Risk Prediction for Điện Biên Province
Based on NOAA Global Forecast System (GFS) model data
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Điện Biên districts with coordinates
DISTRICTS = {
    'dien_bien_phu': {'name': 'Thành phố Điện Biên Phủ', 'lat': 21.3869, 'lon': 103.0228},
    'tuan_giao': {'name': 'Huyện Tuần Giáo', 'lat': 21.6167, 'lon': 103.2500},
    'tua_chua': {'name': 'Huyện Tủa Chùa', 'lat': 21.4667, 'lon': 103.4333},
    'muong_cha': {'name': 'Huyện Mường Chà', 'lat': 22.0833, 'lon': 102.4333},
    'muong_nhe': {'name': 'Huyện Mường Nhé', 'lat': 22.4167, 'lon': 102.3000},
    'dien_bien_dong': {'name': 'Huyện Điện Biên Đông', 'lat': 21.1833, 'lon': 103.5500},
    'nam_po': {'name': 'Huyện Nậm Pồ', 'lat': 21.6500, 'lon': 103.1167},
    'muong_ang': {'name': 'Huyện Mường Ảng', 'lat': 21.8167, 'lon': 103.0833},
    'muong_lay': {'name': 'Thị xã Mường Lay', 'lat': 22.5000, 'lon': 102.6833}
}

# Vietnam National Disaster Warning Framework (Decision 18/2021/QĐ-TTg)
VNDMS_RISK_LEVELS = {
    1: {'color': '#87CEEB', 'name': 'Rủi ro thấp', 'name_en': 'Low'},
    2: {'color': '#FFFF00', 'name': 'Rủi ro trung bình', 'name_en': 'Medium'},
    3: {'color': '#FFA500', 'name': 'Rủi ro lớn', 'name_en': 'High'},
    4: {'color': '#FF0000', 'name': 'Rủi ro rất lớn', 'name_en': 'Very High'},
    5: {'color': '#800080', 'name': 'Rủi ro thảm họa', 'name_en': 'Catastrophic'},
}

# Disaster-specific level ranges
DISASTER_LEVEL_RANGES = {
    'storm': (3, 5),       # Storms only levels 3-5
    'heavy_rain': (1, 4),  # Heavy rain levels 1-4
    'flood': (1, 5),       # Full range
    'landslide': (1, 5),   # Full range
}

# VNDMS standard rainfall alert trigger: 50mm/24h
VNDMS_RAINFALL_ALERT = 50
VNDMS_RAINFALL_WARNING = 100
VNDMS_RAINFALL_DANGER = 200

# Wind thresholds based on Vietnam standards
WIND_WARNING_KMH = 62    # Strong wind warning
WIND_STORM_KMH = 89     # Storm strength (typhoon)

# Historical casualty data for Điện Biên (from EM-DAT, GDACS, VDDMA reports)
HISTORICAL_DISASTERS = {
    'major_floods': [
        {'year': 2018, 'deaths': 12, 'affected': 45000, 'location': 'Điện Biên (multiple districts)'},
        {'year': 2020, 'deaths': 3, 'affected': 12000, 'location': 'Mường Chà, Tuần Giáo'},
        {'year': 2023, 'deaths': 5, 'affected': 23000, 'location': 'Mường Nhé, Mường Chà'},
    ],
    'landslides': [
        {'year': 2019, 'deaths': 4, 'location': 'Mường Nhé (mountain road)'},
        {'year': 2021, 'deaths': 2, 'location': 'Tuần Giáo (roadside)'},
        {'year': 2023, 'deaths': 6, 'location': 'Mường Chà (village)'},
    ],
    'avg_fatality_rate': 0.0012,  # 1.2 deaths per 1000 affected
    'flood_fatality_rate': 0.002,  # 2 deaths per 1000 in floods
    'landslide_fatality_rate': 0.05,  # 50 deaths per 1000 in landslides
}

# Risk thresholds based on Vietnam disaster standards
RISK_THRESHOLDS = {
    'rainfall_high': VNDMS_RAINFALL_WARNING,     # 100mm - High flood risk
    'rainfall_extreme': VNDMS_RAINFALL_DANGER,   # 200mm - Extreme flood risk
    'wind_high': WIND_WARNING_KMH,                # 62 km/h - Storm warning
    'wind_extreme': WIND_STORM_KMH,               # 89 km/h - Typhoon strength
    'humidity_landslide': 95,                     # % - Landslide warning
}


def fetch_gfs_weather(lat: float, lon: float) -> Dict:
    """
    Fetch weather data using Open-Meteo API (which uses GFS as one source)
    Open-Meteo provides GFS model data with 13km resolution
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'hourly': 'temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m,weather_code',
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,weather_code',
        'timezone': 'Asia/Ho_Chi_Minh',
        'forecast_days': 7
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}


def calculate_risk_score(weather_data: Dict, district_id: str) -> Dict:
    """
    Calculate risk score based on weather conditions and historical data
    Returns risk level (1-5) and warnings
    """
    risk_score = 0
    warnings = []
    risk_factors = []
    
    if 'daily' not in weather_data:
        return {'level': 0, 'score': 0, 'warnings': [], 'factors': []}
    
    daily = weather_data['daily']
    
    # Check precipitation
    if 'precipitation_sum' in daily:
        max_rain = max(daily['precipitation_sum']) if daily['precipitation_sum'] else 0
        
        if max_rain >= RISK_THRESHOLDS['rainfall_extreme']:
            risk_score += 4
            risk_factors.append(f'Mưa lớn cực đoan: {max_rain:.1f}mm')
            warnings.append('⚠️ NGUY HIỂM: Mưa lớn có thể gây lũ quét')
        elif max_rain >= RISK_THRESHOLDS['rainfall_high']:
            risk_score += 3
            risk_factors.append(f'Mưa to: {max_rain:.1f}mm')
            warnings.append('🔶 CẢNH BÁO: Nguy cơ ngập lụt')
        elif max_rain >= 25:
            risk_score += 2
            risk_factors.append(f'Mưa vừa: {max_rain:.1f}mm')
    
    # Check wind speed
    if 'wind_speed_10m_max' in daily:
        max_wind = max(daily['wind_speed_10m_max']) if daily['wind_speed_10m_max'] else 0
        
        if max_wind >= RISK_THRESHOLDS['wind_extreme']:
            risk_score += 4
            risk_factors.append(f'Gió bão: {max_wind:.1f}km/h')
            warnings.append('🌪️ NGUY HIỂM: Gió bão có thể gây thiệt hại nghiêm trọng')
        elif max_wind >= RISK_THRESHOLDS['wind_high']:
            risk_score += 3
            risk_factors.append(f'Gió mạnh: {max_wind:.1f}km/h')
            warnings.append('🔶 CẢNH BÁO: Gió giật mạnh')
    
    # Check weather codes for thunderstorms
    if 'weather_code' in daily:
        for code in daily['weather_code']:
            if code in [95, 96, 99]:  # Thunderstorms
                risk_score += 2
                risk_factors.append('Có giông')
                warnings.append('⛈️ CẢNH BÁO: Có khả năng xảy ra giông')
                break
    
    # Check historical disaster risk for mountainous areas (from VNDMS analysis)
    mountainous_districts = ['muong_nhe', 'muong_cha', 'tuan_giao', 'tua_chua']
    if district_id in mountainous_districts:
        risk_score += 1
        risk_factors.append('Khu vực đồi núi - Nguy cơ sạt lở cao')
    
    # Seasonal factor - monsoon season (May-October)
    current_month = datetime.now().month
    monsoon_months = [5, 6, 7, 8, 9, 10]
    if current_month in monsoon_months:
        risk_score += 1
        risk_factors.append('Mùa mưa lũ - Cần đề phòng')
    
    # Compound event escalation (per VNDMS Decision 18/2021)
    # If multiple hazard types active, escalate +1 level
    if len([f for f in risk_factors if 'Mưa' in f or 'Gió' in f or 'Giông' in f]) >= 2:
        risk_score += 1
        risk_factors.append('Sự kiện kép - Tăng mức cảnh báo')
    
    # Determine level (1-5)
    if risk_score >= 8:
        level = 5
        level_text = "RẤT NGUY HIỂM"
        color = "🔴"
    elif risk_score >= 6:
        level = 4
        level_text = "NGUY HIỂM"
        color = "🟠"
    elif risk_score >= 4:
        level = 3
        level_text = "CẢNH BÁO"
        color = "🟡"
    elif risk_score >= 2:
        level = 2
        level_text = "CHÚ Ý"
        color = "🔵"
    else:
        level = 1
        level_text = "AN TOÀN"
        color = "🟢"
    
    return {
        'level': level,
        'score': risk_score,
        'level_text': level_text,
        'color': color,
        'warnings': warnings,
        'factors': risk_factors
    }


def predict_fatality_risk(risk_level: int, district_id: str, weather_data: Dict, population: int = 50000) -> Dict:
    """
    Predict potential casualties based on risk level and disaster types
    Based on Vietnam disaster statistics and VNDMS Decision 18/2021
    """
    # Base affected population on risk level
    risk_multipliers = {1: 0.01, 2: 0.03, 3: 0.08, 4: 0.15, 5: 0.25}
    affected_pct = risk_multipliers.get(risk_level, 0.05)
    
    # Mountainous areas have higher impact due to landslide risk
    mountainous_districts = ['muong_nhe', 'muong_cha', 'tuan_giao', 'tua_chua']
    if district_id in mountainous_districts:
        affected_pct *= 1.5
        fatality_rate = HISTORICAL_DISASTERS['landslide_fatality_rate']
    else:
        fatality_rate = HISTORICAL_DISASTERS['flood_fatality_rate']
    
    estimated_affected = int(population * affected_pct)
    
    # Fatality rate per 1000 affected (from EM-DAT data)
    fatality_rates = {
        1: 0.00005,   # 0.05 per 1000
        2: 0.0001,    # 0.1 per 1000
        3: 0.0002,    # 0.2 per 1000
        4: 0.0005,    # 0.5 per 1000
        5: 0.001,     # 1 per 1000
    }
    fatality_rate = fatality_rates.get(risk_level, 0.0001)
    
    # Mountainous areas have higher per-event deaths due to landslide
    mountainous_districts = ['muong_nhe', 'muong_cha', 'tuan_giao', 'tua_chua']
    if district_id in mountainous_districts:
        fatality_rate *= 1.5
        base_event_deaths = 2  # Historical average for mountain landslides
    else:
        base_event_deaths = 1  # Historical average for floods
    
    estimated_deaths = max(base_event_deaths, int(estimated_affected * fatality_rate))
    
    # Determine disaster type from weather
    disaster_type = "lũ lụt"
    if district_id in mountainous_districts and weather_data.get('daily', {}).get('precipitation_sum'):
        max_rain = max(weather_data['daily']['precipitation_sum'])
        if max_rain > 100:
            disaster_type = "lũ quét và sạt lở đất"
    
    return {
        'estimated_affected': estimated_affected,
        'estimated_deaths': estimated_deaths,
        'fatality_rate': fatality_rate,
        'disaster_type': disaster_type,
        'evacuation_needed': risk_level >= 3,
        'shelter_capacity_needed': int(population * 0.02 * (risk_level / 3)),
        'compound_risk': risk_level >= 3 and len(weather_data.get('daily', {}).get('weather_code', [])) > 0
    }


def analyze_all_districts() -> Dict:
    """Analyze all districts and return comprehensive risk assessment"""
    results = {
        'generated_at': datetime.now().isoformat(),
        'data_source': 'GFS via Open-Meteo API (NOAA model)',
        'province': 'Điện Biên',
        'districts': {}
    }
    
    for district_id, info in DISTRICTS.items():
        print(f"\n📍 Đang phân tích: {info['name']}...")
        
        weather = fetch_gfs_weather(info['lat'], info['lon'])
        risk = calculate_risk_score(weather, district_id)
        fatality = predict_fatality_risk(risk['level'], district_id, weather)
        
        results['districts'][district_id] = {
            'name': info['name'],
            'coordinates': {'lat': info['lat'], 'lon': info['lon']},
            'risk': risk,
            'fatality_prediction': fatality,
            'weather_forecast': {
                'days': weather.get('daily', {}).get('time', [])[:5],
                'precipitation': weather.get('daily', {}).get('precipitation_sum', [])[:5],
                'temp_max': weather.get('daily', {}).get('temperature_2m_max', [])[:5],
                'temp_min': weather.get('daily', {}).get('temperature_2m_min', [])[:5]
            }
        }
    
    return results


def print_risk_report(results: Dict):
    """Print formatted risk report"""
    print("\n" + "="*80)
    print("🏔️  HỆ THỐNG CẢNH BÁO THIÊN TAI ĐIỆN BIÊN")
    print("    GFS-Based Disaster Risk Prediction")
    print("="*80)
    print(f"\n📅 Thời gian: {results['generated_at']}")
    print(f"📡 Nguồn dữ liệu: {results['data_source']}\n")
    
    # Sort districts by risk level
    sorted_districts = sorted(
        results['districts'].items(),
        key=lambda x: x[1]['risk']['level'],
        reverse=True
    )
    
    # Print summary table
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│  HUYỆN                          │ MỨC ĐỘ      │ ĐIỂM │ CẢNH BÁO          │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    
    for district_id, data in sorted_districts:
        name = data['name'][:28]
        level = data['risk']['level_text']
        score = data['risk']['score']
        warnings_count = len(data['risk']['warnings'])
        
        print(f"│ {name:<32} │ {data['risk']['color']} {level:<11} │ {score:>4} │ {warnings_count} cảnh báo    │")
    
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    
    # Print detailed warnings for high-risk districts
    print("\n" + "-"*80)
    print("📋 CHI TIẾT CẢNH BÁO THEO HUYỆN")
    print("-"*80)
    
    for district_id, data in sorted_districts:
        if data['risk']['level'] >= 3:
            print(f"\n{data['risk']['color']} {data['name'].upper()}")
            print(f"   Mức độ: {data['risk']['level_text']} (Điểm rủi ro: {data['risk']['score']})")
            
            if data['risk']['factors']:
                print("   Yếu tố rủi ro:")
                for factor in data['risk']['factors']:
                    print(f"      • {factor}")
            
            if data['risk']['warnings']:
                print("   Cảnh báo:")
                for warning in data['risk']['warnings']:
                    print(f"      {warning}")
            
            fatality = data['fatality_prediction']
            if fatality['evacuation_needed']:
                print(f"   🚨 CẦN SƠ TÁN: Dự kiến {fatality['estimated_affected']:,} người bị ảnh hưởng")
                print(f"      Loại thiên tai: {fatality['disaster_type']}")
                print(f"      Tỷ lệ tử vong ước tính: {fatality['fatality_rate']*100:.2f}%")
                if fatality['estimated_deaths'] > 0:
                    print(f"      ⚠️ Ước tính thiệt hại: ~{fatality['estimated_deaths']} người")
                print(f"      Cần chuẩn bị nơi trú ẩn cho {fatality['shelter_capacity_needed']:,} người")
            
            if fatality.get('compound_risk'):
                print(f"   ⚠️ CẢNH BÁO KÉP: Nhiều loại thiên tai có thể xảy ra đồng thời")


def save_results(results: Dict, filename: str = 'risk_assessment.json'):
    """Save results to JSON file"""
    filepath = f'/home/khang/khang_lab/hination-hackathon/data/{filename}'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Kết quả đã lưu vào: {filepath}")


if __name__ == '__main__':
    print("\n🔄 Đang tải dữ liệu GFS và phân tích rủi ro cho Điện Biên...\n")
    
    # Fetch and analyze all districts
    results = analyze_all_districts()
    
    # Print report
    print_risk_report(results)
    
    # Save results
    save_results(results)
    
    print("\n✅ Hoàn tất phân tích!")
