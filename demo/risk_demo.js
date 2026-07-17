#!/usr/bin/env node

/**
 * Điện Biên Province Weather Risk Demo
 * Fetches real weather data from Open-Meteo API and calculates disaster risk levels
 */

const districts = [
  { id: 'dien_bien_phu', name: 'Thành phố Điện Biên Phủ', lat: 21.3869, lon: 103.0228 },
  { id: 'tuan_giao', name: 'Huyện Tuần Giáo', lat: 21.6167, lon: 103.2500 },
  { id: 'tua_chua', name: 'Huyện Tủa Chùa', lat: 21.4667, lon: 103.4333 },
  { id: 'muong_cha', name: 'Huyện Mường Chà', lat: 22.0833, lon: 102.4333 },
  { id: 'muong_nhe', name: 'Huyện Mường Nhé', lat: 22.4167, lon: 102.3000 },
  { id: 'dien_bien_dong', name: 'Huyện Điện Biên Đông', lat: 21.1833, lon: 103.5500 },
  { id: 'nam_po', name: 'Huyện Nậm Pồ', lat: 21.6500, lon: 103.1167 },
  { id: 'muong_ang', name: 'Huyện Mường Ảng', lat: 21.8167, lon: 103.0833 },
  { id: 'muong_lay', name: 'Thị xã Mường Lay', lat: 22.5000, lon: 102.6833 }
];

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  red: '\x1b[31m',
  redBg: '\x1b[41m',
  yellow: '\x1b[33m',
  yellowBg: '\x1b[43m',
  orange: '\x1b[38;5;208m',
  orangeBg: '\x1b[48;5;208m',
  green: '\x1b[32m',
  greenBg: '\x1b[42m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

// Weather code descriptions (WMO Code)
const weatherCodes = {
  0: 'Trời quang',
  1: 'Ít mây',
  2: 'Nhiều mây',
  3: 'U ám',
  45: 'Sương mù',
  48: 'Sương mù đóng băng',
  51: 'Mưa phùn nhẹ',
  53: 'Mưa phùn vừa',
  55: 'Mưa phùn nặng',
  56: 'Mưa phùn đóng băng nhẹ',
  57: 'Mưa phùn đóng băng nặng',
  61: 'Mưa nhẹ',
  63: 'Mưa vừa',
  65: 'Mưa to',
  66: 'Mưa đóng băng nhẹ',
  67: 'Mưa đóng băng nặng',
  71: 'Tuyết nhẹ',
  73: 'Tuyết vừa',
  75: 'Tuyết to',
  77: 'Hạt tuyết',
  80: 'Mưa rào nhẹ',
  81: 'Mưa rào vừa',
  82: 'Mưa rào to',
  85: 'Mưa tuyết nhẹ',
  86: 'Mưa tuyết nặng',
  95: 'Dông kèm mưa',
  96: 'Dông kèm mưa đá nhẹ',
  99: 'Dông kèm mưa đá nặng'
};

/**
 * Calculate risk level based on weather parameters
 */
function calculateRisk(data) {
  const { precipitation, relative_humidity_2m, wind_speed_10m, weather_code } = data;
  
  let riskLevel = 'SAFE';
  let riskScore = 0;
  const warnings = [];

  // Rainfall risk
  if (precipitation > 20) {
    riskLevel = 'VERY_HIGH';
    riskScore += 3;
    warnings.push(`Mưa rất lớn: ${precipitation}mm/h`);
  } else if (precipitation > 10) {
    if (riskLevel !== 'VERY_HIGH') riskLevel = 'HIGH';
    riskScore += 2;
    warnings.push(`Mưa lớn: ${precipitation}mm/h`);
  } else if (precipitation > 5) {
    if (riskLevel === 'SAFE') riskLevel = 'WATCH';
    riskScore += 1;
    warnings.push(`Mưa vừa: ${precipitation}mm/h`);
  }

  // Humidity risk (landslide warning for mountainous areas)
  if (relative_humidity_2m > 95) {
    if (riskLevel !== 'VERY_HIGH') riskLevel = 'HIGH';
    riskScore += 2;
    warnings.push(`Độ ẩm cao: ${relative_humidity_2m}% - Nguy cơ sạt lở`);
  } else if (relative_humidity_2m > 85) {
    if (riskLevel === 'SAFE') riskLevel = 'WATCH';
    riskScore += 1;
    warnings.push(`Độ ẩm cao: ${relative_humidity_2m}%`);
  }

  // Wind risk (storm warning)
  if (wind_speed_10m > 50) {
    if (riskLevel !== 'VERY_HIGH') riskLevel = 'HIGH';
    riskScore += 2;
    warnings.push(`Gió mạnh: ${wind_speed_10m}km/h - Nguy cơ bão`);
  } else if (wind_speed_10m > 30) {
    if (riskLevel === 'SAFE') riskLevel = 'WATCH';
    riskScore += 1;
    warnings.push(`Gió vừa: ${wind_speed_10m}km/h`);
  }

  // Severe weather codes
  const severeCodes = [65, 67, 75, 82, 86, 95, 96, 99];
  if (severeCodes.includes(weather_code)) {
    if (riskLevel !== 'VERY_HIGH') riskLevel = 'HIGH';
    riskScore += 2;
    warnings.push(`Thời tiết nguy hiểm: ${weatherCodes[weather_code] || 'Không rõ'}`);
  }

  // Upgrade to VERY_HIGH if multiple high-risk factors
  if (riskScore >= 4) {
    riskLevel = 'VERY_HIGH';
  }

  return { riskLevel, riskScore, warnings };
}

/**
 * Get color for risk level
 */
function getRiskColor(riskLevel) {
  switch (riskLevel) {
    case 'VERY_HIGH': return { text: colors.red, bg: colors.redBg };
    case 'HIGH': return { text: colors.orange, bg: colors.orangeBg };
    case 'WATCH': return { text: colors.yellow, bg: colors.yellowBg };
    default: return { text: colors.green, bg: colors.greenBg };
  }
}

/**
 * Get risk label in Vietnamese
 */
function getRiskLabel(riskLevel) {
  switch (riskLevel) {
    case 'VERY_HIGH': return 'NGUY HIỂM RẤT CAO';
    case 'HIGH': return 'NGUY HIỂM CAO';
    case 'WATCH': return 'CẢNH BÁO';
    default: return 'AN TOÀN';
  }
}

/**
 * Fetch weather data for a district
 */
async function fetchWeather(district) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${district.lat}&longitude=${district.lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code&timezone=Asia/Ho_Chi_Minh`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return {
      ...district,
      temperature: data.current.temperature_2m,
      humidity: data.current.relative_humidity_2m,
      precipitation: data.current.precipitation,
      windSpeed: data.current.wind_speed_10m,
      weatherCode: data.current.weather_code,
      weatherDesc: weatherCodes[data.current.weather_code] || 'Không rõ'
    };
  } catch (error) {
    console.error(`Lỗi khi lấy dữ liệu cho ${district.name}: ${error.message}`);
    return null;
  }
}

/**
 * Display results in terminal
 */
function displayResults(results) {
  const now = new Date().toLocaleString('vi-VN', { 
    timeZone: 'Asia/Ho_Chi_Minh',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });

  console.clear();
  console.log(`${colors.cyan}${colors.bold}`);
  console.log('╔══════════════════════════════════════════════════════════════════════════════╗');
  console.log('║        HỆ THỐNG CẢNH BÁO THỜI TIẾT VÀ NGUY CƠ THIÊN TAI - ĐIỆN BIÊN          ║');
  console.log('╚══════════════════════════════════════════════════════════════════════════════╝');
  console.log(`${colors.reset}`);
  console.log(`${colors.blue}Cập nhật lúc: ${now} (Giờ Việt Nam)${colors.reset}`);
  console.log('');
  
  // Summary by risk level
  const summary = {
    'VERY_HIGH': 0,
    'HIGH': 0,
    'WATCH': 0,
    'SAFE': 0
  };

  for (const r of results) {
    if (r) summary[r.risk.riskLevel]++;
  }

  console.log(`${colors.bold}📊 TỔNG QUAN:${colors.reset}`);
  console.log(`  ${colors.red}● Nguy hiểm rất cao: ${summary.VERY_HIGH} huyện${colors.reset}`);
  console.log(`  ${colors.orange}● Nguy hiểm cao: ${summary.HIGH} huyện${colors.reset}`);
  console.log(`  ${colors.yellow}● Cảnh báo: ${summary.WATCH} huyện${colors.reset}`);
  console.log(`  ${colors.green}● An toàn: ${summary.SAFE} huyện${colors.reset}`);
  console.log('');
  console.log('─'.repeat(100));
  console.log('');

  // Sort by risk level (most dangerous first)
  const riskOrder = { 'VERY_HIGH': 0, 'HIGH': 1, 'WATCH': 2, 'SAFE': 3 };
  results.sort((a, b) => {
    if (!a) return 1;
    if (!b) return -1;
    return riskOrder[a.risk.riskLevel] - riskOrder[b.risk.riskLevel];
  });

  // Display each district
  for (const data of results) {
    if (!data) continue;
    
    const riskColor = getRiskColor(data.risk.riskLevel);
    const riskLabel = getRiskLabel(data.risk.riskLevel);
    
    console.log(`${riskColor.bg}${colors.white} ${data.name} ${colors.reset}`);
    console.log(`  ${colors.cyan}Mã huyện: ${data.id}${colors.reset}`);
    console.log(`  ${colors.blue}📍 Tọa độ: ${data.lat}, ${data.lon}${colors.reset}`);
    console.log('');
    console.log(`  🌡️  Nhiệt độ: ${colors.bold}${colors.white}${data.temperature}°C${colors.reset}`);
    console.log(`  💧 Độ ẩm: ${data.humidity}%`);
    console.log(`  🌧️  Mưa: ${data.precipitation}mm/h`);
    console.log(`  💨 Gió: ${data.windSpeed}km/h`);
    console.log(`  ☁️  Thời tiết: ${data.weatherDesc} (code: ${data.weatherCode})`);
    console.log('');
    console.log(`  ${riskColor.bg}${colors.white}⚠️  Mức rủi ro: ${riskLabel}${colors.reset}`);
    
    if (data.risk.warnings.length > 0) {
      console.log(`  ${colors.yellow}Cảnh báo:${colors.reset}`);
      for (const warning of data.risk.warnings) {
        console.log(`    • ${warning}`);
      }
    }
    console.log('');
    console.log('─'.repeat(100));
    console.log('');
  }

  console.log(`${colors.cyan}${colors.bold}╔══════════════════════════════════════════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.cyan}${colors.bold}║  Legend: ${colors.green}[XANH] An toàn${colors.reset} | ${colors.yellow}[VÀNG] Cảnh báo${colors.reset} | ${colors.orange}[CAM] Nguy hiểm${colors.reset} | ${colors.red}[ĐỎ] Nguy hiểm rất cao${colors.reset}  ║`);
  console.log(`${colors.cyan}${colors.bold}╚══════════════════════════════════════════════════════════════════════════════╝${colors.reset}`);
  console.log('');
  console.log(`${colors.blue}Dữ liệu từ Open-Meteo API | Tự động cập nhật mỗi 5 phút${colors.reset}`);
}

/**
 * Main function
 */
async function main() {
  console.log(`${colors.cyan}Đang tải dữ liệu thời tiết cho 9 huyện của Điện Biên...${colors.reset}`);
  console.log('');
  
  // Fetch weather for all districts in parallel
  const weatherData = await Promise.all(districts.map(d => fetchWeather(d)));
  
  // Calculate risk for each district
  const results = weatherData.map(data => {
    if (!data) return null;
    return {
      ...data,
      risk: calculateRisk(data)
    };
  });

  // Display results
  displayResults(results);

  // Schedule next update in 5 minutes
  console.log(`${colors.blue}Đang chờ 5 phút để cập nhật...${colors.reset}`);
  console.log(`Nhấn Ctrl+C để dừng.\n`);
  
  setTimeout(main, 5 * 60 * 1000);
}

// Run
main().catch(console.error);
