import React from 'react';

function WeatherCard({ district, districtName }) {
  const { current } = district;

  // Weather icon mapping
  const getWeatherIcon = (weather) => {
    if (!weather) return '⛅';
    if (weather.includes('Nắng') || weather.includes('Quang')) return '☀️';
    if (weather.includes('Mưa to') || weather.includes('Bão')) return '⛈️';
    if (weather.includes('Mưa rào')) return '🌧️';
    if (weather.includes('Mưa')) return '🌧️';
    if (weather.includes('Giông')) return '🌩️';
    if (weather.includes('Sương')) return '🌫️';
    if (weather.includes('Âm')) return '☁️';
    return '⛅';
  };

  // Air quality index
  const getAQI = (aqi) => {
    if (aqi <= 50) return { level: 'Tốt', color: 'text-green-400', bg: 'bg-green-500/20' };
    if (aqi <= 100) return { level: 'Trung bình', color: 'text-yellow-400', bg: 'bg-yellow-500/20' };
    if (aqi <= 150) return { level: 'Kém', color: 'text-orange-400', bg: 'bg-orange-500/20' };
    return { level: 'Xấu', color: 'text-red-400', bg: 'bg-red-500/20' };
  };

  const aqiInfo = getAQI(35); // Sample AQI

  return (
    <div className="card">
      {/* Header */}
      <div className="p-4 border-b border-slate-700/50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">{districtName}</h3>
            <p className="text-sm text-slate-400">Thời tiết hiện tại</p>
          </div>
          <div className="text-5xl">{getWeatherIcon(current.weather)}</div>
        </div>
      </div>

      {/* Main Weather Info */}
      <div className="p-4">
        {/* Temperature */}
        <div className="text-center mb-6">
          <div className="text-6xl font-bold text-white">
            {current.temp}<span className="text-3xl">°C</span>
          </div>
          <div className="text-slate-400 mt-1">
            Cảm giác như <span className="text-white">{current.feels_like}°C</span>
          </div>
          <div className="mt-2 inline-block px-3 py-1 rounded-full bg-blue-500/20 text-blue-400 text-sm">
            {current.weather}
          </div>
        </div>

        {/* Weather Details Grid */}
        <div className="grid grid-cols-2 gap-4">
          {/* Humidity */}
          <div className="p-3 rounded-lg bg-slate-700/30">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
              <span>💧</span> Độ ẩm
            </div>
            <div className="text-2xl font-semibold text-white">{current.humidity}%</div>
            <div className="w-full bg-slate-600 rounded-full h-1.5 mt-2">
              <div 
                className="bg-blue-500 h-1.5 rounded-full transition-all"
                style={{ width: `${current.humidity}%` }}
              ></div>
            </div>
          </div>

          {/* Wind */}
          <div className="p-3 rounded-lg bg-slate-700/30">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
              <span>🌬️</span> Gió
            </div>
            <div className="text-2xl font-semibold text-white">{current.wind_speed} <span className="text-sm font-normal">km/h</span></div>
            <div className="text-xs text-slate-500 mt-2">Hướng {getWindDirection(current.wind_speed)}</div>
          </div>

          {/* Rainfall */}
          <div className="p-3 rounded-lg bg-slate-700/30">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
              <span>🌧️</span> Lượng mưa
            </div>
            <div className="text-2xl font-semibold text-white">{current.rainfall} <span className="text-sm font-normal">mm</span></div>
            <div className="text-xs text-slate-500 mt-2">Trong 1 giờ qua</div>
          </div>

          {/* Pressure */}
          <div className="p-3 rounded-lg bg-slate-700/30">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
              <span>🧭</span> Áp suất
            </div>
            <div className="text-2xl font-semibold text-white">{current.pressure} <span className="text-sm font-normal">hPa</span></div>
            <div className="text-xs text-slate-500 mt-2">Khí quyển</div>
          </div>
        </div>

        {/* Air Quality */}
        <div className="mt-4 p-3 rounded-lg bg-slate-700/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl">🌿</span>
              <div>
                <div className="text-sm text-slate-400">Chất lượng không khí</div>
                <div className={`font-semibold ${aqiInfo.color}`}>{aqiInfo.level}</div>
              </div>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${aqiInfo.bg} ${aqiInfo.color}`}>
              AQI 35
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-slate-800/50 rounded-b-xl">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Cập nhật: vừa xong</span>
          <span>Nguồn: Open-Meteo</span>
        </div>
      </div>
    </div>
  );
}

export default WeatherCard;
