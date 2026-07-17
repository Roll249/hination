#!/usr/bin/env python3
"""
Weather Data Aggregator - Pulls data from multiple free sources
Part of Hination - AI Weather Warning System
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
ARCHIVE_DIR = DATA_DIR / "archive"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Weather code translations (WMO)
WEATHER_CODES = {
    0: "Trời quang",
    1: "Ít mây",
    2: "Nhiều mây",
    3: "U ám",
    45: "Sương mù",
    48: "Sương mù đóng băng",
    51: "Mưa phùn nhẹ",
    53: "Mưa phùn vừa",
    55: "Mưa phùn nặng",
    61: "Mưa nhẹ",
    63: "Mưa vừa",
    65: "Mưa to",
    71: "Tuyết nhẹ",
    73: "Tuyết vừa",
    75: "Tuyết to",
    80: "Mưa rào nhẹ",
    81: "Mưa rào vừa",
    82: "Mưa rào nặng",
    95: "Giông",
    96: "Giông kèm mưa đá nhẹ",
    99: "Giông kèm mưa đá nặng",
}

# Alert thresholds for Dien Bien region
ALERT_THRESHOLDS = {
    "heavy_rain": {
        "precipitation_mm_per_hour": 15,
        "severity": "warning",
        "action": "Cảnh báo lũ quét, sạt lở đất"
    },
    "extreme_rain": {
        "precipitation_mm_per_hour": 30,
        "severity": "danger",
        "action": "Nguy hiểm! Di dời ngay đến nơi an toàn"
    },
    "cold_wave": {
        "temperature_min_celsius": 5,
        "severity": "warning",
        "action": "Sương muối có thể gây hại cây trồng"
    },
    "frost": {
        "temperature_min_celsius": 0,
        "severity": "danger",
        "action": "Nguy hiểm! Bảo vệ gia súc, cây trồng"
    },
    "high_humidity": {
        "humidity_percent": 99,
        "severity": "info",
        "action": "Độ ẩm rất cao, cảnh giác sương mù"
    },
    "strong_wind": {
        "wind_speed_kmh": 40,
        "severity": "warning",
        "action": "Gió mạnh, tránh xa cây cao và công trình"
    },
    "storm": {
        "wind_speed_kmh": 62,
        "severity": "danger",
        "action": "Bão! Tìm nơi trú ẩn an toàn ngay"
    }
}


class WeatherAggregator:
    """Aggregates weather data from multiple sources"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Hination Weather System/1.0)'
        })

    def fetch_open_meteo(self, lat: float, lon: float, days: int = 7) -> dict[str, Any]:
        """Fetch comprehensive weather data from Open-Meteo API"""
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': [
                    'temperature_2m', 'relative_humidity_2m', 'apparent_temperature',
                    'precipitation', 'weather_code', 'cloud_cover',
                    'wind_speed_10m', 'wind_direction_10m', 'pressure_msl'
                ],
                'hourly': [
                    'temperature_2m', 'relative_humidity_2m', 'precipitation_probability',
                    'precipitation', 'weather_code', 'cloud_cover',
                    'wind_speed_10m', 'wind_gusts_10m', 'visibility'
                ],
                'daily': [
                    'weather_code', 'temperature_2m_max', 'temperature_2m_min',
                    'sunrise', 'sunset', 'precipitation_sum',
                    'precipitation_probability_max', 'wind_speed_10m_max'
                ],
                'timezone': 'Asia/Ho_Chi_Minh',
                'forecast_days': days
            }

            response = self.session.get(
                'https://api.open-meteo.com/v1/forecast',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error fetching Open-Meteo: {e}")
            return {}

    def fetch_elevation(self, lat: float, lon: float) -> float:
        """Get elevation data from Open-Meteo"""
        try:
            params = {
                'latitude': lat,
                'longitude': lon
            }
            response = self.session.get(
                'https://api.open-meteo.com/v1/elevation',
                params=params,
                timeout=10
            )
            data = response.json()
            return data.get('elevation', [0])[0] if data.get('elevation') else 0
        except Exception:
            return 0

    def analyze_alerts(self, weather_data: dict) -> list[dict]:
        """Analyze weather data and generate alerts"""
        alerts = []
        current = weather_data.get('current', {})

        temp = current.get('temperature_2m', 0)
        humidity = current.get('relative_humidity_2m', 0)
        wind_speed = current.get('wind_speed_10m', 0)
        precipitation = current.get('precipitation', 0)

        # Check thresholds
        for name, threshold in ALERT_THRESHOLDS.items():
            if name == "cold_wave" and temp <= threshold["temperature_min_celsius"]:
                alerts.append({
                    "type": name,
                    "severity": threshold["severity"],
                    "value": temp,
                    "unit": "°C",
                    "action": threshold["action"],
                    "timestamp": datetime.now().isoformat()
                })
            elif name == "extreme_rain" and precipitation >= threshold["precipitation_mm_per_hour"]:
                alerts.append({
                    "type": name,
                    "severity": threshold["severity"],
                    "value": precipitation,
                    "unit": "mm/h",
                    "action": threshold["action"],
                    "timestamp": datetime.now().isoformat()
                })
            elif name == "high_humidity" and humidity >= threshold["humidity_percent"]:
                alerts.append({
                    "type": name,
                    "severity": threshold["severity"],
                    "value": humidity,
                    "unit": "%",
                    "action": threshold["action"],
                    "timestamp": datetime.now().isoformat()
                })
            elif name == "storm" and wind_speed >= threshold["wind_speed_kmh"]:
                alerts.append({
                    "type": name,
                    "severity": threshold["severity"],
                    "value": wind_speed,
                    "unit": "km/h",
                    "action": threshold["action"],
                    "timestamp": datetime.now().isoformat()
                })

        return alerts

    def get_weather_description(self, code: int) -> str:
        """Get Vietnamese weather description from WMO code"""
        return WEATHER_CODES.get(code, f"Mã thời tiết {code}")

    def format_alert_message(self, alert: dict, location: str) -> str:
        """Format alert message for display/push"""
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "danger": "🚨"
        }

        emoji = severity_emoji.get(alert.get("severity", "info"), "ℹ️")

        messages = {
            "heavy_rain": f"{emoji} CẢNH BÁO MƯA LỚN tại {location}. Lượng mưa {alert['value']} mm/h. {alert['action']}",
            "extreme_rain": f"{emoji} NGUY HIỂM! Mưa rất lớn tại {location}. {alert['action']}",
            "cold_wave": f"{emoji} CẢNH BÁO LẠNH tại {location}. Nhiệt độ {alert['value']}°C. {alert['action']}",
            "frost": f"{emoji} NGUY HIỂM! Sương giá tại {location}. {alert['action']}",
            "high_humidity": f"{emoji} {location}: Độ ẩm {alert['value']}%. {alert['action']}",
            "strong_wind": f"{emoji} CẢNH BÁO GIÓ MẠNH tại {location}. Tốc độ {alert['value']} km/h. {alert['action']}",
            "storm": f"{emoji} BÃO! tại {location}. Gió {alert['value']} km/h. {alert['action']}"
        }

        return messages.get(alert.get("type"), f"{emoji} Cảnh báo thời tiết tại {location}")


def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("Weather Data Aggregator - Dien Bien Province")
    logger.info("=" * 60)

    aggregator = WeatherAggregator()

    # District locations
    districts = {
        "dien_bien_phu": {"lat": 21.3869, "lon": 103.0228, "name": "Thành phố Điện Biên Phủ"},
        "tuan_giao": {"lat": 21.6167, "lon": 103.2500, "name": "Huyện Tuần Giáo"},
        "tua_chua": {"lat": 21.4667, "lon": 103.4333, "name": "Huyện Tủa Chùa"},
        "muong_ang": {"lat": 21.8167, "lon": 103.0833, "name": "Huyện Mường Ảng"},
        "muong_cha": {"lat": 22.0833, "lon": 102.4333, "name": "Huyện Mường Chà"},
        "muong_nhe": {"lat": 22.4167, "lon": 102.3000, "name": "Huyện Mường Nhé"},
        "dien_bien_dong": {"lat": 21.1833, "lon": 103.5500, "name": "Huyện Điện Biên Đông"},
        "nam_po": {"lat": 21.6500, "lon": 103.1167, "name": "Huyện Nậm Pồ"},
        "muong_lay": {"lat": 22.5000, "lon": 102.6833, "name": "Thị xã Mường Lay"},
    }

    all_data = {
        "province": "Điện Biên",
        "province_code": "DienBien",
        "fetched_at": datetime.now().isoformat(),
        "data_source": "Open-Meteo API",
        "api_url": "https://api.open-meteo.com/v1/forecast",
        "districts": {}
    }

    alerts = []

    for district_id, info in districts.items():
        logger.info(f"Fetching data for {info['name']}...")

        # Get elevation
        elevation = aggregator.fetch_elevation(info['lat'], info['lon'])

        # Get weather data
        weather = aggregator.fetch_open_meteo(info['lat'], info['lon'], days=7)

        if weather:
            # Analyze for alerts
            district_alerts = aggregator.analyze_alerts(weather)

            # Format alerts
            formatted_alerts = []
            for alert in district_alerts:
                formatted_alerts.append({
                    "message": aggregator.format_alert_message(alert, info['name']),
                    **alert
                })
                alerts.append(formatted_alerts[-1])

            # Process daily forecast
            daily_forecast = []
            daily_data = weather.get('daily', {})
            times = daily_data.get('time', [])

            for i, date in enumerate(times):
                day = {
                    "date": date,
                    "weather_code": daily_data.get('weather_code', [None]*len(times))[i] if i < len(times) else None,
                    "weather_description": aggregator.get_weather_description(
                        daily_data.get('weather_code', [0]*len(times))[i] if i < len(times) else 0
                    ),
                    "temp_max": daily_data.get('temperature_2m_max', [None]*len(times))[i] if i < len(times) else None,
                    "temp_min": daily_data.get('temperature_2m_min', [None]*len(times))[i] if i < len(times) else None,
                    "precipitation_sum": daily_data.get('precipitation_sum', [None]*len(times))[i] if i < len(times) else None,
                    "precipitation_probability": daily_data.get('precipitation_probability_max', [None]*len(times))[i] if i < len(times) else None,
                    "wind_speed_max": daily_data.get('wind_speed_10m_max', [None]*len(times))[i] if i < len(times) else None,
                    "sunrise": daily_data.get('sunrise', [None]*len(times))[i] if i < len(times) else None,
                    "sunset": daily_data.get('sunset', [None]*len(times))[i] if i < len(times) else None,
                }
                daily_forecast.append(day)

            # Current conditions
            current = weather.get('current', {})

            all_data['districts'][district_id] = {
                "name": info['name'],
                "coordinates": {"lat": info['lat'], "lon": info['lon']},
                "elevation_m": elevation,
                "current": {
                    "time": current.get('time'),
                    "temperature_c": current.get('temperature_2m'),
                    "feels_like_c": current.get('apparent_temperature'),
                    "humidity_percent": current.get('relative_humidity_2m'),
                    "precipitation_mm": current.get('precipitation'),
                    "weather_code": current.get('weather_code'),
                    "weather_description": aggregator.get_weather_description(current.get('weather_code', 0)),
                    "cloud_cover_percent": current.get('cloud_cover'),
                    "wind_speed_kmh": current.get('wind_speed_10m'),
                    "wind_direction_deg": current.get('wind_direction_10m'),
                    "pressure_hpa": current.get('pressure_msl'),
                },
                "daily_forecast": daily_forecast,
                "alerts": district_alerts
            }

        time.sleep(1)  # Rate limiting

    # Save all data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = ARCHIVE_DIR / f"weather_aggregated_{timestamp}.json"

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    # Also save as latest
    latest_path = DATA_DIR / "weather_latest.json"
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    # Save alerts separately
    if alerts:
        alerts_path = DATA_DIR / "alerts_latest.json"
        with open(alerts_path, 'w', encoding='utf-8') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "count": len(alerts),
                "alerts": alerts
            }, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'='*60}")
    logger.info(f"Data Collection Complete!")
    logger.info(f"{'='*60}")
    logger.info(f"Total districts: {len(all_data['districts'])}")
    logger.info(f"Total alerts: {len(alerts)}")
    logger.info(f"Output: {filepath}")
    logger.info(f"Latest: {latest_path}")

    return all_data


if __name__ == '__main__':
    main()
