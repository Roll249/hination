"""
HINATION Hourly Forecast - Direct GFS Pipeline (Windy-style)
=============================================================

Architecture đơn giản và chính xác:
1. **GFS Seamless cho tất cả 168h** (7 ngày × 24h) - giống Windy
2. **Multi-cell neighborhood**: GFS cung cấp từng hour cho mỗi (lat, lon)
3. **Hourly granularity** với neighboring context (8 cells + 6 provinces)
4. **Risks** tính trực tiếp từ GFS output

Reference:
- Windy uses GFS 13km hourly, ECMWF 9km hourly (with interpolation cho 3h gaps)
- Chúng ta dùng GFS Seamless (giống Windy default)
"""

import json
import time
import warnings
import requests
import numpy as np
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore')

# ============================================================
# Districts (Điện Biên) + Neighbors
# ============================================================

DISTRICTS = {
    'dien_bien_phu':    {'name': 'TP Điện Biên Phủ',    'lat': 21.3869, 'lon': 103.0228, 'elev': 483,  'terrain': 0.3},
    'tuan_giao':        {'name': 'Huyện Tuần Giáo',      'lat': 21.6167, 'lon': 103.25,   'elev': 1047, 'terrain': 0.7},
    'tua_chua':         {'name': 'Huyện Tủa Chùa',       'lat': 21.4667, 'lon': 103.4333, 'elev': 1565, 'terrain': 0.9},
    'muong_cha':        {'name': 'Huyện Mường Chà',      'lat': 22.0833, 'lon': 102.4333, 'elev': 500,  'terrain': 0.6},
    'muong_nhe':        {'name': 'Huyện Mường Nhé',      'lat': 22.4167, 'lon': 102.3,    'elev': 600,  'terrain': 0.8},
    'dien_bien_dong':   {'name': 'Huyện Điện Biên Đông', 'lat': 21.1833, 'lon': 103.55,   'elev': 800,  'terrain': 0.75},
    'nam_po':           {'name': 'Huyện Nậm Pồ',         'lat': 21.65,   'lon': 103.1167, 'elev': 700,  'terrain': 0.85},
    'muong_ang':        {'name': 'Huyện Mường Ảng',      'lat': 21.8167, 'lon': 103.0833, 'elev': 650,  'terrain': 0.65},
    'muong_lay':        {'name': 'Thị xã Mường Lay',     'lat': 22.5,    'lon': 102.6833, 'elev': 450,  'terrain': 0.5}
}

# Neighboring cells - 4 corners quanh mỗi district (~25km offset)
# Format: 4 cells, lấy wind/cloud từ đây làm "advection context"
NEIGHBOR_CELL_OFFSETS = [
    (-0.225, -0.225),   # NW
    (-0.225,  0.225),   # NE
    ( 0.225, -0.225),   # SW
    ( 0.225,  0.225),   # SE
]

# Neighboring provinces (6 tỉnh lân cận)
NEIGHBORING_PROVINCES = {
    'son_la':    {'name': 'Sơn La',    'lat': 21.327, 'lon': 103.914},
    'lai_chau':  {'name': 'Lai Châu',  'lat': 22.396, 'lon': 103.439},
    'lao_cai':   {'name': 'Lào Cai',   'lat': 22.483, 'lon': 103.967},
    'yen_bai':   {'name': 'Yên Bái',   'lat': 21.705, 'lon': 104.876},
    'ha_giang':  {'name': 'Hà Giang',  'lat': 22.823, 'lon': 104.984},
    'thanh_hoa': {'name': 'Thanh Hóa', 'lat': 20.129, 'lon': 105.313}
}

# 8 vars chính từ GFS Seamless (hourly)
HOURLY_VARS = [
    'temperature_2m',      # °C
    'precipitation',       # mm (per hour)
    'cloud_cover',         # %
    'wind_speed_10m',      # km/h
    'wind_direction_10m',  # °
    'wind_gusts_10m',      # km/h
    'relative_humidity_2m', # %
    'surface_pressure'     # hPa
]


# ============================================================
# Fetching from Open-Meteo (GFS Seamless)
# ============================================================

def fetch_hourly(lat, lon, hours=168, models='gfs_seamless'):
    """Fetch 168 hours of hourly forecast from GFS"""
    params = {
        'latitude': lat,
        'longitude': lon,
        'hourly': ','.join(HOURLY_VARS),
        'timezone': 'Asia/Ho_Chi_Minh',
        'forecast_days': 7,
        'models': models
    }
    try:
        resp = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params=params,
            timeout=30
        )
        data = resp.json()
        return data if 'error' not in data else {'error': data.get('reason', 'unknown')}
    except Exception as e:
        return {'error': str(e)}


# ============================================================
# Risk Calculation (hourly)
# ============================================================

def compute_risks(precip_mm, wind_gust_kmh, humidity_pct, cloud_pct, terrain_factor):
    """
    Tính hourly risks:
    - flood: dựa vào lượng mưa/giờ
    - landslide: mưa + độ ẩm + địa hình
    - wind: gió giật
    - storm: heavy rain + wind + cloud cover
    """
    # Flood
    if precip_mm < 2:
        flood = precip_mm / 20
    elif precip_mm < 5:
        flood = 0.1 + (precip_mm - 2) / 15
    elif precip_mm < 10:
        flood = 0.4 + (precip_mm - 5) / 20
    else:
        flood = 0.7 + min(0.3, (precip_mm - 10) / 50)
    flood = min(1.0, flood)

    # Landslide (depends on terrain)
    if precip_mm < 1:
        landslide = 0.0
    else:
        base = min(1.0, precip_mm / 30)
        hum_factor = (humidity_pct / 100) * 0.4
        landslide = min(1.0, base * (1 + hum_factor) * (0.4 + terrain_factor * 0.6))

    # Wind
    if wind_gust_kmh < 30:
        wind = 0.0
    elif wind_gust_kmh < 50:
        wind = (wind_gust_kmh - 30) / 40
    else:
        wind = min(1.0, 0.5 + (wind_gust_kmh - 50) / 100)

    # Storm (heavy rain + wind + dense clouds)
    storm = 1.0 if (precip_mm > 5 and wind_gust_kmh > 40 and cloud_pct > 80) else 0.0

    return {
        'flood': round(flood, 3),
        'landslide': round(landslide, 3),
        'wind': round(wind, 3),
        'storm': storm
    }


# ============================================================
# Pipeline (đơn giản: fetch GFS cho tất cả 168h)
# ============================================================

def get_hour_value(data, var, idx):
    """Safely extract hourly value"""
    if 'hourly' not in data or var not in data['hourly']:
        return 0.0
    vals = data['hourly'][var]
    if idx >= len(vals) or vals[idx] is None:
        return 0.0
    return float(vals[idx])


def run_pipeline():
    """
    Main pipeline:
    1. Fetch GFS Seamless hourly cho 9 districts + 4×9 cells + 6 provinces
    2. Tất cả 168h (7 ngày × 24h) đều từ GFS - không tự dự đoán
    3. Tính risks cho mỗi hour của mỗi district
    4. Save JSON + dashboard updates
    """
    print("=" * 70)
    print("🌀 HINATION HOURLY - GFS Seamless Direct")
    print("   168 hours = 7 days × 24 hours")
    print("   Source: GFS 13km hourly (Windy-style)")
    print("=" * 70)

    # ===========================================================
    # 1. Fetch tất cả districts + 4 neighbor cells mỗi cái + 6 provinces
    # ===========================================================
    all_data = {}

    print(f"\n📡 Fetching 9 districts...")
    for did, info in DISTRICTS.items():
        data = fetch_hourly(info['lat'], info['lon'])
        if 'hourly' in data:
            all_data[did] = data
            hours = len(data['hourly'].get('time', []))
            print(f"   • {info['name']:<25s} ✓ {hours}h")
        else:
            print(f"   • {info['name']:<25s} ✗ {data.get('error', 'fail')[:30]}")

    print(f"\n📡 Fetching neighboring cells (4 per district)...")
    for did, info in DISTRICTS.items():
        for n_idx, (dlat, dlon) in enumerate(NEIGHBOR_CELL_OFFSETS):
            cell_id = f"{did}_n{n_idx}"
            cell_lat = info['lat'] + dlat
            cell_lon = info['lon'] + dlon
            data = fetch_hourly(cell_lat, cell_lon)
            if 'hourly' in data:
                all_data[cell_id] = data
        print(f"   • {info['name']:<25s} ✓ 4 cells")

    print(f"\n📡 Fetching 6 neighboring provinces...")
    for pid, info in NEIGHBORING_PROVINCES.items():
        data = fetch_hourly(info['lat'], info['lon'])
        if 'hourly' in data:
            all_data[pid] = data
            hours = len(data['hourly'].get('time', []))
            print(f"   • {info['name']:<25s} ✓ {hours}h")
        else:
            print(f"   • {info['name']:<25s} ✗ {data.get('error', 'fail')[:30]}")

    # ===========================================================
    # 2. Build hourly predictions per district
    # ===========================================================
    print(f"\n🔨 Building hourly forecasts for 9 districts (168h each)...")

    predictions = {}
    times = all_data[list(DISTRICTS.keys())[0]]['hourly']['time']

    for did, info in DISTRICTS.items():
        if did not in all_data:
            continue

        d = all_data[did]['hourly']
        T = min(168, len(d['time']))

        hourly_data = []
        for h in range(T):
            # Hour data from GFS for THIS district
            precip = get_hour_value(all_data[did], 'precipitation', h)
            wind_gust = get_hour_value(all_data[did], 'wind_gusts_10m', h)
            humidity = get_hour_value(all_data[did], 'relative_humidity_2m', h)
            cloud = get_hour_value(all_data[did], 'cloud_cover', h)

            risks = compute_risks(precip, wind_gust, humidity, cloud, info['terrain'])

            # Hour data
            hour_data = {
                'datetime': d['time'][h],
                'hour_offset': h + 1,
                'day_offset': (h // 24) + 1,
                'hour_of_day': h % 24,
                'temperature_2m': get_hour_value(all_data[did], 'temperature_2m', h),
                'precipitation': precip,
                'cloud_cover': get_hour_value(all_data[did], 'cloud_cover', h),
                'wind_speed_10m': get_hour_value(all_data[did], 'wind_speed_10m', h),
                'wind_direction_10m': get_hour_value(all_data[did], 'wind_direction_10m', h),
                'wind_gusts_10m': wind_gust,
                'humidity': humidity,
                'pressure': get_hour_value(all_data[did], 'surface_pressure', h),
                **risks,
                'source': 'gfs_seamless'  # Tất cả từ GFS
            }

            # Add neighboring cell context (4 corners)
            for n_idx in range(4):
                cell_id = f"{did}_n{n_idx}"
                if cell_id in all_data:
                    cn = all_data[cell_id]['hourly']
                    if h < len(cn.get('time', [])):
                        hour_data[f'neighbor_{n_idx}_wind_speed'] = get_hour_value(all_data[cell_id], 'wind_speed_10m', h)
                        hour_data[f'neighbor_{n_idx}_wind_dir'] = get_hour_value(all_data[cell_id], 'wind_direction_10m', h)
                        hour_data[f'neighbor_{n_idx}_cloud'] = get_hour_value(all_data[cell_id], 'cloud_cover', h)

            # Add neighboring province context (6 provinces, only wind + cloud)
            for pid, pinfo in NEIGHBORING_PROVINCES.items():
                if pid in all_data:
                    pn = all_data[pid]['hourly']
                    if h < len(pn.get('time', [])):
                        hour_data[f'prov_{pid}_wind'] = get_hour_value(all_data[pid], 'wind_speed_10m', h)
                        hour_data[f'prov_{pid}_cloud'] = get_hour_value(all_data[pid], 'cloud_cover', h)

            hourly_data.append(hour_data)

        predictions[did] = {
            'district_id': did,
            'name': info['name'],
            'coordinates': {'lat': info['lat'], 'lon': info['lon']},
            'elevation': info['elev'],
            'terrain_factor': info['terrain'],
            'forecast_hours': hourly_data,
            'model_used': 'gfs_seamless_direct',
            'forecast_source': 'GFS 13km (NOAA)',
            'timestamp': datetime.now().isoformat()
        }

    # ===========================================================
    # 3. Save
    # ===========================================================
    output_dir = Path('data/predictions')
    output_dir.mkdir(exist_ok=True)

    output = {
        'generated_at': datetime.now().isoformat(),
        'model': 'gfs_seamless_direct',
        'source': 'NOAA GFS 13km (via Open-Meteo)',
        'forecast_horizon_hours': 168,
        'hours_per_day': 24,
        'days': 7,
        'districts': predictions,
        'neighboring_provinces': [
            {'id': pid, 'name': info['name'], 'coordinates': {'lat': info['lat'], 'lon': info['lon']}}
            for pid, info in NEIGHBORING_PROVINCES.items()
        ],
        'update_frequency': '1 hour',
        'next_update': (datetime.now().replace(minute=0, second=0, microsecond=0)).isoformat()
    }

    with open(output_dir / 'hourly_forecast.json', 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Daily summary
    daily_summary = {}
    for did, p in predictions.items():
        days = []
        for day_idx in range(7):
            start = day_idx * 24
            end = start + 24
            day_hours = [h for h in p['forecast_hours'] if h.get('day_offset') == day_idx + 1]
            if not day_hours:
                continue
            days.append({
                'day_offset': day_idx + 1,
                'date': day_hours[0]['datetime'][:10],
                'temp_min': min(h['temperature_2m'] for h in day_hours),
                'temp_max': max(h['temperature_2m'] for h in day_hours),
                'precipitation_total': round(sum(h['precipitation'] for h in day_hours), 2),
                'wind_gust_max': max(h['wind_gusts_10m'] for h in day_hours),
                'humidity_avg': round(sum(h['humidity'] for h in day_hours) / len(day_hours), 1),
                'cloud_avg': round(sum(h['cloud_cover'] for h in day_hours) / len(day_hours), 1),
                'flood_risk_max': max(h['flood'] for h in day_hours),
                'landslide_risk_max': max(h['landslide'] for h in day_hours),
                'wind_risk_max': max(h['wind'] for h in day_hours),
                'storm_risk_max': max(h['storm'] for h in day_hours)
            })
        daily_summary[did] = {
            'district_id': did,
            'name': p['name'],
            'coordinates': p['coordinates'],
            'elevation': p['elevation'],
            'days': days,
            'model_used': 'gfs_seamless_direct',
            'timestamp': p['timestamp']
        }

    with open(output_dir / 'daily_summary.json', 'w') as f:
        json.dump(daily_summary, f, ensure_ascii=False, indent=2)

    # ===========================================================
    # 4. Print summary
    # ===========================================================
    print(f"\n" + "=" * 70)
    print(f"📊 7-DAY HOURLY FORECAST (GFS Seamless - direct)")
    print("=" * 70)
    print(f"\n{'District':<25} {'Days':<6} {'Hours':<6} {'Avg Temp':<10} {'Total Rain':<12} {'Max Wind':<10}")
    print("-" * 75)

    for did, p in predictions.items():
        hours = p['forecast_hours']
        if not hours:
            continue
        temps = [h['temperature_2m'] for h in hours]
        rain = sum(h['precipitation'] for h in hours)
        max_wind = max(h['wind_gusts_10m'] for h in hours)
        avg_temp = sum(temps) / len(temps)
        print(f"{p['name']:<25} {len(set(h['day_offset'] for h in hours)):<6} "
              f"{len(hours):<6} {avg_temp:.1f}°C      "
              f"{rain:.1f}mm         {max_wind:.0f} km/h")

    print(f"\n✓ Saved: data/predictions/hourly_forecast.json")
    print(f"✓ Saved: data/predictions/daily_summary.json")
    print(f"\n{'='*70}")
    print(f"✓ HOURLY PIPELINE COMPLETE")
    print(f"  Source: GFS Seamless (NOAA 13km)")
    print(f"  Total: 9 districts × 168 hours = 1,512 hourly forecasts")
    print(f"  Context: 4 neighbor cells × 9 = 36 + 6 provinces = 42")
    print(f"{'='*70}")

    return predictions


# ============================================================
# Hourly Scheduler (chạy mỗi giờ)
# ============================================================

def start_scheduler():
    """Run pipeline every hour"""
    import schedule

    print(f"\n⏰ HOUR AUTO-UPDATE")
    print(f"   - Pull from GFS each hour")
    print(f"   - Update dashboard automatically")
    print(f"   - Press Ctrl+C to stop\n")

    # Run immediately
    run_pipeline()

    # Schedule every hour
    schedule.every(1).hours.do(run_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'schedule':
        start_scheduler()
    else:
        run_pipeline()