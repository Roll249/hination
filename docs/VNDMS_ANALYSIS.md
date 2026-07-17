# VNDMS Analysis: Vietnam Disaster Monitoring System and Risk Classification

## Overview

The **Vietnam Disaster Monitoring System (VNDMS)** — also referred to as Hệ thống giám sát thiên tai Việt Nam — is a digital platform for real-time monitoring and decision support in disaster management. It was developed in 2018 by the **Vietnam Disaster and Dyke Management Authority (VDDMA / Tổng cục Phòng, chống thiên tai)** under the Ministry of Agriculture and Rural Development (MARD), with its operational portal hosted at `vndms.dmptc.gov.vn` and formerly at `vndms.dmc.gov.vn`.

A companion mobile application (App-VNDMS) for iOS and Android was developed by the **Disaster Policy and Technology Center (DMPTC)** to deliver push alerts, early warnings, and real-time data updates to field officials.

> **Source:** VDDMA/DMPTC training documentation (dmc.gov.vn, March 2020); NIAR Taiwan policy analysis (nsstc.niar.org.tw, 2024)

---

## 1. How VNDMS Calculates Warning Levels (Level 1–5)

### 1.1 The Five-Level Disaster Risk Framework

The foundational legal instrument is **Decision 18/2021/QĐ-TTg** (dated April 22, 2021, effective July 1, 2021), issued by the Prime Minister, which defines both the forecast/warning process and the five-level disaster risk classification system.

Disaster risk levels are determined based on four factors:
- **Intensity** (cường độ) of the hazard
- **Scope of impact** (phạm vi ảnh hưởng)
- **Area of direct exposure** (khu vực chịu tác động trực tiếp)
- **Potential for damage** (khả năng gây thiệt hại)

Each disaster type is assigned a maximum number of applicable levels, and levels are color-coded for map visualization:

| Risk Level | Color | Vietnamese | English | Description |
|---|---|---|---|---|
| Level 1 | Light Blue | Rủi ro thấp | Low | Minimal damage expected |
| Level 2 | Light Yellow | Rủi ro trung bình | Medium | Moderate impact |
| Level 3 | Orange | Rủi ro lớn | High | Significant damage |
| Level 4 | Red | Rủi ro rất lớn | Very High | Severe impact |
| Level 5 | Purple | Rủi ro thảm họa | Catastrophic | Mass casualties, massive destruction |

### 1.2 Risk Level Ranges by Disaster Type

Not all disaster types use all five levels. Decision 18/2021/QĐ-TTg assigns maximum applicable levels per hazard category:

| Disaster Type | Applicable Levels | Notes |
|---|---|---|
| Tropical depression / Storm | Level 3–5 only | Minimum risk level is 3 |
| Tornado, lightning, hail | Level 1–2 only | Maximum risk level is 2 |
| Heavy rain | Level 1–4 | Four-tier system |
| Flood / Flash flood | Level 1–5 (full range) | Based on water level thresholds |
| Landslide / Debris flow | Level 1–5 (full range) | Varies by slope and rainfall |
| Drought | Level 1–5 | Based on rainfall deficit and duration |
| Coastal erosion | Level 1–5 | Progressive shoreline retreat |
| Strong winds at sea | Level 1–5 | Beaufort scale-based |

### 1.3 Cascading Level Escalation

When two or more disaster types occur simultaneously or consecutively, the risk level may be escalated:
- **+1 level** escalation for compound events based on cumulative impact
- **+2 level** escalation possible when there is risk of serious casualties and property loss
- **Maximum cap: Level 5**

This escalation rule means the effective risk level shown by VNDMS is not purely a function of a single hazard's magnitude — it reflects compound risk conditions.

> **Source:** Decision 18/2021/QĐ-TTg; analysis from vpcp.chinhphu.vn and quanlynhanuoc.vn

---

## 2. Data Sources Used by VNDMS

### 2.1 Real-Time Monitoring Data

VNDMS integrates real-time and near-real-time data streams from multiple networks:

| Data Type | Source | Update Frequency |
|---|---|---|
| **Rainfall** | National Hydro-Meteorological station network (NCHMF, MONRE) | Hourly / sub-hourly |
| **Water levels** | 244+ hydrological stations nationwide | Hourly |
| **Reservoir levels** | Irrigation and hydroelectric dam monitoring | Real-time |
| **River discharge** | Calculated from water level + rating curves | Hourly |
| **Wind speed/direction** | Coastal and inland weather stations | Hourly |
| **Sea conditions** | Buoy network, satellite | Varies |
| **Vessel tracking** | Maritime monitoring (AIS) | Real-time |
| **Dyke/camera surveillance** | Dike monitoring camera network | Live feed |
| **Dam safety cameras** | Hydropower dam surveillance | Live feed |

### 2.2 Static/Reference Data Layers

- Existing disaster prevention infrastructure (dykes, levees, reservoirs)
- Local disaster response resources (equipment, personnel)
- Disaster risk maps (bản đồ rủi ro thiên tai)
- Topographic and geological data

### 2.3 Alert Thresholds for Key Hazards

Based on VDDMA operational guidance, VNDMS triggers alerts when:

- **Rainfall** exceeds **50 mm in 24 hours**
- **Wind speeds** reach warning levels for maritime/surface conditions
- **Reservoir levels** at irrigation or hydroelectric dams exceed safe operational thresholds

> **Source:** VDDMA/DMPTC training materials (dmc.gov.vn); NIAR Taiwan analysis

---

## 3. Flood Warning Level Calculations

### 3.1 Decision 05/2020/QĐ-TTg: Water Level Thresholds

The Prime Minister's **Decision 05/2020/QĐ-TTg** (January 31, 2020) defines water level thresholds corresponding to Flood Alarm Levels I, II, and III at **244 hydrological stations** across Vietnam. These are the operational flood warning levels used by VNDMS.

The three-level flood alarm system corresponds to:

| Flood Alarm Level | Probability/Return Period | Typical Impact |
|---|---|---|
| **Level I (Cấp I)** | Return period < 50% (i.e., more frequent than 1-in-2-year event) | Agricultural inundation, aquaculture areas, low riverbanks |
| **Level II (Cấp II)** | Return period 25–55% (roughly 1-in-2 to 1-in-4 year) | Wide agricultural inundation; begins affecting residential areas |
| **Level III (Cấp III)** | Return period 10–30% (roughly 1-in-4 to 1-in-10 year) | Deep, widespread flooding; multiple residential areas affected |

### 3.2 Selected Station Thresholds (Examples)

Decision 05/2020/QĐ-TTg specifies absolute water levels at key stations:

| River / Station | Alarm Level I | Alarm Level II | Alarm Level III |
|---|---|---|---|
| **Sông Đà – Hòa Bình** | 20.0 m | 21.0 m | 22.0 m |
| **Sông Hồng – Hà Nội (Long Biên)** | 9.5 m | 10.5 m | 11.5 m |
| **Sông Mã – Xã Là** | 279.5 m | 280.5 m | 281.5 m |
| **Sông Hàn – Cẩm Lệ (Đà Nẵng)** | 1.0 m | 2.0 m | 2.5 m |
| **Sông Sài Gòn – Phú An** | 1.4 m | 1.5 m | 1.6 m |
| **Sông Mekong Delta** | Varies by province | Varies | Varies |

> **Note:** For the **Điện Biên** region, the relevant river is the **Nậm Rốm** (a tributary of the Đà/Ngw River system). Specific station thresholds for Nậm Rốm are defined within the 244-station annex of Decision 05/2020/QĐ-TTg. Thresholds are determined based on historical flood frequency analysis, not fixed absolute values.

### 3.3 Technical Methodology: Thông tư 14/2021/TT-BTNMT

The Ministry of Natural Resources and Environment (MONRE) issued **Thông tư 14/2021/TT-BTNMT** (August 31, 2021), which prescribes the technical methodology for constructing water level alarm thresholds. The process involves:

1. **Historical flood frequency analysis** using observed maximum annual water levels
2. **Rating curve construction** linking water level to discharge
3. **Flood mapping** to determine inundation extent at each threshold
4. **Risk map overlay** to calculate what percentage of the flood risk zone is affected at each level
5. **Cross-validation** with existing infrastructure (dyke crest levels, settlement elevations)

The technical specifications require:
- Flood Alarm I: corresponds to return period where <50% of flood risk area is affected; risk is "very low to low"
- Flood Alarm II: return period 25–55%; risk is "low to medium"; residential impact begins
- Flood Alarm III: return period 10–30%; risk is "medium to high and very high"; widespread inundation

---

## 4. Heavy Rain Classification

### 4.1 Rainfall Thresholds

While Decision 18/2021/QĐ-TTg defines heavy rain risk levels (Levels 1–4), the specific rainfall magnitude thresholds are not fixed nationally — they vary by region, season, and local climatology. However, the operational VNDMS threshold for triggering a rainfall alert is:

- **≥ 50 mm in 24 hours** — standard alert trigger for "heavy rain" warnings

Regional thresholds for higher risk levels typically follow patterns such as:

| Rainfall Category | Typical 24h Accumulation | Risk Level |
|---|---|---|
| Heavy rain warning | ≥ 50 mm/24h | Level 1–2 |
| Very heavy rain | ≥ 100 mm/24h | Level 2–3 |
| torrential rain | ≥ 150–200 mm/24h | Level 3–4 |
| Extremely heavy rain | ≥ 300+ mm/24h | Level 4+ |

These are indicative ranges. Actual thresholds are calibrated per station and per basin based on local historical rainfall distributions.

### 4.2 Forecasting Standards: QCVN 18:2019/BTNMT

**QCVN 18:2019/BTNMT** — the National Technical Regulation on Flood Forecasting and Warning — is the core standard governing the methodology:

- **Minimum forecast lead time:** 12 hours for major river systems (Hồng-Thái Bình, Đồng Nai, Cả, Mã, Vu Gia–Thu Bồn, Ba, Sê San, Srêpok)
- **Minimum forecast lead time:** 24 hours for the Mekong Delta (sông Cửu Long)
- **Minimum forecast lead time:** 6 hours for smaller rivers
- **Required rainfall data:** at least 2/3 of rain gauges on the basin must have valid 24-hour data
- **Required water level data:** at least 2/3 of stations must have data at 4 daily observation times (01:00, 07:00, 13:00, 19:00)
- **Forecast validity period:** each forecast model/plan is valid for up to 5 years before requiring recalibration
- **Forecast accuracy criteria:** maximum allowable time error (TSTĐ) must be within permitted bounds; spatial reliability requires ≥50% of forecast locations to experience the predicted flood event

Flood magnitude classification under QCVN 18:2019/BTNMT:
- **Minor flood (Lũ nhỏ):** Hmax < HmaxP70%
- **Medium flood (Lũ trung bình):** HmaxP70% ≤ Hmax ≤ HmaxP30%
- **Major flood (Lũ lớn):** Hmax > HmaxP30%

Where HmaxP70% is the water level with 70% exceedance probability (i.e., a relatively frequent event) and HmaxP30% is the 30% exceedance probability (rarer, more severe event).

> **Source:** Thông tư 22/2019/TT-BTNMT; QCVN 18:2019/BTNMT as published on thuvienphapluat.vn; Thông tư 14/2021/TT-BTNMT

---

## 5. Storm/Tropical Cyclone Classification

### 5.1 Vietnam's Storm Intensity Scale

Vietnam uses the **Beaufort wind scale** for storm classification. Decision 245/2006/QĐ-TTg (issued after Typhoons Chanchu and Xangsane in 2006) extended the national wind scale to Level 17 (maximum 220 km/h). Decision 18/2021/QĐ-TTg reaffirmed this framework:

| Category | Wind Speed (m/s) | Wind Speed (km/h) | Beaufort Level |
|---|---|---|---|
| Tropical Depression (Áp thấp nhiệt đới) | ≤ 17.1 | ≤ 61 | 6–7 |
| Tropical Storm (Bão) | 17.2–24.4 | 62–88 | 8–9 |
| Severe Tropical Storm (Bão mạnh) | 24.5–32.6 | 89–117 | 10–11 |
| Typhoon (Bão rất mạnh) | 32.7–50.9 | 118–183 | 12–15 |
| Super Typhoon (Siêu bão) | ≥ 51.0 | ≥ 184 | ≥ 16 |

### 5.2 Storm Impact by Wind Level

Vietnam's National Hydro-Meteorological Forecasting Center (NCHMF) provides impact descriptions for each wind level:

- **Level 8 (17.2–20.7 m/s):** Trees shake; difficult to walk against wind; roof tiles may be blown off; seas very rough; dangerous for vessels
- **Level 9 (20.8–24.4 m/s):** Broken branches; structural roof damage; seas very rough; very dangerous for vessels
- **Level 10 (24.5–28.4 m/s):** Trees uprooted; widespread structural damage; seas extremely rough; vessels may be wrecked
- **Level 11 (28.5–32.6 m/s):** Widespread destruction; trees and poles knocked down; seas become white with foam; vessels wrecked
- **Level 12 (32.7–36.9 m/s):** Catastrophic damage; houses destroyed; widespread flooding in coastal areas
- **Level 13–15 (37.0–50.9 m/s):** Devastating destruction; entire forests flattened; catastrophic flooding
- **Level 16+ (≥ 51.0 m/s):** Total destruction; almost nothing survives; extreme catastrophic conditions

> **Source:** NCHMF storm classification tables; dmc.gov.vn basic knowledge page; vnmha.mae.gov.vn wind impact analysis

---

## 6. Landslide and Debris Flow Risk Classification

### 6.1 Current State

Vietnam's landslide and debris flow early warning infrastructure is less developed than its flood warning system. According to the **Vietnam Institute of Geosciences and Mineral Resources (VIGMR)**, Vietnam has established early warning stations for landslides, rockfalls, debris flows, flash floods, and mudslides, but:

- Coverage remains inadequate
- Few stations can provide accurate real-time warnings
- Most systems lack real-time data processing capability
- Equipment is largely imported, creating maintenance and integration challenges
- Wireless network infrastructure in mountainous areas often fails during disasters, disrupting communications

### 6.2 Rainfall-Triggered Thresholds

Landslide and debris flow warnings in Vietnam are typically triggered by rainfall thresholds, which vary by:

- **Slope angle** — steeper slopes fail at lower rainfall accumulations
- **Soil type and saturation** — clay-rich soils fail at lower thresholds than sandy soils
- **Vegetation cover** — deforestation dramatically lowers thresholds
- **Prior rainfall** — antecedent moisture conditions are critical
- **Geological setting** — tectonic history, fault proximity

Common approaches include:
- **Cumulative rainfall thresholds** (e.g., 100–200 mm over 3–5 days)
- **Intensity-duration thresholds** (rainfall rate × duration curves)
- **Real-time soil moisture models** using antecedent rainfall indices

Taiwan's **Soil and Water Conservation Bureau** collaborated with VIGMR/MONRE to establish a **debris flow monitoring station in Sa Pa District, Lào Cai Province** in 2019, demonstrating the international cooperation approach Vietnam uses to address this gap.

> **Source:** VIGMR Director Trịnh Hải Sơn statements via TECO in Vietnam (2024); NIAR Taiwan analysis

---

## 7. Điện Biên Province Disaster Prevention Context

### 7.1 Specific Risk Profile

Điện Biên Province faces compound disaster risks:
- **Riverine flooding** in the Điện Biên valley (lòng chảo Điện Biên)
- **Flash floods and debris flows** in mountainous tributary catchments
- **Landslides** along transportation corridors and settlement areas
- **Drought** in dry season (November–April)

The **Nậm Rốm River** is the primary flood risk river in the province, flowing through Điện Biên Phủ city. The valley's enclosed topography creates funneling effects that amplify flood impacts.

### 7.2 Key Planning Documents

| Document | Key Content |
|---|---|
| **Quyết định 596/QĐ-UBND** (2016) | Flood drainage master plan for Điện Biên valley, to 2025, orientation to 2035 |
| **Chỉ thị 04/CT-UBND 2020** | Annual disaster prevention directives, identifies flood-prone and landslide-prone zones |
| **Đề án 170/QĐ-TTg** | Multi-hazard river basin management project for Nậm Rốm |
| **EU/AFD-funded project** (981+ billion VND) | Integrated structural + non-structural measures: 14.7 km of riverbank protection, sediment trapping, real-time hydrological monitoring, Decision Support System (DSS) |

The EU/AFD-supported project is particularly relevant to VNDMS integration, as it includes building a **Decision Support System (DSS)** for the Nậm Rốm basin that integrates real-time hydrological data to support local government decision-making.

### 7.3 Điện Biên-Specific Warning Considerations

- No major hydrological station on Nậm Rốm has nationally published thresholds equivalent to the Decision 05/2020/QĐ-TTg stations (which focus on larger river systems)
- Flood warning in the valley relies on a combination of:
  - Upstream rainfall gauges (cumulative 24h, 48h, 72h)
  - Local water level observations at informal/emporary stations
  - Model-based flash flood guidance from NCHMF
  - Community-based observation networks
- The mountainous terrain means flash flood warning lead times can be as short as **15–60 minutes**

---

## 8. Related Systems: VinAWARE

### 8.1 System Overview

**VinAWARE** is Vietnam's second major disaster monitoring platform, developed by MARD's Disaster Management Center (DMC) in partnership with the **Pacific Disaster Center (PDC)** with funding from USAID and USTDA. Development began in 2012; official launch was in 2018.

### 8.2 VinAWARE vs. VNDMS

| Aspect | VNDMS | VinAWARE |
|---|---|---|
| **Developed by** | VDDMA / DMPTC | MARD DMC + PDC (USAID) |
| **Primary focus** | Broad disaster monitoring | Flood modeling + dam safety |
| **Dams monitored** | General monitoring | 6,000+ dams (primary mandate) |
| **Decision support** | Monitoring + alerts | Impact-based forecasting + scenario modeling |
| **International basis** | Domestic development | PDC DisasterAWARE platform |
| **Launched** | 2018 | 2018 (Phase 2) |

### 8.3 Scientific/Academic Approaches

Vietnamese academic research on flood early warning commonly employs:

| Method | Application |
|---|---|
| **HEC-HMS** | Rainfall-runoff modeling for flood prediction |
| **HEC-RAS** | Hydraulic modeling of flood inundation |
| **SWAT** | Watershed-scale hydrological modeling |
| **Bankfull discharge regression models** | Empirical threshold derivation from field surveys |
| **Random Forest / ML algorithms** | Pattern recognition in historical flood data |
| **Soil moisture models** | Antecedent rainfall-based flash flood guidance |

A 2026 Springer study (Nguyen et al., Thuyloi University) demonstrated a real-time flash flood warning system for the **Tra River basin** using HEC-HMS with bankfull discharge thresholds derived from field surveys — a methodology directly applicable to the Nậm Rốm basin in Điện Biên.

> **Source:** Nguyen et al. (2026), Water Resources, Springer Nature; PDC Vietnam documentation (reliefweb.int)

---

## 9. Institutional Framework

### 9.1 Key Agencies

| Agency | Abbreviation | Role |
|---|---|---|
| **Vietnam Disaster and Dyke Management Authority** | VDDMA | VNDMS development and operation |
| **Disaster Policy and Technology Center** | DMPTC | VNDMS technical implementation |
| **National Center for Hydro-Meteorological Forecasting** | NCHMF | Weather and flood forecasting |
| **Vietnam Hydro-Meteorological Administration** | VHMA | Hydro-meteorological data network |
| **Ministry of Natural Resources and Environment** | MONRE | Environmental monitoring, QCVN standards |
| **Ministry of Agriculture and Rural Development** | MARD | VinAWARE, dam safety, agricultural disaster |
| **Vietnam Institute of Geosciences and Mineral Resources** | VIGMR | Landslide and geological hazard research |
| **National Steering Committee for Natural Disaster Prevention** | — | Top-level coordination |

### 9.2 Legal Framework

| Instrument | Date | Subject |
|---|---|---|
| **Law 33/2013/QH13** | 2013 | Law on Natural Disaster Prevention and Control |
| **Law 60/2020/QH14** | 2020 (revised) | Revised disaster prevention law |
| **Decision 245/2006/QĐ-TTg** | 2006 | Extended wind scale to Level 17 |
| **Nghị định 66/2021/ND-CP** | 2021 | Disaster information dissemination rules |
| **Nghị định 78/2021/NĐ-CP** | 2021 | Natural Disaster Prevention Fund |
| **Decision 18/2021/QĐ-TTg** | 2021 | Forecast/warning and 5-level risk system |
| **Decision 05/2020/QĐ-TTg** | 2020 | Water level alarm thresholds at 244 stations |
| **Thông tư 22/2019/TT-BTNMT** | 2019 | QCVN 18:2019/BTNMT flood forecasting standard |
| **Thông tư 14/2021/TT-BTNMT** | 2021 | Technical methodology for water level thresholds |
| **Decision 46/2014/QĐ-TTg** | 2014 | Wave and wind scale table |
| **Decision 379/QĐ-TTg** | 2021 | National disaster strategy to 2030/2050 |
| **Decision 342/QĐ-TTg** | 2022 | National disaster prevention plan to 2025 |

### 9.3 Information Dissemination Requirements

Under Nghị định 66/2021/ND-CP, broadcast media must provide updates:
- **Level 1–3 disasters:** Every **3 hours**
- **Level 4–5 disasters:** Every **1 hour**

---

## 10. Summary: VNDMS Algorithm Inputs and Logic

### 10.1 Input Data Flow

```
[RAINFALL DATA] ────┐
[WATER LEVEL DATA] ──┼──→ [FORECASTING MODEL] ──→ [RISK CALCULATION] ──→ [VNDMS ALERT]
[DAM/RESERVOIR] ────┤   (QCVN 18:2019 or        (Decision 18/2021)       (5-level output)
[WIND/DIRECTION] ───┤    HEC-HMS/etc.)                                    + color map
[SURGE/WAVE] ───────┤
[SATELLITE] ────────┘
```

### 10.2 Risk Calculation Rules

1. **Base level** determined by the primary hazard's intensity against type-specific thresholds
2. **Type capping** applied (e.g., storm minimum Level 3; tornado maximum Level 2)
3. **Compound event escalation** (+1 or +2) if multiple hazards coincide
4. **Final level** capped at Level 5

### 10.3 Known Limitations

- Landslide/debris flow thresholds are region-specific and not uniformly standardized nationally
- Mountainous provinces (including Điện Biên) have sparse station coverage
- Flash flood warning lead times in small catchments can be extremely short (minutes)
- Cross-system data integration between VNDMS and VinAWARE is not seamless
- Real-time data gaps remain in areas with poor telecommunications infrastructure

---

## 11. Recommendations for HINATION System Alignment

Based on this analysis, the hination-hackathon system should consider:

| Recommendation | Rationale |
|---|---|
| Implement Decision 18/2021/QĐ-TTg's 5-level framework as the core risk schema | This is the national legal standard; VNDMS uses this framework |
| Use QCVN 18:2019/BTNMT methodology for flood level classification | National technical standard with defined probability thresholds |
| Integrate rainfall ≥50 mm/24h as a baseline alert trigger | VNDMS operational threshold |
| For Điện Biên: establish Nậm Rốm-specific thresholds calibrated to local return periods | No national station thresholds exist for this sub-basin |
| For flash flood: implement intensity-duration rainfall thresholds with very short lead time logic | Mountainous terrain means flash flood is primary risk in upstream areas |
| Use compound risk escalation (+1/+2) when multiple hazards are active | Explicit rule in Decision 18/2021/QĐ-TTg |
| Include wind speed mapping to Beaufort Levels 8–17 for storm classification | Vietnam's official storm classification system |
| Build modular hazard type handlers since each disaster type has different level ranges | Storm (3–5), tornado (1–2), heavy rain (1–4), flood (1–5) |

---

## References

1. VDDMA/DMPTC. "Instructions for use and exploitation of information on Vietnam Disaster Monitoring System." dmc.gov.vn (March 2020). http://www.dmc.gov.vn/news-detail/instructions-for-use-and-exploitation-of-information-on-vietnam-disaster-monitoring-system-cd9899-32.html?lang=en-US

2. NIAR Taiwan. "Vietnam – Disaster Management." New Southbound Science & Technology Cooperation Network (December 2024). https://nsstc.niar.org.tw/en/highlights/analysis/2024-12-19-vn-dm

3. Thủ tướng Chính phủ. "Quyết định số 18/2021/QĐ-TTg về dự báo, cảnh báo, truyền tin thiên tai và cấp độ rủi ro thiên tai." (April 22, 2021).

4. Thủ tướng Chính phủ. "Quyết định số 05/2020/QĐ-TTg quy định mực nước tương ứng với các cấp báo động lũ." (January 31, 2020).

5. Bộ Tài nguyên và Môi trường. "Thông tư 14/2021/TT-BTNMT quy định kỹ thuật xây dựng mực nước tương ứng với các cấp báo động lũ." (August 31, 2021).

6. Bộ Tài nguyên và Môi trường. "Thông tư 22/2019/TT-BTNMT ban hành QCVN 18:2019/BTNMT về dự báo, cảnh báo lũ." (December 25, 2019).

7. Thủ tướng Chính phủ. "Quyết định số 245/2006/QĐ-TTg về quy định thang đo gió bão." (2006).

8. Chính phủ. "Nghị định 66/2021/ND-CP hướng dẫn Luật Phòng, chống thiên tai." (July 2021).

9. UBND tỉnh Điện Biên. "Quyết định số 596/QĐ-UBND về quy hoạch tiêu thoát lũ khu vực lòng chảo Điện Biên đến 2025, định hướng 2035." (April 28, 2016).

10. UBND tỉnh Điện Biên. "Chỉ thị 04/CT-UBND về phòng chống thiên tai và tìm kiếm cứu nạn năm 2020." (2020).

11. Thủ tướng Chính phủ. "Quyết định 170/QĐ-TTg phê duyệt dự án quản lý đa thiên tai lưu vực sông Nậm Rốm." (EU/AFD supported project).

12. EU-AFD. "Hỗ trợ Điện Biên quản lý thiên tai sông Nậm Rốm." SETP Vietnam. https://setp.vn/vi/eu_news/eu-va-afd-ho-tro-dien-bien-quan-ly-thien-tai-song-nam-rom/

13. NCHMF / Trung tâm Chính sách và Kỹ thuật PCTT. "Bão và phân loại cấp gió." dmc.gov.vn/basic-knowledge/storm-pt32.html

14. Trung tâm Dự báo Khí tượng Thủy văn quốc gia. "Mô tả cấp gió bão và mức độ ảnh hưởng." vnmha.mae.gov.vn

15. Nguyen, H., Hoang, H., Nguyen, S., & Tran, C.K. (2026). "Developing a Real-Time Flash Flood Early Warning System for the Tra River Basin: Combining Field Surveys and Hydrological Modeling." Water Resources, 53, 277–288. Springer Nature. https://doi.org/10.1134/S0097807825601554

16. PDC / USAID. "Vietnam Flood Early Warning Project Phase 2." ReliefWeb. https://reliefweb.int/report/viet-nam/vietnam-flood-early-warning-project-phase-2-brings-stakeholders-together

17. Thủ tướng Chính phủ. "Quyết định 379/QĐ-TTg Chiến lược quốc gia phòng, chống thiên tai đến năm 2030, tầm nhìn 2050." (March 2021).

18. Thủ tướng Chính phủ. "Quyết định 342/QĐ-TTg Kế hoạch phòng, chống thiên tai quốc gia đến năm 2025." (March 2022).

19. Wikipedia. "Tropical cyclones in Vietnam." https://en.wikipedia.org/wiki/Tropical_cyclones_in_Vietnam

---

*Document prepared as part of the HINATION hackathon project. Last updated: July 2026.*
*This analysis synthesizes publicly available Vietnamese government regulations, international academic literature, and policy analyses. For operational use, consult the original Vietnamese legal texts for authoritative threshold values.*
