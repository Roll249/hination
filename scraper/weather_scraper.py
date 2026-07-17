#!/usr/bin/env python3
"""
Weather and Natural Disaster Data Scraper for Dien Bien Province
Part of Hination - AI Weather Warning System
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Geographic coordinates for Dien Bien districts
DIEN_BIEN_LOCATIONS = {
    "dien_bien_phu": {"lat": 21.3869, "lon": 103.0228, "district": "Điện Biên Phủ"},
    "dien_bien": {"lat": 21.2833, "lon": 103.3667, "district": "Điện Biên"},
    "tua_chua": {"lat": 21.4667, "lon": 103.4333, "district": "Tủa Chùa"},
    "tuan_giao": {"lat": 21.6167, "lon": 103.2500, "district": "Tuần Giáo"},
    "muong_ang": {"lat": 21.8167, "lon": 103.0833, "district": "Mường Ảng"},
    "muong_cha": {"lat": 22.0833, "lon": 102.4333, "district": "Mường Chà"},
    "muong_nhe": {"lat": 22.4167, "lon": 102.3000, "district": "Mường Nhé"},
    "dien_bien_dong": {"lat": 21.1833, "lon": 103.5500, "district": "Điện Biên Đông"},
    "nam_po": {"lat": 21.6500, "lon": 103.1167, "district": "Nậm Pồ"},
    "muong_lay": {"lat": 22.5000, "lon": 102.6833, "district": "Thị xã Mường Lay"},
}


class WeatherScraper:
    """Scraper for weather and natural disaster data"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache_duration = timedelta(hours=1)

    def _get_cache_path(self, source: str) -> Path:
        """Get cache file path for a source"""
        return CACHE_DIR / f"{source}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False
        cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - cache_time < self.cache_duration

    def save_to_cache(self, source: str, data: dict):
        """Save data to cache"""
        cache_path = self._get_cache_path(source)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'data': data
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"Cached data for {source}")

    def load_from_cache(self, source: str) -> dict | None:
        """Load data from cache if valid"""
        cache_path = self._get_cache_path(source)
        if self._is_cache_valid(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            logger.info(f"Loaded cached data for {source}")
            return cached['data']
        return None

    def fetch_kttv_dien_bien(self) -> dict[str, Any]:
        """Fetch weather data from Dien Bien KTTV station website"""
        logger.info("Fetching KTTV Dien Bien weather data...")

        # Check cache first
        cached = self.load_from_cache('kttv_dien_bien')
        if cached:
            return cached

        try:
            response = self.session.get(
                'https://kttvttb.vn/dien-bien',
                timeout=30
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            data = {
                'source': 'kttvttb.vn',
                'url': 'https://kttvttb.vn/dien-bien',
                'fetched_at': datetime.now().isoformat(),
                'location': 'Dien Bien',
                'current': {},
                'hourly': [],
                'air_quality': {},
                'districts': []
            }

            # Extract current weather data
            # This will vary based on actual page structure
            data['current'] = self._parse_kttv_current(soup)

            # Extract hourly forecast
            data['hourly'] = self._parse_kttv_hourly(soup)

            # Extract air quality
            data['air_quality'] = self._parse_kttv_air_quality(soup)

            # Save to file
            self._save_weather_data('kttv_dien_bien', data)

            return data

        except Exception as e:
            logger.error(f"Error fetching KTTV data: {e}")
            return {'error': str(e)}

    def _parse_kttv_current(self, soup: BeautifulSoup) -> dict:
        """Parse current weather conditions"""
        current = {}

        try:
            # Find temperature
            temp_elem = soup.find(string=re.compile(r'\d+°'))
            if temp_elem:
                current['temperature'] = temp_elem.strip()

            # Find weather condition
            condition_elem = soup.find(string=re.compile(r'Mưa|Nắng|Ngày|Đêm'))
            if condition_elem:
                current['condition'] = condition_elem.strip()

            # Find humidity
            humidity_match = re.search(r'(\d+)%', response.text if 'response' in dir() else str(soup))
            if humidity_match:
                current['humidity'] = int(humidity_match.group(1))

        except Exception as e:
            logger.warning(f"Error parsing current conditions: {e}")

        return current

    def _parse_kttv_hourly(self, soup: BeautifulSoup) -> list[dict]:
        """Parse hourly forecast data"""
        hourly = []

        try:
            # Pattern: time -> temperature -> humidity
            time_pattern = re.compile(r'(\d{2}:\d{2})')
            temp_pattern = re.compile(r'(\d+)°')

            # Parse hourly data from text
            hourly_text = soup.get_text()

            # Extract all temperature mentions
            temps = temp_pattern.findall(hourly_text)
            times = time_pattern.findall(hourly_text)

            for i, (time, temp) in enumerate(zip(times[:24], temps[:24])):
                hourly.append({
                    'time': time,
                    'temperature': int(temp),
                    'hour_index': i
                })

        except Exception as e:
            logger.warning(f"Error parsing hourly data: {e}")

        return hourly

    def _parse_kttv_air_quality(self, soup: BeautifulSoup) -> dict:
        """Parse air quality data"""
        aq = {}

        try:
            text = soup.get_text()

            # Extract pollutant values
            patterns = {
                'co': r'CO\s*([\d.]+)',
                'no2': r'NO₂\s*([\d.]+)',
                'o3': r'O₃\s*([\d.]+)',
                'pm25': r'PM2\.5\s*([\d.]+)',
                'pm10': r'PM10\s*([\d.]+)',
                'so2': r'SO₂\s*([\d.]+)'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    aq[key] = float(match.group(1))

        except Exception as e:
            logger.warning(f"Error parsing air quality: {e}")

        return aq

    def fetch_open_meteo(self, lat: float, lon: float, days: int = 7) -> dict[str, Any]:
        """Fetch weather data from Open-Meteo API (free, no API key required)"""
        source = f'open_meteo_{lat}_{lon}'
        logger.info(f"Fetching Open-Meteo data for {lat}, {lon}...")

        # Check cache
        cached = self.load_from_cache(source)
        if cached:
            return cached

        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m',
                'hourly': 'temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,cloud_cover,wind_speed_10m,wind_gusts_10m',
                'daily': 'weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,wind_speed_10m_max',
                'timezone': 'Asia/Ho_Chi_Minh',
                'forecast_days': days
            }

            response = self.session.get(
                'https://api.open-meteo.com/v1/forecast',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Process and structure the data
            processed = {
                'source': 'Open-Meteo',
                'url': 'https://api.open-meteo.com/v1/forecast',
                'fetched_at': datetime.now().isoformat(),
                'coordinates': {'lat': lat, 'lon': lon},
                'current': data.get('current', {}),
                'hourly': self._process_hourly(data.get('hourly', {})),
                'daily': self._process_daily(data.get('daily', {})),
                'units': data.get('units', {})
            }

            self.save_to_cache(source, processed)
            self._save_weather_data(source, processed)

            return processed

        except Exception as e:
            logger.error(f"Error fetching Open-Meteo data: {e}")
            return {'error': str(e)}

    def _process_hourly(self, hourly_data: dict) -> list[dict]:
        """Process hourly data into structured format"""
        processed = []
        times = hourly_data.get('time', [])

        for i, time in enumerate(times):
            hour = {
                'datetime': time,
                'temperature_2m': hourly_data.get('temperature_2m', [None]*len(times))[i] if i < len(times) else None,
                'humidity': hourly_data.get('relative_humidity_2m', [None]*len(times))[i] if i < len(times) else None,
                'precipitation_probability': hourly_data.get('precipitation_probability', [None]*len(times))[i] if i < len(times) else None,
                'precipitation': hourly_data.get('precipitation', [None]*len(times))[i] if i < len(times) else None,
                'weather_code': hourly_data.get('weather_code', [None]*len(times))[i] if i < len(times) else None,
                'cloud_cover': hourly_data.get('cloud_cover', [None]*len(times))[i] if i < len(times) else None,
                'wind_speed': hourly_data.get('wind_speed_10m', [None]*len(times))[i] if i < len(times) else None,
                'wind_gusts': hourly_data.get('wind_gusts_10m', [None]*len(times))[i] if i < len(times) else None,
            }
            processed.append(hour)

        return processed

    def _process_daily(self, daily_data: dict) -> list[dict]:
        """Process daily data into structured format"""
        processed = []
        times = daily_data.get('time', [])

        for i, time in enumerate(times):
            day = {
                'date': time,
                'weather_code': daily_data.get('weather_code', [None]*len(times))[i] if i < len(times) else None,
                'temp_max': daily_data.get('temperature_2m_max', [None]*len(times))[i] if i < len(times) else None,
                'temp_min': daily_data.get('temperature_2m_min', [None]*len(times))[i] if i < len(times) else None,
                'sunrise': daily_data.get('sunrise', [None]*len(times))[i] if i < len(times) else None,
                'sunset': daily_data.get('sunset', [None]*len(times))[i] if i < len(times) else None,
                'precipitation_sum': daily_data.get('precipitation_sum', [None]*len(times))[i] if i < len(times) else None,
                'precipitation_probability_max': daily_data.get('precipitation_probability_max', [None]*len(times))[i] if i < len(times) else None,
                'wind_speed_max': daily_data.get('wind_speed_10m_max', [None]*len(times))[i] if i < len(times) else None,
            }
            processed.append(day)

        return processed

    def fetch_all_districts(self, days: int = 7) -> dict[str, Any]:
        """Fetch weather data for all Dien Bien districts"""
        logger.info("Fetching weather data for all districts...")

        all_data = {
            'province': 'Dien Bien',
            'fetched_at': datetime.now().isoformat(),
            'districts': {}
        }

        for district_id, info in DIEN_BIEN_LOCATIONS.items():
            logger.info(f"Fetching data for {info['district']}...")
            try:
                data = self.fetch_open_meteo(
                    lat=info['lat'],
                    lon=info['lon'],
                    days=days
                )
                all_data['districts'][district_id] = {
                    **info,
                    'weather': data
                }
                # Rate limiting
                import time
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error fetching {info['district']}: {e}")
                all_data['districts'][district_id] = {
                    **info,
                    'error': str(e)
                }

        self._save_weather_data('all_districts', all_data)
        return all_data

    def _save_weather_data(self, name: str, data: dict):
        """Save weather data to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = OUTPUT_DIR / f"{name}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved weather data to {filename}")

        # Also save as latest
        latest_path = OUTPUT_DIR / f"{name}_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class DisasterDataScraper:
    """Scraper for natural disaster data"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_disaster_news(self) -> list[dict]:
        """Fetch disaster-related news from various sources"""
        logger.info("Fetching disaster news...")

        news_items = []

        # VNExpress disaster section
        try:
            response = self.session.get(
                'https://vnexpress.net/tags/thien-tai-viet-nam-66717.html',
                timeout=30
            )
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article', class_='item_news')

            for article in articles[:10]:
                title_elem = article.find('h3') or article.find('h2')
                title = title_elem.get_text(strip=True) if title_elem else ''

                link_elem = article.find('a')
                link = link_elem.get('href', '') if link_elem else ''

                date_elem = article.find('span', class_='time')
                date = date_elem.get_text(strip=True) if date_elem else ''

                news_items.append({
                    'title': title,
                    'link': link,
                    'date': date,
                    'source': 'vnexpress.net',
                    'category': 'disaster_news'
                })
        except Exception as e:
            logger.error(f"Error fetching VnExpress: {e}")

        # Save news data
        self._save_disaster_data('news', news_items)
        return news_items

    def fetch_flood_alerts(self) -> list[dict]:
        """Fetch flood alert data from national sources"""
        logger.info("Fetching flood alerts...")

        alerts = []

        # Placeholder for actual API calls to disaster management agencies
        # In production, these would be actual API endpoints

        self._save_disaster_data('flood_alerts', alerts)
        return alerts

    def fetch_storm_tracking(self) -> list[dict]:
        """Fetch storm tracking data"""
        logger.info("Fetching storm tracking data...")

        storms = []

        # Placeholder for tropical storm data
        # Could integrate with: https://www.weather.gov.hk/wa/c_storm.htm

        self._save_disaster_data('storms', storms)
        return storms

    def _save_disaster_data(self, name: str, data: list):
        """Save disaster data to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = DATA_DIR / "disasters" / f"{name}_{timestamp}.json"
        filename.parent.mkdir(parents=True, exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'fetched_at': datetime.now().isoformat(),
                'data': data
            }, f, ensure_ascii=False, indent=2)


def main():
    """Main function to run all scrapers"""
    logger.info("=" * 60)
    logger.info("Starting Weather & Disaster Data Collection")
    logger.info("=" * 60)

    weather_scraper = WeatherScraper()
    disaster_scraper = DisasterDataScraper()

    # 1. Fetch KTTV data
    logger.info("\n[1/4] Fetching KTTV Dien Bien data...")
    kttv_data = weather_scraper.fetch_kttv_dien_bien()
    logger.info(f"KTTV data fetched: {len(kttv_data)} keys")

    # 2. Fetch Open-Meteo for main city
    logger.info("\n[2/4] Fetching Open-Meteo for Điện Biên Phủ...")
    main_location = DIEN_BIEN_LOCATIONS['dien_bien_phu']
    open_meteo_data = weather_scraper.fetch_open_meteo(
        lat=main_location['lat'],
        lon=main_location['lon'],
        days=7
    )
    logger.info(f"Open-Meteo data: {len(open_meteo_data)} keys")

    # 3. Fetch all districts
    logger.info("\n[3/4] Fetching all district data...")
    all_districts = weather_scraper.fetch_all_districts(days=7)
    logger.info(f"Fetched data for {len(all_districts.get('districts', {}))} districts")

    # 4. Fetch disaster news
    logger.info("\n[4/4] Fetching disaster news...")
    disaster_news = disaster_scraper.fetch_disaster_news()
    logger.info(f"Fetched {len(disaster_news)} news items")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Data Collection Summary")
    logger.info("=" * 60)
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Files saved: {len(list(OUTPUT_DIR.glob('*.json')))}")

    return {
        'kttv_data': kttv_data,
        'open_meteo': open_meteo_data,
        'all_districts': all_districts,
        'disaster_news': disaster_news
    }


if __name__ == '__main__':
    main()
