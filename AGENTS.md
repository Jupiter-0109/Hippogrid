# AGENTS.md — HippoGrid Architectural Rules & Agent Guidelines

## 1. Project Identity

- **Project Name**: HippoGrid
- **Expanded Name**: Healthcare Infrastructure & Primary-care Planning Optimization Grid
- **Tagline**: *"Don't just predict the shortage. Guarantee the service."*
- **Core Concept**: Service-continuity assurance digital twin for Primary Health Centre (PHC) networks.

> **CRITICAL DIRECTIVE**: The project was previously named with an older working title. Under NO circumstances should any legacy names be introduced into the UI, code, comments, documentation, schemas, or commit records. Always use **HIPPOGRID**.

---

## 2. Core Architectural Questions HippoGrid Answers

1. Which essential service is at risk?
2. At which PHC?
3. How many hours until service continuity is compromised?
4. Which dependency is causing the risk?
5. What combination of shocks can break the network?
6. What resource intervention can preserve service continuity?
7. How confident is the recommendation?
8. What did the human decision-maker approve or modify?

---

## 3. Technology Stack & Operational Guardrails

- **Python**: `3.10.7` strictly. DO NOT upgrade Python or use syntax incompatible with 3.10.7.
- **Backend**: FastAPI + Uvicorn
- **Database**: Supabase PostgreSQL (System of Record).
  - Do NOT create SQLite as the application database.
  - Do NOT create a local database fallback.
  - Always access operational database tables via SQLAlchemy ORM in backend.
- **Frontend**: React + TypeScript + Vite.
  - Modern Vanilla CSS styling system.
  - Left navigation, top header, rounded cards (18–24px), subtle shadows, light blue/grey background.
  - Isolated mock data layer until API integration phases.
- **Scientific / ML / Optimization**:
  - `scikit-learn` + `xgboost` (Predictive continuity & conformal bounds)
  - `OR-Tools` (Resource transfer and scheduling optimization)
  - `NetworkX` (PHC topological logistics and referral graphs)
- **Deterministic Guarantees**: Random seed is strictly fixed to **42** across all stochastic routines and simulations.

---

## 4. Phase Progression Rules

- **Phase 0 (Current)**:
  - Repository structure, configuration files, documentation, migration schema.
  - FastAPI application with `GET /health` returning `{"status": "ok", "project": "HippoGrid"}`.
  - SQLAlchemy session configuration and Supabase PostgreSQL connectivity validation.
  - Initial React + TypeScript + Vite shell matching the UI aesthetic.
  - Passing tests (`pytest -q`, `npm run build`).
- **Phase 1+ (Future)**:
  - Synthetic data generation, ingestion pipelines, simulation twin, conformal forecasting, and optimization will ONLY be implemented in subsequent phases upon explicit instruction.
  - Do not implement forecasting, optimization, federated learning, or RAG in Phase 0.

---

## 5. Security & Data Integrity

- Never commit real credentials or expose `service_role` secrets.
- Frontend must NEVER receive direct raw database connection credentials or execute unauthenticated DDL/DML.
- All simulation outputs must be explicitly labeled as **simulation results**. Do not invent clinical healthcare diagnoses or fake actual patient identities.
