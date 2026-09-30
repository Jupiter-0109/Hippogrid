# HIPPOGRID
### Healthcare Infrastructure & Primary-care Planning Optimization Grid

[![Python 3.10.7](https://img.shields.io/badge/python-3.10.7-blue.svg)](https://www.python.org/downloads/release/python-3107/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 72 Passing](https://img.shields.io/badge/tests-72%20passed-brightgreen.svg)]()
[![Repository](https://img.shields.io/badge/GitHub-Joelrajjoe%2FHippogrid-181717.svg?logo=github)](https://github.com/Joelrajjoe/Hippogrid.git)

> *"Don't just predict the shortage. Guarantee the service."*

**HippoGrid** is a production-grade service-continuity assurance digital twin engineered for Primary Health Centre (PHC) networks. Rather than emitting detached alerts, HippoGrid proactively computes multi-dependency vulnerability horizons (pharmaceuticals, cold chain, workforce, inpatient beds, power, logistics corridors) and synthesizes mathematically assured, human-reviewed resource rebalancing interventions.

---

## The 8 Core Questions HippoGrid Answers

1. **Which essential service is at risk?** (e.g., Diarrhoeal Care, Maternal Delivery, Cold Chain Vaccination)
2. **At which PHC?** (e.g., `PHC-DST-A1-04` — North Sector-4)
3. **How many hours until service continuity is compromised?** (e.g., Service Capability Horizon = 28.2 hours)
4. **Which dependency is causing the risk?** (e.g., Oral Rehydration Salts & Zinc buffer exhaustion)
5. **What combination of shocks can break the network?** (e.g., Reverse stress frontier at $\|S\| = 0.411$: 2.32x monsoon rain, 33% road closures, 26% staff absenteeism, 1.85x demand surge)
6. **What resource intervention can preserve service continuity?** (e.g., OR-Tools MILP transfer of 87 units ORS from `PHC-DST-A1-03` to `PHC-DST-A1-04`)
7. **How confident is the recommendation?** (Split conformal prediction bounds: $[4.2, 8.1]$ cases at 90% finite-sample empirical coverage)
8. **What did the human decision-maker approve or modify?** (Parametric review override recorded with reason code into the Regret Ledger with immutable audit trail)

---

## System Architecture

```text
Hippogrid/
├── AGENTS.md                  # System rules, design directives, random seed 42
├── PROGRESS.md                # 16-phase milestone delivery tracker
├── README.md                  # Architecture, setup guide, and documentation
├── requirements.txt           # Pinned dependencies for Python 3.10.7
├── .env.example               # Environment variables template
├── pytest.ini                 # Pytest configuration and path discovery
│
├── config/
│   ├── params.yaml            # Operational thresholds, simulation params, seed 42
│   └── service_map.yaml       # Clinical service dependency topology & burn rates
│
├── supabase/
│   └── migrations/            # SQL migration scripts for 27 system-of-record tables
│
├── backend/
│   ├── main.py                # FastAPI entrypoint, middleware, router aggregation
│   ├── api/                   # REST API route handlers:
│   │   ├── health.py          # GET /health
│   │   ├── data_quality.py    # GET /api/v1/data-quality
│   │   ├── continuity.py      # GET /api/v1/sch/horizons, /api/v1/continuity/status
│   │   ├── forecast.py        # GET /api/v1/forecast, /api/v1/forecast/conformal
│   │   ├── simulate.py        # POST /api/v1/simulate, GET /api/v1/simulate/results
│   │   ├── plan.py            # POST /api/v1/plan/prescribe
│   │   ├── stress.py          # GET /api/v1/stress/frontier, /api/v1/stress/fragility
│   │   ├── feedback.py        # POST /api/v1/feedback/review
│   │   └── federated.py       # GET /api/v1/federated/evaluate, POST /train
│   ├── core/                  # Configuration, schemas, data quality validator
│   ├── db/                    # SQLAlchemy engine, session management, ORM models
│   ├── sim/                   # Network digital twin, topology generator, spillover
│   ├── ml/                    # Feature engineering, XGBoost forecasting, conformal
│   ├── sch/                   # Service-Capability Graph, bottleneck & horizon engine
│   ├── opt/                   # Two-stage OR-Tools MILP resource prescriber
│   ├── stress/                # Reverse stress engine & empirical resilience frontier
│   ├── federated/             # Federated learning (FedAvg) shock response engine
│   └── feedback/              # Human review validation & Regret Ledger
│
├── frontend/                  # React + TypeScript + Vite modern command center
│   ├── src/
│   │   ├── components/        # Network Resilience Map (Leaflet), KPI cards, tables
│   │   ├── types/             # Domain TypeScript interfaces
│   │   ├── services/          # API client & mock data fallback layer
│   │   ├── App.tsx            # Main command center shell with 10 view tabs
│   │   └── index.css          # Vanilla CSS design system (Tailwind-free)
│   ├── package.json           # Frontend dependencies
│   └── vite.config.ts         # Vite bundler configuration
│
├── data/
│   ├── raw/                   # 18-month daily telemetry across 3 states & 36 PHCs
│   └── processed/results/     # Benchmarks and evaluation results (E1-E6)
│
├── tests/                     # 72 automated unit, integration, and regression tests
├── docs/                      # Technical documentation & experimental results
└── scripts/                   # CLI runners:
    ├── demo.py                # Phase 16 interactive 5-day lifecycle demonstration
    ├── run_evaluations.py     # Automated experimental benchmarks (E1-E6)
    ├── generate_synthetic_data.py # Synthetic data generation engine
    └── test_db_connection.py  # Supabase PostgreSQL connectivity verification
```

---

## Environment Setup & Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Joelrajjoe/Hippogrid.git
cd Hippogrid
```

---

### Step 2: Backend Setup (Python 3.10.7)

HippoGrid requires **Python 3.10.7** strictly.

#### Windows (PowerShell)
```powershell
# 1. Verify Python version
python --version
# Expected: Python 3.10.7

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install pinned requirements
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Linux / macOS (Bash)
```bash
# 1. Verify Python version
python3 --version
# Expected: Python 3.10.7

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip and install pinned requirements
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 3: Frontend Setup (Node.js 18+ / 20+)

```bash
cd frontend
npm install
cd ..
```

---

### Step 4: Configure Environment Variables

Copy the template configuration file:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Configure your credentials inside `.env`:
```ini
ENVIRONMENT=development
LOG_LEVEL=INFO
RANDOM_SEED=42

# Backend Host & Port
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Supabase PostgreSQL (System of Record)
SUPABASE_URL=https://ucihhursqublehkxpqqm.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
DATABASE_URL=postgresql://postgres:your_password@db.ucihhursqublehkxpqqm.supabase.co:5432/postgres

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://ucihhursqublehkxpqqm.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_publishable_key
```

---

## Running the Application

### 1. Run the End-to-End Command Center Demo

Experience the full 5-day proactive assurance lifecycle (`Day -4` to `Day 0`, plus Stress Lab and Audit Trail) with live calculations from the running system:

```bash
python scripts/demo.py
```

---

### 2. Start the Backend API Server

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health check verification:
  ```bash
  curl http://localhost:8000/health
  # Response: {"status":"ok","project":"HippoGrid"}
  ```

---

### 3. Start the Frontend Command Center

In a separate terminal:

```bash
cd frontend
npm run dev
```

Open your browser at: **`http://localhost:5173`**

The command center features:
- **Resilience Map**: Interactive Leaflet topology with PHC nodes, warehouse hubs, and supply corridors.
- **KPI Metrics**: Total Monitored PHCs (36), Services at Risk, Mean Horizon (SCH), Quality Score.
- **Service Continuity Table**: Real-time capability horizons and limiting dependencies.
- **Forecast Center**: XGBoost demand projections with 90% conformal uncertainty bands.
- **Resource Prescriber**: Recommended transfer plans with travel times and assurance scores.
- **Stress Lab**: Interactive Reverse Stress Frontier (Severity vs. Failure Probability).
- **Human-in-the-Loop Review**: Actionable Approve, Edit, Reject interface with audit log capture.

To verify a production frontend bundle build:
```bash
cd frontend
npm run build
```

---

### 4. Run Automated Evaluation Benchmarks

To execute the 6 scientific evaluation benchmarks (Alerts, Conformal, Prescriber Policies, Reverse Stress, Federated FedAvg, and Ablation):

```bash
python scripts/run_evaluations.py
```

Results are stored in `data/processed/results/` and summarized in `docs/RESULTS.md`.

---

### 5. Run the Automated Test Suite

HippoGrid includes 72 unit, integration, and regression tests:

```bash
python -m pytest -q
```
*Expected: `72 passed in ~50s`.*

---

## Database Schema & Migrations

HippoGrid uses **Supabase PostgreSQL** as its system of record. Migrations are organized in `supabase/migrations/`:

| Migration File | Description |
| :--- | :--- |
| `20260930000001_initial_schema.sql` | Master geography (`states`, `districts`, `phcs`, `warehouses`, `services`, `medicines`) |
| `20260930000002_daily_telemetry_schema.sql` | Daily operational telemetry (inventory, patient visits, beds, workforce, power, weather, roads) |
| `20260930000003_phase1_relational_schema.sql` | Relational integrity constraints, foreign keys, composite indexes, analytical views |
| `20260930000004_data_quality_results.sql` | Data quality auditing table (`data_quality_results`) |

To verify PostgreSQL database connectivity:
```bash
python scripts/test_db_connection.py
```

---

## Core Operational Guarantees

1. **Deterministic Reproducibility**: All stochastic procedures, random initializations, and Monte Carlo scenario twins are fixed to `seed = 42`.
2. **Conservation of Demand Guarantee**: Strict physical patient flow conservation: $\text{Total Demand} = \text{Served Patients} + \text{Unserved Patients}$. No patients are created or destroyed during spillover.
3. **Finite-Sample Uncertainty Coverage**: Split conformal calibration bounds guarantee a strictly calibrated coverage floor (e.g. 90%) without assuming Gaussian error distributions.
4. **Equity-Aware Transfer Optimization**: The Two-Stage OR-Tools Mixed-Integer Linear Program guarantees donor PHC stock never drops below the 36-hour clinical safety floor.
5. **Human-in-the-Loop Auditability**: Every plan modification or override is preserved in the Regret Ledger with reason codes, clinical notes, and cryptographic provenance.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
