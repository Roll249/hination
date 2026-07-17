# Hination - Disaster Prediction Model Architecture

## 1. Model Design for Disaster Zonation & Prediction

Dựa trên nghiên cứu của Mateu et al. (2025) về Spatio-Temporal Point Processes, chúng ta áp dụng phương pháp tương tự cho thiên tai Điện Biên.

### 1.1 Problem Formulation

```
Thiên tai tại Điện Biên = Spatial Point Process
- Events: lũ quét, sạt lở đất, sương muối, bão
- Location: tọa độ (lat, lon) của các điểm xảy ra thiên tai
- Time: thời gian xảy ra
- Marks: loại thiên tai, mức độ nghiêm trọng
```

### 1.2 Model Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         HINATION DISASTER PREDICTION MODEL                        │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                              INPUT LAYER                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Weather    │  │  Elevation  │  │   Slope     │  │   Land      │            │
│  │  Grid       │  │  Grid       │  │   Grid      │  │   Cover     │            │
│  │  (64x64)    │  │  (64x64)    │  │   (64x64)   │  │   (64x64)   │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         CONVOLUTIONAL BLOCK 1                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Input: (64, 64, 4)  →  Conv2D(32, 3x3) → BatchNorm → ReLU            │    │
│  │  → MaxPooling(2,2) → Dropout(0.2)                                      │    │
│  │  Output: (31, 31, 32)                                                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Conv2D(64, 3x3) → BatchNorm → ReLU                                    │    │
│  │  → MaxPooling(2,2) → Dropout(0.3)                                      │    │
│  │  Output: (14, 14, 64)                                                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Conv2D(128, 3x3) → BatchNorm → ReLU                                   │    │
│  │  → MaxPooling(2,2) → Dropout(0.3)                                      │    │
│  │  Output: (6, 6, 128)                                                    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         TEMPORAL ENCODING (LSTM)                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Input Sequence: Weather patterns over past 24 hours                    │    │
│  │  → LSTM(128, return_sequences=True)                                    │    │
│  │  → LSTM(64)                                                            │    │
│  │  Output: Temporal features (64,)                                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         FUSION LAYER                                      │    │
│  │  Concatenate[Spatial Features(6,6,128) + Temporal Features(64,)]        │    │
│  │  → Dense(256) → ReLU → Dropout(0.4)                                    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         OUTPUT LAYER                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Multi-Task Heads                                   │    │
│  │                                                                          │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │    │
│  │  │  Flood Risk      │  │  Landslide Risk  │  │  Cold Wave Risk  │       │    │
│  │  │  (Sigmoid)       │  │  (Sigmoid)       │  │  (Sigmoid)       │       │    │
│  │  │  [0, 1]         │  │  [0, 1]         │  │  [0, 1]         │       │    │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘       │    │
│  │                                                                          │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │                    Risk Zonation Map                              │  │    │
│  │  │                    (64x64x3) - RGB probability grid              │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Hawkes Process for Temporal Clustering

Áp dụng Self-Exciting Point Process cho dự đoán chuỗi thiên tai:

```
λ(t) = μ + Σᵢ α·exp(-β·(t - tᵢ))

Trong đó:
- λ(t): Cường độ xảy ra thiên tai tại thời điểm t
- μ: Cường độ nền (baseline)
- α: Hệ số kích hoạt (triggering effect)
- β: Hệ số suy giảm theo thời gian
- tᵢ: Thời điểm các sự kiện trước đó
```

### 1.4 Training Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TRAINING PIPELINE                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │       DATA COLLECTION               │
                    │  ┌───────────────────────────────┐  │
                    │  │ Open-Meteo API (9 huyện)    │  │
                    │  │ Historical disaster data      │  │
                    │  │ KTTV website scraping        │  │
                    │  │ VNDMS (if accessible)       │  │
                    │  └───────────────────────────────┘  │
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────┐
                    │       FEATURE ENGINEERING            │
                    │  ┌───────────────────────────────┐  │
                    │  │ Grid cells: 64x64             │  │
                    │  │ Features:                      │  │
                    │  │   - Rainfall (mm)             │  │
                    │  │   - Temperature (°C)          │  │
                    │  │   - Humidity (%)               │  │
                    │  │   - Elevation (m)              │  │
                    │  │   - Slope (degrees)            │  │
                    │  │   - Land cover type            │  │
                    │  └───────────────────────────────┘  │
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────┐
                    │       DATA AUGMENTATION             │
                    │  ┌───────────────────────────────┐  │
                    │  │ SOP Permutations (Mateu 2024) │  │
                    │  │ Time shift augmentation       │  │
                    │  │ Noise injection               │  │
                    │  └───────────────────────────────┘  │
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────┐
                    │       MODEL TRAINING                 │
                    │  ┌───────────────────────────────┐  │
                    │  │ Batch size: 32               │  │
                    │  │ Learning rate: 1e-4          │  │
                    │  │ Optimizer: Adam              │  │
                    │  │ Loss: BCE + Focal Loss       │  │
                    │  │ Epochs: 100 (early stop)    │  │
                    │  └───────────────────────────────┘  │
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────┐
                    │       EVALUATION                    │
                    │  ┌───────────────────────────────┐  │
                    │  │ Metrics:                      │  │
                    │  │   - AUC-ROC                   │  │
                    │  │   - Precision/Recall           │  │
                    │  │   - F1-Score                  │  │
                    │  │   - Brier Score               │  │
                    │  └───────────────────────────────┘  │
                    └─────────────────────────────────────┘
```

### 1.5 1-Hour Ahead Prediction

```
Input: Weather data at time t
Output: Risk probability at time t+1 hour

┌─────────────────────────────────────────────────────────────┐
│  Prediction Window = 1 hour                                 │
│                                                              │
│  [t-24h] [t-23h] ... [t-2h] [t-1h] [t] → [t+1h]        │
│  ─────────────────────────────────────────────────────     │
│  Historical data                      Current    Prediction   │
└─────────────────────────────────────────────────────────────┘
```

## 2. Map Integration

### 2.1 Map API Options

| Provider | Pros | Cons | Free Tier |
|----------|------|------|----------|
| **Leaflet + OpenStreetMap** | Miễn phí, mã nguồn mở | Cần tự host tiles | Unlimited |
| **Mapbox** | Đẹp, nhiều style | Cần API key | 50k requests/tháng |
| **Google Maps** | Chất lượng cao | Đắt tiền | $200 credit/tháng |
| **MapTiler** | Vietnam map tốt | Cần key | 100k requests/tháng |

**Recommendation**: Leaflet + OpenStreetMap cho prototype, Mapbox cho production.

### 2.2 Map Features for Disaster Warning

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAP OVERLAY LAYERS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Base Map (OpenStreetMap/Mapbox)                     │
│           ↓                                                     │
│  Layer 2: Elevation/Topography (SRTM Data)                     │
│           ↓                                                     │
│  Layer 3: Land Cover (ESA Copernicus)                         │
│           ↓                                                     │
│  Layer 4: Real-time Weather (from Open-Meteo)                 │
│           ↓                                                     │
│  Layer 5: Risk Zonation Overlay (Model Output)                │
│           - Green: Low risk                                     │
│           - Yellow: Moderate risk                              │
│           - Orange: High risk                                  │
│           - Red: Severe risk                                    │
│           ↓                                                     │
│  Layer 6: Alert Markers (Active warnings)                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Real-time Update Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         REAL-TIME SYSTEM ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Open-Meteo    │     │   Our Model      │     │    Web App      │
│   API           │────▶│   Inference      │────▶│    (Map)        │
│   (Every 15min) │     │   (GPU/CPU)    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Alert Engine  │
                    │   (Thresholds)  │
                    └─────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │   Zalo   │       │   SMS    │       │  Loa     │
    │   Bot    │       │  Gateway │       │ (Speaker)│
    └──────────┘       └──────────┘       └──────────┘
```

## 4. Tech Stack

```yaml
# Backend
- FastAPI: High-performance async API
- PyTorch: Model inference
- Redis: Caching weather data
- PostgreSQL: Historical data storage

# Frontend
- React 18: UI framework
- Leaflet: Map visualization
- TailwindCSS: Styling
- Chart.js: Charts/graphs

# ML
- PyTorch: Model training
- NVIDIA GPU: Training acceleration
- MLflow: Experiment tracking

# Deployment
- Docker: Containerization
- Kubernetes: Orchestration (optional)
- Cloudflare: CDN + Tunnel
```

## 5. Alert Thresholds

```python
ALERT_THRESHOLDS = {
    "flood": {
        "rainfall_1h_mm": 15,      # Moderate rain
        "rainfall_3h_mm": 30,      # Heavy rain
        "rainfall_6h_mm": 50,      # Very heavy rain
    },
    "landslide": {
        "slope_degrees": 25,        # Steep slope
        "rainfall_24h_mm": 100,     # Sustained rain
        "saturation_percent": 80,   # Soil saturation
    },
    "cold_wave": {
        "temp_min_celsius": 5,       # Cold
        "temp_min_celsius": 0,       # Frost
    },
    "storm": {
        "wind_speed_kmh": 62,       # Gale force
        "wind_speed_kmh": 89,       # Storm
    }
}
```

## 6. File Structure

```
hination/
├── model/
│   ├── train.py              # Training script
│   ├── model.py              # Model architecture
│   ├── dataset.py            # Dataset class
│   ├── transforms.py         # Data augmentation
│   └── requirements.txt       # ML dependencies
│
├── backend/
│   ├── main.py               # FastAPI app
│   ├── routes/
│   │   ├── weather.py        # Weather API
│   │   ├── alerts.py          # Alerts API
│   │   └── prediction.py       # Prediction API
│   ├── services/
│   │   ├── weather_service.py  # Open-Meteo integration
│   │   ├── prediction_service.py # Model inference
│   │   └── alert_service.py    # Alert generation
│   └── models/
│       └── schemas.py          # Pydantic schemas
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map.jsx         # Leaflet map
│   │   │   ├── WeatherCard.jsx # Weather display
│   │   │   ├── AlertPanel.jsx  # Alerts display
│   │   │   └── ForecastChart.jsx # Forecast graph
│   │   ├── pages/
│   │   │   └── Dashboard.jsx   # Main dashboard
│   │   └── App.jsx
│   └── package.json
│
├── docker-compose.yml
└── README.md
```
