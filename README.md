# 🌿 GreenOrch v3.0 — Carbon-Aware Sustainable Cloud Scheduler

> **3SVK Hackathon | Track 4: Sustainable Orchestration**
> Energy-Efficient Kubernetes Workload Management · ESG Compliant · Before vs After Comparison

---

## 🎯 What This Project Does

GreenOrch v3 is a full-stack platform that demonstrates how **intelligent Kubernetes orchestration reduces carbon emissions** by scheduling cloud workloads to the most energy-efficient region.

### Track 4 Requirements Fulfilled

| Requirement | Implementation |
|-------------|----------------|
| ✅ K8s Workload Scheduling | Simulates pod placement across 8 K8s clusters |
| ✅ Energy Efficiency Monitoring | Real-time CPU/RAM/Energy per cluster |
| ✅ Before vs After Comparison | Side-by-side Traditional vs GreenOrch results |
| ✅ Cloud Carbon Footprint Reduction | 62-97% CO₂ reduction demonstrated |
| ✅ ESG Standards | Full E/S/G report with grades per region |
| ✅ DevOps / Kubernetes Focus | K8s YAML configs, cluster monitor page |

---

## 🚀 VS Code — Run Commands

### Prerequisites Check
```bash
python --version    # needs any version (3.8–3.14 all work)
node --version      # needs 16+
npm --version
```

### Terminal 1 — Backend
```bash
cd backend
pip install fastapi uvicorn pydantic python-multipart
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Terminal 2 — Frontend
```bash
cd frontend
npm install
npm start
```

**Expected output:**
```
Compiled successfully!
Local:  http://localhost:3000
```

### ✅ Open in browser: http://localhost:3000

---

## 🌐 Vercel Deployment — Step by Step

### Step 1 — Push to GitHub
```bash
# From project root (greenorch_v3 folder)
git init
echo "node_modules/" > .gitignore
echo "__pycache__/" >> .gitignore
git add .
git commit -m "GreenOrch v3 — Track 4 Sustainable Orchestration"
git remote add origin https://github.com/YOUR_USERNAME/greenorch-v3.git
git push -u origin main
```

### Step 2 — Deploy Backend on Vercel
1. Go to **vercel.com** → **Add New Project**
2. Import your GitHub repo
3. Set **Root Directory** → `backend`
4. **Framework Preset** → `Other`
5. Click **Deploy**
6. Copy your backend URL → e.g. `https://greenorch-v3-api.vercel.app`

### Step 3 — Update Frontend API URL
Open `frontend/src/App.jsx` line 6:
```js
const API = process.env.REACT_APP_API_URL || "https://greenorch-v3-api.vercel.app";
```
Replace with your actual backend URL.

### Step 4 — Deploy Frontend on Vercel
1. Go to **vercel.com** → **Add New Project** again
2. Import the **same** repo
3. Set **Root Directory** → `frontend`
4. **Framework Preset** → `Create React App`
5. Add **Environment Variable**:
   - Name: `REACT_APP_API_URL`
   - Value: `https://greenorch-v3-api.vercel.app` (your backend URL)
6. Click **Deploy**

### Step 5 — Push and Auto-Deploy
```bash
git add frontend/src/App.jsx
git commit -m "Connect frontend to production API"
git push
```
Vercel auto-redeploys in ~1 minute.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health + service info |
| GET | `/api/v1/health` | System components health |
| GET | `/api/v1/regions` | All 8 K8s regions with live carbon |
| GET | `/api/v1/carbon/live` | Real-time carbon feed (30s) |
| GET | `/api/v1/carbon/budget` | Monthly CO₂ budget tracker |
| POST | `/api/v1/workloads` | Schedule a K8s workload |
| POST | `/api/v1/simulations` | Batch simulation (20 workloads) |
| GET | `/api/v1/analytics/summary` | 30-day Before vs After analytics |
| GET | `/api/v1/ml/forecast` | 24h CPU forecast |
| GET | `/api/v1/k8s/clusters` | All K8s cluster status |
| GET | `/api/v1/esg/report` | Full ESG report with grades |
| GET | `/api/v1/workloads/history` | Recent workload history |

**Swagger UI:** `http://localhost:8000/docs`
**ReDoc:** `http://localhost:8000/redoc`

---

## 🧠 Core Algorithm

```
Energy  = CPU_Load × PowerFactor × Execution_Time × PUE
CO₂     = Energy × Regional_Carbon_Intensity
Score   = CO₂_norm(0.70) + Cost_norm(0.20) + Latency_norm(0.10)
Savings = ((Before - After) / Before) × 100
```

### ML Ensemble Model
```
Predicted_CPU = LR(40%) + MovingAvg(35%) + TimePattern(25%)
```

---

## 🌍 K8s Clusters

| Cluster | Provider | CO₂/kWh | Renewable | ESG Score |
|---------|----------|---------|-----------|-----------|
| aks-eu-north-prod | Azure | 0.013 | 98% | 97/100 |
| eks-us-west-prod | AWS | 0.091 | 89% | 84/100 |
| gke-us-central-prod | GCP | 0.147 | 79% | 76/100 |
| eks-eu-west-prod | AWS | 0.198 | 71% | 68/100 |
| aks-eu-central-prod | Azure | 0.233 | 65% | 61/100 |
| eks-us-east-prod | AWS | 0.386 | 42% | 40/100 |
| gke-ap-southeast-prod | GCP | 0.431 | 35% | 33/100 |
| gke-asia-south-prod | GCP | 0.708 | 18% | 14/100 |

---

## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| **Dashboard** | KPIs, live feed, world map, before/after trend |
| **K8s Simulation** | Submit workload → see Before vs After comparison |
| **Cluster Monitor** | All 8 K8s clusters — CPU/RAM/pods/carbon |
| **ESG Report** | E/S/G breakdown, grades, recommendations |
| **Analytics** | ML forecast, hourly carbon, renewable mix |
| **Metrics** | 30-day log, algorithm docs, CSV export |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Recharts (charts), CSS-in-JS |
| Backend | Python FastAPI (pure Python, no compiled deps) |
| ML Model | Custom Ensemble: LR + MovingAvg + TimePattern |
| K8s Simulation | Python cluster simulator |
| ESG Engine | E/S/G scoring across all 8 regions |
| Deployment | Vercel (frontend + backend) |

---

## ✅ Python 3.14 Compatible

**Zero compiled dependencies** — no numpy, pandas, scikit-learn needed.
All ML and math is implemented in pure Python standard library.

```
pip install fastapi uvicorn pydantic python-multipart
```
That's it. Works on Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14.

---

*GreenOrch v3.0 · Track 4: Sustainable Orchestration · 3SVK Hackathon · Cre8Techin Jury*
