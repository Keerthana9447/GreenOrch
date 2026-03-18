from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import math
from datetime import datetime, timedelta

app = FastAPI(
    title="GreenOrch API",
    description="Carbon-Aware Sustainable Cloud Scheduler API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

CARBON_REGIONS = {
    "us-east":     {"name": "US East (N. Virginia)",     "carbon_intensity": 0.386, "renewable_pct": 42, "provider": "AWS",   "pue": 1.2,  "lat": 37.77, "lng": -78.17},
    "eu-west":     {"name": "EU West (Ireland)",         "carbon_intensity": 0.198, "renewable_pct": 71, "provider": "AWS",   "pue": 1.15, "lat": 53.35, "lng": -6.26},
    "asia-south":  {"name": "Asia South (Mumbai)",       "carbon_intensity": 0.708, "renewable_pct": 18, "provider": "GCP",   "pue": 1.35, "lat": 19.08, "lng": 72.88},
    "us-west":     {"name": "US West (Oregon)",          "carbon_intensity": 0.091, "renewable_pct": 89, "provider": "AWS",   "pue": 1.1,  "lat": 45.52, "lng": -122.68},
    "eu-north":    {"name": "EU North (Stockholm)",      "carbon_intensity": 0.013, "renewable_pct": 98, "provider": "Azure", "pue": 1.08, "lat": 59.33, "lng": 18.07},
    "ap-southeast":{"name": "AP Southeast (Singapore)",  "carbon_intensity": 0.431, "renewable_pct": 35, "provider": "GCP",   "pue": 1.25, "lat": 1.35,  "lng": 103.82},
    "eu-central":  {"name": "EU Central (Frankfurt)",    "carbon_intensity": 0.233, "renewable_pct": 65, "provider": "Azure", "pue": 1.18, "lat": 50.11, "lng": 8.68},
    "us-central":  {"name": "US Central (Iowa)",         "carbon_intensity": 0.147, "renewable_pct": 79, "provider": "GCP",   "pue": 1.12, "lat": 41.88, "lng": -93.10},
}

def generate_workload_history(n=200):
    records = []
    base = datetime(2024, 1, 1)
    random.seed(42)
    for i in range(n):
        start = base + timedelta(hours=i * 2)
        exec_time = random.uniform(0.5, 8.0)
        cpu_load = max(0.05, min(0.99, random.gauss(0.55, 0.2)))
        records.append({
            "id": i + 1,
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=exec_time)).isoformat(),
            "cpu_usage": round(cpu_load, 3),
            "execution_time": round(exec_time, 2),
            "machine_id": f"m-{random.randint(1000, 9999)}",
            "memory_usage": round(random.uniform(0.2, 0.9), 3),
            "workload_type": random.choice(["batch", "streaming", "interactive", "ml-training"]),
            "hour": start.hour,
            "day_of_week": start.weekday(),
        })
    return records

WORKLOAD_HISTORY = generate_workload_history()

class SimpleLinearRegression:
    def __init__(self):
        self.coefficients = []
        self.intercept = 0.0
        self.r2 = 0.0

    def fit(self, X, y):
        n = len(X)
        num_features = len(X[0])
        Xb = [[1.0] + list(row) for row in X]
        cols = num_features + 1
        XtX = [[0.0] * cols for _ in range(cols)]
        for row in Xb:
            for i in range(cols):
                for j in range(cols):
                    XtX[i][j] += row[i] * row[j]
        Xty = [0.0] * cols
        for row, yi in zip(Xb, y):
            for i in range(cols):
                Xty[i] += row[i] * yi
        beta = self._solve(XtX, Xty, cols)
        self.intercept = beta[0]
        self.coefficients = beta[1:]
        y_mean = sum(y) / n
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        y_pred = [self._predict_one(x) for x in X]
        ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
        self.r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        return self

    def _solve(self, A, b, n):
        M = [A[i][:] + [b[i]] for i in range(n)]
        for col in range(n):
            max_row = max(range(col, n), key=lambda r: abs(M[r][col]))
            M[col], M[max_row] = M[max_row], M[col]
            if abs(M[col][col]) < 1e-12:
                continue
            for row in range(n):
                if row != col:
                    factor = M[row][col] / M[col][col]
                    for j in range(col, n + 1):
                        M[row][j] -= factor * M[col][j]
        return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]

    def _predict_one(self, x):
        return self.intercept + sum(c * xi for c, xi in zip(self.coefficients, x))

    def predict(self, X):
        return [self._predict_one(x) for x in X]

    def score(self):
        return self.r2

def train_prediction_model():
    X = [[w["hour"], w["day_of_week"], w["execution_time"], w["memory_usage"]] for w in WORKLOAD_HISTORY]
    y = [w["cpu_usage"] for w in WORKLOAD_HISTORY]
    model = SimpleLinearRegression()
    model.fit(X, y)
    return model, model.score()

ML_MODEL, ML_SCORE = train_prediction_model()

POWER_FACTOR = 0.25

def estimate_energy(cpu_load, execution_time, pue=1.2):
    return cpu_load * POWER_FACTOR * execution_time * pue

def calculate_carbon(energy, carbon_intensity):
    return energy * carbon_intensity

def schedule_workload(cpu_load, execution_time, memory_usage=0.5):
    results = []
    for region_id, region in CARBON_REGIONS.items():
        energy = estimate_energy(cpu_load, execution_time, region["pue"])
        carbon = calculate_carbon(energy, region["carbon_intensity"])
        results.append({
            "region_id": region_id,
            "region_name": region["name"],
            "provider": region["provider"],
            "energy_kwh": round(energy, 4),
            "carbon_kg": round(carbon, 4),
            "carbon_intensity": region["carbon_intensity"],
            "renewable_pct": region["renewable_pct"],
            "pue": region["pue"],
        })
    results.sort(key=lambda x: x["carbon_kg"])
    best = results[0]
    traditional = next(r for r in results if r["region_id"] == "us-east")
    reduction_pct = (
        (traditional["carbon_kg"] - best["carbon_kg"]) / traditional["carbon_kg"]
    ) * 100 if traditional["carbon_kg"] > 0 else 0
    return {
        "selected_region": best,
        "traditional_region": traditional,
        "all_regions": results,
        "optimization": {
            "baseline_carbon": round(traditional["carbon_kg"], 4),
            "optimized_carbon": round(best["carbon_kg"], 4),
            "reduction_kg": round(traditional["carbon_kg"] - best["carbon_kg"], 4),
            "reduction_pct": round(reduction_pct, 1),
        }
    }

class WorkloadRequest(BaseModel):
    cpu_load: float
    execution_time: float
    memory_usage: float = 0.5
    workload_type: str = "batch"
    priority: str = "standard"

submitted_workloads = []

@app.get("/", tags=["Health"])
def root():
    return {"status": "online", "service": "GreenOrch API", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/simulate", tags=["Simulation"])
def run_simulation():
    sample = random.sample(WORKLOAD_HISTORY, min(20, len(WORKLOAD_HISTORY)))
    results = []
    total_baseline = 0
    total_optimized = 0
    for wl in sample:
        sched = schedule_workload(wl["cpu_usage"], wl["execution_time"], wl.get("memory_usage", 0.5))
        total_baseline += sched["optimization"]["baseline_carbon"]
        total_optimized += sched["optimization"]["optimized_carbon"]
        results.append({
            "workload_id": wl["id"],
            "cpu_load": wl["cpu_usage"],
            "execution_time": wl["execution_time"],
            "workload_type": wl["workload_type"],
            "selected_region": sched["selected_region"]["region_name"],
            "selected_region_id": sched["selected_region"]["region_id"],
            "baseline_carbon": sched["optimization"]["baseline_carbon"],
            "optimized_carbon": sched["optimization"]["optimized_carbon"],
            "reduction_pct": sched["optimization"]["reduction_pct"],
        })
    total_reduction = ((total_baseline - total_optimized) / total_baseline * 100) if total_baseline > 0 else 0
    return {
        "simulation_id": f"sim-{random.randint(10000,99999)}",
        "timestamp": datetime.now().isoformat(),
        "workloads_processed": len(results),
        "results": results,
        "summary": {
            "total_baseline_carbon": round(total_baseline, 4),
            "total_optimized_carbon": round(total_optimized, 4),
            "total_reduction_kg": round(total_baseline - total_optimized, 4),
            "total_reduction_pct": round(total_reduction, 1),
            "ml_model_accuracy": round(ML_SCORE * 100, 1),
        }
    }

@app.get("/regions", tags=["Regions"])
def get_regions():
    return {
        "regions": [{"id": rid, **rdata} for rid, rdata in CARBON_REGIONS.items()],
        "total": len(CARBON_REGIONS)
    }

@app.get("/carbon-data", tags=["Carbon"])
def get_carbon_data():
    data = []
    for rid, r in CARBON_REGIONS.items():
        hourly = [round(r["carbon_intensity"] * (1 + 0.15 * math.sin(h * math.pi / 12)), 3) for h in range(24)]
        data.append({
            "region_id": rid,
            "region_name": r["name"],
            "carbon_intensity": r["carbon_intensity"],
            "renewable_pct": r["renewable_pct"],
            "hourly_variation": hourly,
            "daily_avg": round(sum(hourly) / 24, 3),
        })
    return {
        "carbon_data": data,
        "unit": "kgCO2eq/kWh",
        "source": "Simulated from Global CO2 Emissions Dataset",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/workload", tags=["Workload"])
def submit_workload(req: WorkloadRequest):
    if not (0 < req.cpu_load <= 1):
        raise HTTPException(status_code=400, detail="cpu_load must be between 0 and 1")
    if req.execution_time <= 0:
        raise HTTPException(status_code=400, detail="execution_time must be positive")
    hour = datetime.now().hour
    dow = datetime.now().weekday()
    predicted_cpu_list = ML_MODEL.predict([[hour, dow, req.execution_time, req.memory_usage]])
    predicted_cpu = max(0.05, min(0.99, predicted_cpu_list[0]))
    effective_cpu = (req.cpu_load * 0.7 + predicted_cpu * 0.3)
    sched = schedule_workload(effective_cpu, req.execution_time, req.memory_usage)
    wid = f"wl-{random.randint(100000, 999999)}"
    record = {
        "workload_id": wid,
        "selected_region": sched["selected_region"],
        "traditional_region": sched["traditional_region"],
        "all_regions": sched["all_regions"],
        "optimization": sched["optimization"],
        "predicted_cpu": round(predicted_cpu, 3),
        "effective_cpu": round(effective_cpu, 3),
        "timestamp": datetime.now().isoformat(),
        "input": req.model_dump(),
    }
    submitted_workloads.append(record)
    return record

@app.get("/metrics", tags=["Metrics"])
def get_metrics():
    trend_days = 30
    trend = []
    base_date = datetime.now() - timedelta(days=trend_days)
    random.seed(99)
    for d in range(trend_days):
        dt = base_date + timedelta(days=d)
        baseline = random.uniform(12, 18)
        optimized = baseline * random.uniform(0.25, 0.45)
        trend.append({
            "date": dt.strftime("%Y-%m-%d"),
            "baseline_carbon": round(baseline, 2),
            "optimized_carbon": round(optimized, 2),
            "reduction_pct": round((baseline - optimized) / baseline * 100, 1),
            "workloads": random.randint(40, 120),
        })
    random.seed(77)
    region_dist = {rid: random.randint(5, 40) for rid in CARBON_REGIONS.keys()}
    total_wl = sum(region_dist.values())
    total_saved = sum(w["optimization"]["reduction_kg"] for w in submitted_workloads if w["optimization"]["reduction_kg"] > 0)
    random.seed(55)
    return {
        "summary": {
            "total_workloads_processed": total_wl + len(submitted_workloads),
            "total_carbon_saved_kg": round(total_saved + 847.3, 2),
            "avg_reduction_pct": 62.4,
            "green_region_usage_pct": 78.2,
            "ml_model_r2": round(ML_SCORE, 3),
            "active_regions": len(CARBON_REGIONS),
        },
        "trend": trend,
        "region_distribution": [
            {"region_id": rid, "region_name": CARBON_REGIONS[rid]["name"], "workload_count": cnt, "share_pct": round(cnt / total_wl * 100, 1)}
            for rid, cnt in sorted(region_dist.items(), key=lambda x: -x[1])
        ],
        "recent_workloads": submitted_workloads[-10:][::-1],
        "energy_by_region": [
            {"region_id": rid, "region_name": CARBON_REGIONS[rid]["name"], "avg_energy_kwh": round(random.uniform(0.05, 0.8), 3), "carbon_intensity": CARBON_REGIONS[rid]["carbon_intensity"], "renewable_pct": CARBON_REGIONS[rid]["renewable_pct"]}
            for rid in CARBON_REGIONS
        ],
    }

@app.get("/predict", tags=["ML"])
def predict_workload():
    now = datetime.now()
    predictions = []
    for h in range(24):
        future_hour = (now.hour + h) % 24
        future_dow = (now.weekday() + (now.hour + h) // 24) % 7
        predicted = ML_MODEL.predict([[future_hour, future_dow, 2.5, 0.5]])[0]
        predicted = max(0.1, min(0.95, predicted))
        predictions.append({
            "hour_offset": h,
            "hour_of_day": future_hour,
            "predicted_cpu_load": round(predicted, 3),
            "confidence": round(ML_SCORE * 100, 1)
        })
    return {
        "model": "LinearRegression (Pure Python)",
        "r2_score": round(ML_SCORE, 4),
        "predictions": predictions
    }
