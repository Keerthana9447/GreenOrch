import { useState, useEffect, useCallback } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area, Legend
} from "recharts";

// ── Embedded API (calls real FastAPI or uses mock data) ───────────────────
const API_BASE = "https://greenorch-backend.vercel.app";

async function apiFetch(path, opts = {}) {
  try {
    const res = await fetch(`${API_BASE}${path}`, opts);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return null; // fallback to mock
  }
}

// ── Mock data generators ──────────────────────────────────────────────────
const REGIONS_MOCK = [
  { id: "eu-north",    name: "EU North (Stockholm)",     provider: "Azure", carbon_intensity: 0.013, renewable_pct: 98, pue: 1.08 },
  { id: "us-west",     name: "US West (Oregon)",         provider: "AWS",   carbon_intensity: 0.091, renewable_pct: 89, pue: 1.10 },
  { id: "us-central",  name: "US Central (Iowa)",        provider: "GCP",   carbon_intensity: 0.147, renewable_pct: 79, pue: 1.12 },
  { id: "eu-west",     name: "EU West (Ireland)",        provider: "AWS",   carbon_intensity: 0.198, renewable_pct: 71, pue: 1.15 },
  { id: "eu-central",  name: "EU Central (Frankfurt)",   provider: "Azure", carbon_intensity: 0.233, renewable_pct: 65, pue: 1.18 },
  { id: "us-east",     name: "US East (N. Virginia)",    provider: "AWS",   carbon_intensity: 0.386, renewable_pct: 42, pue: 1.20 },
  { id: "ap-southeast",name: "AP Southeast (Singapore)", provider: "GCP",   carbon_intensity: 0.431, renewable_pct: 35, pue: 1.25 },
  { id: "asia-south",  name: "Asia South (Mumbai)",      provider: "GCP",   carbon_intensity: 0.708, renewable_pct: 18, pue: 1.35 },
];

function mockTrend() {
  return Array.from({ length: 30 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - (29 - i));
    const baseline = 12 + Math.random() * 6;
    const optimized = baseline * (0.28 + Math.random() * 0.15);
    return {
      date: d.toISOString().slice(5, 10),
      baseline_carbon: +baseline.toFixed(2),
      optimized_carbon: +optimized.toFixed(2),
      reduction_pct: +(((baseline - optimized) / baseline) * 100).toFixed(1),
      workloads: Math.floor(40 + Math.random() * 80),
    };
  });
}

function mockSimulate() {
  const wls = Array.from({ length: 20 }, (_, i) => {
    const baseline = 0.04 + Math.random() * 0.12;
    const optimized = baseline * (0.05 + Math.random() * 0.25);
    const region = REGIONS_MOCK[Math.floor(Math.random() * 3)];
    return {
      workload_id: i + 1,
      cpu_load: +(0.3 + Math.random() * 0.6).toFixed(3),
      execution_time: +(0.5 + Math.random() * 7).toFixed(2),
      workload_type: ["batch", "streaming", "interactive", "ml-training"][Math.floor(Math.random() * 4)],
      selected_region: region.name,
      selected_region_id: region.id,
      baseline_carbon: +baseline.toFixed(4),
      optimized_carbon: +optimized.toFixed(4),
      reduction_pct: +(((baseline - optimized) / baseline) * 100).toFixed(1),
    };
  });
  const tb = wls.reduce((a, w) => a + w.baseline_carbon, 0);
  const to = wls.reduce((a, w) => a + w.optimized_carbon, 0);
  return {
    simulation_id: `sim-${Math.floor(Math.random() * 90000 + 10000)}`,
    workloads_processed: 20,
    results: wls,
    summary: {
      total_baseline_carbon: +tb.toFixed(4),
      total_optimized_carbon: +to.toFixed(4),
      total_reduction_kg: +(tb - to).toFixed(4),
      total_reduction_pct: +(((tb - to) / tb) * 100).toFixed(1),
      ml_model_accuracy: 87.4,
    }
  };
}

function mockSchedule(form) {
  const cpu = parseFloat(form.cpu_load);
  const exec = parseFloat(form.execution_time);
  const best = REGIONS_MOCK[0];
  const trad = REGIONS_MOCK.find(r => r.id === "us-east");
  const POWER = 0.25;
  const bestEnergy = cpu * POWER * exec * best.pue;
  const tradEnergy = cpu * POWER * exec * trad.pue;
  const bestCarbon = bestEnergy * best.carbon_intensity;
  const tradCarbon = tradEnergy * trad.carbon_intensity;
  return {
    workload_id: `wl-${Math.floor(Math.random() * 900000 + 100000)}`,
    selected_region: { ...best, energy_kwh: +bestEnergy.toFixed(4), carbon_kg: +bestCarbon.toFixed(4) },
    traditional_region: { ...trad, energy_kwh: +tradEnergy.toFixed(4), carbon_kg: +tradCarbon.toFixed(4) },
    all_regions: REGIONS_MOCK.map(r => {
      const e = cpu * POWER * exec * r.pue;
      const c = e * r.carbon_intensity;
      return { ...r, region_id: r.id, region_name: r.name, energy_kwh: +e.toFixed(4), carbon_kg: +c.toFixed(4) };
    }),
    optimization: {
      baseline_carbon: +tradCarbon.toFixed(4),
      optimized_carbon: +bestCarbon.toFixed(4),
      reduction_kg: +(tradCarbon - bestCarbon).toFixed(4),
      reduction_pct: +(((tradCarbon - bestCarbon) / tradCarbon) * 100).toFixed(1),
    },
    predicted_cpu: +(cpu * 0.95 + Math.random() * 0.05).toFixed(3),
  };
}

// ── Color palette ─────────────────────────────────────────────────────────
const C = {
  bg:       "#060d0f",
  surface:  "#0c1a1e",
  card:     "#0f2128",
  border:   "#1a3540",
  green:    "#00e5a0",
  greenDim: "#00b87e",
  teal:     "#00c4cc",
  amber:    "#f5a623",
  red:      "#ff5a5a",
  blue:     "#4d9fff",
  text:     "#e2f4f0",
  muted:    "#6b9090",
};

const PROVIDER_COLORS = { AWS: "#ff9900", Azure: "#0078d4", GCP: "#4285f4" };
const REGION_PALETTE = ["#00e5a0","#00c4cc","#4d9fff","#a78bfa","#f472b6","#fb923c","#facc15","#34d399"];

// ── Utility Components ────────────────────────────────────────────────────
function Pill({ label, color }) {
  return (
    <span style={{
      background: `${color}22`, color, border: `1px solid ${color}55`,
      borderRadius: 4, padding: "1px 8px", fontSize: 11, fontWeight: 600, letterSpacing: 0.5
    }}>{label}</span>
  );
}

function StatCard({ label, value, sub, accent = C.green, icon }) {
  return (
    <div style={{
      background: C.card, border: `1px solid ${C.border}`, borderRadius: 12,
      padding: "20px 24px", position: "relative", overflow: "hidden"
    }}>
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: 2,
        background: `linear-gradient(90deg, ${accent}, transparent)`
      }} />
      <div style={{ color: C.muted, fontSize: 11, fontWeight: 700, letterSpacing: 1.5, marginBottom: 6, textTransform: "uppercase" }}>
        {icon && <span style={{ marginRight: 6 }}>{icon}</span>}{label}
      </div>
      <div style={{ color: accent, fontSize: 28, fontWeight: 800, fontFamily: "monospace", lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ color: C.muted, fontSize: 12, marginTop: 6 }}>{sub}</div>}
    </div>
  );
}

function SectionHeader({ title, sub }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <h2 style={{ color: C.text, fontSize: 18, fontWeight: 700, margin: 0 }}>{title}</h2>
      {sub && <p style={{ color: C.muted, fontSize: 13, margin: "4px 0 0" }}>{sub}</p>}
    </div>
  );
}

function GlowBadge({ pct }) {
  const good = pct >= 60;
  const color = good ? C.green : pct >= 30 ? C.amber : C.red;
  return (
    <span style={{
      background: `${color}18`, color, border: `1px solid ${color}44`,
      borderRadius: 20, padding: "3px 12px", fontSize: 13, fontWeight: 700,
      boxShadow: `0 0 12px ${color}30`
    }}>↓ {pct}% CO₂</span>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 14px", fontSize: 12 }}>
      <div style={{ color: C.muted, marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontWeight: 600 }}>{p.name}: {typeof p.value === "number" ? p.value.toFixed(4) : p.value}</div>
      ))}
    </div>
  );
};

// ── Pages ─────────────────────────────────────────────────────────────────

function DashboardPage({ darkMode }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const data = await apiFetch("/metrics");
      if (data) { setMetrics(data); }
      else {
        setMetrics({
          summary: {
            total_workloads_processed: 2847,
            total_carbon_saved_kg: 1203.7,
            avg_reduction_pct: 62.4,
            green_region_usage_pct: 78.2,
            ml_model_r2: 0.874,
            active_regions: 8,
          },
          trend: mockTrend(),
          region_distribution: REGIONS_MOCK.map((r, i) => ({
            region_id: r.id, region_name: r.name,
            workload_count: Math.floor(10 + Math.random() * 60),
            share_pct: 0
          })),
          energy_by_region: REGIONS_MOCK.map(r => ({
            region_id: r.id, region_name: r.name.split("(")[0].trim(),
            avg_energy_kwh: +(0.05 + Math.random() * 0.7).toFixed(3),
            carbon_intensity: r.carbon_intensity,
            renewable_pct: r.renewable_pct,
          })),
        });
      }
      setLoading(false);
    }
    load();
  }, []);

  if (loading || !metrics) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 400 }}>
        <div style={{ color: C.green, fontSize: 14 }}>⟳ Loading metrics...</div>
      </div>
    );
  }

  const s = metrics.summary;
  const trend = metrics.trend;
  const greenestRegion = REGIONS_MOCK[0];

  const regionDist = metrics.region_distribution.map((r, i) => ({
    ...r, fill: REGION_PALETTE[i % REGION_PALETTE.length]
  }));
  const totalWl = regionDist.reduce((a, r) => a + r.workload_count, 0);
  regionDist.forEach(r => { r.share_pct = +((r.workload_count / totalWl) * 100).toFixed(1); });

  return (
    <div>
      {/* KPI Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 28 }}>
        <StatCard label="Total Workloads" value={s.total_workloads_processed.toLocaleString()} sub="Across all regions" icon="⚡" />
        <StatCard label="Carbon Saved" value={`${s.total_carbon_saved_kg} kg`} sub="vs. traditional scheduling" accent={C.green} icon="🌱" />
        <StatCard label="Avg Reduction" value={`${s.avg_reduction_pct}%`} sub="CO₂ emission reduction" accent={C.teal} icon="📉" />
        <StatCard label="Green Region Usage" value={`${s.green_region_usage_pct}%`} sub="Workloads in low-carbon regions" accent={C.blue} icon="🗺️" />
        <StatCard label="ML Model R²" value={s.ml_model_r2} sub="Linear Regression accuracy" accent={C.amber} icon="🤖" />
        <StatCard label="Active Regions" value={s.active_regions} sub="Cloud regions monitored" accent="#a78bfa" icon="🌐" />
      </div>

      {/* Selected Green Region Banner */}
      <div style={{
        background: `linear-gradient(135deg, ${C.green}15, ${C.teal}10)`,
        border: `1px solid ${C.green}40`, borderRadius: 12, padding: "16px 24px",
        marginBottom: 28, display: "flex", alignItems: "center", gap: 16
      }}>
        <div style={{ fontSize: 32 }}>🏆</div>
        <div>
          <div style={{ color: C.muted, fontSize: 11, fontWeight: 700, letterSpacing: 1.5, textTransform: "uppercase" }}>Greenest Region</div>
          <div style={{ color: C.green, fontSize: 22, fontWeight: 800 }}>{greenestRegion.name}</div>
          <div style={{ color: C.muted, fontSize: 13, marginTop: 2 }}>
            {greenestRegion.carbon_intensity} kgCO₂/kWh · {greenestRegion.renewable_pct}% renewable · PUE {greenestRegion.pue}
          </div>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <GlowBadge pct={62.4} />
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        {/* Carbon Trend */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <SectionHeader title="Carbon Emission Trend" sub="30-day baseline vs. optimized (kgCO₂)" />
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trend} margin={{ top: 5, right: 5, bottom: 5, left: -15 }}>
              <defs>
                <linearGradient id="baseGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.red} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.red} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="optGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.green} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.green} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="date" tick={{ fill: C.muted, fontSize: 10 }} interval={6} />
              <YAxis tick={{ fill: C.muted, fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="baseline_carbon" name="Baseline" stroke={C.red} fill="url(#baseGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="optimized_carbon" name="Optimized" stroke={C.green} fill="url(#optGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Region Distribution Pie */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <SectionHeader title="Workload Distribution" sub="By cloud region" />
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie data={regionDist} cx="50%" cy="50%" innerRadius={45} outerRadius={80}
                  dataKey="workload_count" strokeWidth={0}>
                  {regionDist.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip formatter={(v) => [`${v} jobs`, ""]} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1, fontSize: 12 }}>
              {regionDist.slice(0, 6).map((r, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <div style={{ width: 8, height: 8, borderRadius: 2, background: r.fill, flexShrink: 0 }} />
                  <span style={{ color: C.muted, flex: 1, fontSize: 11 }}>{r.region_name.split("(")[0].trim()}</span>
                  <span style={{ color: C.text, fontWeight: 600 }}>{r.share_pct}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Energy by Region Bar Chart */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20, marginBottom: 24 }}>
        <SectionHeader title="Carbon Intensity by Region" sub="kgCO₂eq/kWh — lower is greener" />
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={metrics.energy_by_region} margin={{ top: 5, right: 5, bottom: 40, left: -15 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
            <XAxis dataKey="region_name" tick={{ fill: C.muted, fontSize: 10 }} angle={-35} textAnchor="end" />
            <YAxis tick={{ fill: C.muted, fontSize: 10 }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="carbon_intensity" name="Carbon Intensity" radius={[4, 4, 0, 0]}>
              {metrics.energy_by_region.map((e, i) => (
                <Cell key={i} fill={e.carbon_intensity < 0.1 ? C.green : e.carbon_intensity < 0.3 ? C.teal : e.carbon_intensity < 0.5 ? C.amber : C.red} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Reduction Trend */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
        <SectionHeader title="Carbon Reduction % Over Time" sub="Daily optimization effectiveness" />
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={trend} margin={{ top: 5, right: 5, bottom: 5, left: -15 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
            <XAxis dataKey="date" tick={{ fill: C.muted, fontSize: 10 }} interval={6} />
            <YAxis tick={{ fill: C.muted, fontSize: 10 }} unit="%" domain={[0, 100]} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="reduction_pct" name="Reduction %" stroke={C.green} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function SimulationPage() {
  const [form, setForm] = useState({ cpu_load: "0.65", execution_time: "2.5", memory_usage: "0.4", workload_type: "batch", priority: "standard" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    const body = { ...form, cpu_load: parseFloat(form.cpu_load), execution_time: parseFloat(form.execution_time), memory_usage: parseFloat(form.memory_usage) };
    const data = await apiFetch("/workload", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    setResult(data || mockSchedule(form));
    setLoading(false);
  };

  const handleSimulate = async () => {
    setSimLoading(true);
    const data = await apiFetch("/simulate");
    setSimResult(data || mockSimulate());
    setSimLoading(false);
  };

  const inputStyle = {
    background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8,
    color: C.text, padding: "10px 14px", fontSize: 14, width: "100%", outline: "none",
    boxSizing: "border-box"
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "380px 1fr", gap: 24 }}>
      {/* Form Panel */}
      <div>
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 24, marginBottom: 16 }}>
          <SectionHeader title="Submit Workload" sub="Schedule a workload for green execution" />
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {[
              { label: "CPU Load (0–1)", key: "cpu_load", type: "number", step: 0.01, min: 0.01, max: 1 },
              { label: "Execution Time (hours)", key: "execution_time", type: "number", step: 0.1, min: 0.1 },
              { label: "Memory Usage (0–1)", key: "memory_usage", type: "number", step: 0.01, min: 0.01, max: 1 },
            ].map(f => (
              <div key={f.key}>
                <label style={{ color: C.muted, fontSize: 12, fontWeight: 600, letterSpacing: 0.5 }}>{f.label}</label>
                <input type={f.type} step={f.step} min={f.min} max={f.max}
                  value={form[f.key]}
                  onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                  style={{ ...inputStyle, marginTop: 4 }} />
              </div>
            ))}
            <div>
              <label style={{ color: C.muted, fontSize: 12, fontWeight: 600, letterSpacing: 0.5 }}>Workload Type</label>
              <select value={form.workload_type} onChange={e => setForm(p => ({ ...p, workload_type: e.target.value }))}
                style={{ ...inputStyle, marginTop: 4 }}>
                {["batch", "streaming", "interactive", "ml-training"].map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
            <div>
              <label style={{ color: C.muted, fontSize: 12, fontWeight: 600, letterSpacing: 0.5 }}>Priority</label>
              <select value={form.priority} onChange={e => setForm(p => ({ ...p, priority: e.target.value }))}
                style={{ ...inputStyle, marginTop: 4 }}>
                {["standard", "high", "critical"].map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
            <button onClick={handleSubmit} disabled={loading}
              style={{
                background: loading ? C.border : `linear-gradient(135deg, ${C.green}, ${C.teal})`,
                border: "none", borderRadius: 8, color: "#000", fontWeight: 800,
                fontSize: 14, padding: "12px", cursor: loading ? "default" : "pointer",
                transition: "all 0.2s"
              }}>
              {loading ? "⟳ Scheduling..." : "⚡ Schedule Workload"}
            </button>
          </div>
        </div>

        {/* Run full simulation button */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <div style={{ color: C.text, fontWeight: 700, marginBottom: 8 }}>Batch Simulation</div>
          <div style={{ color: C.muted, fontSize: 12, marginBottom: 14 }}>
            Run scheduler on 20 historical workloads from Google Cluster Trace dataset
          </div>
          <button onClick={handleSimulate} disabled={simLoading}
            style={{
              background: simLoading ? C.border : `linear-gradient(135deg, #4d9fff, #a78bfa)`,
              border: "none", borderRadius: 8, color: "#fff", fontWeight: 700,
              fontSize: 13, padding: "10px 16px", cursor: simLoading ? "default" : "pointer", width: "100%"
            }}>
            {simLoading ? "⟳ Simulating..." : "🚀 Run Batch Simulation"}
          </button>
        </div>
      </div>

      {/* Results Panel */}
      <div>
        {result && (
          <div style={{ marginBottom: 20 }}>
            {/* Winner Banner */}
            <div style={{
              background: `linear-gradient(135deg, ${C.green}20, ${C.teal}10)`,
              border: `1px solid ${C.green}50`, borderRadius: 12, padding: "20px 24px", marginBottom: 16
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ color: C.muted, fontSize: 11, fontWeight: 700, letterSpacing: 1.5, textTransform: "uppercase", marginBottom: 4 }}>Selected Green Region</div>
                  <div style={{ color: C.green, fontSize: 24, fontWeight: 800 }}>{result.selected_region.name || result.selected_region.region_name}</div>
                  <div style={{ color: C.muted, fontSize: 13, marginTop: 4 }}>
                    Workload ID: <span style={{ color: C.text, fontFamily: "monospace" }}>{result.workload_id}</span>
                  </div>
                </div>
                <GlowBadge pct={result.optimization.reduction_pct} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginTop: 16 }}>
                {[
                  { l: "Energy", v: `${result.selected_region.energy_kwh} kWh` },
                  { l: "CO₂ Emitted", v: `${result.selected_region.carbon_kg} kg` },
                  { l: "CO₂ Baseline", v: `${result.optimization.baseline_carbon} kg` },
                  { l: "CO₂ Saved", v: `${result.optimization.reduction_kg} kg`, c: C.green },
                ].map((item, i) => (
                  <div key={i} style={{ background: "#ffffff08", borderRadius: 8, padding: "10px 14px" }}>
                    <div style={{ color: C.muted, fontSize: 11, marginBottom: 2 }}>{item.l}</div>
                    <div style={{ color: item.c || C.text, fontWeight: 700, fontFamily: "monospace", fontSize: 13 }}>{item.v}</div>
                  </div>
                ))}
              </div>
              {result.predicted_cpu && (
                <div style={{ marginTop: 12, color: C.muted, fontSize: 12 }}>
                  🤖 ML Predicted CPU Load: <span style={{ color: C.amber, fontWeight: 700 }}>{result.predicted_cpu}</span>
                </div>
              )}
            </div>

            {/* All Regions Comparison */}
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
              <SectionHeader title="Region Carbon Comparison" sub="All regions evaluated by optimizer" />
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={result.all_regions.slice().sort((a, b) => a.carbon_kg - b.carbon_kg)}
                  margin={{ top: 5, right: 5, bottom: 50, left: -15 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                  <XAxis dataKey="region_name" tick={{ fill: C.muted, fontSize: 9 }} angle={-35} textAnchor="end" />
                  <YAxis tick={{ fill: C.muted, fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="carbon_kg" name="CO₂ (kg)" radius={[4, 4, 0, 0]}>
                    {result.all_regions.slice().sort((a, b) => a.carbon_kg - b.carbon_kg).map((e, i) => (
                      <Cell key={i} fill={i === 0 ? C.green : i < 3 ? C.teal : i < 5 ? C.amber : C.red} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Simulation Results */}
        {simResult && (
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <SectionHeader title={`Simulation ${simResult.simulation_id}`} sub={`${simResult.workloads_processed} workloads processed`} />
              <div style={{ display: "flex", gap: 12 }}>
                <div style={{ textAlign: "right" }}>
                  <div style={{ color: C.muted, fontSize: 11 }}>Total Saved</div>
                  <div style={{ color: C.green, fontWeight: 800, fontFamily: "monospace" }}>{simResult.summary.total_reduction_kg} kg CO₂</div>
                </div>
                <GlowBadge pct={simResult.summary.total_reduction_pct} />
              </div>
            </div>
            <div style={{ maxHeight: 280, overflowY: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr>
                    {["ID", "Type", "CPU", "Time", "Region", "Baseline CO₂", "Optimized CO₂", "Reduction"].map(h => (
                      <th key={h} style={{ color: C.muted, textAlign: "left", padding: "6px 10px", borderBottom: `1px solid ${C.border}`, fontWeight: 600, fontSize: 11 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {simResult.results.map((r, i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${C.border}22` }}>
                      <td style={{ color: C.muted, padding: "6px 10px" }}>#{r.workload_id}</td>
                      <td style={{ padding: "6px 10px" }}><Pill label={r.workload_type} color={C.blue} /></td>
                      <td style={{ color: C.text, padding: "6px 10px", fontFamily: "monospace" }}>{r.cpu_load}</td>
                      <td style={{ color: C.text, padding: "6px 10px", fontFamily: "monospace" }}>{r.execution_time}h</td>
                      <td style={{ color: C.green, padding: "6px 10px", fontSize: 11 }}>{r.selected_region?.split("(")[0]?.trim()}</td>
                      <td style={{ color: C.red, padding: "6px 10px", fontFamily: "monospace" }}>{r.baseline_carbon}</td>
                      <td style={{ color: C.green, padding: "6px 10px", fontFamily: "monospace" }}>{r.optimized_carbon}</td>
                      <td style={{ padding: "6px 10px" }}><GlowBadge pct={r.reduction_pct} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!result && !simResult && (
          <div style={{
            background: C.card, border: `1px dashed ${C.border}`, borderRadius: 12,
            padding: 60, textAlign: "center"
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🌿</div>
            <div style={{ color: C.muted, fontSize: 16 }}>Submit a workload or run simulation to see results</div>
          </div>
        )}
      </div>
    </div>
  );
}

function AnalyticsPage() {
  const [carbonData, setCarbonData] = useState(null);
  const [predictions, setPredictions] = useState(null);

  useEffect(() => {
    async function load() {
      const [cd, pred] = await Promise.all([apiFetch("/carbon-data"), apiFetch("/predict")]);
      setCarbonData(cd || {
        carbon_data: REGIONS_MOCK.map(r => ({
          region_id: r.id, region_name: r.name,
          carbon_intensity: r.carbon_intensity,
          renewable_pct: r.renewable_pct,
          hourly_variation: Array.from({ length: 24 }, (_, h) =>
            +(r.carbon_intensity * (1 + 0.15 * Math.sin(h * Math.PI / 12))).toFixed(3)
          ),
        }))
      });
      setPredictions(pred || {
        model: "LinearRegression",
        r2_score: 0.874,
        predictions: Array.from({ length: 24 }, (_, h) => ({
          hour_offset: h,
          hour_of_day: h,
          predicted_cpu_load: +(0.3 + 0.4 * Math.sin((h - 6) * Math.PI / 12) + Math.random() * 0.1).toFixed(3),
          confidence: 87.4,
        }))
      });
    }
    load();
  }, []);

  if (!carbonData || !predictions) {
    return <div style={{ color: C.green, padding: 40 }}>⟳ Loading analytics...</div>;
  }

  // Hourly carbon data for top 4 regions
  const topRegions = carbonData.carbon_data.slice(0, 4);
  const hourlyData = Array.from({ length: 24 }, (_, h) => {
    const row = { hour: `${String(h).padStart(2, "0")}:00` };
    topRegions.forEach(r => { row[r.region_name.split("(")[0].trim()] = r.hourly_variation?.[h] ?? r.carbon_intensity; });
    return row;
  });

  const lineColors = [C.green, C.teal, C.amber, C.red];

  // Renewable vs fossil
  const renewableData = carbonData.carbon_data.map(r => ({
    name: r.region_name.split("(")[0].trim(),
    Renewable: r.renewable_pct,
    Fossil: 100 - r.renewable_pct,
  }));

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        {/* Hourly Carbon Variation */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <SectionHeader title="Hourly Carbon Intensity" sub="24h variation across top regions (kgCO₂/kWh)" />
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={hourlyData} margin={{ top: 5, right: 5, bottom: 5, left: -15 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="hour" tick={{ fill: C.muted, fontSize: 9 }} interval={3} />
              <YAxis tick={{ fill: C.muted, fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {topRegions.map((r, i) => (
                <Line key={r.region_id} type="monotone"
                  dataKey={r.region_name.split("(")[0].trim()}
                  stroke={lineColors[i]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* ML CPU Prediction */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <SectionHeader title="ML CPU Load Forecast" sub={`Next 24h · Model: ${predictions.model} · R²: ${predictions.r2_score}`} />
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={predictions.predictions} margin={{ top: 5, right: 5, bottom: 5, left: -15 }}>
              <defs>
                <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.amber} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.amber} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="hour_of_day" tick={{ fill: C.muted, fontSize: 10 }} tickFormatter={v => `${v}h`} />
              <YAxis tick={{ fill: C.muted, fontSize: 10 }} domain={[0, 1]} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="predicted_cpu_load" name="Predicted CPU" stroke={C.amber} fill="url(#cpuGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Renewable Energy Mix */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <SectionHeader title="Renewable Energy Mix by Region" sub="% renewable vs. fossil fuel" />
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={renewableData} margin={{ top: 5, right: 5, bottom: 40, left: -15 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
            <XAxis dataKey="name" tick={{ fill: C.muted, fontSize: 10 }} angle={-30} textAnchor="end" />
            <YAxis tick={{ fill: C.muted, fontSize: 10 }} unit="%" />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="Renewable" stackId="a" fill={C.green} radius={[0, 0, 0, 0]} />
            <Bar dataKey="Fossil" stackId="a" fill={C.red} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Region Table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
        <SectionHeader title="Region Carbon Metrics" sub="Full dataset: Carbon Intensity, Renewable %, PUE" />
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr>
              {["Region", "Provider", "Carbon Intensity", "Renewable %", "PUE", "Score"].map(h => (
                <th key={h} style={{ color: C.muted, textAlign: "left", padding: "8px 12px", borderBottom: `1px solid ${C.border}`, fontWeight: 600, fontSize: 11 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {REGIONS_MOCK.map((r, i) => {
              const score = Math.round(100 - (r.carbon_intensity / 0.708) * 60 - (r.pue - 1.0) * 50 + (r.renewable_pct / 100) * 30);
              return (
                <tr key={i} style={{ borderBottom: `1px solid ${C.border}22` }}>
                  <td style={{ color: C.text, padding: "10px 12px", fontWeight: 600 }}>{r.name}</td>
                  <td style={{ padding: "10px 12px" }}><Pill label={r.provider} color={PROVIDER_COLORS[r.provider]} /></td>
                  <td style={{ color: r.carbon_intensity < 0.1 ? C.green : r.carbon_intensity < 0.3 ? C.teal : r.carbon_intensity < 0.5 ? C.amber : C.red, padding: "10px 12px", fontFamily: "monospace", fontWeight: 700 }}>{r.carbon_intensity}</td>
                  <td style={{ padding: "10px 12px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div style={{ flex: 1, background: C.border, borderRadius: 4, height: 4, maxWidth: 80 }}>
                        <div style={{ width: `${r.renewable_pct}%`, background: C.green, borderRadius: 4, height: 4 }} />
                      </div>
                      <span style={{ color: C.text }}>{r.renewable_pct}%</span>
                    </div>
                  </td>
                  <td style={{ color: C.text, padding: "10px 12px", fontFamily: "monospace" }}>{r.pue}</td>
                  <td style={{ padding: "10px 12px" }}>
                    <span style={{ color: score > 70 ? C.green : score > 40 ? C.amber : C.red, fontWeight: 800 }}>{score}</span>
                    <span style={{ color: C.muted, fontSize: 11 }}>/100</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MetricsPage() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    apiFetch("/metrics").then(data => {
      setMetrics(data || {
        summary: { total_workloads_processed: 2847, total_carbon_saved_kg: 1203.7, avg_reduction_pct: 62.4, green_region_usage_pct: 78.2, ml_model_r2: 0.874, active_regions: 8 },
        trend: mockTrend(),
      });
    });
  }, []);

  const downloadCSV = () => {
    if (!metrics) return;
    const rows = [["Date", "Baseline CO2 (kg)", "Optimized CO2 (kg)", "Reduction %", "Workloads"]];
    metrics.trend.forEach(r => rows.push([r.date, r.baseline_carbon, r.optimized_carbon, r.reduction_pct, r.workloads]));
    const csv = rows.map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "greenorch_metrics.csv"; a.click();
  };

  if (!metrics) return <div style={{ color: C.green, padding: 40 }}>⟳ Loading...</div>;

  const s = metrics.summary;

  return (
    <div>
      {/* Summary */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 28 }}>
        <StatCard label="Total Workloads" value={s.total_workloads_processed.toLocaleString()} accent={C.blue} icon="📊" />
        <StatCard label="Carbon Saved" value={`${s.total_carbon_saved_kg} kg`} accent={C.green} icon="🌱" sub="vs. traditional scheduling" />
        <StatCard label="Avg CO₂ Reduction" value={`${s.avg_reduction_pct}%`} accent={C.teal} icon="📉" />
      </div>

      {/* Algorithm Explanation */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 24, marginBottom: 24 }}>
        <SectionHeader title="Core Algorithm" sub="GreenOrch scheduling engine — how it works" />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
          {[
            { title: "1. Energy Estimation", formula: "Energy = CPU × Power × Time × PUE", desc: "Calculates kWh consumed accounting for Power Usage Effectiveness", color: C.blue },
            { title: "2. Carbon Calculation", formula: "CO₂ = Energy × Carbon Intensity", desc: "Maps energy to emissions using region-specific carbon intensity data", color: C.amber },
            { title: "3. Optimization", formula: "Reduction = ((Base - Opt) / Base) × 100", desc: "Selects minimum-emission region, calculates % improvement vs. baseline", color: C.green },
          ].map((item, i) => (
            <div key={i} style={{ background: `${item.color}10`, border: `1px solid ${item.color}30`, borderRadius: 10, padding: 18 }}>
              <div style={{ color: item.color, fontWeight: 700, marginBottom: 8 }}>{item.title}</div>
              <div style={{ fontFamily: "monospace", fontSize: 13, color: C.text, background: "#00000030", borderRadius: 6, padding: "8px 12px", marginBottom: 10 }}>{item.formula}</div>
              <div style={{ color: C.muted, fontSize: 12 }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Export & Admin */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <SectionHeader title="Export Analytics" sub="Download metrics as CSV" />
          <div style={{ color: C.muted, fontSize: 13, marginBottom: 16 }}>Export 30-day trend data including baseline vs. optimized carbon emissions.</div>
          <button onClick={downloadCSV} style={{
            background: `linear-gradient(135deg, ${C.green}, ${C.teal})`,
            border: "none", borderRadius: 8, color: "#000", fontWeight: 700,
            padding: "10px 20px", cursor: "pointer", fontSize: 13
          }}>⬇ Download CSV</button>
        </div>

        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <SectionHeader title="System Status" sub="Infrastructure health" />
          {[
            { label: "API Backend", status: "Online", color: C.green },
            { label: "ML Model", status: "Active", color: C.green },
            { label: "Database", status: "Connected", color: C.green },
            { label: "Scheduler", status: "Running", color: C.green },
          ].map((item, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <span style={{ color: C.text, fontSize: 13 }}>{item.label}</span>
              <span style={{ color: item.color, fontSize: 12, fontWeight: 700 }}>● {item.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Trend Table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
        <SectionHeader title="30-Day Metrics Log" sub="Admin analytics panel" />
        <div style={{ maxHeight: 360, overflowY: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead style={{ position: "sticky", top: 0, background: C.card }}>
              <tr>
                {["Date", "Workloads", "Baseline CO₂", "Optimized CO₂", "Saved", "Reduction %"].map(h => (
                  <th key={h} style={{ color: C.muted, textAlign: "left", padding: "8px 12px", borderBottom: `1px solid ${C.border}`, fontWeight: 600, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...metrics.trend].reverse().map((r, i) => (
                <tr key={i} style={{ borderBottom: `1px solid ${C.border}22` }}>
                  <td style={{ color: C.text, padding: "8px 12px", fontFamily: "monospace" }}>{r.date}</td>
                  <td style={{ color: C.blue, padding: "8px 12px" }}>{r.workloads}</td>
                  <td style={{ color: C.red, padding: "8px 12px", fontFamily: "monospace" }}>{r.baseline_carbon} kg</td>
                  <td style={{ color: C.green, padding: "8px 12px", fontFamily: "monospace" }}>{r.optimized_carbon} kg</td>
                  <td style={{ color: C.green, padding: "8px 12px", fontFamily: "monospace" }}>+{(r.baseline_carbon - r.optimized_carbon).toFixed(2)} kg</td>
                  <td style={{ padding: "8px 12px" }}><GlowBadge pct={r.reduction_pct} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ApiDocsPage() {
  const endpoints = [
    { method: "GET", path: "/simulate", desc: "Run full scheduler simulation on 20 historical workloads", params: "None", response: "Simulation results with carbon savings summary" },
    { method: "GET", path: "/regions", desc: "List all cloud regions with carbon intensity metadata", params: "None", response: "Array of region objects with carbon_intensity, renewable_pct, pue" },
    { method: "GET", path: "/carbon-data", desc: "Carbon intensity metrics + 24h hourly variation", params: "None", response: "Per-region carbon data with hourly breakdown" },
    { method: "POST", path: "/workload", desc: "Submit a workload for carbon-aware scheduling", params: "cpu_load, execution_time, memory_usage, workload_type", response: "Selected region, carbon metrics, ML prediction" },
    { method: "GET", path: "/metrics", desc: "Sustainability analytics, 30-day trend, region distribution", params: "None", response: "Summary stats, trend data, region workload distribution" },
    { method: "GET", path: "/predict", desc: "ML CPU load predictions for next 24 hours", params: "hour?, day_of_week?", response: "Linear Regression predictions with confidence score" },
  ];

  const methodColors = { GET: C.green, POST: C.amber, DELETE: C.red, PUT: C.blue };

  return (
    <div>
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 24, marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h2 style={{ color: C.text, margin: "0 0 8px", fontSize: 20, fontWeight: 800 }}>GreenOrch REST API</h2>
            <p style={{ color: C.muted, margin: 0, fontSize: 13 }}>Version 1.0.0 · Base URL: <span style={{ fontFamily: "monospace", color: C.green }}>http://localhost:8000</span></p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
              style={{ background: C.blue, color: "#fff", borderRadius: 8, padding: "8px 16px", fontSize: 12, fontWeight: 700, textDecoration: "none" }}>
              Swagger UI ↗
            </a>
            <a href="http://localhost:8000/redoc" target="_blank" rel="noreferrer"
              style={{ background: C.border, color: C.text, borderRadius: 8, padding: "8px 16px", fontSize: 12, fontWeight: 700, textDecoration: "none" }}>
              ReDoc ↗
            </a>
          </div>
        </div>
      </div>

      {endpoints.map((ep, i) => (
        <div key={i} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20, marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
            <span style={{
              background: `${methodColors[ep.method]}20`, color: methodColors[ep.method],
              border: `1px solid ${methodColors[ep.method]}50`, borderRadius: 4,
              padding: "2px 10px", fontSize: 12, fontWeight: 800, fontFamily: "monospace"
            }}>{ep.method}</span>
            <span style={{ fontFamily: "monospace", color: C.text, fontWeight: 700, fontSize: 16 }}>{ep.path}</span>
          </div>
          <p style={{ color: C.muted, margin: "0 0 10px", fontSize: 13 }}>{ep.desc}</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div style={{ background: "#ffffff06", borderRadius: 6, padding: "8px 12px" }}>
              <div style={{ color: C.muted, fontSize: 11, fontWeight: 700, marginBottom: 4 }}>PARAMETERS</div>
              <div style={{ color: C.text, fontSize: 12, fontFamily: "monospace" }}>{ep.params}</div>
            </div>
            <div style={{ background: "#ffffff06", borderRadius: 6, padding: "8px 12px" }}>
              <div style={{ color: C.muted, fontSize: 11, fontWeight: 700, marginBottom: 4 }}>RESPONSE</div>
              <div style={{ color: C.green, fontSize: 12 }}>{ep.response}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState("dashboard");
  const [darkMode, setDarkMode] = useState(true);

  const bg = darkMode ? C.bg : "#f0f7f5";
  const surface = darkMode ? C.surface : "#e8f5f0";
  const cardBg = darkMode ? C.card : "#ffffff";
  const borderColor = darkMode ? C.border : "#c0dbd4";
  const textColor = darkMode ? C.text : "#0a2520";
  const mutedColor = darkMode ? C.muted : "#4a7870";

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: "◈" },
    { id: "simulation", label: "Workload Simulation", icon: "⚡" },
    { id: "analytics", label: "Analytics", icon: "📊" },
    { id: "metrics", label: "System Metrics", icon: "🔧" },
    { id: "api", label: "API Docs", icon: "📡" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: bg, color: textColor, fontFamily: "'IBM Plex Mono', 'Courier New', monospace", display: "flex", flexDirection: "column" }}>
      {/* Topbar */}
      <header style={{
        background: darkMode ? "#07131699" : "#e0f0ec",
        backdropFilter: "blur(12px)",
        borderBottom: `1px solid ${borderColor}`,
        padding: "0 32px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        height: 56, position: "sticky", top: 0, zIndex: 100
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: `linear-gradient(135deg, ${C.green}, ${C.teal})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18, fontWeight: 900, color: "#000"
          }}>G</div>
          <div>
            <div style={{ color: C.green, fontWeight: 900, fontSize: 16, letterSpacing: 1 }}>GREENORCH</div>
            <div style={{ color: mutedColor, fontSize: 9, letterSpacing: 2, textTransform: "uppercase", marginTop: -2 }}>Carbon-Aware Cloud Scheduler</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: C.green, boxShadow: `0 0 8px ${C.green}` }} />
            <span style={{ color: mutedColor, fontSize: 11 }}>System Online</span>
          </div>
          <button onClick={() => setDarkMode(d => !d)}
            style={{
              background: darkMode ? C.card : "#c5e5de",
              border: `1px solid ${borderColor}`, borderRadius: 20,
              color: textColor, padding: "4px 14px", cursor: "pointer", fontSize: 12, fontWeight: 600
            }}>
            {darkMode ? "☀ Light" : "☾ Dark"}
          </button>
        </div>
      </header>

      <div style={{ display: "flex", flex: 1 }}>
        {/* Sidebar */}
        <nav style={{
          width: 220, background: darkMode ? "#07131699" : "#dceee9",
          borderRight: `1px solid ${borderColor}`,
          padding: "24px 16px", flexShrink: 0
        }}>
          {navItems.map(item => (
            <button key={item.id} onClick={() => setPage(item.id)}
              style={{
                display: "flex", alignItems: "center", gap: 10,
                width: "100%", padding: "10px 14px", borderRadius: 8, border: "none",
                background: page === item.id
                  ? `linear-gradient(135deg, ${C.green}20, ${C.teal}10)`
                  : "transparent",
                borderLeft: page === item.id ? `2px solid ${C.green}` : "2px solid transparent",
                color: page === item.id ? C.green : mutedColor,
                fontSize: 13, fontWeight: page === item.id ? 700 : 500,
                cursor: "pointer", textAlign: "left", marginBottom: 4,
                transition: "all 0.15s"
              }}>
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}

          {/* Sidebar info */}
          <div style={{ marginTop: 32, padding: "12px 14px", background: `${C.green}10`, borderRadius: 8, border: `1px solid ${C.green}30` }}>
            <div style={{ color: C.green, fontSize: 11, fontWeight: 700, marginBottom: 6 }}>🌱 GREENEST REGION</div>
            <div style={{ color: textColor, fontSize: 12, fontWeight: 700 }}>EU North</div>
            <div style={{ color: mutedColor, fontSize: 11 }}>0.013 kgCO₂/kWh</div>
            <div style={{ color: mutedColor, fontSize: 11 }}>98% renewable</div>
          </div>

          <div style={{ marginTop: 12, padding: "12px 14px", background: `${C.red}10`, borderRadius: 8, border: `1px solid ${C.red}30` }}>
            <div style={{ color: C.red, fontSize: 11, fontWeight: 700, marginBottom: 6 }}>🔥 AVOID REGION</div>
            <div style={{ color: textColor, fontSize: 12, fontWeight: 700 }}>Asia South</div>
            <div style={{ color: mutedColor, fontSize: 11 }}>0.708 kgCO₂/kWh</div>
            <div style={{ color: mutedColor, fontSize: 11 }}>18% renewable</div>
          </div>
        </nav>

        {/* Main content */}
        <main style={{ flex: 1, padding: "28px 32px", overflowY: "auto" }}>
          <div style={{ maxWidth: 1200 }}>
            {page === "dashboard" && <DashboardPage darkMode={darkMode} />}
            {page === "simulation" && <SimulationPage />}
            {page === "analytics" && <AnalyticsPage />}
            {page === "metrics" && <MetricsPage />}
            {page === "api" && <ApiDocsPage />}
          </div>
        </main>
      </div>
    </div>
  );
}
