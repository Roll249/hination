# HINATION - API & Data Sources Documentation

## Mục lục
1. [Tổng quan Data Sources](#1-tổng-quan-data-sources)
2. [Nguồn dữ liệu thời tiết](#2-nguồn-dữ-liệu-thời-tiết)
3. [Nguồn dữ liệu thiên tai](#3-nguồn-dữ-liệu-thiên-tai)
4. [API Endpoints](#4-api-endpoints)
5. [Data Models](#5-data-models)
6. [Historical Data](#6-historical-data)
7. [Training Data](#7-training-data-cho-model-ml)

---

## 1. Tổng quan Data Sources

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HINATION DATA FLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ Open-Meteo   │    │    KTTV      │    │   GDACS      │              │
│  │   API        │    │  Web Scrap   │    │   API        │              │
│  │ (Miễn phí)   │    │ (Trung tâm  │    │ (UN/OCHA)    │              │
│  │              │    │ Khí tượng)   │    │              │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                    │                    │                      │
│         └────────────────────┼────────────────────┘                      │
│                              ▼                                           │
│                    ┌──────────────────┐                                 │
│                    │  Weather Scraper │                                 │
│                    │ (scraper/)       │                                 │
│                    └────────┬─────────┘                                 │
│                             │                                           │
│              ┌──────────────┼──────────────┐                           │
│              ▼              ▼              ▼                             │
│       ┌───────────┐ ┌───────────┐ ┌───────────┐                       │
│       │   data/   │ │   data/   │ │   data/   │                       │
│       │   raw/    │ │   cache/  │ │ historical/                      │
│       └───────────┘ └───────────┘ └───────────┘                       │
│                             │                                           │
│                             ▼                                           │
│                    ┌──────────────────┐                                 │
│                    │  Risk Assessment │                                 │
│                    │ (demo/risk_pred) │                                 │
│                    └────────┬─────────┘                                 │
│                             │                                           │
│                             ▼                                           │
│                    ┌──────────────────┐                                 │
│                    │    Frontend      │                                 │
│                    │   Dashboard      │                                 │
│                    └──────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Nguồn dữ liệu thời tiết

### 2.1 Open-Meteo API (Nguồn chính)

**Website:** https://open-meteo.com/

**Loại:** Miễn phí, không cần API key

**Endpoints:**

| Endpoint | Mô tả | Độ phân giải |
|----------|--------|--------------|
| `/v1/forecast` | Dự báo thời tiết | 0.1° (~11km) |
| `/v1/archive` | Dữ liệu lịch sử (ERA5) | 0.25° |

**Parameters cho forecast:**
```
latitude: float (21.0 - 22.5)
longitude: float (102.0 - 104.0)
hourly: temperature_2m, relative_humidity_2m, precipitation, weather_code, wind_speed_10m, wind_direction_10m
daily: temperature_2m_max, temperature_2m_min, precipitation_sum, weather_code
timezone: Asia/Ho_Chi_Minh
forecast_days: 7
```

**Files sử dụng:**
- `data/weather_latest.json` - Dữ liệu mới nhất
- `data/weather_comprehensive.json` - Tổng hợp tất cả huyện
- `data/cache/open_meteo_*.json` - Cache theo tọa độ
- `data/raw/open_meteo_*.json` - Raw data

### 2.2 KTTV (Trung tâm Khí tượng Thủy văn)

**Website:** https://kttvttb.vn/

**Loại:** Web Scraping

**Data scraped:**
- Dữ liệu quan trắc hiện tại
- Cảnh báo thời tiết
- Dự báo địa phương

**Files:**
- `data/raw/kttv_dien_bien_latest.json`
- `data/raw/kttv_dien_bien_YYYYMMDD_HHMMSS.json`

### 2.3 NCHMF (Trung tâm Hải văn Quốc gia)

**Website:** https://nchmf.gov.vn/

**Loại:** Cảnh báo bão

**Files:**
- `data/disasters/baochinh_*.json`

---

## 3. Nguồn dữ liệu thiên tai

### 3.1 GDACS (Global Disaster Alert and Coordination System)

**Website:** https://www.gdacs.org/

**API:** https://www.gdacs.org/datahub/

**Loại:** UN/OCHA - Miễn phí

**Data:**
- Cyclone alerts
- Earthquake alerts
- Flood alerts

**Files:**
- `data/historical/gdacs_vietnam_sample.json`

### 3.2 VNDMS (Vietnam Disaster Monitoring System)

**Website:** https://vndms.gov.vn/

**Loại:** Chính phủ (Cần tài khoản)

**Tham khảo:** `docs/VNDMS_ANALYSIS.md`

### 3.3 Tin tức thiên tai

**Sources:**
- VnExpress: https://vnexpress.net/
- Tuổi Trẻ: https://tuoitre.vn/

**Files:**
- `data/disasters/news_*.json`
- `data/disasters/vnexpress_*.json`
- `data/disasters/tuoitre_*.json`

---

## 4. API Endpoints

### 4.1 Backend API (Port 4000)

```
┌─────────────────────────────────────────────────────────┐
│                    BACKEND API                          │
│                    Port: 4000                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  GET  /health                   Health check            │
│                                                          │
│  GET  /api/auth/login           Đăng nhập               │
│  POST /api/auth/register        Đăng ký                  │
│                                                          │
│  GET  /api/admin/districts      Danh sách huyện         │
│  GET  /api/admin/weather       Dữ liệu thời tiết       │
│  GET  /api/admin/alerts        Cảnh báo hiện tại       │
│  POST /api/admin/alerts         Tạo cảnh báo           │
│                                                          │
│  POST /api/scoring/calculate   Tính điểm rủi ro        │
│  GET  /api/scoring/history     Lịch sử tính điểm       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Weather Endpoints

```
GET  /api/weather/latest              - Dữ liệu thời tiết mới nhất
GET  /api/weather/forecast?days=7    - Dự báo N ngày
GET  /api/weather/historical         - Dữ liệu lịch sử
GET  /api/weather/codes              - Mã thời tiết WMO
```

### 4.3 Risk Assessment Endpoints

```
GET  /api/risk/assessment            - Đánh giá rủi ro tất cả huyện
GET  /api/risk/district/{id}         - Rủi ro theo huyện
POST /api/risk/calculate             - Tính rủi ro (body: district_id, weather)
GET  /api/vndms/framework            - Framework VNDMS
```

### 4.4 Alert Endpoints

```
GET  /api/alerts                     - Danh sách cảnh báo
GET  /api/alerts/{type}              - Cảnh báo theo loại
POST /api/alerts/acknowledge         - Xác nhận đã đọc
```

### 4.5 Demo Server (Port 5000)

```
GET  /demo/index.html                - Demo risk assessment
GET  /data/risk_assessment.json      - JSON risk data
```

---

## 5. Data Models

### 5.1 Weather Data Model

```typescript
interface WeatherData {
  province: string;
  province_code: string;
  fetched_at: string;          // ISO 8601
  data_source: string;         // "Open-Meteo API"
  
  districts: {
    [district_id: string]: {
      name: string;
      coordinates: {
        lat: number;
        lon: number;
      };
      elevation_m: number;
      
      current: {
        time: string;
        temperature_c: number;
        feels_like_c: number;
        humidity_percent: number;
        precipitation_mm: number;
        weather_code: number;         // WMO code
        weather_description: string;
        cloud_cover_percent: number;
        wind_speed_kmh: number;
        wind_direction_deg: number;
        pressure_hpa: number;
      };
      
      daily_forecast: Array<{
        date: string;
        weather_code: number;
        weather_description: string;
        temp_max: number;
        temp_min: number;
        precipitation_sum: number;
        precipitation_probability: number;
        wind_speed_max: number;
        sunrise: string;
        sunset: string;
      }>;
    };
  };
}
```

### 5.2 Risk Assessment Model

```typescript
interface RiskAssessment {
  generated_at: string;
  data_source: string;
  province: string;
  
  districts: {
    [district_id: string]: {
      name: string;
      coordinates: { lat: number; lon: number };
      
      risk: {
        level: number;          // 1-5 (VNDMS standard)
        score: number;          // Raw risk score
        level_text: string;     // "AN TOÀN", "CHÚ Ý", "CẢNH BÁO", "NGUY HIỂM"
        color: string;          // Emoji indicator
        factors: string[];      // Risk factors
        warnings: string[];     // Warning messages
      };
      
      weather_forecast: {
        precipitation: number[];  // Next 7 days
        temp_max: number[];
        temp_max: number[];
      };
      
      fatality_prediction: {
        evacuation_needed: boolean;
        estimated_affected: number;
        death_rate_estimate: number;
        shelter_needed: number;
        primary_hazard: string;
      };
    };
  };
}
```

### 5.3 Alert Model

```typescript
interface Alert {
  id: string;
  type: 'heavy_rain' | 'cold_wave' | 'storm' | 'flood' | 'landslide';
  severity: 'info' | 'warning' | 'danger';
  district_id: string;
  district_name: string;
  
  value: number;
  unit: string;
  
  action_vi: string;
  action_th: string;           // Tiếng Thái
  action_hmong: string;       // Tiếng H'Mông
  
  timestamp: string;
  acknowledged: boolean;
  acknowledged_at?: string;
}
```

### 5.4 WMO Weather Codes

```typescript
const WEATHER_CODES = {
  // Clear
  0: { vi: "Trời quang", en: "Clear sky" },
  1: { vi: "Ít mây", en: "Mainly clear" },
  2: { vi: "Nhiều mây", en: "Partly cloudy" },
  3: { vi: "U ám", en: "Overcast" },
  
  // Drizzle
  51: { vi: "Mưa phùn nhẹ", en: "Light drizzle" },
  53: { vi: "Mưa phùn vừa", en: "Moderate drizzle" },
  55: { vi: "Mưa phùn nặng", en: "Dense drizzle" },
  
  // Rain
  61: { vi: "Mưa nhẹ", en: "Slight rain" },
  63: { vi: "Mưa vừa", en: "Moderate rain" },
  65: { vi: "Mưa to", en: "Heavy rain" },
  
  // Showers
  80: { vi: "Mưa rào nhẹ", en: "Slight rain showers" },
  81: { vi: "Mưa rào vừa", en: "Moderate rain showers" },
  82: { vi: "Mưa rào nặng", en: "Violent rain showers" },
  
  // Thunderstorm
  95: { vi: "Giông", en: "Thunderstorm" },
  96: { vi: "Giông kèm mưa đá nhẹ", en: "Thunderstorm with slight hail" },
  99: { vi: "Giông kèm mưa đá nặng", en: "Thunderstorm with heavy hail" }
};
```

---

## 6. Historical Data

### 6.1 Cấu trúc thư mục

```
data/
├── historical/
│   ├── dien_bien_2024_06.json      # Tháng 6/2024
│   ├── open_meteo_june_2024_sample.json
│   ├── open_meteo_monsoon_2024_sample.json
│   ├── weather_codes_reference.json  # WMO codes
│   ├── gdacs_vietnam_sample.json    # GDACS sample
│   └── fetch_disaster_alerts.py     # Script thu thập
│
├── raw/                             # Raw data từ sources
│   ├── open_meteo_{lat}_{lon}_latest.json
│   ├── open_meteo_{lat}_{lon}_YYYYMMDD_HHMMSS.json
│   ├── kttv_dien_bien_latest.json
│   └── all_districts_latest.json
│
├── cache/                           # Cached data
│   └── open_meteo_{lat}_{lon}.json
│
├── disasters/                        # Tin tức thiên tai
│   ├── baochinh_YYYYMMDD_HHMMSS.json
│   ├── news_YYYYMMDD_HHMMSS.json
│   ├── vnexpress_YYYYMMDD_HHMMSS.json
│   └── tuoitre_YYYYMMDD_HHMMSS.json
│
└── archive/                          # Archived data
    └── weather_aggregated_*.json
```

### 6.2 Historical Data Sources

| File | Source | Period | Format |
|------|--------|--------|--------|
| `dien_bien_2024_06.json` | Open-Meteo Archive | June 2024 | ERA5 |
| `open_meteo_june_2024_sample.json` | Open-Meteo Archive | June 2024 | Sample |
| `open_meteo_monsoon_2024_sample.json` | Open-Meteo Archive | Monsoon 2024 | Sample |
| `gdacs_vietnam_sample.json` | GDACS | Ongoing | JSON |

---

## 7. Training Data cho Model ML

### 7.1 Model Architecture

**File:** `model/model.py`

```
DisasterPredictionModel
├── SpatialEncoder (CNN)
│   ├── Conv2d → BatchNorm → ReLU → MaxPool
│   ├── Conv2d → BatchNorm → ReLU → MaxPool
│   └── Conv2d → BatchNorm → ReLU → MaxPool
│
├── TemporalEncoder (LSTM)
│   ├── Bidirectional LSTM
│   └── Output: 256 features
│
├── HawkesAttention (Self-Attention)
│   └── Multi-head attention
│
├── Fusion Layer
│   ├── Linear → BatchNorm → ReLU → Dropout
│   └── Linear → BatchNorm → ReLU → Dropout
│
└── Output Heads
    ├── flood_head (Binary classification)
    ├── landslide_head (Binary classification)
    ├── cold_wave_head (Binary classification)
    └── zonation_decoder (Segmentation map)
```

### 7.2 Training Data Structure

```python
class DisasterDataset:
    """
    Mỗi sample chứa:
    - Spatial features: Grid 4 channels (rainfall, temp, humidity, wind)
    - Temporal features: Sequence 24 giờ × 8 features
    - Labels: flood, landslide, cold_wave (0-1)
    """
    
    # Spatial Grid: (batch, 4, 64, 64)
    # Channels: [rainfall, temperature, humidity, wind]
    
    # Temporal Sequence: (batch, 24, 8)
    # Features: [rainfall, temp, humidity, wind, pressure, cloud, 
    #            hours_of_rain, consecutive_rain_hours]
```

### 7.3 Training Pipeline

```python
# Files cần thiết cho training:
model/
├── model.py          # Model architecture
├── train.py          # Training loop
└── checkpoints/      # Saved models
    ├── checkpoint_epoch_*.pt
    └── latest.pt

# Run training:
cd model
python train.py --samples 10000 --epochs 50 --batch-size 32

# Generated synthetic data:
# - weather_data: List[Dict] - 24h weather sequences
# - labels: List[Dict] - flood/landslide/cold_wave probabilities
```

### 7.4 Feature Engineering

| Feature | Source | Range | Description |
|---------|--------|-------|-------------|
| `rainfall` | Open-Meteo | 0-100mm | Lượng mưa |
| `temperature` | Open-Meteo | -10 to 45°C | Nhiệt độ |
| `humidity` | Open-Meteo | 0-100% | Độ ẩm |
| `wind_speed` | Open-Meteo | 0-100 km/h | Tốc độ gió |
| `pressure` | Open-Meteo | hPa | Áp suất |
| `cloud_cover` | Open-Meteo | 0-100% | Độ che phủ mây |
| `hours_of_rain` | Computed | 0-24h | Số giờ mưa |
| `consecutive_rain_hours` | Computed | 0-48h | Số giờ mưa liên tiếp |

### 7.5 Risk Thresholds (VNDMS Framework)

```yaml
alerts:
  heavy_rain:
    precipitation_mm_per_hour: 15
    severity: warning
    
  extreme_rain:
    precipitation_mm_per_hour: 30
    severity: danger
    
  cold_wave:
    temperature_min_celsius: 5
    severity: warning
    
  frost:
    temperature_min_celsius: 0
    severity: danger
    
  strong_wind:
    wind_speed_kmh: 40
    severity: warning
    
  storm:
    wind_speed_kmh: 62
    severity: danger
```

---

## 8. Collection Scripts

### 8.1 Weather Scraper

**File:** `scraper/weather_scraper.py`

```bash
# Thu thập tất cả huyện
cd scraper
python weather_scraper.py --all

# Thu thập 1 huyện
python weather_scraper.py --district dien_bien_phu

# Thu thập historical data
python weather_scraper.py --historical --year 2024 --month 6
```

### 8.2 Disaster News Scraper

**File:** `scraper/disaster_news_scraper.py`

```bash
# Thu thập tin tức
cd scraper
python disaster_news_scraper.py --source vnexpress --days 7
python disaster_news_scraper.py --source tuoitre --days 7
```

### 8.3 Collect All

**File:** `scraper/collect_all.py`

```bash
# Thu thập tất cả dữ liệu
cd scraper
python collect_all.py
```

---

## 9. Quick Reference

### API URLs

| Service | URL | Port |
|---------|-----|------|
| Backend | http://localhost:4000 | 4000 |
| Frontend | http://localhost:3100 | 3100 |
| Demo | http://localhost:5000/demo | 5000 |

### Key Files

| File | Purpose |
|------|---------|
| `data/weather_latest.json` | Latest weather data |
| `data/risk_assessment.json` | Risk assessment results |
| `data/alerts_current.json` | Current alerts |
| `demo/risk_prediction.py` | Risk prediction script |
| `model/train.py` | ML model training |

### District IDs

| ID | Name | Lat | Lon |
|----|------|-----|-----|
| `dien_bien_phu` | TP Điện Biên Phủ | 21.3869 | 103.0228 |
| `tuan_giao` | Huyện Tuần Giáo | 21.6167 | 103.25 |
| `tua_chua` | Huyện Tủa Chùa | 21.4667 | 103.4333 |
| `muong_cha` | Huyện Mường Chà | 22.0833 | 102.4333 |
| `muong_nhe` | Huyện Mường Nhé | 22.4167 | 102.3 |
| `dien_bien_dong` | Huyện Điện Biên Đông | 21.1833 | 103.55 |
| `nam_po` | Huyện Nậm Pồ | 21.65 | 103.1167 |
| `muong_ang` | Huyện Mường Ảng | 21.8167 | 103.0833 |
| `muong_lay` | Thị xã Mường Lay | 22.5 | 102.6833 |

---

*Document generated: 2026-07-17*
*Hination Hackathon - Điện Biên*
