# Vietnam Disaster Monitoring System (VNDMS) Research

**Research Date:** July 17, 2026  
**Sources:** Web research, official government documentation, international cooperation reports

---

## Executive Summary

The Vietnam Disaster Monitoring System (VNDMS) is a centralized, web-based platform developed by the Vietnam Disaster and Dyke Management Authority (VDDMA) to integrate real-time disaster monitoring data for disaster prevention and emergency response. The system was built in 2018 and provides monitoring capabilities for hydro-meteorological data, reservoirs, and maritime activities.

---

## 1. System Overview

### 1.1 Official Websites
- **Primary Portal:** https://vndms.gov.vn
- **Alternate Portal:** https://vndms.dmc.gov.vn
- **Disaster Management Center:** http://dmc.gov.vn

### 1.2 Administrative Structure

| Organization | Vietnamese Name | Role |
|--------------|-----------------|------|
| Vietnam Disaster and Dyke Management Authority (VDDMA) | Tổng cục Phòng chống Thiên tai | System owner, oversight |
| Disaster Policy and Technology Center (DPTC) | Trung tâm Chính sách và Kỹ thuật PCTT | Technical development, operation |
| National Center for Hydro-Meteorological Forecasting (NCHMF) | Trung tâm Dự báo KTTV Quốc gia | Hydro-meteorological data source |
| Vietnam Meteorological Hydrological Administration (VMHA) | Cục Khí tượng Thủy văn | Meteorological data authority |

### 1.3 System Development Timeline

The VNDMS was developed in **2018** by VDDMA and has been continuously upgraded since then. The system follows a phased development approach (3 phases planned).

---

## 2. Data Sources

### 2.1 Hydro-Meteorological Data

The system integrates real-time and near-real-time data from multiple networks:

| Data Type | Sources | Update Frequency |
|-----------|---------|------------------|
| **Rainfall** | Automatic stations (GPRS/GSM), Manual stations | Automatic: hourly; Manual: every 6h (1h, 7h, 13h, 19h) |
| **Water Levels** | River gauges, tidal stations | Real-time |
| **Wind** | Meteorological stations | Real-time |
| **Temperature** | Weather stations | Hourly |
| **Soil Moisture** | Environmental monitoring stations | Hourly |

**Data Transmission Methods:**
- GPRS/GSM automatic transmission
- Manual entry via FieldVisits interface
- API integration with NCHMF

### 2.2 Reservoir Data

The system monitors multiple reservoir types:

| Reservoir Type | Monitoring Focus |
|----------------|------------------|
| **Hydropower reservoirs** | Water levels, spillway discharge |
| **Irrigation reservoirs** | Capacity thresholds, safety levels |
| **Multi-purpose reservoirs** | Combined monitoring |

### 2.3 Maritime/Vessel Data

- Fishing vessel tracking (Giám sát tàu cá)
- Maritime activity monitoring

### 2.4 Camera Monitoring Systems

The system integrates video feeds from:
- Dyke monitoring cameras (Camera giám sát hệ thống đê điều)
- Irrigation reservoir cameras
- Hydropower reservoir cameras
- Coastal monitoring (ĐBSCL - Mekong Delta)
- Beach surveillance

### 2.5 Additional Data Layers

- Historical typhoon data
- Socio-economic data for disaster risk assessment
- Disaster prevention infrastructure data
- Dyke system information
- Flash flood and landslide risk zones

---

## 3. Alert Thresholds and Warning Levels

### 3.1 National Disaster Risk Classification (Decision 18/2021/QĐ-TTg)

Vietnam uses a **5-level risk classification system**:

| Level | Color | Risk Description |
|-------|-------|------------------|
| Level 1 | Light Blue | Low risk |
| Level 2 | Light Yellow | Moderate risk |
| Level 3 | Orange | High risk |
| Level 4 | Red | Very high risk |
| Level 5 | Purple | Catastrophic |

### 3.2 Rainfall Warning Thresholds

Based on Decision 18/2021/QĐ-TTg and regional vulnerability:

| Warning Level | 24h Rainfall | Conditions |
|---------------|--------------|------------|
| **Level 1** | 100-200 mm | In low/medium risk areas with prior rain 1-2 days |
| **Level 1** | >200-400 mm | In low risk areas with prior rain >2 days |
| **Level 2** | 100-200 mm | In higher susceptibility regions |
| **Level 2** | >200-400 mm | In medium to very high risk areas |
| **Level 3** | 100-200 mm | In very high risk areas with prior rain 1-2 days |
| **Level 3** | >200-400 mm | In high/very high risk areas with prior rain >2 days |

### 3.3 VNDMS-Specific Alert Triggers

According to documentation, VNDMS generates alerts for:
- Rainfall exceeding **50mm in 24 hours**
- Strong winds
- Reservoir levels exceeding suitable thresholds (irrigation/hydroelectric)

### 3.4 Flood Warning Levels

Flood warning follows a 3-level system based on river gauge readings:

| Level | Vietnamese | Description |
|-------|------------|-------------|
| Alert Level 1 (BĐ1) | Báo động 1 | Flood threshold reached |
| Alert Level 2 (BĐ2) | Báo động 2 | Moderate flooding |
| Alert Level 3 (BĐ3) | Báo động 3 | Severe flooding |

---

## 4. API Endpoints and Data Access

### 4.1 Public API Availability

**Finding: No publicly documented API**

VNDMS does not have published public API documentation. Access is restricted to authorized officials with valid login accounts. The system uses:
- Login authentication with `__RequestVerificationToken` (CSRF protection)
- Session-based access control

### 4.2 Data Export Capabilities

From training documentation, authorized users can:
- Export rainfall data files from the system
- Export water level data files
- Generate data reports for specific time periods

### 4.3 Alternative Data Access Methods

For external users seeking hydro-meteorological data:

1. **Formal Application Process** (via dichvucong.gov.vn)
   - Submit application to Ministry of Agriculture and Environment
   - Pay prescribed fees
   - Data provided within 1 working day after payment

2. **National Public Service Portal:** https://dichvucong.mae.gov.vn

3. **NCHMF Website:** https://nchmf.gov.vn (limited public data)

---

## 5. System Architecture Components

### 5.1 Core System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    VNDMS Architecture                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ Web Portal  │  │ Mobile App  │  │ Data Export │      │
│  │ vndms.gov.vn│  │ App-VNDMS   │  │   Tools     │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         │                │                │               │
│  ┌──────┴────────────────┴────────────────┴──────┐      │
│  │              Integration Layer                   │      │
│  │         (Data Aggregation & Processing)         │      │
│  └──────┬────────────────┬────────────────┬──────┘      │
│         │                │                │               │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐      │
│  │ Hydro-Met   │  │ Reservoir   │  │ Maritime    │      │
│  │ Data Hub    │  │ Monitoring  │  │ Tracking    │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         │                │                │               │
│  ┌──────┴────────────────┴────────────────┴──────┐      │
│  │        External Data Sources                    │      │
│  │  • NCHMF API    • VMHA WISKI                   │      │
│  │  • Regional Centers  • Automatic Stations      │      │
│  └─────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Related Systems

| System | Description | Integration |
|--------|-------------|-------------|
| **VinAWARE** | PDC-developed flood modeling & dam safety | DMC/MARD partnership |
| **SEAFFGS** | Flash flood guidance system | API integration with CDH |
| **WeatherPlus** | Weather monitoring extension | Camera integration |
| **DELFT-FEWS** | Flood forecasting framework | Modeling integration |

### 5.3 Mobile Application (App-VNDMS)

Available for:
- **Android:** Google Play Store
- **iOS:** App Store

Features:
- Real-time disaster alerts
- Push notifications for thresholds
- Field-level data updates
- GPS location-based warnings

---

## 6. Data Standards and Technical Specifications

### 6.1 Technical Standards

| Standard | Description |
|----------|-------------|
| QCVN-18-2019/BTNMT | Technical standard for flood forecasting and warning |
| Decision 03/2020/QĐ-TTg | Regulations on forecasting, warning, and disaster communication |
| Decision 18/2021/QĐ-TTg | Disaster risk levels and warning levels |
| Thông tư 25/2022/TT-BTNMT | Technical procedures for hazardous hydro-meteorological forecasting |

### 6.2 Data Update Frequencies

| Data Type | Update Interval |
|-----------|----------------|
| Automatic rainfall stations | Every 1 hour |
| Manual rainfall stations | Every 6 hours (1h, 7h, 13h, 19h) |
| River water levels | Real-time |
| Reservoir levels | Real-time |
| Weather radar | Every 10-15 minutes |
| Satellite (Himawari 8/9) | Near real-time |
| Lightning data | Real-time |
| Model forecasts (MAP, FMAP) | Every 1-3 hours |
| Landslide thresholds | Daily |

---

## 7. Access Requirements

### 7.1 User Access Levels

The system requires official authorization:

1. **Central Level Officials** - Full access to national data
2. **Provincial Level Officials** - Regional data access
3. **District Level Officials** - Local jurisdiction data
4. **On-duty Personnel** - 24/7 monitoring access

### 7.2 Authentication

- Login via official credentials
- CSRF token protection (`__RequestVerificationToken`)
- Role-based access control

### 7.3 For External/Hackathon Use

**Recommendation:** Contact the Disaster Prevention Policy and Technology Center for:
- Data access agreements
- API evaluation
- Research partnerships

---

## 8. Key Findings Summary

### 8.1 Data Sources Available
- ✅ Rainfall (automatic + manual stations)
- ✅ Water level (river gauges)
- ✅ Wind speed/direction
- ✅ Temperature
- ✅ Reservoir levels (hydropower + irrigation)
- ✅ Maritime vessel tracking
- ✅ Camera feeds (dykes, reservoirs, coastal)
- ✅ Historical disaster data

### 8.2 API Access
- ❌ No public API documentation found
- ✅ Data export available for authorized users
- ✅ Alternative: Formal application to Ministry for official data

### 8.3 Alert Thresholds
- ✅ 5-level risk classification system
- ✅ Rainfall thresholds: 50mm/24h (VNDMS), regional variations per Decision 18/2021
- ✅ Flood warning levels: BĐ1, BĐ2, BĐ3
- ✅ Reservoir capacity thresholds

### 8.4 System Architecture
- ✅ Web-based centralized platform
- ✅ Mobile app (iOS/Android)
- ✅ Integration with NCHMF and regional centers
- ✅ Camera monitoring network

---

## 9. Recommendations for Hackathon Integration

### 9.1 Data Access Strategies

1. **Primary Approach:** Use official data request process via dichvucong.gov.vn
2. **Alternative:** Contact DPTC directly for research partnerships
3. **Secondary Sources:**
   - NCHMF website for public forecasts/warnings
   - VMHA data hub
   - Open data initiatives

### 9.2 Potential Integration Points

| Source | Data Available | Access Method |
|--------|----------------|---------------|
| NCHMF | Weather forecasts, warnings | Website |
| VMHA | Historical hydro-meteorological data | WISKI portal |
| SEAFFGS | Flash flood guidance | API (CDH) |
| Regional Centers | Local monitoring data | Direct contact |

### 9.3 Contact Information

- **VNDMS Support:** Via vndms.dmc.gov.vn
- **DPTC:** Disaster Policy and Technology Center
- **Data Requests:** dichvucong.mae.gov.vn

---

## 10. References

1. Vietnam Disaster Monitoring System (VNDMS) - https://vndms.gov.vn
2. Disaster Management Center (DMC) - http://dmc.gov.vn
3. National Center for Hydro-Meteorological Forecasting - https://nchmf.gov.vn
4. Decision 18/2021/QĐ-TTg on disaster forecasting, warning, and risk levels
5. Decision 03/2020/QĐ-TTg on forecasting and warning regulations
6. Thông tư 25/2022/TT-BTNMT on hazardous weather forecasting procedures
7. QCVN-18-2019/BTNMT flood warning technical standard
8. New Southbound Science & Technology Collaboration Platform - Vietnam Disaster Management Analysis

---

*Document compiled for Hination Hackathon research purposes*
