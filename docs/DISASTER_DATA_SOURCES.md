# Disaster Data Sources for Điện Biên Province, Vietnam

This document catalogs real disaster and weather data sources for Điện Biên province that can be integrated into the HINATION hackathon dashboard.

---

## 1. Open-Meteo Historical Weather API ✅ WORKING

### Overview
- **Provider**: Open-Meteo (open-meteo.com)
- **Data Source**: ECMWF ERA5 reanalysis (1940-present, 9km resolution)
- **API Endpoint**: `https://archive-api.open-meteo.com/v1/archive`
- **License**: Free for non-commercial use, API key not required
- **Status**: ✅ Confirmed working with Điện Biên coordinates

### Điện Biên Coordinates
- **City Center**: 21.3869°N, 103.0228°E (Điện Biên Phủ)
- **Province Bounds**: 21.0°N - 22.7°N, 102.1°E - 103.6°E

### API Parameters

```
latitude=21.38
longitude=103.02
start_date=YYYY-MM-DD
end_date=YYYY-MM-DD
daily=<variable_list>
hourly=<variable_list>
timezone=Asia/Ho_Chi_Minh
```

### Available Daily Variables
| Variable | Description | Unit |
|----------|-------------|------|
| `temperature_2m_max` | Maximum daily temperature | °C |
| `temperature_2m_min` | Minimum daily temperature | °C |
| `temperature_2m_mean` | Mean daily temperature | °C |
| `precipitation_sum` | Daily precipitation total | mm |
| `rain_sum` | Daily rain total | mm |
| `snowfall_sum` | Daily snowfall | cm |
| `wind_speed_10m_max` | Maximum wind speed | km/h |
| `wind_gusts_10m_max` | Maximum wind gusts | km/h |
| `wind_direction_10m_dominant` | Dominant wind direction | ° |
| `weather_code` | WMO weather code | code |
| `sunshine_duration` | Sunshine duration | seconds |

### Available Hourly Variables
| Variable | Description | Unit |
|----------|-------------|------|
| `temperature_2m` | Temperature at 2m | °C |
| `relative_humidity_2m` | Relative humidity | % |
| `precipitation` | Precipitation | mm |
| `rain` | Rain | mm |
| `weather_code` | WMO code | code |
| `cloud_cover` | Cloud cover | % |
| `wind_speed_10m` | Wind speed | km/h |
| `wind_direction_10m` | Wind direction | ° |
| `soil_moisture_0_to_7cm` | Soil moisture | m³/m³ |

### Example API Calls

**Basic Daily Weather (June 2024 - Monsoon Season)**:
```bash
curl "https://archive-api.open-meteo.com/v1/archive?\
  latitude=21.38&longitude=103.02&\
  start_date=2024-06-01&end_date=2024-06-10&\
  daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&\
  timezone=Asia/Ho_Chi_Minh"
```

**Extended Historical Data (2024)**:
```bash
curl "https://archive-api.open-meteo.com/v1/archive?\
  latitude=21.38&longitude=103.02&\
  start_date=2024-01-01&end_date=2024-12-31&\
  daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&\
  timezone=Asia/Ho_Chi_Minh"
```

### Sample Response
```json
{
  "latitude": 21.335676,
  "longitude": 103.02752,
  "utc_offset_seconds": 25200,
  "timezone": "Asia/Ho_Chi_Minh",
  "elevation": 493.0,
  "daily": {
    "time": ["2024-06-01", "2024-06-02"],
    "temperature_2m_max": [31.8, 29.7],
    "temperature_2m_min": [23.5, 23.1],
    "precipitation_sum": [10.40, 25.40],
    "weather_code": [63, 65]
  }
}
```

### WMO Weather Codes
| Code | Vietnamese | English |
|------|-----------|---------|
| 0 | Trời quang | Clear sky |
| 1-3 | Ít mây đến U ám | Mainly clear to overcast |
| 45, 48 | Sương mù | Fog |
| 51, 53, 55 | Mưa phùn nhẹ/vừa/nặng | Drizzle |
| 61, 63, 65 | Mưa nhẹ/vừa/to | Rain |
| 71, 73, 75 | Tuyết | Snow |
| 80, 81, 82 | Mưa rào nhẹ/vừa/nặng | Rain showers |
| 95, 96, 99 | Giông, Giông kèm mưa đá | Thunderstorm |

---

## 2. Open-Meteo Real-time Forecast API ✅ WORKING

### Overview
- **Provider**: Open-Meteo
- **API Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Coverage**: 7-day forecast + past 7-90 days
- **Status**: ✅ Currently used in HINATION dashboard

### Parameters for Real-time Data
```
latitude=21.38
longitude=103.02
current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m
daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code
timezone=Asia/Ho_Chi_Minh
forecast_days=7
past_days=7
```

### Sample Response (Currently in use)
Located at: `data/weather_comprehensive.json`

---

## 3. GDACS (Global Disaster Alert and Coordination System)

### Overview
- **Provider**: United Nations / European Union
- **API Endpoint**: `https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH`
- **Data Type**: Real-time disaster events, alerts
- **Coverage**: Global, including Vietnam
- **Status**: ⚠️ Returns limited results for Vietnam

### Event Types
| Code | Description |
|------|-------------|
| FL | Flood |
| TC | Tropical Cyclone |
| EQ | Earthquake |
| DR | Drought |
| VO | Volcanic eruption |
| TS | Tsunami |

### API Parameters
```
fromDate=YYYY-MM-DD
toDate=YYYY-MM-DD
eventlist=FL,TC,DR (comma-separated)
alertlevel=Green;Orange;Red (semicolon-separated)
```

### Example API Call
```bash
curl "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?\
  eventlist=FL,TC,DR&\
  fromDate=2020-01-01&toDate=2026-12-31&\
  alertlevel=Green;Orange;Red"
```

### Sample Vietnam Events Found
```json
{
  "eventtype": "FL",
  "name": "Flood in Vietnam",
  "fromdate": "2026-06-25T01:00:00",
  "todate": "2026-07-06T01:00:00",
  "alertlevel": "Green",
  "country": "Vietnam"
}
```

### Known Issues
- Maximum 100 records per request
- Vietnam-specific queries may return empty results
- Limited historical data (typically last 2-3 years)

---

## 4. EM-DAT (Emergency Events Database)

### Overview
- **Provider**: Centre for Research on the Epidemiology of Disasters (CRED), UCLouvain
- **Website**: https://www.emdat.be/
- **Data Type**: Historical disaster statistics
- **License**: Public datasets available via HDX (Humanitarian Data Exchange)

### HDX Dataset for Vietnam
- **URL**: https://data.humdata.org/dataset/emdat-country-profiles-vnm
- **Format**: Excel (.xlsx)
- **Content**: Aggregated disaster statistics by year (2000-2026)
- **Metrics**:
  - Number of disasters
  - Total people affected
  - Total deaths
  - Economic losses

### Download Command
```bash
# Download from HDX (requires manual URL extraction)
# Dataset: EMDAT-country-profiles_VNM_2026_07_08.xlsx
```

### Data Format
Each row contains:
- Year
- Disaster subtype
- Number of disasters
- People affected
- Deaths
- Economic damage (original + adjusted)

---

## 5. Vietnam Government Data Sources

### 5.1 VDDMA (Vietnam Disaster and Dyke Management Authority)

- **Website**: https://phongchongthientai.mard.gov.vn/
- **Portal**: https://vndms.dmptc.gov.vn/
- **Status**: ⚠️ No public API, web-based dashboards only

### 5.2 NCHMF (National Center for Hydro-Meteorological Forecasting)

- **Website**: https://nchmf.gov.vn/
- **English**: https://nchmf.gov.vn/kttvsiteE/en-US/2/index.html
- **Content**:
  - Daily weather forecasts
  - Hydrological warnings
  - Tropical cyclone tracking
  - Flash flood/landslide alerts
- **Status**: ⚠️ Web interface only, no public API

### 5.3 Vietnam Disaster Monitoring System (VNDMS)

- **URL**: https://vndms.dmc.gov.vn/
- **Features**:
  - Real-time camera monitoring
  - Weather stations
  - Water level monitoring
  - Landslide monitoring
- **Status**: ⚠️ Internal government system

---

## 6. Data Scraping Opportunities

### 6.1 KTTV Weather Warnings

The existing `data/raw/kttv_dien_bien_*.json` files contain:
- Current weather observations
- District-level data
- Weather warnings in Vietnamese

### 6.2 News Sources (Already Active)

The project already scrapes:
- VnExpress: `data/disasters/vnexpress_*.json`
- Báo Chính: `data/disasters/baochinh_*.json`
- Tuổi Trẻ: `data/disasters/tuoitre_*.json`

---

## 7. Recommended Data Integration Strategy

### Tier 1: Immediate (Already Working)
- ✅ Open-Meteo real-time forecast
- ✅ Open-Meteo historical archive
- ✅ Existing news scrapers

### Tier 2: Short-term (Can Implement)
- ⏳ GDACS API integration for disaster alerts
- ⏳ Extended Open-Meteo historical data (2020-2024)
- ⏳ EM-DAT historical statistics download

### Tier 3: Long-term (Requires Collaboration)
- 🔒 Vietnam government data portal API access
- 🔒 NCHMF direct data feed
- 🔒 Provincial disaster management data

---

## 8. Sample Data Files Created

### 8.1 Historical Weather Sample (June 2024)
- **File**: `data/historical/open_meteo_june_2024_sample.json`
- **Content**: 10-day sample from monsoon season
- **Purpose**: Test historical data parsing

### 8.2 Disaster Events Sample
- **File**: `data/historical/gdacs_vietnam_sample.json`
- **Content**: Recent GDACS events affecting Vietnam
- **Purpose**: Disaster alert integration testing

### 8.3 Weather Warning Codes Reference
- **File**: `data/historical/weather_codes_reference.json`
- **Content**: WMO weather codes with Vietnamese descriptions

---

## 9. Code Examples

### Python: Fetch Historical Weather Data

```python
import requests
import json
from datetime import datetime, timedelta

def fetch_historical_weather(lat, lon, start_date, end_date, variables):
    """Fetch historical weather data from Open-Meteo Archive API"""
    base_url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(variables),
        "timezone": "Asia/Ho_Chi_Minh"
    }
    
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_year_of_data(lat, lon, year):
    """Fetch full year of daily weather data"""
    variables = [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "weather_code"
    ]
    
    start = f"{year}-01-01"
    end = f"{year}-12-31"
    
    return fetch_historical_weather(lat, lon, start, end, variables)

# Usage
data = fetch_year_of_data(21.38, 103.02, 2024)
print(json.dumps(data, indent=2))
```

### JavaScript/TypeScript: Fetch with Node.js

```javascript
async function fetchHistoricalWeather(lat, lon, startDate, endDate) {
  const baseUrl = 'https://archive-api.open-meteo.com/v1/archive';
  const params = new URLSearchParams({
    latitude: lat.toString(),
    longitude: lon.toString(),
    start_date: startDate,
    end_date: endDate,
    daily: 'temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code',
    timezone: 'Asia/Ho_Chi_Minh'
  });

  const response = await fetch(`${baseUrl}?${params}`);
  if (!response.ok) throw new Error('API request failed');
  return response.json();
}

// Usage
const weatherData = await fetchHistoricalWeather(
  21.38, 103.02, '2024-06-01', '2024-06-10'
);
console.log(JSON.stringify(weatherData, null, 2));
```

### Bash: Bulk Historical Data Download

```bash
#!/bin/bash
# Download multiple years of historical weather data

LAT=21.38
LON=103.02
OUTPUT_DIR="data/historical"

for YEAR in 2020 2021 2022 2023 2024; do
  echo "Downloading ${YEAR} data..."
  curl -s "https://archive-api.open-meteo.com/v1/archive?\
    latitude=${LAT}&longitude=${LON}&\
    start_date=${YEAR}-01-01&end_date=${YEAR}-12-31&\
    daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&\
    timezone=Asia/Ho_Chi_Minh" \
    -o "${OUTPUT_DIR}/dien_bien_${YEAR}.json"
  echo "Saved: ${OUTPUT_DIR}/dien_bien_${YEAR}.json"
done
```

---

## 10. Data Quality Notes

### Open-Meteo ERA5
- **Resolution**: 9km grid cells
- **Accuracy**: Reanalysis model, may differ from local observations
- **Elevation**: 493m at Điện Biên Phủ center
- **Mountain areas**: May underestimate precipitation in valleys

### GDACS
- **Coverage**: Only major disasters (>10 deaths or >100 affected)
- **Vietnam events**: Limited recent records for Điện Biên specifically
- **Recommendation**: Use as supplement, not primary source

### EM-DAT
- **Aggregation**: Country-level, not province-specific
- **Updates**: Quarterly
- **Format**: Excel requires parsing

---

## 11. Next Steps

1. **Download EM-DAT Vietnam data** from HDX manually
2. **Integrate GDACS alerts** into dashboard
3. **Build historical weather archive** (2020-2024)
4. **Add province-specific disaster scraping** from Vietnam news
5. **Request API access** from VDDMA/NCHMF for official data

---

*Document created: 2026-07-17*
*Last updated: 2026-07-17*
