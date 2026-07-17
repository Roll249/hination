import express from 'express';
import cors from 'cors';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = 4000;

// Middleware
app.use(cors());
app.use(express.json());

// Helper to read JSON data files
const readDataFile = (filepath) => {
  try {
    return JSON.parse(readFileSync(filepath, 'utf-8'));
  } catch (e) {
    console.error(`Error reading ${filepath}:`, e.message);
    return null;
  }
};

// VNDMS Risk Level Framework (Decision 18/2021/QĐ-TTg)
const VNDMS_RISK_LEVELS = {
  1: { color: '#87CEEB', name: 'Rủi ro thấp', name_en: 'Low' },
  2: { color: '#FFFF00', name: 'Rủi ro trung bình', name_en: 'Medium' },
  3: { color: '#FFA500', name: 'Rủi ro lớn', name_en: 'High' },
  4: { color: '#FF0000', name: 'Rủi ro rất lớn', name_en: 'Very High' },
  5: { color: '#800080', name: 'Rủi ro thảm họa', name_en: 'Catastrophic' },
};

// Điện Biên districts
const DISTRICTS = {
  'dien_bien_phu': { name: 'Thành phố Điện Biên Phủ', lat: 21.3869, lon: 103.0228 },
  'tuan_giao': { name: 'Huyện Tuần Giáo', lat: 21.6167, lon: 103.2500 },
  'tua_chua': { name: 'Huyện Tủa Chùa', lat: 21.4667, lon: 103.4333 },
  'muong_cha': { name: 'Huyện Mường Chà', lat: 22.0833, lon: 102.4333 },
  'muong_nhe': { name: 'Huyện Mường Nhé', lat: 22.4167, lon: 102.3000 },
  'dien_bien_dong': { name: 'Huyện Điện Biên Đông', lat: 21.1833, lon: 103.5500 },
  'nam_po': { name: 'Huyện Nậm Pồ', lat: 21.6500, lon: 103.1167 },
  'muong_ang': { name: 'Huyện Mường Ảng', lat: 21.8167, lon: 103.0833 },
  'muong_lay': { name: 'Thị xã Mường Lay', lat: 22.5000, lon: 102.6833 }
};

// WMO Weather Codes
const WEATHER_CODES = {
  0: { vi: 'Trời quang', en: 'Clear sky' },
  1: { vi: 'Ít mây', en: 'Mainly clear' },
  2: { vi: 'Nhiều mây', en: 'Partly cloudy' },
  3: { vi: 'U ám', en: 'Overcast' },
  61: { vi: 'Mưa nhẹ', en: 'Light rain' },
  63: { vi: 'Mưa vừa', en: 'Moderate rain' },
  65: { vi: 'Mưa to', en: 'Heavy rain' },
  80: { vi: 'Mưa rào nhẹ', en: 'Light showers' },
  81: { vi: 'Mưa rào vừa', en: 'Moderate showers' },
  82: { vi: 'Mưa rào nặng', en: 'Violent showers' },
  95: { vi: 'Giông', en: 'Thunderstorm' },
  96: { vi: 'Giông kèm mưa đá nhẹ', en: 'Thunderstorm with slight hail' },
  99: { vi: 'Giông kèm mưa đá nặng', en: 'Thunderstorm with heavy hail' }
};

// Alert thresholds (VNDMS standard)
const ALERT_THRESHOLDS = {
  heavy_rain: 50,      // mm/24h
  extreme_rain: 100,   // mm/24h
  strong_wind: 40,      // km/h
  storm_wind: 62,       // km/h
  high_humidity: 95,    // %
  cold_wave: 10,        // °C
  frost: 0              // °C
};

// Calculate risk level based on weather conditions
const calculateRiskLevel = (weather) => {
  let score = 0;
  const factors = [];
  const warnings = [];

  // Rainfall factor
  if (weather.rainfall >= ALERT_THRESHOLDS.extreme_rain) {
    score += 4;
    factors.push('Mưa cực đoan');
    warnings.push({ type: 'extreme_rain', message: '⚠️ NGUY HIỂM: Mưa lớn có thể gây lũ quét' });
  } else if (weather.rainfall >= ALERT_THRESHOLDS.heavy_rain) {
    score += 3;
    factors.push('Mưa to');
    warnings.push({ type: 'heavy_rain', message: '🔶 CẢNH BÁO: Nguy cơ ngập lụt' });
  } else if (weather.rainfall >= 25) {
    score += 1;
    factors.push('Mưa vừa');
  }

  // Wind factor
  if (weather.wind_speed >= ALERT_THRESHOLDS.storm_wind) {
    score += 4;
    factors.push('Gió bão');
    warnings.push({ type: 'storm', message: '🌪️ NGUY HIỂM: Gió bão có thể gây thiệt hại' });
  } else if (weather.wind_speed >= ALERT_THRESHOLDS.strong_wind) {
    score += 2;
    factors.push('Gió mạnh');
  }

  // Humidity/Landslide risk
  if (weather.humidity >= ALERT_THRESHOLDS.high_humidity) {
    score += 2;
    factors.push('Độ ẩm rất cao - Nguy cơ sạt lở');
    warnings.push({ type: 'landslide', message: '⛰️ CẢNH BÁO: Nguy cơ sạt lở đất' });
  }

  // Thunderstorm
  if (weather.weather_code >= 95) {
    score += 2;
    factors.push('Có giông');
    warnings.push({ type: 'thunderstorm', message: '⛈️ CẢNH BÁO: Có khả năng xảy ra giông' });
  }

  // Cold weather
  if (weather.temp <= ALERT_THRESHOLDS.frost) {
    score += 3;
    factors.push('Băng giá/Sương muối');
    warnings.push({ type: 'frost', message: '❄️ CẢNH BÁO: Băng giá có thể gây hại' });
  } else if (weather.temp <= ALERT_THRESHOLDS.cold_wave) {
    score += 2;
    factors.push('Lạnh sâu');
  }

  // Determine level (1-5) per VNDMS
  let level, levelText, color;
  if (score >= 8) {
    level = 5;
    levelText = 'Rủi ro thảm họa';
    color = '#800080';
  } else if (score >= 6) {
    level = 4;
    levelText = 'Rủi ro rất lớn';
    color = '#FF0000';
  } else if (score >= 4) {
    level = 3;
    levelText = 'Rủi ro lớn';
    color = '#FFA500';
  } else if (score >= 2) {
    level = 2;
    levelText = 'Rủi ro trung bình';
    color = '#FFFF00';
  } else {
    level = 1;
    levelText = 'Rủi ro thấp';
    color = '#87CEEB';
  }

  return { level, levelText, color, score, factors, warnings };
};

// API Routes

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    service: 'Hination Backend API',
    version: '1.0.0'
  });
});

// Get districts list
app.get('/api/districts', (req, res) => {
  res.json({
    success: true,
    data: Object.entries(DISTRICTS).map(([id, info]) => ({
      id,
      ...info
    }))
  });
});

// Get latest weather data
app.get('/api/weather/latest', (req, res) => {
  const weatherData = readDataFile(join(__dirname, '../data/weather_latest.json'));
  
  if (weatherData) {
    res.json({ success: true, data: weatherData });
  } else {
    // Return mock data if file not found
    res.json({
      success: true,
      data: {
        province: 'Điện Biên',
        fetched_at: new Date().toISOString(),
        data_source: 'Open-Meteo API',
        districts: DISTRICTS
      }
    });
  }
});

// Get risk assessment
app.get('/api/risk/assessment', (req, res) => {
  const riskData = readDataFile(join(__dirname, '../data/risk_assessment.json'));
  
  if (riskData) {
    res.json({ success: true, data: riskData });
  } else {
    res.status(404).json({ 
      success: false, 
      error: 'Risk assessment data not found. Run risk_prediction.py first.' 
    });
  }
});

// Get risk by district
app.get('/api/risk/district/:id', (req, res) => {
  const { id } = req.params;
  const riskData = readDataFile(join(__dirname, '../data/risk_assessment.json'));
  
  if (riskData && riskData.districts && riskData.districts[id]) {
    res.json({ success: true, data: riskData.districts[id] });
  } else {
    res.status(404).json({ success: false, error: 'District not found' });
  }
});

// Get weather codes reference
app.get('/api/weather/codes', (req, res) => {
  const codesData = readDataFile(join(__dirname, '../data/historical/weather_codes_reference.json'));
  
  if (codesData) {
    res.json({ success: true, data: codesData });
  } else {
    // Return inline codes if file not found
    res.json({ success: true, data: WEATHER_CODES });
  }
});

// Get alerts
app.get('/api/alerts', (req, res) => {
  const alertsData = readDataFile(join(__dirname, '../data/alerts_current.json'));
  
  res.json({
    success: true,
    data: alertsData || { alerts: [], timestamp: new Date().toISOString() }
  });
});

// Historical weather data endpoint
app.get('/api/weather/historical', (req, res) => {
  const { month, year } = req.query;
  let filepath = join(__dirname, '../data/historical/dien_bien_2024_06.json');
  
  if (year && month) {
    filepath = join(__dirname, `../data/historical/dien_bien_${year}_${month}.json`);
  }
  
  const data = readDataFile(filepath);
  
  if (data) {
    res.json({ success: true, data });
  } else {
    res.status(404).json({ success: false, error: 'Historical data not found' });
  }
});

// Calculate risk for a specific district (real-time)
app.post('/api/risk/calculate', (req, res) => {
  const { district_id, weather } = req.body;
  
  if (!district_id || !weather) {
    return res.status(400).json({ 
      success: false, 
      error: 'Missing district_id or weather data' 
    });
  }
  
  const district = DISTRICTS[district_id];
  if (!district) {
    return res.status(404).json({ success: false, error: 'District not found' });
  }
  
  const risk = calculateRiskLevel(weather);
  
  res.json({
    success: true,
    data: {
      district_id,
      district_name: district.name,
      ...risk,
      weather,
      calculated_at: new Date().toISOString()
    }
  });
});

// VNDMS framework info
app.get('/api/vndms/framework', (req, res) => {
  res.json({
    success: true,
    data: {
      name: 'VNDMS Risk Framework',
      source: 'Decision 18/2021/QĐ-TTg',
      levels: VNDMS_RISK_LEVELS,
      thresholds: ALERT_THRESHOLDS,
      description: 'Vietnam National Disaster Warning Framework'
    }
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🌦️  HINATION BACKEND API                                 ║
║    ─────────────────────────────────────────                 ║
║                                                              ║
║    Server running on port ${PORT}                              ║
║                                                              ║
║    Endpoints:                                                ║
║    • GET  /api/health          - Health check                ║
║    • GET  /api/districts       - List all districts          ║
║    • GET  /api/weather/latest  - Latest weather data         ║
║    • GET  /api/risk/assessment - Risk assessment             ║
║    • GET  /api/risk/district/:id - Risk by district          ║
║    • POST /api/risk/calculate  - Calculate risk              ║
║    • GET  /api/vndms/framework - VNDMS framework info        ║
║    • GET  /api/alerts          - Current alerts              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
  `);
});
