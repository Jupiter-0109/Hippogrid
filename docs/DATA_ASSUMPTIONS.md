# HippoGrid — Synthetic Data Generation Assumptions & Statistical Models

**Project**: HIPPOGRID (Healthcare Infrastructure & Primary-care Planning Optimization Grid)  
**Document Version**: 1.0 (Phase 2 Delivery)  
**Random Seed**: Strict fixed seed `42` (`np.random.default_rng(42)`)  
**Time Horizon**: 2024-01-01 to 2025-06-30 (18 months / 547 calendar days)

---

## 1. Network Topology & Hierarchy

HippoGrid models a multi-tier public primary healthcare network across 3 distinct geopolitical states:

```
State A (Highland Region) — 18 Months (2024-01-01 to 2025-06-30)
├── District A1 (North Aranya)
│   ├── Warehouse WH-DST-A1 (Central Medical Depot)
│   └── 6 PHCs (PHC-DST-A1-01 to PHC-DST-A1-06)
└── District A2 (South Devgarh)
    ├── Warehouse WH-DST-A2
    └── 6 PHCs (PHC-DST-A2-01 to PHC-DST-A2-06)

State B (Riverine Valley) — 12 Months (2024-07-01 to 2025-06-30)
├── District B1 (East Barani)
│   ├── Warehouse WH-DST-B1
│   └── 6 PHCs (PHC-DST-B1-01 to PHC-DST-B1-06)
└── District B2 (West Kusuma)
    ├── Warehouse WH-DST-B2
    └── 6 PHCs (PHC-DST-B2-01 to PHC-DST-B2-06)

State C (Plateau Corridor) — 18 Months (2024-01-01 to 2025-06-30) [Low Disaster History]
├── District C1 (Chinar Ridge)
│   ├── Warehouse WH-DST-C1
│   └── 6 PHCs (PHC-DST-C1-01 to PHC-DST-C1-06)
└── District C2 (Dharani Plain)
    ├── Warehouse WH-DST-C2
    └── 6 PHCs (PHC-DST-C2-01 to PHC-DST-C2-06)
```

- **States**: Exactly 3
- **Districts**: Exactly 6 (2 per state)
- **Primary Health Centres (PHCs)**: Exactly 36 (6 per district)
- **Warehouses**: Exactly 6 (1 central warehouse co-located with district HQ)

---

## 2. Temporal Staggering & State Invariants

| State Code | Operational Period | Duration | Invariant Rules |
| :--- | :--- | :--- | :--- |
| **STA** | 2024-01-01 to 2025-06-30 | 18 Months (547 days) | Full baseline monsoon vulnerability; flash flood risks. |
| **STB** | 2024-07-01 to 2025-06-30 | 12 Months (365 days) | Onboarded mid-year; high riverine flooding vulnerability. |
| **STC** | 2024-01-01 to 2025-06-30 | 18 Months (547 days) | **Lower disaster history**: Strictly capped at **exactly 2 major flood events** across the entire 18 months. |

---

## 3. Meteorological Modeling (Weather & Disasters)

### A. Temperature (Yearly Seasonality)
Daily mean ambient temperature follows an astronomical harmonic curve with sinusoidal variation:
$$T(d) = 27.5 + 11.0 \cdot \sin\left(\frac{2\pi \cdot (d - 75)}{365.25}\right) + \epsilon_T, \quad \epsilon_T \sim \mathcal{N}(0, 1.8^2)$$
- Peak summer occurs in May ($\approx 38^\circ\text{C}$ to $42^\circ\text{C}$).
- Winter troughs in January ($\approx 14^\circ\text{C}$ to $18^\circ\text{C}$).

### B. Rainfall & Monsoon Effects
- **Monsoon Window**: Day of year 182 to 273 (July 1 to September 30).
- **States A & B**:
  - Monsoon days have a $58\%$ probability of rainfall, modeled as $\text{Gamma}(\alpha=2.5, \beta=18.0)$.
  - Major flood event trigger: daily rainfall $\ge 110.0\text{ mm}$, setting `flood_risk = 'SEVERE'`.
- **State C (Low Disaster History)**:
  - Specifically configured with **exactly 2 major flood events** on `2024-08-14` and `2024-09-08` in District C1 with moderate spillover to District C2.
  - All other days have significantly attenuated rainfall distributions ($\text{Exp}(\lambda=8.5\text{ mm})$ on rain days), ensuring a low disaster profile.

---

## 4. Epidemiological & Healthcare Demand Modeling

Healthcare demand is non-random, deterministically coupling catchment population, day-of-week rhythms, and environmental shocks.

### A. Population Scaling
Each PHC has a catchment population $P_i \in [18,000, 52,000]$, representing rural/semi-urban cluster populations. We define:
$$k_i = \frac{P_i}{1000}$$

### B. Weekly Seasonality (Day-of-Week Effect)
Primary care attendance strongly depends on the weekly cycle:
- **Monday**: $1.25\times$ (backlog from weekend)
- **Tuesday**: $1.15\times$
- **Wednesday**: $1.05\times$
- **Thursday**: $1.00\times$ (nominal)
- **Friday**: $1.05\times$
- **Saturday**: $0.90\times$
- **Sunday**: $0.35\times$ (OPD closed; emergency only)

### C. Rainfall Lag Dynamics
Environmental diseases exhibit physiological and ecological incubation lags:
1. **Acute Diarrheal Cases** (Waterborne):
   - Contamination of shallow dug wells and runoff occurs during heavy downpours.
   - Clinical presentation surges **2 to 3 days post heavy rainfall** ($>40\text{ mm}$):
     $$\text{Cases}_{\text{diarrhea}}(t) \propto k_i \cdot \left[1 + 2.5 \cdot \mathbf{1}_{\{R_{t-2} > 40 \lor R_{t-3} > 40\}}\right]$$
2. **Fever / Vector-Borne Cases** (Malaria / Dengue):
   - Mosquito vector breeding requires stagnant water pooling following monsoon downpours.
   - Clinical fever presentations surge **7 to 10 days post rainfall**:
     $$\text{Cases}_{\text{fever}}(t) \propto k_i \cdot \left[1 + 2.0 \cdot \mathbf{1}_{\{R_{t-8} > 35\}}\right]$$

### D. Deliveries & Emergency
- **Deliveries**: Modeled as $\text{Poisson}(\lambda = 0.08 \cdot k_i)$, generating 1 to 4 deliveries per day per PHC.
- **Emergency Cases**: Modeled as $\text{Poisson}(\lambda = 0.12 \cdot k_i)$.

### E. Realistic Outliers
Specific acute outbreaks are injected at vulnerable remote facilities:
- **Acute Gastroenteritis Outbreak**: `PHC-DST-A1-05` on `2024-08-20` (contaminated village storage tank) produces a $5.2\times$ spike in diarrheal cases ($Z\text{-score} > 5.0$).
- **Dengue Outbreak Cluster**: `PHC-DST-B1-02` on `2024-10-12` produces a $4.5\times$ spike in fever cases ($Z\text{-score} > 4.5$).

---

## 5. Pharmaceutical Inventory & Supply Chain Dynamics

### A. Demand-Driven Consumption Matrix
Medicines are directly consumed based on patient presentations:
- **`oxytocin_inj`**: $2.0\text{ ampoules}$ per delivery.
- **`amoxicillin_500mg`**: $0.35\text{ strips}$ per general OPD case.
- **`ors_sachets`**: $3.0\text{ sachets}$ per diarrheal case.
- **`paracetamol_500mg`**: $1.5\text{ strips}$ per fever case.
- **`iv_fluids_rl`**: $1.8\text{ bottles}$ per emergency case $+ 0.8\text{ bottles}$ per severe diarrheal case.

### B. Continuity & Stockout Formulation (Zero Negative Stock Guarantee)
For each facility $i$, medicine $m$, and day $t$:
$$\text{Available}_{i,m}(t) = \text{OpeningStock}_{i,m}(t) + \text{Received}_{i,m}(t)$$
$$\text{Consumed}_{i,m}(t) = \min\left(\text{Available}_{i,m}(t), \text{Demand}_{i,m}(t)\right)$$
$$\text{ClosingStock}_{i,m}(t) = \text{Available}_{i,m}(t) - \text{Consumed}_{i,m}(t) \ge 0$$
$$\text{OpeningStock}_{i,m}(t+1) = \text{ClosingStock}_{i,m}(t)$$
If demand exceeds available stock, a **stockout** occurs ($\text{Consumed} < \text{Demand}$, $\text{ClosingStock} = 0$), guaranteeing **zero negative stock**.

### C. Replenishment Orders & Lead Times
- PHCs place bi-weekly bulk replenishment orders (every 14 days) to the district central warehouse.
- **Baseline Lead Time**: 3 days.
- **Weather / Flood Delay**: Expands to 7 days if road networks are degraded or blocked due to severe weather.

---

## 6. Workforce & Absenteeism

- **Staffing Footprint**:
  - Medical Officers (MO): 1 to 2
  - Staff Nurses: 2 to 4
  - Auxiliary Nurse Midwives (ANM): 2 to 4
- **Baseline Absenteeism**: $4\%$ to $8\%$.
- **Sunday Absence**: Spikes by $+40\%$ (skeleton emergency duty).
- **Extreme Weather / Road Impassability**: When roads are blocked by flooding, staff traveling from district headquarters cannot reach remote centers, increasing absenteeism by $+30\%$ to $+55\%$.

---

## 7. Bed Occupancy

- Total PHC bed capacity: 4 to 10 beds.
- Daily admissions: 100% of deliveries (staying 1–2 days) $+ 40\%$ of emergency cases $+ 15\%$ of severe dehydrating diarrhea.
- Available beds: $\max(0, \text{TotalBeds} - \text{OccupiedBeds})$.

---

## 8. Power Grid Reliability & Fuel Consumption

- **Baseline Outage**: $1.8\text{ hours/day}$ (semi-urban) vs $3.8\text{ hours/day}$ (remote).
- **Storm / Grid Trip Effect**: Heavy rain ($>80\text{ mm}$) and flooding increase grid outages by $7.0$ to $14.0\text{ hours/day}$.
- **Grid Uptime**: $24.0 - \text{OutageHours}$.
- **Generator Fuel**: $2.2\text{ liters/outage hour}$ for standard $15\text{ kVA}$ diesel generators, reduced by $15\%$ for hybrid solar facilities.

---

## 9. Road Logistics & Travel Times

- Road segments link adjacent PHCs in each district chain and connect each PHC to its district warehouse.
- **Baseline Transit Speed**: $40\text{ km/h}$.
- **Dynamic Road Status**:
  - `OPEN`: Nominal conditions ($0.95\times$ to $1.1\times$ travel time).
  - `DEGRADED`: Moderate rainfall ($>40\text{ mm}$), travel time increases to $1.4\times - 2.0\times$.
  - `BLOCKED`: Severe flood / rainfall $>90\text{ mm}$, travel time increases $4.5\times - 7.0\times$ due to road submersion.

---

## 10. Data Quality Artifacts (Missing Values)

To reflect real-world sensor dropouts and cellular telemetry failures, a controlled missing-value injection is applied:
- `rainfall_mm` and `temperature_celsius`: $1.5\%$ missing (`NaN`).
- `outage_hours` and `grid_uptime_hours`: $2.0\%$ missing.
- `opd_cases` and `emergency_cases`: $1.8\%$ missing.
- `absenteeism_rate`: $2.0\%$ missing.

All missing percentages are bounded strictly between $1.0\%$ and $2.5\%$.
