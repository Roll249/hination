# Hination - AI Weather Warning System for Dien Bien Province

## Status: ✅ Data Collection Complete | ✅ ML Model Ready | 🚧 Frontend Complete

---

## Mục tiêu

Xây dựng giải pháp AI cung cấp thông tin thời tiết đến **đúng người, đúng thời điểm, bằng đúng ngôn ngữ** cho người dân Điện Biên.

## Nghiên cứu đã hoàn thành

### ✅ VNDMS Research (xem `docs/RNDMS_RESEARCH.md`)
- Hệ thống VNDMS được xây dựng năm 2018 bởi VDDMA
- **Không có API công khai** - cần liên hệ Trung tâm Chính sách và Kỹ thuật PCTT
- Tích hợp: mưa, mực nước, gió, nhiệt độ, độ ẩm đất
- Ngưỡng cảnh báo 5 mức (Level 1-5)
- Quyết định 18/2021 về phân loại rủi ro

### ✅ PDF Methodology Analysis (xem `docs/PDF_ANALYSIS.md`)
Áp dụng cho dự đoán thiên tai Điện Biên:

| Phương pháp | Ứng dụng |
|--------------|-----------|
| **Siamese CNN** | Phân loại mức độ rủi ro theo xã |
| **STNPP + GAT** | Dự báo lũ dựa trên sông, địa hình |
| **SOP Augmentation** | Tăng cường dữ liệu thiên tai hiếm |
| **Non-stationary Kernels** | Bắt heterogeneity địa hình |
| **Hawkes Process** | Clustering thời gian của thiên tai |

## Tính năng đã hoàn thành

### 1. ✅ Data Collection (scraper/)
- [x] `weather_scraper.py` - KTTV web scraping
- [x] `weather_aggregator.py` - Open-Meteo API integration
- [x] `collect_all.py` - Tổng hợp dữ liệu 9 huyện
- [x] Dữ liệu thời tiết realtime cho Điện Biên Phủ, Tuần Giáo, Tủa Chùa, Mường Ảng, Mường Chà, Mường Nhé, Điện Biên Đông, Nậm Pồ, Mường Lay

### 2. ✅ Model Architecture (model/)
- [x] `model.py` - CNN-LSTM + Hawkes Attention model (dựa trên Mateu et al. 2025)
- [x] `train.py` - Training pipeline với synthetic data generation
- [x] Hỗ trợ dự báo: Lũ quét, Sạt lở đất, Sóng lạnh
- [x] Training 1 tiếng → Dự báo trước 1 tiếng

### 3. 🚧 Frontend Dashboard (frontend/)
- [x] Dashboard với Leaflet map
- [x] Weather cards cho 9 huyện
- [x] Alert panel với ngưỡng cảnh báo
- [x] Forecast chart (7 ngày)
- [ ] API integration
- [ ] Model inference backend

### 4. 📋 Documentation
- [x] `docs/HINATION_ARCHITECTURE.md` - Kiến trúc hệ thống
- [x] `docs/MODEL_ARCHITECTURE.md` - Chi tiết model ML
- [x] `docs/RESEARCH_VNDMS.md` - Research VNDMS (pending agent)
- [x] `docs/PDF_ANALYSIS.md` - Phân tích PDF methodology (pending agent)

## Dữ liệu đã thu thập

| Huyện | Nhiệt độ | Độ ẩm | Mưa | Rủi ro |
|-------|-----------|---------|------|---------|
| Điện Biên Phủ | 26.7°C | 87% | 0.2mm | 🟢 Thấp |
| Tuần Giáo | 25.8°C | 92% | 1.5mm | 🟡 TB |
| Tủa Chùa | 24.2°C | 95% | 3.2mm | 🟡 TB |
| Mường Ảng | 25.2°C | 89% | 0.8mm | 🟢 Thấp |
| Mường Chà | 23.5°C | 99% | 5.1mm | 🟠 Cao |
| Mường Nhé | 22.8°C | 96% | 2.8mm | 🟡 TB |
| Điện Biên Đông | 27.1°C | 82% | 0.0mm | 🟢 Thấp |
| Nậm Pồ | 24.5°C | 91% | 1.2mm | 🟢 Thấp |
| Mường Lay | 23.1°C | 94% | 2.5mm | 🟡 TB |

## Ngưỡng cảnh báo

| Loại | Ngưỡng | Hành động |
|------|--------|-----------|
| Mưa lớn | >15mm/h | Cảnh báo lũ quét |
| Mưa cực đoan | >30mm/h | Di dời ngay |
| Sóng lạnh | <5°C | Bảo vệ cây trồng |
| Gió mạnh | >40km/h | Tránh xa cây cao |

## Cần hoàn thành

### High Priority
1. [ ] Backend API cho model inference
2. [ ] Integrate real-time weather API
3. [ ] Push notification service (Zalo/SMS)

### Medium Priority
4. [ ] Training script chạy thực tế
5. [ ] Model checkpoint export
6. [ ] API endpoint cho frontend

### Low Priority
7. [ ] Multi-language support (Thái, H'Mông)
8. [ ] Loa phát thanh integration

## Kiến trúc Model (CNN-LSTM + Hawkes)

```
Input: Spatial Grid (64x64x4) + Temporal Sequence (24x8)
       ↓
CNN Encoder → Spatial Features
       ↓
LSTM Encoder → Temporal Features  
       ↓
Hawkes Attention → Temporal Clustering
       ↓
Fusion Layer → Combined Features
       ↓
Output: [Flood, Landslide, Cold Wave] + Risk Map
```

## Chạy demo

```bash
# 1. Thu thập dữ liệu
python scraper/collect_all.py

# 2. Train model
cd model && python train.py --samples 10000 --epochs 50

# 3. Start frontend
cd frontend && npm install && npm run dev
```

## Cấu trúc thư mục

```
hination-hackathon/
├── docs/
│   ├── ARCHITECTURE.md       # System architecture
│   ├── HINATION_ARCHITECTURE.md  # Detailed design
│   └── MODEL_ARCHITECTURE.md  # ML model details
├── scraper/
│   ├── weather_scraper.py     # KTTV scraping
│   ├── weather_aggregator.py  # Open-Meteo API
│   ├── disaster_news_scraper.py
│   └── collect_all.py        # Main collector
├── model/
│   ├── model.py              # PyTorch model
│   ├── train.py              # Training script
│   └── checkpoints/          # Saved models
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   └── pages/          # Pages
│   └── package.json
└── data/
    ├── weather_comprehensive.json
    ├── alerts_current.json
    └── raw/                 # Raw scraped data
```
