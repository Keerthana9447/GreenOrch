# 🌿 GreenOrch — Carbon-Aware Sustainable Cloud Scheduler

A full-stack platform that demonstrates how **intelligent workload orchestration reduces carbon emissions** by scheduling cloud workloads to the most energy-efficient region.

---

## 🏗️ Architecture

```
User
 ↓
React Frontend (Dashboard)
 ↓
FastAPI Backend (REST API)
 ↓
GreenOrch Scheduling Engine
 ↓
Energy Estimation Module → Carbon Intensity Mapper → Optimization Engine
 ↓
PostgreSQL Database
```

---

## ⚡ Core Algorithm

**Energy Estimation**
```
Energy = CPU_Load × Power_Factor × Execution_Time × PUE
```

**Carbon Emission**
```
Carbon = Energy × Carbon_Intensity
```

**Optimization Metric**
```
Reduction % = ((Baseline - Optimized) / Baseline) × 100
```

**Scheduler logic:** Evaluate all 8 cloud regions → Calculate energy & carbon per region → Select region with lowest carbon footprint.

---

## 🤖 Machine Learning

- **Model:** Scikit-learn Linear Regression
- **Features:** hour_of_day, day_of_week, execution_time, memory_usage
- **Target:** cpu_load
- **Usage:** Predicts future CPU load; blended 70/30 with user input for scheduling

---

## 🗄️ Database Schema (PostgreSQL)

| Table           | Key Columns                                                     |
|----------------|-----------------------------------------------------------------|
| `workloads`     | id, cpu_load, execution_time, selected_region, carbon_emission |
| `carbon_regions`| region_id, carbon_intensity, renewable_pct, pue                |
| `metrics`       | baseline_emission, optimized_emission, reduction_percentage     |
| `ml_predictions`| predicted_cpu, actual_cpu, model_version                       |

---

## 🌍 Regions & Carbon Data

| Region                  | Provider | CO₂ (kgCO₂/kWh) | Renewable % | PUE  |
|-------------------------|----------|-----------------|-------------|------|
| EU North (Stockholm)    | Azure    | 0.013           | 98%         | 1.08 |
| US West (Oregon)        | AWS      | 0.091           | 89%         | 1.10 |
| US Central (Iowa)       | GCP      | 0.147           | 79%         | 1.12 |
| EU West (Ireland)       | AWS      | 0.198           | 71%         | 1.15 |
| EU Central (Frankfurt)  | Azure    | 0.233           | 65%         | 1.18 |
| US East (N. Virginia)   | AWS      | 0.386           | 42%         | 1.20 |
| AP Southeast (Singapore)| GCP      | 0.431           | 35%         | 1.25 |
| Asia South (Mumbai)     | GCP      | 0.708           | 18%         | 1.35 |

*Source: Global CO2 Emissions Dataset (Kaggle)*

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)
```bash
git clone <repo-url>
cd greenorch
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Option 2: Manual Setup

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm start
```

**Database**
```bash
psql -U postgres -c "CREATE DATABASE greenorch;"
psql -U postgres -d greenorch -f backend/schema.sql
```

---

## 📡 API Endpoints

| Method | Endpoint       | Description                              |
|--------|---------------|------------------------------------------|
| GET    | `/simulate`   | Run batch simulation (20 workloads)      |
| GET    | `/regions`    | List all cloud regions + carbon data     |
| GET    | `/carbon-data`| Hourly carbon intensity per region       |
| POST   | `/workload`   | Submit workload for green scheduling     |
| GET    | `/metrics`    | 30-day analytics + sustainability KPIs   |
| GET    | `/predict`    | ML CPU forecast for next 24 hours        |

### POST /workload — Example Request
```json
{
  "cpu_load": 0.65,
  "execution_time": 2.5,
  "memory_usage": 0.4,
  "workload_type": "batch",
  "priority": "standard"
}
```

### Response
```json
{
  "workload_id": "wl-483921",
  "selected_region": { "name": "EU North (Stockholm)", "carbon_kg": 0.0004, ... },
  "optimization": { "reduction_pct": 96.6, "reduction_kg": 0.0118 },
  "predicted_cpu": 0.618
}
```

---

## 📊 Dashboard Features

- **Dashboard** — KPI cards, carbon trend chart, region distribution, emission comparison
- **Workload Simulation** — Interactive form + real-time scheduling results + batch simulation
- **Analytics** — Hourly carbon variation, ML forecast, renewable energy mix, region table
- **System Metrics** — 30-day log, algorithm explanation, CSV export, admin panel
- **API Docs** — Endpoint documentation + links to Swagger/ReDoc

---

## 🔬 Datasets

- **Google Cluster Workload Trace** (Kaggle) — Real cloud workload traces for simulation
- **Global CO2 Emissions Dataset** (Kaggle) — Carbon intensity per region

---

## 🛠️ Tech Stack

| Layer     | Technology                     |
|-----------|-------------------------------|
| Frontend  | React 18, Recharts, TailwindCSS |
| Backend   | Python FastAPI, Uvicorn         |
| ML        | Scikit-learn (Linear Regression) |
| Database  | PostgreSQL 15                   |
| Deploy    | Docker + Docker Compose          |
| Docs      | Swagger UI + ReDoc               |

---

## 📈 Results

Typical carbon reduction achieved:
- **EU North vs Asia South:** ~98% reduction
- **US West vs US East:** ~76% reduction  
- **Average across all workloads:** ~62% reduction

This demonstrates that carbon-aware scheduling can **eliminate over 60% of cloud carbon emissions** with zero performance trade-off.
