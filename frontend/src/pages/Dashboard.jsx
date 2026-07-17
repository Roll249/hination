import React, { useState, useEffect, useRef } from 'react';
import Map from '../components/Map';
import WeatherCard from '../components/WeatherCard';
import AlertPanel from '../components/AlertPanel';
import ForecastChart from '../components/ForecastChart';
import DistrictSelector from '../components/DistrictSelector';

// Sample weather data for Dien Bien districts
const DISTRICTS_DATA = {
  'dien_bien_phu': {
    name: 'Thành phố Điện Biên Phủ',
    lat: 21.3869,
    lon: 103.0228,
    current: {
      temp: 26.7,
      humidity: 87,
      rainfall: 0.2,
      wind_speed: 10.5,
      weather: 'Mưa phùn vừa',
      pressure: 1005,
      feels_like: 31.6
    },
    forecast: [
      { time: '14:00', temp: 27, rain: 20, weather: 'Mưa rào' },
      { time: '15:00', temp: 26, rain: 35, weather: 'Mưa rào' },
      { time: '16:00', temp: 25, rain: 50, weather: 'Mưa to' },
      { time: '17:00', temp: 24, rain: 45, weather: 'Mưa rào' },
      { time: '18:00', temp: 23, rain: 30, weather: 'Mưa nhẹ' },
    ],
    alerts: []
  },
  'tuan_giao': {
    name: 'Huyện Tuần Giáo',
    lat: 21.6167,
    lon: 103.2500,
    current: {
      temp: 25.8,
      humidity: 92,
      rainfall: 1.5,
      wind_speed: 8.2,
      weather: 'Mưa rào',
      pressure: 1004,
      feels_like: 30.1
    },
    forecast: [],
    alerts: []
  },
  'tua_chua': {
    name: 'Huyện Tủa Chùa',
    lat: 21.4667,
    lon: 103.4333,
    current: {
      temp: 24.2,
      humidity: 95,
      rainfall: 3.2,
      wind_speed: 5.5,
      weather: 'Mưa rào',
      pressure: 1003,
      feels_like: 28.5
    },
    forecast: [],
    alerts: []
  },
  'muong_cha': {
    name: 'Huyện Mường Chà',
    lat: 22.0833,
    lon: 102.4333,
    current: {
      temp: 23.5,
      humidity: 99,
      rainfall: 5.1,
      wind_speed: 3.2,
      weather: 'Mưa to',
      pressure: 1002,
      feels_like: 27.8
    },
    forecast: [],
    alerts: [{ type: 'high_humidity', severity: 'info', message: 'Độ ẩm rất cao, cảnh giác sương mù' }]
  },
  'muong_nhe': {
    name: 'Huyện Mường Nhé',
    lat: 22.4167,
    lon: 102.3000,
    current: {
      temp: 22.8,
      humidity: 96,
      rainfall: 2.8,
      wind_speed: 4.1,
      weather: 'Mưa rào',
      pressure: 1001,
      feels_like: 26.5
    },
    forecast: [],
    alerts: []
  },
  'dien_bien_dong': {
    name: 'Huyện Điện Biên Đông',
    lat: 21.1833,
    lon: 103.5500,
    current: {
      temp: 27.1,
      humidity: 82,
      rainfall: 0.0,
      wind_speed: 12.3,
      weather: 'Nắng ít mây',
      pressure: 1006,
      feels_like: 32.0
    },
    forecast: [],
    alerts: []
  },
  'nam_po': {
    name: 'Huyện Nậm Pồ',
    lat: 21.6500,
    lon: 103.1167,
    current: {
      temp: 24.5,
      humidity: 91,
      rainfall: 1.2,
      wind_speed: 6.8,
      weather: 'Mưa nhẹ',
      pressure: 1004,
      feels_like: 29.2
    },
    forecast: [],
    alerts: []
  },
  'muong_ang': {
    name: 'Huyện Mường Ảng',
    lat: 21.8167,
    lon: 103.0833,
    current: {
      temp: 25.2,
      humidity: 89,
      rainfall: 0.8,
      wind_speed: 7.5,
      weather: 'Mưa phùn',
      pressure: 1005,
      feels_like: 30.0
    },
    forecast: [],
    alerts: []
  },
  'muong_lay': {
    name: 'Thị xã Mường Lay',
    lat: 22.5000,
    lon: 102.6833,
    current: {
      temp: 23.1,
      humidity: 94,
      rainfall: 2.5,
      wind_speed: 5.2,
      weather: 'Mưa rào',
      pressure: 1003,
      feels_like: 27.0
    },
    forecast: [],
    alerts: []
  }
};

function Dashboard() {
  const [selectedDistrict, setSelectedDistrict] = useState('dien_bien_phu');
  const [weatherData, setWeatherData] = useState(DISTRICTS_DATA);
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [mapCenter, setMapCenter] = useState([21.3869, 103.0228]);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [refreshInterval, setRefreshInterval] = useState(15); // minutes

  // Update time
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Select district handler
  const handleDistrictSelect = (districtId) => {
    setSelectedDistrict(districtId);
    const district = DISTRICTS_DATA[districtId];
    if (district) {
      setMapCenter([district.lat, district.lon]);
    }
  };

  // Get weather icon based on condition
  const getWeatherIcon = (weather) => {
    if (weather.includes('Nắng')) return '☀️';
    if (weather.includes('Mưa to')) return '⛈️';
    if (weather.includes('Mưa')) return '🌧️';
    if (weather.includes('Giông')) return '🌩️';
    if (weather.includes('Sương')) return '🌫️';
    return '⛅';
  };

  // Risk level calculation
  const calculateRiskLevel = (data) => {
    let risk = 0;
    if (data.current.rainfall > 5) risk += 3;
    else if (data.current.rainfall > 2) risk += 2;
    else if (data.current.rainfall > 0.5) risk += 1;
    
    if (data.current.humidity > 95) risk += 2;
    else if (data.current.humidity > 85) risk += 1;
    
    if (data.current.temp < 5) risk += 3;
    else if (data.current.temp < 10) risk += 2;
    else if (data.current.temp < 15) risk += 1;

    if (risk >= 5) return 'severe';
    if (risk >= 3) return 'high';
    if (risk >= 2) return 'moderate';
    return 'low';
  };

  const selectedData = weatherData[selectedDistrict];
  const riskLevel = calculateRiskLevel(selectedData);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-slate-900/80 border-b border-slate-700/50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo & Title */}
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 p-0.5">
                <div className="w-full h-full rounded-xl bg-slate-900 flex items-center justify-center">
                  <span className="text-2xl">🌦️</span>
                </div>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">HINATION</h1>
                <p className="text-xs text-slate-400">Hệ Thống Cảnh Báo Thiên Tai Điện Biên</p>
              </div>
            </div>

            {/* Time & Status */}
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-sm text-slate-400">
                  {currentTime.toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
                </div>
                <div className="text-2xl font-mono text-white">
                  {currentTime.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </div>
              </div>
              
              {/* Status Indicators */}
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800/50">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-green-400">Online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Map & Alerts */}
          <div className="lg:col-span-2 space-y-6">
            {/* Map */}
            <div className="card overflow-hidden">
              <div className="p-4 border-b border-slate-700/50 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span>🗺️</span> Bản đồ cảnh báo
                </h2>
                <div className="flex items-center gap-4">
                  {/* Legend */}
                  <div className="flex items-center gap-3 text-xs">
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded bg-emerald-500"></div>
                      <span className="text-slate-400">Thấp</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded bg-yellow-500"></div>
                      <span className="text-slate-400">TB</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded bg-orange-500"></div>
                      <span className="text-slate-400">Cao</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded bg-red-500"></div>
                      <span className="text-slate-400">Nguy hiểm</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="h-[500px]">
                <Map 
                  center={mapCenter}
                  districts={weatherData}
                  selectedDistrict={selectedDistrict}
                  onDistrictSelect={handleDistrictSelect}
                />
              </div>
            </div>

            {/* Forecast Chart */}
            <div className="card">
              <div className="p-4 border-b border-slate-700/50">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span>📈</span> Dự báo thời tiết 7 ngày
                </h2>
              </div>
              <div className="p-4">
                <ForecastChart districtData={selectedData} />
              </div>
            </div>
          </div>

          {/* Right Column - Weather & Alerts */}
          <div className="space-y-6">
            {/* Current Weather */}
            <WeatherCard 
              district={selectedData}
              districtName={Object.values(DISTRICTS_DATA).find(d => d.lat === selectedData.lat)?.name || 'Điện Biên Phủ'}
            />

            {/* Alert Panel */}
            <AlertPanel alerts={selectedData.alerts} />

            {/* District List */}
            <DistrictSelector 
              districts={weatherData}
              selectedId={selectedDistrict}
              onSelect={handleDistrictSelect}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700/50 py-4 mt-8">
        <div className="container mx-auto px-4 text-center text-sm text-slate-500">
          <p>Hination - Hệ Thống Cảnh Báo Thiên Tai Điện Biên | Dữ liệu: Open-Meteo API</p>
          <p className="mt-1">Cập nhật: {currentTime.toLocaleString('vi-VN')}</p>
        </div>
      </footer>
    </div>
  );
}

export default Dashboard;
