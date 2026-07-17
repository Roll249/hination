# Hination - Kiến Trúc Hệ Thống Cảnh Báo Thời Tiết & Thiên Tai Điện Biên

## 1. Tổng Quan Hệ Thống

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INTERNET / NGƯỜI DÙNG                               │
│                                                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │   Mobile     │  │   Web App    │  │   Zalo Bot   │  │   SMS/API    │  │
│   │   (React)    │  │   (Next.js)  │  │   (Chatbot)  │  │   (Telegram) │  │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└──────────┼─────────────────┼─────────────────┼─────────────────┼──────────┘
           │                 │                 │                 │
           ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY / LOAD BALANCER                          │
│                         (Nginx hoặc Cloudflare)                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND SERVICE                                    │
│                           (Node.js/Express)                                  │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                        Weather Service                                │  │
│   │   - Open-Meteo API Integration                                       │  │
│   │   - KTTV Web Scraping                                                │  │
│   │   - Data Processing & Normalization                                  │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                        Alert Engine                                   │  │
│   │   - Threshold Monitoring                                              │  │
│   │   - Alert Generation                                                 │  │
│   │   - Multi-language Message Generation (Thai, Hmong, Vietnamese)      │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                        Notification Service                           │  │
│   │   - Zalo OA Integration                                              │  │
│   │   - SMS Gateway (VNPT/Gateway)                                      │  │
│   │   - Broadcast Speaker Command                                         │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                        Location Service                               │  │
│   │   - District/Commune Mapping                                         │  │
│   │   - Ethnic Language Selection                                        │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL     │     │     Redis       │     │    RabbitMQ     │
│   (Weather DB)  │     │   (Cache/Locks) │     │   (Job Queue)   │
│   :5444         │     │   :6380         │     │   :5673         │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Worker      │
                                              │   (AI Process)  │
                                              │   - Translation │
                                              │   - TTS/Images │
                                              └─────────────────┘
```

## 2. Nguồn Dữ Liệu

### 2.1 Nguồn Chính (Miễn phí, Độ phân giải cao)

| Nguồn | Loại dữ liệu | API/URL | Độ phân giải | Cập nhật |
|-------|--------------|---------|--------------|----------|
| **Open-Meteo** | Thời tiết, dự báo | `api.open-meteo.com` | 0.1° (~11km) | 15 phút |
| **KTTV Trung Trung Bộ** | Thời tiết địa phương | `kttvttb.vn` | Tỉnh | Hàng giờ |
| **NCHMF** | Cảnh báo bão | `nchmf.gov.vn` | Quốc gia | Realtime |

### 2.2 Nguồn Tham Khảo (Cần đăng nhập)

| Nguồn | Loại dữ liệu | Ghi chú |
|-------|--------------|---------|
| **VNDMS** | Giám sát thiên tai, mưa, mực nước | Yêu cầu tài khoản chính quyền |
| **App-VNDMS** | Cảnh báo realtime | Chỉ cho cán bộ chính quyền |

### 2.3 Cấu trúc Dữ liệu Thời Tiết

```typescript
interface WeatherData {
  location: {
    district_id: string;
    name: string;
    coordinates: { lat: number; lon: number };
    elevation_m: number;
  };
  
  current: {
    time: string;
    temperature_c: number;
    feels_like_c: number;
    humidity_percent: number;
    precipitation_mm: number;
    weather_code: number;
    weather_description: string;
    wind_speed_kmh: number;
    wind_direction_deg: number;
    pressure_hpa: number;
  };
  
  daily_forecast: Array<{
    date: string;
    weather_description: string;
    temp_max: number;
    temp_min: number;
    precipitation_sum: number;
    precipitation_probability: number;
    wind_speed_max: number;
    sunrise: string;
    sunset: string;
  }>;
  
  alerts: Alert[];
}

interface Alert {
  type: 'heavy_rain' | 'cold_wave' | 'storm' | 'flood' | 'frost';
  severity: 'info' | 'warning' | 'danger';
  value: number;
  unit: string;
  action: string; // Tiếng Việt
  action_ethnic?: string; // Thái/H'Mông
  timestamp: string;
}
```

## 3. Ngưỡng Cảnh Báo cho Điện Biên

```yaml
# Alert Thresholds for Dien Bien Province

alerts:
  heavy_rain:
    precipitation_mm_per_hour: 15
    severity: warning
    icon: 🌧️
    action_vi: "Cảnh báo lũ quét, sạt lở đất ở khu vực miền núi"
    action_th: "เตือนดินถล่มในพื้นที่ภูเขา"
    action_hmong: "Qhia mob rau txog kev nyob hauv cov xeem tshaj lawr"
    
  extreme_rain:
    precipitation_mm_per_hour: 30
    severity: danger
    icon: 🚨
    action_vi: "NGUY HIỂM! Di dời ngay đến nơi an toàn"
    action_th: "อันตราย! อพยพไปยังที่ปลอดภัย"
    action_hmong: "Tsis tau mob! Txhob mus rau qhov chaw muaj kev nyab xeeb"
    
  cold_wave:
    temperature_min_celsius: 5
    severity: warning
    icon: 🥶
    action_vi: "Sương muối có thể gây hại cây trồng, gia súc"
    action_th: "น้ำค้างแข็งอาจทำลายพืชผล"
    action_hmong: "Qab zib tuaj yeem ua hauv kom tsis zoo rau noc xwm"

  frost:
    temperature_min_celsius: 0
    severity: danger
    icon: ❄️
    action_vi: "Nguy hiểm! Bảo vệ gia súc, cây trồng"
    action_th: "อันตราย! ปกป้องสัตว์และพืชผล"
    action_hmong: "Tsis tau mob! Txo tshuaj ntsuag, noc xwm"

  strong_wind:
    wind_speed_kmh: 40
    severity: warning
    icon: 💨
    action_vi: "Gió mạnh, tránh xa cây cao và công trình"
    action_th: "ลมแรง ห่างจากต้นไม้สูงและอาคาร"
    action_hmong: "ntuj txhij, txhob nyob ze cov ntim siab thiab tsev"

  storm:
    wind_speed_kmh: 62
    severity: danger
    icon: 🌀
    action_vi: "BÃO! Tìm nơi trú ẩn an toàn ngay"
    action_th: "พายุ! ค้นหาที่หลบภัยที่ปลอดภัย"
    action_hmong: "Tshuab! Nrhiav qhov chaw muaj kev nyab xeeb tam sim no"

  high_humidity:
    humidity_percent: 99
    severity: info
    icon: 🌫️
    action_vi: "Độ ẩm rất cao, cảnh giác sương mù dày đặc"
    action_th: "ความชื้นสูงมาก ระวังหมอกหนา"
    action_hmong: "Ntim qab zib siab heev, muaj ntsuag ntsuag"
```

## 4. Các Kênh Phân Phối

### 4.1 Zalo Official Account (Zalo OA)

```javascript
// Gửi thông báo qua Zalo
const sendZaloNotification = async (userId, alert) => {
  const message = {
    uid: userId,
    message: {
      text: alert.message,
      attachment: {
        type: "image",
        url: alert.icon_url // Hình ảnh cảnh báo
      }
    }
  };
  // Sử dụng Zalo API với access token
};
```

### 4.2 SMS Gateway

```javascript
// Gửi SMS cảnh báo
const sendSMS = async (phoneNumber, alert) => {
  // Sử dụng VNPT SMS Gateway hoặc Viettel
  const message = `⚠️${alert.type}: ${alert.action_vi}`;
  // Giới hạn 160 ký tự cho SMS
};
```

### 4.3 Public Speaker System (Loa phát thanh)

```javascript
// Tạo lệnh phát thanh
const generateSpeakerCommand = (alert, district) => {
  return {
    district_id: district,
    command: "PLAY_WARNING",
    priority: alert.severity === 'danger' ? 1 : 2,
    audio_url: `/audio/${alert.type}_${alert.severity}_${district}.mp3`,
    repeat: alert.severity === 'danger' ? 3 : 1
  };
};
```

### 4.4 Translation cho Ngôn ngữ Dân tộc

```typescript
// Dịch sang tiếng Thái
const translateToThai = (text: string): string => {
  // Sử dụng Google Translate API hoặc model địa phương
};

// Dịch sang tiếng H'Mông
const translateToHmong = (text: string): string => {
  // Model dịch chuyên biệt cho tiếng H'Mông
};
```

## 5. Cấu trúc Database

```sql
-- Bảng thời tiết theo huyện
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    district_id VARCHAR(50) NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    temperature_c DECIMAL(4,1),
    humidity_percent INTEGER,
    precipitation_mm DECIMAL(5,2),
    wind_speed_kmh DECIMAL(5,1),
    weather_code INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng cảnh báo
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    district_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(20) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    value DECIMAL(10,2),
    unit VARCHAR(10),
    message_vi TEXT,
    message_th TEXT,
    message_hmong TEXT,
    triggered_at TIMESTAMP NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP
);

-- Bảng người dùng đăng ký nhận thông báo
CREATE TABLE subscribers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20),
    zalo_id VARCHAR(50),
    district_id VARCHAR(50),
    language VARCHAR(10) DEFAULT 'vi',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng lịch sử phát thanh
CREATE TABLE broadcast_history (
    id SERIAL PRIMARY KEY,
    district_id VARCHAR(50),
    alert_id INTEGER REFERENCES alerts(id),
    played_at TIMESTAMP,
    status VARCHAR(20)
);

-- Index
CREATE INDEX idx_weather_district_time ON weather_data(district_id, recorded_at DESC);
CREATE INDEX idx_alerts_district ON alerts(district_id, triggered_at DESC);
CREATE INDEX idx_subscribers_district ON subscribers(district_id);
```

## 6. Lộ Trình Triển Khai

### Phase 1: Data Collection (1-2 tuần)
- [x] Open-Meteo API integration (hoàn thành)
- [x] KTTV web scraping (hoàn thành)
- [ ] Historical disaster data collection
- [ ] District boundary mapping

### Phase 2: Alert Engine (2 tuần)
- [ ] Threshold monitoring system
- [ ] Alert generation logic
- [ ] Multi-language message generation

### Phase 3: Notification Channels (2 tuần)
- [ ] Zalo OA integration
- [ ] SMS gateway setup
- [ ] Speaker command system

### Phase 4: UI/UX (2 tuần)
- [ ] Web dashboard cho quản lý
- [ ] Mobile app cho người dân
- [ ] Visual warning system (icons, colors)

### Phase 5: Testing & Deployment (1 tuần)
- [ ] UAT với người dân địa phương
- [ ] Pilot tại 1-2 xã
- [ ] Production deployment

## 7. So Sánh với VNDMS

| Tính năng | VNDMS | Hination |
|-----------|-------|----------|
| **Mục tiêu** | Giám sát cho chính quyền | Cảnh báo cho người dân |
| **Người dùng** | Cán bộ nhà nước | Người dân vùng cao |
| **Ngôn ngữ** | Tiếng Việt | Việt + Thái + H'Mông |
| **Kênh** | Web app | Zalo + SMS + Loa phát thanh |
| **Độ phân giải** | Trạm quan trắc | Tiểu vùng (xã/bản) |
| **API** | Không công khai | Open-Meteo (miễn phí) |

## 8. Chi Phí Ước Tính

| Thành phần | Chi phí/tháng |
|-----------|--------------|
| Server (VPS 4GB RAM) | ~$10-20 |
| Open-Meteo API | Miễn phí |
| Zalo OA | Miễn phí |
| SMS Gateway (10,000 SMS) | ~$20-30 |
| Domain + SSL | ~$5 |
| **Tổng** | **~$35-55** |

## 9. Tham Khảo Kiến Trúc VNDMS

Dựa trên nghiên cứu:

**VNDMS (Vietnam Disaster Monitoring System)**:
- Được xây dựng năm 2018 bởi Trung tâm Chính sách và Kỹ thuật phòng chống thiên tai
- Tích hợp: Khí tượng, thủy văn, hồ chứa, tàu thuyền
- Cảnh báo: Mưa >50mm/24h, gió mạnh, mực nước vượt mức
- Đối tượng: Cán bộ trực ban cấp trung ương và địa phương
- **Không có API công khai** - cần tài khoản chính quyền

**Nguồn tham khảo**:
- Website: https://vndms.gov.vn
- Hướng dẫn: http://dmc.gov.vn
- Trung tâm: Trung tâm Chính sách và Kỹ thuật PCTT (VNDMA)
