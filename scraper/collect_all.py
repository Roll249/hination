#!/usr/bin/env python3
"""
Hination - Comprehensive Data Collection System
Collects weather, disaster data for Dien Bien Province
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.weather_scraper import WeatherScraper, DIEN_BIEN_LOCATIONS
from scraper.weather_aggregator import WeatherAggregator, ALERT_THRESHOLDS, WEATHER_CODES


def _process_daily_forecast(daily_data, aggregator):
    """Process daily forecast data safely"""
    times = daily_data.get('time', [])
    forecast = []
    for i, date in enumerate(times):
        weather_code = daily_data.get('weather_code', [0]*len(times))[i] if i < len(times) else 0
        forecast.append({
            "date": date,
            "weather_description": aggregator.get_weather_description(weather_code),
            "temp_max": daily_data.get('temperature_2m_max', [None]*len(times))[i] if i < len(times) else None,
            "temp_min": daily_data.get('temperature_2m_min', [None]*len(times))[i] if i < len(times) else None,
            "precipitation_sum": daily_data.get('precipitation_sum', [None]*len(times))[i] if i < len(times) else None,
        })
    return forecast


def _get_next_update_time():
    """Get next update time (top of next hour)"""
    now = datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0)
    if next_hour <= now:
        next_hour += timedelta(hours=1)
    return next_hour.isoformat()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def collect_all_data() -> dict[str, Any]:
    """Collect all weather and disaster data"""
    logger.info("=" * 70)
    logger.info("HINATION - Weather & Disaster Data Collection System")
    logger.info("=" * 70)

    results = {
        "collection_time": datetime.now().isoformat(),
        "status": "success",
        "data_sources": [],
        "districts_collected": 0,
        "alerts_generated": 0,
        "files_created": []
    }

    # 1. Collect Open-Meteo data for all districts
    logger.info("\n[1/4] Collecting Open-Meteo weather data...")
    try:
        aggregator = WeatherAggregator()
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
            "fetched_at": datetime.now().isoformat(),
            "data_source": "Open-Meteo API",
            "districts": {}
        }

        all_alerts = []

        for district_id, info in districts.items():
            weather = aggregator.fetch_open_meteo(info['lat'], info['lon'], days=7)
            if weather:
                elevation = aggregator.fetch_elevation(info['lat'], info['lon'])
                alerts = aggregator.analyze_alerts(weather)

                current = weather.get('current', {})
                daily_data = weather.get('daily', {})

                all_data['districts'][district_id] = {
                    "name": info['name'],
                    "coordinates": {"lat": info['lat'], "lon": info['lon']},
                    "elevation_m": elevation,
                    "current": {
                        "temperature_c": current.get('temperature_2m'),
                        "humidity_percent": current.get('relative_humidity_2m'),
                        "precipitation_mm": current.get('precipitation'),
                        "weather_code": current.get('weather_code'),
                        "weather_description": aggregator.get_weather_description(current.get('weather_code', 0)),
                        "wind_speed_kmh": current.get('wind_speed_10m'),
                        "wind_direction_deg": current.get('wind_direction_10m'),
                    },
                    "daily_forecast": _process_daily_forecast(daily_data, aggregator),
                    "alerts": alerts
                }

                for alert in alerts:
                    all_alerts.append({
                        "district": info['name'],
                        "message": aggregator.format_alert_message(alert, info['name']),
                        **alert
                    })

                results["districts_collected"] += 1

            import time
            time.sleep(0.5)

        # Save weather data
        weather_path = DATA_DIR / "weather_comprehensive.json"
        with open(weather_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        results["files_created"].append(str(weather_path))
        results["data_sources"].append("Open-Meteo API")

        logger.info(f"✓ Collected weather data for {results['districts_collected']} districts")

    except Exception as e:
        logger.error(f"Error collecting weather data: {e}")
        results["status"] = "partial"

    # 2. Collect KTTV data
    logger.info("\n[2/4] Collecting KTTV Dien Bien data...")
    try:
        scraper = WeatherScraper()
        kttv_data = scraper.fetch_kttv_dien_bien()

        kttv_path = DATA_DIR / "raw" / f"kttv_dien_bien_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        kttv_path.parent.mkdir(parents=True, exist_ok=True)

        with open(kttv_path, 'w', encoding='utf-8') as f:
            json.dump(kttv_data, f, ensure_ascii=False, indent=2)

        results["files_created"].append(str(kttv_path))
        results["data_sources"].append("KTTV Website")
        logger.info(f"✓ Collected KTTV data")

    except Exception as e:
        logger.error(f"Error collecting KTTV data: {e}")

    # 3. Generate alerts summary
    logger.info("\n[3/4] Generating alerts summary...")
    try:
        if all_alerts:
            alerts_path = DATA_DIR / "alerts_current.json"
            with open(alerts_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "generated_at": datetime.now().isoformat(),
                    "total_alerts": len(all_alerts),
                    "alerts": all_alerts
                }, f, ensure_ascii=False, indent=2)
            results["files_created"].append(str(alerts_path))
            results["alerts_generated"] = len(all_alerts)
            logger.info(f"✓ Generated {len(all_alerts)} alerts")
    except Exception as e:
        logger.error(f"Error generating alerts: {e}")

    # 4. Generate summary report
    logger.info("\n[4/4] Generating summary report...")
    try:
        summary = {
            "report_time": datetime.now().isoformat(),
            "province": "Điện Biên",
            "collection_summary": results,
            "data_coverage": {
                "districts": results["districts_collected"],
                "total_districts": 9,
                "coverage_percent": round(results["districts_collected"] / 9 * 100, 1)
            },
            "alert_thresholds": {
                "heavy_rain": f">{ALERT_THRESHOLDS['heavy_rain']['precipitation_mm_per_hour']} mm/h",
                "extreme_rain": f">{ALERT_THRESHOLDS['extreme_rain']['precipitation_mm_per_hour']} mm/h",
                "cold_wave": f"<{ALERT_THRESHOLDS['cold_wave']['temperature_min_celsius']}°C",
                "strong_wind": f">{ALERT_THRESHOLDS['strong_wind']['wind_speed_kmh']} km/h",
            },
            "weather_codes": WEATHER_CODES,
            "next_update": _get_next_update_time()
        }

        summary_path = DATA_DIR / "collection_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        results["files_created"].append(str(summary_path))

    except Exception as e:
        logger.error(f"Error generating summary: {e}")

    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("COLLECTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Status: {results['status']}")
    logger.info(f"Districts collected: {results['districts_collected']}/9")
    logger.info(f"Alerts generated: {results['alerts_generated']}")
    logger.info(f"Data sources: {', '.join(results['data_sources'])}")
    logger.info(f"Files created: {len(results['files_created'])}")
    logger.info(f"\nFiles saved to: {DATA_DIR}")
    for f in results["files_created"]:
        logger.info(f"  - {Path(f).name}")

    return results


if __name__ == '__main__':
    collect_all_data()
