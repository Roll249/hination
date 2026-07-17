#!/usr/bin/env python3
"""
Historical Weather Data Fetcher for Điện Biên Province, Vietnam

This script fetches historical weather data from Open-Meteo's Archive API
and saves it to JSON files for use in the HINATION dashboard.

Usage:
    python fetch_historical_data.py --year 2024
    python fetch_historical_data.py --start 2020 --end 2024
    python fetch_historical_data.py --month 2024 6  # June 2024
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' library required. Install with: pip install requests")
    sys.exit(1)


# Điện Biên Province coordinates
DIEN_BIEN_COORDS = {
    "city_center": {"lat": 21.3869, "lon": 103.0228, "name": "Điện Biên Phủ"},
    "province_bounds": {"lat_min": 21.0, "lat_max": 22.7, "lon_min": 102.1, "lon_max": 103.6}
}

# District coordinates
DISTRICT_COORDS = {
    "dien_bien_phu": {"lat": 21.3869, "lon": 103.0228, "name": "Thành phố Điện Biên Phủ"},
    "tuan_giao": {"lat": 21.6167, "lon": 103.25, "name": "Huyện Tuần Giáo"},
    "tua_chua": {"lat": 21.4667, "lon": 103.4333, "name": "Huyện Tủa Chùa"},
    "muong_ang": {"lat": 21.8167, "lon": 103.0833, "name": "Huyện Mường Ảng"},
    "muong_cha": {"lat": 22.0833, "lon": 102.4333, "name": "Huyện Mường Chà"},
    "muong_nhe": {"lat": 22.4167, "lon": 102.3, "name": "Huyện Mường Nhé"},
    "dien_bien_dong": {"lat": 21.1833, "lon": 103.55, "name": "Huyện Điện Biên Đông"},
    "nam_po": {"lat": 21.65, "lon": 103.1167, "name": "Huyện Nậm Pồ"},
    "muong_lay": {"lat": 22.5, "lon": 102.6833, "name": "Thị xã Mường Lay"},
}

# API Configuration
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEZONE = "Asia/Ho_Chi_Minh"

# Variables to fetch
DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "rain_sum",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "weather_code",
]

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
]


def fetch_weather_data(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    daily_vars: Optional[List[str]] = None,
    hourly_vars: Optional[List[str]] = None,
) -> dict:
    """Fetch historical weather data from Open-Meteo Archive API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "timezone": TIMEZONE,
    }
    
    if daily_vars:
        params["daily"] = ",".join(daily_vars)
    if hourly_vars:
        params["hourly"] = ",".join(hourly_vars)
    
    print(f"  Fetching: {start_date} to {end_date}")
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching data: {e}")
        return {"error": str(e)}


def save_json(data: dict, filepath: Path):
    """Save data to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {filepath}")


def fetch_year_data(year: int, output_dir: Path, daily_only: bool = True):
    """Fetch a full year of daily weather data for all districts."""
    print(f"\n📅 Fetching year {year} data...")
    
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    daily_vars = DAILY_VARIABLES if daily_only else None
    hourly_vars = None if daily_only else HOURLY_VARIABLES
    
    all_districts_data = {
        "province": "Điện Biên",
        "year": year,
        "fetched_at": datetime.now().isoformat(),
        "source": "Open-Meteo Archive API (ERA5)",
        "timezone": TIMEZONE,
        "districts": {}
    }
    
    for district_id, coords in DISTRICT_COORDS.items():
        print(f"\n  📍 {coords['name']} ({district_id})")
        data = fetch_weather_data(
            coords["lat"],
            coords["lon"],
            start_date,
            end_date,
            daily_vars=daily_vars,
            hourly_vars=hourly_vars,
        )
        
        if "error" not in data:
            all_districts_data["districts"][district_id] = {
                "name": coords["name"],
                "coordinates": {"lat": coords["lat"], "lon": coords["lon"]},
                "data": data
            }
    
    # Save combined data
    output_file = output_dir / f"dien_bien_{year}_daily.json"
    save_json(all_districts_data, output_file)
    
    return all_districts_data


def fetch_month_data(year: int, month: int, output_dir: Path):
    """Fetch a specific month of data."""
    print(f"\n📅 Fetching {year}-{month:02d} data...")
    
    start_date = f"{year}-{month:02d}-01"
    # Calculate end date
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    lat = DIEN_BIEN_COORDS["city_center"]["lat"]
    lon = DIEN_BIEN_COORDS["city_center"]["lon"]
    
    data = fetch_weather_data(lat, lon, start_date, end_date, daily_vars=DAILY_VARIABLES)
    
    if "error" not in data:
        output_file = output_dir / f"dien_bien_{year}_{month:02d}.json"
        result = {
            "province": "Điện Biên",
            "city_center": DIEN_BIEN_COORDS["city_center"],
            "year": year,
            "month": month,
            "fetched_at": datetime.now().isoformat(),
            "source": "Open-Meteo Archive API (ERA5)",
            "data": data
        }
        save_json(result, output_file)
        return result
    
    return {"error": "Failed to fetch data"}


def analyze_monsoon_pattern(data: dict) -> dict:
    """Analyze monsoon patterns from weather data."""
    if "daily" not in data:
        return {"error": "No daily data available"}
    
    daily = data["daily"]
    precipitation = daily.get("precipitation_sum", [])
    dates = daily.get("time", [])
    
    # Calculate monthly totals
    monthly_precip = {}
    for i, date_str in enumerate(dates):
        if i < len(precipitation):
            month_key = date_str[:7]  # YYYY-MM
            monthly_precip[month_key] = monthly_precip.get(month_key, 0) + precipitation[i]
    
    # Find heavy rain days (>30mm)
    heavy_rain_days = []
    for i, precip in enumerate(precipitation):
        if precip > 30:
            heavy_rain_days.append({"date": dates[i], "precipitation": precip})
    
    return {
        "monthly_precipitation_mm": monthly_precip,
        "total_annual_precipitation_mm": sum(precipitation),
        "heavy_rain_days_count": len(heavy_rain_days),
        "heavy_rain_days": heavy_rain_days[:10]  # Top 10
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch historical weather data for Điện Biên")
    parser.add_argument("--year", type=int, help="Single year to fetch (e.g., 2024)")
    parser.add_argument("--start", type=int, help="Start year for range")
    parser.add_argument("--end", type=int, help="End year for range")
    parser.add_argument("--month", nargs=2, type=int, metavar=("YEAR", "MONTH"), help="Specific month")
    parser.add_argument("--output-dir", type=str, default="data/historical", help="Output directory")
    parser.add_argument("--analyze", action="store_true", help="Analyze monsoon patterns")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.month:
        year, month = args.month
        fetch_month_data(year, month, output_dir)
    
    elif args.year:
        fetch_year_data(args.year, output_dir)
    
    elif args.start and args.end:
        for year in range(args.start, args.end + 1):
            fetch_year_data(year, output_dir)
    
    else:
        # Default: fetch 2024 data
        print("No specific period specified. Fetching 2024 data by default...")
        fetch_year_data(2024, output_dir)
    
    print("\n✅ Data fetching complete!")
    print(f"📁 Output directory: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
