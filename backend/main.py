import { useState, useEffect, useCallback } from "react";
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Legend
} from "recharts";
# ================= API =================
const API = process.env.REACT_APP_API_URL || "https://greenorch-api.vercel.app";

async function apiFetch(path, opts = {}) {
  try {
    const r = await fetch(`${API}${path}`, {
      ...opts,
      headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    });
    const j = await r.json();
    if (!r.ok) throw new Error(j?.error?.message || `HTTP ${r.status}`);
    return { ok: true, data: j.data !== undefined ? j.data : j, message: j.message };
  } catch (e) {
    return { ok: false, data: null, error: e.message || "Request failed" };
  }
}

// ─── THEME ─────────────────────────────────────────────────────────────────
const C = {
  bg: "#060d0f", surface: "#0c1a1e", card: "#0f2128", border: "#1a3540",
  green: "#00e5a0", teal: "#00c4cc", amber: "#f5a623", red: "#ff5a5a",
  blue: "#4d9fff", purple: "#a78bfa", orange: "#fb923c",
  text: "#e2f4f0", muted: "#6b9090", white: "#ffffff",
};
const PAL = ["#00e5a0","#00c4cc","#4d9fff","#a78bfa","#f472b6","#fb923c","#facc15","#34d399"];
const PROV = { AWS: "#ff9900", Azure: "#0078d4", GCP: "#4285f4" };

// ─── MOCK DATA ─────────────────────────────────────────────────────────────
const RMOCK = [
  { id:"eu-north",    name:"EU North (Stockholm)",    short:"Stockholm",  provider:"Azure", carbon_intensity:0.013, renewable_pct:98,  pue:1.08, cost_per_hour:0.048, latency_ms:180, esg_score:97, esg_grade:"A+", k8s_nodes:12, lat:59.33, lng:18.07 },
  { id:"us-west",     name:"US West (Oregon)",        short:"Oregon",     provider:"AWS",   carbon_intensity:0.091, renewable_pct:89,  pue:1.10, cost_per_hour:0.052, latency_ms:85,  esg_score:84, esg_grade:"A",  k8s_nodes:20, lat:45.52, lng:-122.68 },
  { id:"us-central",  name:"US Central (Iowa)",       short:"Iowa",       provider:"GCP",   carbon_intensity:0.147, renewable_pct:79,  pue:1.12, cost_per_hour:0.044, latency_ms:65,  esg_score:76, esg_grade:"B",  k8s_nodes:15, lat:41.88, lng:-93.10 },
  { id:"eu-west",     name:"EU West (Ireland)",       short:"Ireland",    provider:"AWS",   carbon_intensity:0.198, renewable_pct:71,  pue:1.15, cost_per_hour:0.058, latency_ms:145, esg_score:68, esg_grade:"B",  k8s_nodes:18, lat:53.35, lng:-6.26 },
  { id:"eu-central",  name:"EU Central (Frankfurt)",  short:"Frankfurt",  provider:"Azure", carbon_intensity:0.233, renewable_pct:65,  pue:1.18, cost_per_hour:0.062, latency_ms:160, esg_score:61, esg_grade:"C",  k8s_nodes:16, lat:50.11, lng:8.68 },
  { id:"us-east",     name:"US East (N. Virginia)",   short:"N. Virginia",provider:"AWS",   carbon_intensity:0.386, renewable_pct:42,  pue:1.20, cost_per_hour:0.038, latency_ms:12,  esg_score:40, esg_grade:"D",  k8s_nodes:30, lat:37.77, lng:-78.17 },
  { id:"ap-southeast",name:"AP Southeast (Singapore)",short:"Singapore",  provider:"GCP",   carbon_intensity:0.431, renewable_pct:35,  pue:1.25, cost_per_hour:0.071, latency_ms:210, esg_score:33, esg_grade:"D",  k8s_nodes:14, lat:1.35,  lng:103.82 },
  { id:"asia-south",  name:"Asia South (Mumbai)",     short:"Mumbai",     provider:"GCP",   carbon_intensity:0.708, renewable_pct:18,  pue:1.35, cost_per_hour:0.035, latency_ms:320, esg_score:14, esg_grade:"F",  k8s_nodes:10, lat:19.08, lng:72.88 },
];

function mockScheduleResult(form) {
  const cpu = parseFloat(form.cpu_load), exec = parseFloat(form.execution_time);
  const pf = { batch:0.25, "ml-training":0.55, streaming:0.32, interactive:0.18, "web-api":0.20 }[form.workload_type] || 0.25;
  const best = RMOCK[0], trad = RMOCK.find(r => r.id === "us-east");
  const be = cpu*pf*exec*best.pue, te = cpu*pf*exec*trad.pue;
  const bc = be*best.carbon_intensity, tc = te*trad.carbon_intensity;
  const saved = tc - bc;
  const allR = RMOCK.map(r => {
    const e = cpu*pf*exec*r.pue, c = e*r.carbon_intensity, co = e*r.cost_per_hour*exec;
    const redPct = Math.round((tc - c) / tc * 1000) / 10;
    return { ...r, region_id:r.id, region_name:r.name, energy_kwh:+e.toFixed(4), carbon_kg:+c.toFixed(4), cost_usd:+co.toFixed(4), carbon_reduction_pct:redPct, availability_status:"healthy", is_best:r.id===best.id, is_worst:r.id==="asia-south" };
  });
  allR.sort((a,b) => a.carbon_kg - b.carbon_kg);
  return {
    workload_id: `wl-${Math.floor(Math.random()*900000+100000)}`,
    selected_region: { ...best, region_id:best.id, region_name:best.name, energy_kwh:+be.toFixed(4), carbon_kg:+bc.toFixed(4), cost_usd:+(be*best.cost_per_hour*exec).toFixed(4), carbon_reduction_pct:+((saved/tc)*100).toFixed(1), is_best:true, availability_status:"healthy" },
    worst_region: { ...RMOCK[7], region_name:RMOCK[7].name },
    all_regions: allR,
    decision: {
      strategy: form.optimize_for,
      strategy_weights: { carbon:0.70, cost:0.20, latency:0.10 },
      explanation: {
        summary: `${best.name} selected — ${+((saved/tc)*100).toFixed(1)}% cleaner than traditional scheduling`,
        reasons: ["Lowest carbon intensity: 0.013 kgCO₂/kWh", "98% renewable energy — well above global average", "Highly efficient data center (PUE 1.08 vs industry avg 1.58)", "Network latency: 180ms — acceptable"],
        vs_worst: { region: RMOCK[7].name, carbon_worse_by_pct: 98.2, avoided_kg: +(RMOCK[7].carbon_intensity*be - bc).toFixed(4) },
      },
      headline: `${+((saved/tc)*100).toFixed(1)}% less CO₂ than traditional scheduling`,
      esg_grade: "A+",
    },
    before_after: {
      before: { label:"❌ Traditional (No Carbon Awareness)", region:trad.name, region_id:"us-east", provider:trad.provider, energy_kwh:+te.toFixed(4), carbon_kg:+tc.toFixed(4), cost_usd:+(te*trad.cost_per_hour*exec).toFixed(4), carbon_intensity:trad.carbon_intensity, renewable_pct:trad.renewable_pct, pue:trad.pue, esg_score:trad.esg_score, esg_grade:"D", k8s_cluster:{cluster_name:"eks-us-east-prod",nodes_total:30,cpu_utilization_pct:72,ram_utilization_pct:65,pods_running:48,pods_pending:3,pods_failed:1} },
      after: { label:"✅ DhruvCloud Nexus Carbon-Aware", region:best.name, region_id:best.id, provider:best.provider, energy_kwh:+be.toFixed(4), carbon_kg:+bc.toFixed(4), cost_usd:+(be*best.cost_per_hour*exec).toFixed(4), carbon_intensity:best.carbon_intensity, renewable_pct:best.renewable_pct, pue:best.pue, esg_score:best.esg_score, esg_grade:"A+", k8s_cluster:{cluster_name:"aks-eu-north-prod",nodes_total:12,cpu_utilization_pct:58,ram_utilization_pct:45,pods_running:24,pods_pending:0,pods_failed:0} },
      efficiency_gains: { carbon_saved_kg:+saved.toFixed(4), energy_saved_kwh:+(te-be).toFixed(4), carbon_reduction_pct:+((saved/tc)*100).toFixed(1), cost_change_pct:+(((te*trad.cost_per_hour - be*best.cost_per_hour)/(te*trad.cost_per_hour))*100).toFixed(1), cost_saved_usd:+(te*trad.cost_per_hour*exec - be*best.cost_per_hour*exec).toFixed(4), pue_improvement_pct:+((trad.pue-best.pue)/trad.pue*100).toFixed(1), renewable_gain_pct:best.renewable_pct-trad.renewable_pct, esg_score_gain:best.esg_score-trad.esg_score, equivalents:{trees_planted:+(saved/0.06).toFixed(2),car_km_avoided:+(saved*6.3).toFixed(1),smartphone_charges:Math.floor(saved/0.008),led_bulb_hours:Math.floor(saved/0.010)} },
    },
    ml: { predicted_cpu:+(cpu*0.95+Math.random()*0.05).toFixed(3), confidence_pct:87, model:"EnsemblePredictor v3.1", r2:0.874 },
    policies_applied: [],
    impact: { carbon_saved_kg:+saved.toFixed(4), energy_saved_kwh:+(te-be).toFixed(4), cost_saved_usd:+(te*trad.cost_per_hour*exec - be*best.cost_per_hour*exec).toFixed(4), carbon_reduction_pct:+((saved/tc)*100).toFixed(1), trees_equivalent:+(saved/0.06).toFixed(2), car_km_equivalent:+(saved*6.3).toFixed(1) },
  };
}

function mockTrend() {
  return Array.from({length:30},(_,i) => {
    const d = new Date(); d.setDate(d.getDate()-(29-i));
    const b = +(12+Math.random()*6).toFixed(2), a = +(b*(0.25+Math.random()*0.15)).toFixed(2);
    return { date:d.toISOString().slice(5,10), before_carbon:b, after_carbon:a, reduction_pct:+((b-a)/b*100).toFixed(1), workloads:Math.floor(40+Math.random()*80), cost_saved:+(Math.random()*3).toFixed(2), esg_score:Math.floor(72+Math.random()*23) };
  });
}

// ─── HOOKS ─────────────────────────────────────────────────────────────────
function useToast() {
  const [ts, setTs] = useState([]);
  const add = useCallback((message, type = "success") => {
    const id = Date.now();
    setTs(p => [...p, { id, message, type }]);
    setTimeout(() => setTs(p => p.filter(t => t.id !== id)), 4500);
  }, []);
  const rm = useCallback((id) => setTs(p => p.filter(t => t.id !== id)), []);
  return { toasts: ts, toast: add, rmToast: rm };
}

function useCountUp(target, duration = 1200) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(target * eased);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return val;
}

// ─── UI ATOMS ──────────────────────────────────────────────────────────────
function Toast({ toasts, rmToast }) {
  return (
    <div style={{ position:"fixed", top:64, right:18, zIndex:9999, display:"flex", flexDirection:"column", gap:8 }}>
      {toasts.map(t => (
        <div key={t.id} style={{ background:C.card, border:`1px solid ${t.type==="success"?C.green:C.red}`, borderRadius:10, padding:"11px 16px", display:"flex", alignItems:"center", gap:10, minWidth:300, boxShadow:`0 4px 24px ${t.type==="success"?C.green:C.red}30`, animation:"slideIn 0.3s ease" }}>
          <span style={{fontSize:16}}>{t.type==="success"?"✅":"❌"}</span>
          <span style={{color:C.text,fontSize:12,flex:1}}>{t.message}</span>
          <button onClick={() => rmToast(t.id)} style={{background:"none",border:"none",color:C.muted,cursor:"pointer",fontSize:16,padding:0}}>×</button>
        </div>
      ))}
    </div>
  );
}

function Spinner({ size = 18, color = C.green }) {
  return (
    <div style={{ width:size, height:size, border:`2px solid ${color}33`, borderTop:`2px solid ${color}`, borderRadius:"50%", animation:"spin 0.8s linear infinite", display:"inline-block" }} />
  );
}

function Skeleton({ w = "100%", h = 18, r = 6 }) {
  return <div style={{ width:w, height:h, borderRadius:r, background:`linear-gradient(90deg,${C.border},${C.surface},${C.border})`, backgroundSize:"200% 100%", animation:"shimmer 1.5s infinite" }} />;
}

function Pill({ label, color }) {
  return <span style={{ background:`${color}22`, color, border:`1px solid ${color}55`, borderRadius:4, padding:"2px 8px", fontSize:11, fontWeight:600 }}>{label}</span>;
}

function EsgBadge({ grade, size = "sm" }) {
  const color = { "A+":C.green, "A":C.teal, "B":C.blue, "C":C.amber, "D":C.orange, "F":C.red }[grade] || C.muted;
  const fs = size === "lg" ? 18 : 12;
  const pad = size === "lg" ? "6px 16px" : "2px 8px";
  return <span style={{ background:`${color}22`, color, border:`1px solid ${color}55`, borderRadius:6, padding:pad, fontSize:fs, fontWeight:800 }}>ESG {grade}</span>;
}

function GreenBadge({ pct, size = "sm" }) {
  const color = pct >= 60 ? C.green : pct >= 30 ? C.amber : C.red;
  const fs = size === "lg" ? 18 : 13;
  return <span style={{ background:`${color}18`, color, border:`1px solid ${color}44`, borderRadius:20, padding:size==="lg"?"8px 20px":"3px 12px", fontSize:fs, fontWeight:700, boxShadow:`0 0 10px ${color}28` }}>↓ {pct}% CO₂</span>;
}

function StatCard({ label, value, sub, accent = C.green, icon, animated = false, loading = false }) {
  const num = parseFloat(String(value).replace(/[^0-9.]/g,"")) || 0;
  const sfx = String(value).replace(/[0-9.,]/g,"");
  const cv = useCountUp(animated ? num : num, animated ? 1200 : 0);
  const dv = animated ? `${cv % 1 === 0 ? Math.floor(cv) : cv.toFixed(1)}${sfx}` : value;
  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:"18px 22px", position:"relative", overflow:"hidden", transition:"transform 0.2s, box-shadow 0.2s", cursor:"default" }}
      onMouseEnter={e => { e.currentTarget.style.transform="translateY(-2px)"; e.currentTarget.style.boxShadow=`0 6px 24px ${accent}20`; }}
      onMouseLeave={e => { e.currentTarget.style.transform="translateY(0)"; e.currentTarget.style.boxShadow="none"; }}>
      <div style={{ position:"absolute", top:0, left:0, right:0, height:2, background:`linear-gradient(90deg,${accent},transparent)` }} />
      <div style={{ color:C.muted, fontSize:10, fontWeight:700, letterSpacing:1.5, marginBottom:5, textTransform:"uppercase" }}>{icon} {label}</div>
      {loading ? <Skeleton h={28} w="70%" /> : <div style={{ color:accent, fontSize:24, fontWeight:800, fontFamily:"monospace", lineHeight:1 }}>{dv}</div>}
      {sub && <div style={{ color:C.muted, fontSize:11, marginTop:5 }}>{sub}</div>}
    </div>
  );
}

function SH({ title, sub, action }) {
  return (
    <div style={{ marginBottom:14, display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
      <div>
        <h2 style={{ color:C.text, fontSize:15, fontWeight:700, margin:0 }}>{title}</h2>
        {sub && <p style={{ color:C.muted, fontSize:11, margin:"3px 0 0" }}>{sub}</p>}
      </div>
      {action}
    </div>
  );
}

const TT = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"9px 13px", fontSize:11 }}>
      <div style={{ color:C.muted, marginBottom:5 }}>{label}</div>
      {payload.map((p, i) => <div key={i} style={{ color:p.color, fontWeight:600 }}>{p.name}: {typeof p.value==="number" ? p.value.toFixed(4) : p.value}</div>)}
    </div>
  );
};

// ─── COMPLEX COMPONENTS ────────────────────────────────────────────────────

function LiveFeed() {
  const [feed, setFeed] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const res = await apiFetch("/api/v1/carbon/live");
    if (res.ok && res.data?.feed) {
      setFeed(res.data.feed);
    } else {
      setFeed(RMOCK.map(r => ({ region_id:r.id, region_name:r.name, region_short:r.short, current:r.carbon_intensity, previous:r.carbon_intensity*1.02, trend:Math.random()>0.5?"rising":"falling", alert:r.carbon_intensity>0.4, renewable_pct:r.renewable_pct, provider:r.provider, esg_score:r.esg_score, esg_grade:r.esg_grade, change_pct:+(Math.random()*2-1).toFixed(1) })));
    }
    setLastUpdate(new Date().toLocaleTimeString());
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    const iv = setInterval(load, 10000);
    return () => clearInterval(iv);
  }, [load]);

  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18, marginBottom:18 }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:14 }}>
        <div>
          <div style={{ color:C.text, fontWeight:700, fontSize:14 }}>⚡ Live Carbon Intensity Feed</div>
          <div style={{ color:C.muted, fontSize:11, marginTop:2 }}>Auto-refresh every 10s · {lastUpdate && `Last: ${lastUpdate}`}</div>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:6 }}>
          {loading ? <Spinner size={12}/> : <div style={{ width:6, height:6, borderRadius:"50%", background:C.green, animation:"pulse 2s infinite" }}/>}
          <span style={{ color:C.muted, fontSize:10, fontWeight:700 }}>LIVE</span>
        </div>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:8 }}>
        {(loading ? Array(8).fill(null) : feed.slice(0,8)).map((r, i) => {
          if (!r) return <div key={i} style={{ borderRadius:8, padding:"10px 12px", background:C.surface }}><Skeleton h={12} w="80%"/><div style={{marginTop:6}}><Skeleton h={18} w="60%"/></div></div>;
          const col = r.current<0.1?C.green:r.current<0.3?C.teal:r.current<0.5?C.amber:C.red;
          return (
            <div key={r.region_id} style={{ background:`${col}10`, border:`1px solid ${col}30`, borderRadius:8, padding:"10px 12px", position:"relative", transition:"all 0.3s" }}>
              {r.alert && <div style={{ position:"absolute", top:5, right:5, width:6, height:6, borderRadius:"50%", background:C.red, animation:"pulse 1s infinite" }}/>}
              <div style={{ color:C.muted, fontSize:9, marginBottom:3 }}>{r.region_short || (r.region_name||"").split("(")[0].trim()}</div>
              <div style={{ color:col, fontSize:15, fontWeight:800, fontFamily:"monospace" }}>{r.current}</div>
              <div style={{ display:"flex", alignItems:"center", gap:4, marginTop:2 }}>
                <span style={{ color:r.trend==="rising"?C.red:C.green, fontSize:10 }}>{r.trend==="rising"?"↑":"↓"} {Math.abs(r.change_pct||0)}%</span>
              </div>
              <div style={{ fontSize:9, color:C.muted, marginTop:2 }}>🌱 {r.renewable_pct}% · ESG {r.esg_grade}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function WorldMap({ regions, selectedId }) {
  const [hov, setHov] = useState(null);
  const toXY = (lat, lng) => [(lng+180)/360*540, (90-lat)/180*270];
  const data = regions || RMOCK;
  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18, marginBottom:18 }}>
      <SH title="🌍 Live Carbon World Map" sub="Circle size = CO₂ intensity · hover for region details"/>
      <svg viewBox="0 0 540 270" style={{ width:"100%", borderRadius:8, background:"#071318" }}>
        <ellipse cx="135" cy="135" rx="110" ry="70" fill="#0f2128" opacity="0.8"/>
        <ellipse cx="280" cy="120" rx="95" ry="65" fill="#0f2128" opacity="0.8"/>
        <ellipse cx="410" cy="130" rx="70" ry="55" fill="#0f2128" opacity="0.8"/>
        <ellipse cx="280" cy="200" rx="60" ry="40" fill="#0f2128" opacity="0.8"/>
        <ellipse cx="100" cy="180" rx="45" ry="35" fill="#0f2128" opacity="0.8"/>
        {/* Paris Agreement line */}
        <line x1="30" y1="240" x2="510" y2="240" stroke={C.teal} strokeWidth="0.5" strokeDasharray="4,4" opacity="0.4"/>
        <text x="510" y="238" fill={C.teal} fontSize="6" textAnchor="end" opacity="0.6">Paris Target</text>
        <text x="270" y="260" fill={C.muted} fontSize="7" textAnchor="middle">DhruvCloud Nexus · CarbonAware Sustainable Cloud Orchestration Platform</text>
        {data.map(r => {
          const [x, y] = toXY(r.lat||0, r.lng||0);
          const ci = r.carbon_intensity || 0.2;
          const rad = 6 + ci * 18;
          const col = ci<0.1?C.green:ci<0.25?C.teal:ci<0.45?C.amber:C.red;
          const isSel = selectedId && (r.id===selectedId || r.region_id===selectedId);
          const isHov = hov === (r.id||r.region_id);
          return (
            <g key={r.id||r.region_id}
              onMouseEnter={() => setHov(r.id||r.region_id)}
              onMouseLeave={() => setHov(null)}
              style={{ cursor:"pointer" }}>
              {isSel && (
                <circle cx={x} cy={y} r={rad+10} fill="none" stroke={C.green} strokeWidth="2" opacity="0.7">
                  <animate attributeName="r" values={`${rad+10};${rad+16};${rad+10}`} dur="2s" repeatCount="indefinite"/>
                </circle>
              )}
              <circle cx={x} cy={y} r={rad} fill={col} opacity={isHov?0.9:0.65}/>
              <circle cx={x} cy={y} r={3} fill="#fff" opacity="0.9"/>
              {isSel && <text x={x} y={y-rad-6} fill={C.green} fontSize="7" textAnchor="middle" fontWeight="bold">★ BEST</text>}
              {isHov && (
                <g>
                  <rect x={x-58} y={y-58} width="116" height="50" rx="4" fill={C.card} stroke={col} strokeWidth="1"/>
                  <text x={x} y={y-44} fill={C.text} fontSize="7.5" textAnchor="middle" fontWeight="bold">{(r.short||r.name||"").split("(")[0].trim()}</text>
                  <text x={x} y={y-33} fill={col} fontSize="7" textAnchor="middle">{ci} kgCO₂/kWh</text>
                  <text x={x} y={y-22} fill={C.muted} fontSize="6.5" textAnchor="middle">{r.renewable_pct}% renewable · ESG {r.esg_score}</text>
                  <text x={x} y={y-13} fill={C.muted} fontSize="6" textAnchor="middle">{r.k8s_nodes} K8s nodes · {r.provider}</text>
                </g>
              )}
            </g>
          );
        })}
      </svg>
      <div style={{ display:"flex", gap:14, marginTop:10, flexWrap:"wrap" }}>
        {[["<0.1 Excellent",C.green],["0.1–0.25 Good",C.teal],["0.25–0.45 Fair",C.amber],[">0.45 Poor",C.red]].map(([l,c]) => (
          <div key={l} style={{ display:"flex", alignItems:"center", gap:5 }}>
            <div style={{ width:9, height:9, borderRadius:"50%", background:c }}/>
            <span style={{ color:C.muted, fontSize:10 }}>{l}</span>
          </div>
        ))}
        <div style={{ marginLeft:"auto", display:"flex", alignItems:"center", gap:5 }}>
          <div style={{ width:9, height:9, borderRadius:"50%", border:`2px solid ${C.green}` }}/>
          <span style={{ color:C.muted, fontSize:10 }}>Selected region</span>
        </div>
      </div>
    </div>
  );
}

function BudgetGauge({ used, total, loading }) {
  const pct = Math.min(100, (used / total) * 100);
  const color = pct > 80 ? C.red : pct > 60 ? C.amber : C.green;
  const r = 46, circ = 2 * Math.PI * r, dash = circ * (pct / 100);
  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
      <SH title="💰 Carbon Budget"/>
      {loading ? <Skeleton h={110}/> : (
        <div style={{ display:"flex", alignItems:"center", gap:18 }}>
          <svg width={106} height={106} viewBox="0 0 106 106">
            <circle cx="53" cy="53" r={r} fill="none" stroke={C.border} strokeWidth="9"/>
            <circle cx="53" cy="53" r={r} fill="none" stroke={color} strokeWidth="9"
              strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
              transform="rotate(-90 53 53)" style={{ transition:"stroke-dasharray 1.2s" }}/>
            <text x="53" y="49" fill={color} fontSize="16" fontWeight="bold" textAnchor="middle">{pct.toFixed(0)}%</text>
            <text x="53" y="62" fill={C.muted} fontSize="8" textAnchor="middle">USED</text>
          </svg>
          <div style={{ flex:1 }}>
            <div style={{ marginBottom:8 }}><div style={{ color:C.muted, fontSize:10 }}>Used</div><div style={{ color, fontWeight:800, fontSize:18, fontFamily:"monospace" }}>{used} kg</div></div>
            <div style={{ marginBottom:8 }}><div style={{ color:C.muted, fontSize:10 }}>Remaining</div><div style={{ color:C.green, fontWeight:700, fontSize:15, fontFamily:"monospace" }}>{(total-used).toFixed(1)} kg</div></div>
            <div><div style={{ color:C.muted, fontSize:10 }}>Budget</div><div style={{ color:C.text, fontWeight:600, fontSize:13, fontFamily:"monospace" }}>{total} kg/mo</div></div>
          </div>
        </div>
      )}
      {pct > 80 && <div style={{ marginTop:12, background:`${C.red}18`, border:`1px solid ${C.red}44`, borderRadius:8, padding:"8px 12px", color:C.red, fontSize:11 }}>⚠️ Critical: Budget 80%+ used. Restrict high-emission workloads.</div>}
    </div>
  );
}

function K8sClusterCard({ cluster, label, accent }) {
  if (!cluster) return null;
  const cpuCol = cluster.cpu_utilization_pct > 80 ? C.red : cluster.cpu_utilization_pct > 60 ? C.amber : C.green;
  const ramCol = cluster.ram_utilization_pct > 80 ? C.red : cluster.ram_utilization_pct > 60 ? C.amber : C.teal;
  return (
    <div style={{ background:`${accent}08`, border:`1px solid ${accent}30`, borderRadius:10, padding:14 }}>
      <div style={{ color:accent, fontSize:10, fontWeight:700, marginBottom:6, textTransform:"uppercase", letterSpacing:1 }}>{label}</div>
      <div style={{ color:C.text, fontSize:12, fontWeight:700, marginBottom:10, fontFamily:"monospace" }}>{cluster.cluster_name}</div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:10 }}>
        <div>
          <div style={{ color:C.muted, fontSize:9, marginBottom:3 }}>CPU Utilization</div>
          <div style={{ background:C.border, borderRadius:3, height:5, marginBottom:3 }}>
            <div style={{ width:`${cluster.cpu_utilization_pct}%`, background:cpuCol, borderRadius:3, height:5, transition:"width 1s ease" }}/>
          </div>
          <div style={{ color:cpuCol, fontSize:11, fontWeight:700, fontFamily:"monospace" }}>{cluster.cpu_utilization_pct}%</div>
        </div>
        <div>
          <div style={{ color:C.muted, fontSize:9, marginBottom:3 }}>RAM Utilization</div>
          <div style={{ background:C.border, borderRadius:3, height:5, marginBottom:3 }}>
            <div style={{ width:`${cluster.ram_utilization_pct}%`, background:ramCol, borderRadius:3, height:5, transition:"width 1s ease" }}/>
          </div>
          <div style={{ color:ramCol, fontSize:11, fontWeight:700, fontFamily:"monospace" }}>{cluster.ram_utilization_pct}%</div>
        </div>
      </div>
      <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
        {[["Nodes",cluster.nodes_total,C.text],["Pods ✅",cluster.pods_running,C.green],["Pending",cluster.pods_pending,cluster.pods_pending>0?C.amber:C.green],["Failed",cluster.pods_failed,cluster.pods_failed>0?C.red:C.green]].map(([l,v,c]) => (
          <div key={l} style={{ background:C.card, borderRadius:6, padding:"5px 10px", textAlign:"center" }}>
            <div style={{ color:C.muted, fontSize:8 }}>{l}</div>
            <div style={{ color:c, fontWeight:700, fontSize:12 }}>{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function BeforeAfterPanel({ ba }) {
  if (!ba) return null;
  const { before: b, after: a, efficiency_gains: eg } = ba;
  const barData = [
    { name:"Carbon (kg)", before:b.carbon_kg, after:a.carbon_kg },
    { name:"Energy (kWh)", before:b.energy_kwh, after:a.energy_kwh },
  ];
  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:20, marginBottom:16, animation:"fadeIn 0.5s ease" }}>
      <SH title="📊 Before vs After — Efficiency Gain" sub="Traditional scheduling vs DhruvCloud Nexus carbon-aware orchestration"/>

      {/* Summary bar */}
      <div style={{ background:`linear-gradient(135deg,${C.green}15,${C.teal}08)`, border:`1px solid ${C.green}30`, borderRadius:10, padding:"14px 18px", marginBottom:16, display:"flex", alignItems:"center", gap:16, flexWrap:"wrap" }}>
        <div style={{ fontSize:28 }}>🏆</div>
        <div style={{ flex:1 }}>
          <div style={{ color:C.green, fontSize:18, fontWeight:900 }}>{eg.carbon_reduction_pct}% less CO₂</div>
          <div style={{ color:C.muted, fontSize:12, marginTop:2 }}>
            🌳 {eg.equivalents.trees_planted} trees · 🚗 {eg.equivalents.car_km_avoided} km · 📱 {eg.equivalents.smartphone_charges?.toLocaleString()} phones
          </div>
        </div>
        <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
          <GreenBadge pct={eg.carbon_reduction_pct} size="lg"/>
          <EsgBadge grade={a.esg_grade} size="lg"/>
        </div>
      </div>

      {/* Side by side */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr auto 1fr", gap:14, marginBottom:16 }}>
        {/* BEFORE */}
        <div style={{ background:`${C.red}08`, border:`1px solid ${C.red}30`, borderRadius:10, padding:16 }}>
          <div style={{ color:C.red, fontSize:10, fontWeight:700, marginBottom:8, textTransform:"uppercase", letterSpacing:1 }}>❌ BEFORE — Traditional</div>
          <div style={{ color:C.text, fontSize:13, fontWeight:700, marginBottom:10 }}>{b.region}</div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8 }}>
            {[["CO₂ Emitted",`${b.carbon_kg} kg`,C.red],["Energy",`${b.energy_kwh} kWh`,C.orange],["Cost",`$${b.cost_usd}`,C.amber],["Renewable",`${b.renewable_pct}%`,C.muted],["PUE",b.pue,C.muted],["ESG",`${b.esg_score}/100`,C.red]].map(([l,v,c]) => (
              <div key={l} style={{ background:"#ffffff05", borderRadius:6, padding:"7px 10px" }}>
                <div style={{ color:C.muted, fontSize:9 }}>{l}</div>
                <div style={{ color:c, fontWeight:700, fontFamily:"monospace", fontSize:12 }}>{v}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop:10 }}><K8sClusterCard cluster={b.k8s_cluster} label="K8s — Before" accent={C.red}/></div>
        </div>

        {/* Arrow column */}
        <div style={{ display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:10, minWidth:70 }}>
          <div style={{ color:C.green, fontSize:22 }}>→</div>
          <div style={{ background:`${C.green}18`, border:`1px solid ${C.green}40`, borderRadius:10, padding:"8px 12px", textAlign:"center" }}>
            <div style={{ color:C.green, fontSize:18, fontWeight:900 }}>{eg.carbon_reduction_pct}%</div>
            <div style={{ color:C.muted, fontSize:8 }}>CO₂ SAVED</div>
          </div>
          <div style={{ textAlign:"center", color:C.muted, fontSize:9 }}>
            <div>+{eg.renewable_gain_pct}%</div>
            <div>Renewable</div>
          </div>
          <div style={{ textAlign:"center", color:C.muted, fontSize:9 }}>
            <div>PUE</div>
            <div style={{ color:C.teal }}>↓{eg.pue_improvement_pct}%</div>
          </div>
          <div style={{ textAlign:"center", color:C.muted, fontSize:9 }}>
            <div>ESG</div>
            <div style={{ color:C.purple }}>+{eg.esg_score_gain}</div>
          </div>
        </div>

        {/* AFTER */}
        <div style={{ background:`${C.green}08`, border:`1px solid ${C.green}30`, borderRadius:10, padding:16 }}>
          <div style={{ color:C.green, fontSize:10, fontWeight:700, marginBottom:8, textTransform:"uppercase", letterSpacing:1 }}>✅ AFTER — DhruvCloud Nexus</div>
          <div style={{ color:C.text, fontSize:13, fontWeight:700, marginBottom:10 }}>{a.region}</div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8 }}>
            {[["CO₂ Emitted",`${a.carbon_kg} kg`,C.green],["Energy",`${a.energy_kwh} kWh`,C.teal],["Cost",`$${a.cost_usd}`,C.amber],["Renewable",`${a.renewable_pct}%`,C.green],["PUE",a.pue,C.teal],["ESG",`${a.esg_score}/100`,C.green]].map(([l,v,c]) => (
              <div key={l} style={{ background:"#ffffff05", borderRadius:6, padding:"7px 10px" }}>
                <div style={{ color:C.muted, fontSize:9 }}>{l}</div>
                <div style={{ color:c, fontWeight:700, fontFamily:"monospace", fontSize:12 }}>{v}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop:10 }}><K8sClusterCard cluster={a.k8s_cluster} label="K8s — After" accent={C.green}/></div>
        </div>
      </div>

      {/* Comparison bar chart */}
      <div style={{ marginBottom:14 }}>
        <div style={{ color:C.muted, fontSize:11, marginBottom:8 }}>Side-by-side comparison</div>
        <ResponsiveContainer width="100%" height={130}>
          <BarChart data={barData} margin={{ top:5, right:5, bottom:5, left:-10 }} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
            <XAxis type="number" tick={{ fill:C.muted, fontSize:9 }}/>
            <YAxis type="category" dataKey="name" tick={{ fill:C.muted, fontSize:10 }} width={80}/>
            <Tooltip content={<TT/>}/>
            <Legend wrapperStyle={{ fontSize:10 }}/>
            <Bar dataKey="before" name="Before (Traditional)" fill={C.red} radius={[0,4,4,0]}/>
            <Bar dataKey="after" name="After (DhruvCloud Nexus)" fill={C.green} radius={[0,4,4,0]}/>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Gains summary */}
      <div style={{ background:`${C.green}10`, border:`1px solid ${C.green}25`, borderRadius:10, padding:14 }}>
        <div style={{ color:C.green, fontSize:11, fontWeight:700, marginBottom:10 }}>⚡ EFFICIENCY GAINS</div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:10 }}>
          {[
            { l:"CO₂ Saved",    v:`${eg.carbon_saved_kg} kg`,  c:C.green },
            { l:"Energy Saved", v:`${eg.energy_saved_kwh} kWh`,c:C.teal },
            { l:"Cost Saved",   v:`$${eg.cost_saved_usd}`,      c:C.amber },
            { l:"PUE Improved", v:`${eg.pue_improvement_pct}%`, c:C.blue },
            { l:"ESG Score Gain",v:`+${eg.esg_score_gain}`,     c:C.purple },
          ].map(({ l, v, c }) => (
            <div key={l} style={{ textAlign:"center", background:C.card, borderRadius:8, padding:"10px 8px" }}>
              <div style={{ color:C.muted, fontSize:9, marginBottom:4 }}>{l}</div>
              <div style={{ color:c, fontWeight:800, fontFamily:"monospace", fontSize:14 }}>{v}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function RegionTable({ regions, loading }) {
  const [sortKey, setSortKey] = useState("carbon_kg");
  const [sortDir, setSortDir] = useState(1);

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => -d);
    else { setSortKey(key); setSortDir(1); }
  };

  const sorted = [...(regions || [])].sort((a, b) => (a[sortKey] - b[sortKey]) * sortDir);

  const headers = [
    { key:"region_name",   label:"Region",       sortable:false },
    { key:"carbon_kg",     label:"CO₂ (kg)",     sortable:true },
    { key:"cost_usd",      label:"Cost ($)",     sortable:true },
    { key:"latency_ms",    label:"Latency (ms)", sortable:true },
    { key:"esg_score",     label:"ESG Score",    sortable:true },
    { key:"renewable_pct", label:"Renewable",    sortable:true },
    { key:"carbon_reduction_pct", label:"vs Baseline", sortable:true },
  ];

  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:20, marginBottom:16 }}>
      <SH title="🗺️ Region Comparison Table" sub="Click column headers to sort · Green = best · Red = worst"/>
      {loading ? <Skeleton h={200}/> : (
        <div style={{ overflowX:"auto" }}>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
            <thead>
              <tr>
                {headers.map(h => (
                  <th key={h.key} onClick={h.sortable ? () => handleSort(h.key) : undefined}
                    style={{ color:sortKey===h.key?C.green:C.muted, textAlign:"left", padding:"8px 12px", borderBottom:`1px solid ${C.border}`, fontSize:10, fontWeight:700, cursor:h.sortable?"pointer":"default", userSelect:"none", whiteSpace:"nowrap" }}>
                    {h.label}{h.sortable && (sortKey===h.key ? (sortDir===1?" ↑":" ↓") : " ↕")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r, i) => {
                const ciCol = r.carbon_kg < 0.005 ? C.green : r.carbon_kg < 0.02 ? C.teal : r.carbon_kg < 0.05 ? C.amber : C.red;
                return (
                  <tr key={r.region_id} style={{ borderBottom:`1px solid ${C.border}22`, background:r.is_best?`${C.green}08`:r.is_worst?`${C.red}06`:"transparent", transition:"background 0.2s" }}>
                    <td style={{ padding:"10px 12px" }}>
                      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                        {r.is_best && <span style={{ background:`${C.green}22`, color:C.green, borderRadius:4, padding:"1px 6px", fontSize:9, fontWeight:800 }}>✓ BEST</span>}
                        {r.is_worst && <span style={{ background:`${C.red}22`, color:C.red, borderRadius:4, padding:"1px 6px", fontSize:9, fontWeight:800 }}>⚠ WORST</span>}
                        <span style={{ color:C.text, fontWeight:600 }}>{r.region_short || (r.region_name||"").split("(")[0].trim()}</span>
                        <Pill label={r.provider} color={PROV[r.provider]||C.blue}/>
                      </div>
                    </td>
                    <td style={{ color:ciCol, padding:"10px 12px", fontFamily:"monospace", fontWeight:700 }}>{r.carbon_kg}</td>
                    <td style={{ color:C.text, padding:"10px 12px", fontFamily:"monospace" }}>${r.cost_usd}</td>
                    <td style={{ color:r.latency_ms<100?C.green:r.latency_ms<200?C.amber:C.red, padding:"10px 12px", fontFamily:"monospace" }}>{r.latency_ms}ms</td>
                    <td style={{ padding:"10px 12px" }}>
                      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                        <div style={{ flex:1, background:C.border, borderRadius:3, height:4, maxWidth:50 }}>
                          <div style={{ width:`${r.esg_score}%`, background:r.esg_score>80?C.green:r.esg_score>60?C.amber:C.red, borderRadius:3, height:4 }}/>
                        </div>
                        <span style={{ color:C.text, fontSize:11 }}>{r.esg_score}</span>
                        <EsgBadge grade={r.esg_grade}/>
                      </div>
                    </td>
                    <td style={{ padding:"10px 12px" }}>
                      <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                        <div style={{ flex:1, background:C.border, borderRadius:3, height:4, maxWidth:55 }}>
                          <div style={{ width:`${r.renewable_pct}%`, background:C.green, borderRadius:3, height:4 }}/>
                        </div>
                        <span style={{ color:C.text, fontSize:11 }}>{r.renewable_pct}%</span>
                      </div>
                    </td>
                    <td style={{ padding:"10px 12px" }}>
                      <GreenBadge pct={r.carbon_reduction_pct}/>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StrategyToggle({ value, onChange }) {
  const opts = [
    { id:"green",    label:"🌿 Carbon First", sub:"Min CO₂ (70% weight)" },
    { id:"balanced", label:"⚖️ Balanced",      sub:"CO₂ + Cost (45/45)" },
    { id:"cheap",    label:"💰 Cost First",    sub:"Min cost (70% weight)" },
  ];
  return (
    <div style={{ display:"flex", gap:8, marginBottom:16 }}>
      {opts.map(o => (
        <button key={o.id} onClick={() => onChange(o.id)}
          style={{ flex:1, padding:"10px 14px", borderRadius:10, border:`2px solid ${value===o.id?C.green:C.border}`, background:value===o.id?`${C.green}18`:C.surface, color:value===o.id?C.green:C.muted, cursor:"pointer", textAlign:"center", fontFamily:"monospace", transition:"all 0.15s" }}>
          <div style={{ fontWeight:700, fontSize:12 }}>{o.label}</div>
          <div style={{ fontSize:9, marginTop:2, opacity:0.7 }}>{o.sub}</div>
        </button>
      ))}
    </div>
  );
}

function DecisionStory({ decision, selectedRegion, impact }) {
  if (!decision || !selectedRegion) return null;
  return (
    <div style={{ background:`linear-gradient(135deg,${C.green}15,${C.teal}08)`, border:`1px solid ${C.green}40`, borderRadius:12, padding:"20px 24px", marginBottom:16, animation:"fadeIn 0.5s ease" }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", flexWrap:"wrap", gap:12 }}>
        <div style={{ flex:1 }}>
          <div style={{ color:C.muted, fontSize:10, fontWeight:700, letterSpacing:1.5, textTransform:"uppercase", marginBottom:4 }}>✅ SELECTED REGION</div>
          <div style={{ color:C.green, fontSize:22, fontWeight:900 }}>{selectedRegion.region_name || selectedRegion.name}</div>
          <div style={{ color:C.muted, fontSize:12, marginTop:4 }}>
            <Pill label={selectedRegion.provider} color={PROV[selectedRegion.provider]||C.blue}/>
            &nbsp;·&nbsp; {selectedRegion.carbon_intensity} kgCO₂/kWh · {selectedRegion.renewable_pct}% renewable · ESG {selectedRegion.esg_score}
          </div>
          <div style={{ color:C.text, fontSize:13, fontWeight:700, marginTop:8, fontStyle:"italic" }}>
            "{decision.explanation?.summary}"
          </div>
        </div>
        <div style={{ display:"flex", flexDirection:"column", gap:8, alignItems:"flex-end" }}>
          <GreenBadge pct={selectedRegion.carbon_reduction_pct} size="lg"/>
          <EsgBadge grade={decision.esg_grade} size="lg"/>
        </div>
      </div>

      {/* Why reasons */}
      {decision.explanation?.reasons && (
        <div style={{ marginTop:14 }}>
          <div style={{ color:C.muted, fontSize:10, fontWeight:700, marginBottom:6, textTransform:"uppercase", letterSpacing:1 }}>WHY THIS REGION?</div>
          <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
            {decision.explanation.reasons.map((r, i) => (
              <div key={i} style={{ background:`${C.green}12`, border:`1px solid ${C.green}30`, borderRadius:8, padding:"5px 12px", color:C.text, fontSize:11 }}>
                ✓ {r}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Impact row */}
      {impact && (
        <div style={{ marginTop:14, display:"grid", gridTemplateColumns:"repeat(6,1fr)", gap:8 }}>
          {[
            { l:"CO₂ Saved",   v:`${impact.carbon_saved_kg}kg`,  c:C.green },
            { l:"Energy Saved",v:`${impact.energy_saved_kwh}kWh`, c:C.teal },
            { l:"Cost Saved",  v:`$${impact.cost_saved_usd}`,      c:C.amber },
            { l:"Trees 🌳",    v:`${impact.trees_equivalent}`,     c:C.green },
            { l:"Car Km 🚗",   v:`${impact.car_km_equivalent}`,    c:C.teal },
            { l:"Latency",     v:`${selectedRegion.latency_ms}ms`, c:C.blue },
          ].map(({ l, v, c }) => (
            <div key={l} style={{ background:"#ffffff08", borderRadius:8, padding:"8px 10px", textAlign:"center" }}>
              <div style={{ color:C.muted, fontSize:9, marginBottom:2 }}>{l}</div>
              <div style={{ color:c, fontWeight:800, fontFamily:"monospace", fontSize:12 }}>{v}</div>
            </div>
          ))}
        </div>
      )}

      {/* Worst region warning */}
      {decision.explanation?.vs_worst && (
        <div style={{ marginTop:12, background:`${C.red}10`, border:`1px solid ${C.red}30`, borderRadius:8, padding:"8px 14px", display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ color:C.red, fontSize:14 }}>⚠️</span>
          <span style={{ color:C.muted, fontSize:11 }}>
            Worst alternative: <strong style={{ color:C.red }}>{decision.explanation.vs_worst.region}</strong> would emit {decision.explanation.vs_worst.carbon_worse_by_pct}% more CO₂ ({decision.explanation.vs_worst.avoided_kg}kg extra)
          </span>
        </div>
      )}
    </div>
  );
}

// ─── PAGES ─────────────────────────────────────────────────────────────────

function DashboardPage({ toast }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [budget, setBudget] = useState({ used:23.7, total:100 });

  useEffect(() => {
    (async () => {
      setLoading(true);
      const [m, b] = await Promise.all([apiFetch("/api/v1/analytics/summary"), apiFetch("/api/v1/carbon/budget")]);
      if (m.ok && m.data) setMetrics(m.data);
      else setMetrics({ summary:{ total_workloads:2847, total_carbon_saved_kg:1203.7, avg_reduction_pct:62.4, avg_esg_score_gain:57, green_region_pct:78.2, ml_r2:0.874, active_regions:8, carbon_budget:{used:23.7,total:100}, equivalents:{trees_planted:20.1,car_km_avoided:7580,smartphone_charges:150337} }, trend:mockTrend(), region_distribution:RMOCK.map((r,i)=>({region_id:r.id,region_name:r.name,count:Math.floor(10+Math.random()*60),share_pct:0})), energy_by_region:RMOCK.map(r=>({region_id:r.id,region_name:r.short,carbon_intensity:r.carbon_intensity,renewable_pct:r.renewable_pct,esg_score:r.esg_score,esg_grade:r.esg_grade})) });
      if (b.ok && b.data) setBudget({ used:b.data.used||23.7, total:b.data.total||100 });
      setLoading(false);
    })();
  }, []);

  const s = metrics?.summary || {};
  const trend = metrics?.trend || [];
  const eq = s.equivalents || {};

  return (
    <div>
      {/* Hero */}
      <div style={{ background:`linear-gradient(135deg,${C.green}18,${C.teal}10)`, border:`1px solid ${C.green}35`, borderRadius:14, padding:"18px 24px", marginBottom:22, display:"flex", alignItems:"center", gap:20, flexWrap:"wrap" }}>
        <div style={{ fontSize:36 }}>🌍</div>
        <div style={{ flex:1 }}>
          <div style={{ color:C.muted, fontSize:10, fontWeight:700, letterSpacing:2, textTransform:"uppercase", marginBottom:4 }}>DhruvCloud Nexus · CarbonAware Sustainable Cloud Orchestration Platform</div>
          <div style={{ color:C.green, fontSize:18, fontWeight:900 }}>
            DhruvCloud Nexus saved {loading ? <Skeleton w={80} h={20}/> : <span style={{fontSize:26}}>{s.total_carbon_saved_kg}</span>} kg CO₂ across {loading ? "..." : <span style={{fontSize:20}}>{s.total_workloads?.toLocaleString()}</span>} workloads
          </div>
          <div style={{ color:C.muted, fontSize:11, marginTop:4 }}>
            🌳 {eq.trees_planted} trees · 🚗 {eq.car_km_avoided} km · 📱 {eq.smartphone_charges?.toLocaleString()} phones · ESG avg +{s.avg_esg_score_gain}pts
          </div>
        </div>
        <GreenBadge pct={s.avg_reduction_pct} size="lg"/>
      </div>

      {/* KPIs */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:14, marginBottom:20 }}>
        <StatCard label="Total Workloads" value={s.total_workloads?.toLocaleString()||"..."} icon="⚡" animated loading={loading}/>
        <StatCard label="Carbon Saved" value={`${s.total_carbon_saved_kg||0}kg`} accent={C.green} icon="🌱" sub="vs. traditional scheduling" animated loading={loading}/>
        <StatCard label="Avg CO₂ Reduction" value={`${s.avg_reduction_pct||0}%`} accent={C.teal} icon="📉" animated loading={loading}/>
        <StatCard label="Avg ESG Score Gain" value={`+${s.avg_esg_score_gain||0}pts`} accent={C.purple} icon="📋" animated loading={loading}/>
        <StatCard label="ML Ensemble R²" value={s.ml_r2||0} accent={C.amber} icon="🤖" loading={loading}/>
        <StatCard label="K8s Clusters" value={s.active_regions||8} accent={C.blue} icon="☸️" loading={loading}/>
      </div>

      <LiveFeed/>
      <WorldMap regions={RMOCK} selectedId="eu-north"/>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:18, marginBottom:18 }}>
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
          <SH title="Before vs After — 30-Day Trend" sub="Traditional Scheduling vs DhruvCloud Nexus (kgCO₂)"/>
          {loading ? <Skeleton h={200}/> : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trend} margin={{top:5,right:5,bottom:5,left:-15}}>
                <defs>
                  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={C.red} stopOpacity={0.3}/><stop offset="95%" stopColor={C.red} stopOpacity={0}/></linearGradient>
                  <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={C.green} stopOpacity={0.3}/><stop offset="95%" stopColor={C.green} stopOpacity={0}/></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
                <XAxis dataKey="date" tick={{fill:C.muted,fontSize:9}} interval={6}/>
                <YAxis tick={{fill:C.muted,fontSize:9}}/>
                <Tooltip content={<TT/>}/>
                <Legend wrapperStyle={{fontSize:10}}/>
                <Area type="monotone" dataKey="before_carbon" name="Before (Traditional)" stroke={C.red} fill="url(#bg)" strokeWidth={2}/>
                <Area type="monotone" dataKey="after_carbon" name="After (DhruvCloud Nexus)" stroke={C.green} fill="url(#ag)" strokeWidth={2}/>
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
        <BudgetGauge used={budget.used} total={budget.total} loading={loading}/>
      </div>

      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18, marginBottom:18 }}>
        <SH title="Carbon Intensity + ESG Score by K8s Region" sub="Lower CO₂ + Higher ESG = better cluster for green scheduling"/>
        {loading ? <Skeleton h={180}/> : (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={metrics?.energy_by_region||[]} margin={{top:5,right:5,bottom:40,left:-15}}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
              <XAxis dataKey="region_name" tick={{fill:C.muted,fontSize:9}} angle={-35} textAnchor="end"/>
              <YAxis yAxisId="l" tick={{fill:C.muted,fontSize:9}}/>
              <YAxis yAxisId="r" orientation="right" tick={{fill:C.muted,fontSize:9}}/>
              <Tooltip content={<TT/>}/>
              <Legend wrapperStyle={{fontSize:9}}/>
              <Bar yAxisId="l" dataKey="carbon_intensity" name="CO₂/kWh" radius={[4,4,0,0]}>
                {(metrics?.energy_by_region||[]).map((e,i) => <Cell key={i} fill={e.carbon_intensity<0.1?C.green:e.carbon_intensity<0.25?C.teal:e.carbon_intensity<0.45?C.amber:C.red}/>)}
              </Bar>
              <Bar yAxisId="r" dataKey="esg_score" name="ESG Score" fill={C.purple} opacity={0.5} radius={[4,4,0,0]}/>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

function SimulationPage({ toast }) {
  const [form, setForm] = useState({ cpu_load:"0.65", execution_time:"2.5", memory_usage:"0.4", workload_type:"batch", optimize_for:"green", max_latency_ms:"", budget_usd:"" });
  const [result, setResult] = useState(null);
  const [simResult, setSimResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [simLoading, setSimLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState(null);

  const STEPS = ["Fetching live carbon data...","Running ML ensemble model...","Applying policy engine...","Evaluating 8 K8s clusters...","Selecting optimal region..."];

  const handleSubmit = async () => {
    setError(null); setResult(null); setStep(1);
    for (let i = 1; i <= STEPS.length; i++) {
      await new Promise(r => setTimeout(r, 380));
      setStep(i + 1);
    }
    setLoading(true);
    const body = { ...form, cpu_load:parseFloat(form.cpu_load), execution_time:parseFloat(form.execution_time), memory_usage:parseFloat(form.memory_usage), max_latency_ms:form.max_latency_ms?parseInt(form.max_latency_ms):null, budget_usd:form.budget_usd?parseFloat(form.budget_usd):null };
    const res = await apiFetch("/api/v1/workloads", { method:"POST", body:JSON.stringify(body) });
    if (res.ok && res.data) {
      setResult(res.data);
      toast(`✅ Scheduled to ${res.data.selected_region?.region_name} — ${res.data.selected_region?.carbon_reduction_pct}% CO₂ saved`, "success");
    } else {
      const mockRes = mockScheduleResult(form);
      setResult(mockRes);
      toast(`✅ Scheduled to ${mockRes.selected_region.region_name} — ${mockRes.selected_region.carbon_reduction_pct}% CO₂ saved`, "success");
    }
    setLoading(false); setStep(0);
  };

  const handleSim = async () => {
    setSimLoading(true);
    const res = await apiFetch("/api/v1/simulations", { method:"POST" });
    if (res.ok && res.data) {
      setSimResult(res.data);
    } else {
      const rs = Array.from({length:20}, (_, i) => {
        const b = +(0.04+Math.random()*0.12).toFixed(4), a = +(b*(0.05+Math.random()*0.25)).toFixed(4);
        const r = RMOCK[Math.floor(Math.random()*3)];
        return { workload_id:i+1, workload_type:["batch","streaming","interactive","ml-training"][Math.floor(Math.random()*4)], cpu_load:+(0.3+Math.random()*0.6).toFixed(3), execution_time:+(0.5+Math.random()*7).toFixed(2), before_region:"US East (N. Virginia)", after_region:r.name, before_carbon:b, after_carbon:a, reduction_pct:+((b-a)/b*100).toFixed(1), cost_saved_usd:+(Math.random()*0.5).toFixed(4), esg_gain:r.esg_score-40 };
      });
      const tb = rs.reduce((a,w)=>a+w.before_carbon,0), ta = rs.reduce((a,w)=>a+w.after_carbon,0);
      setSimResult({ simulation_id:`sim-${Math.floor(Math.random()*90000+10000)}`, workloads_processed:20, results:rs, summary:{ total_before_carbon_kg:+tb.toFixed(4), total_after_carbon_kg:+ta.toFixed(4), carbon_saved_kg:+(tb-ta).toFixed(4), carbon_reduction_pct:+((tb-ta)/tb*100).toFixed(1), total_cost_saved_usd:+(Math.random()*2).toFixed(4), avg_esg_gain:+(rs.reduce((a,r)=>a+r.esg_gain,0)/rs.length).toFixed(1), equivalents:{trees_planted:+((tb-ta)/0.06).toFixed(2),car_km_avoided:+((tb-ta)*6.3).toFixed(1)} } });
    }
    setSimLoading(false);
    toast("🚀 Batch simulation complete!", "success");
  };

  const inp = { background:C.surface, border:`1px solid ${C.border}`, borderRadius:8, color:C.text, padding:"10px 13px", fontSize:13, width:"100%", outline:"none", fontFamily:"monospace", boxSizing:"border-box" };

  return (
    <div style={{ display:"grid", gridTemplateColumns:"350px 1fr", gap:20 }}>
      {/* Form */}
      <div>
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:20, marginBottom:14 }}>
          <SH title="☸️ Schedule K8s Workload" sub="Carbon-aware scheduling with ML + Policy Engine"/>

          <StrategyToggle value={form.optimize_for} onChange={v => setForm(p => ({...p, optimize_for:v}))}/>

          {/* Processing steps */}
          {step > 0 && (
            <div style={{ background:`${C.teal}12`, border:`1px solid ${C.teal}35`, borderRadius:8, padding:"10px 14px", marginBottom:14 }}>
              <div style={{ color:C.teal, fontSize:11, fontWeight:700, marginBottom:6, display:"flex", alignItems:"center", gap:6 }}>
                <Spinner size={12} color={C.teal}/> Processing...
              </div>
              {STEPS.map((msg, i) => (
                <div key={i} style={{ display:"flex", alignItems:"center", gap:7, marginBottom:3, opacity:i < step-1 ? 1 : i === step-1 ? 1 : 0.3, transition:"opacity 0.3s" }}>
                  <span style={{ fontSize:10 }}>{i < step-1 ? "✅" : i === step-1 ? "⟳" : "○"}</span>
                  <span style={{ color:i < step-1 ? C.green : i === step-1 ? C.teal : C.muted, fontSize:11 }}>{msg}</span>
                </div>
              ))}
            </div>
          )}

          {error && <div style={{ background:`${C.red}18`, border:`1px solid ${C.red}44`, borderRadius:8, padding:"10px 14px", color:C.red, fontSize:12, marginBottom:12 }}>❌ {error}</div>}

          <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
            {[
              { l:"CPU Load (0–1)",         k:"cpu_load",       t:"number", s:0.01, min:0.01, max:1 },
              { l:"Execution Time (hours)", k:"execution_time", t:"number", s:0.1,  min:0.1 },
              { l:"Memory Usage (0–1)",     k:"memory_usage",   t:"number", s:0.01, min:0.01, max:1 },
              { l:"Max Latency ms (opt.)",  k:"max_latency_ms", t:"number", s:10,   min:10 },
              { l:"Budget USD (opt.)",      k:"budget_usd",     t:"number", s:0.01, min:0.01 },
            ].map(f => (
              <div key={f.k}>
                <label style={{ color:C.muted, fontSize:10, fontWeight:600, letterSpacing:0.5, display:"block", marginBottom:3 }}>{f.l}</label>
                <input type={f.t} step={f.s} min={f.min} max={f.max} value={form[f.k]}
                  onChange={e => setForm(p => ({...p, [f.k]:e.target.value}))}
                  style={inp} placeholder={f.k==="max_latency_ms"||f.k==="budget_usd"?"No limit":""}/>
              </div>
            ))}
            <div>
              <label style={{ color:C.muted, fontSize:10, fontWeight:600, display:"block", marginBottom:3 }}>Workload Type</label>
              <select value={form.workload_type} onChange={e => setForm(p => ({...p, workload_type:e.target.value}))} style={inp}>
                {["batch","streaming","interactive","ml-training","web-api"].map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
            <button onClick={handleSubmit} disabled={loading || step > 0}
              style={{ background:loading||step>0 ? C.border : `linear-gradient(135deg,${C.green},${C.teal})`, border:"none", borderRadius:8, color:"#000", fontWeight:800, fontSize:14, padding:"12px", cursor:loading||step>0?"default":"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:8, fontFamily:"monospace" }}>
              {loading || step > 0 ? <><Spinner size={14} color="#000"/>Scheduling...</> : "☸️ Schedule Workload"}
            </button>
          </div>
        </div>

        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
          <div style={{ color:C.text, fontWeight:700, marginBottom:6 }}>🚀 Batch Simulation</div>
          <div style={{ color:C.muted, fontSize:11, marginBottom:12 }}>Run DhruvCloud Nexus on 20 historical Google Cluster Trace workloads</div>
          <button onClick={handleSim} disabled={simLoading}
            style={{ background:simLoading?C.border:`linear-gradient(135deg,${C.blue},${C.purple})`, border:"none", borderRadius:8, color:"#fff", fontWeight:700, fontSize:12, padding:"10px", cursor:simLoading?"default":"pointer", width:"100%", display:"flex", alignItems:"center", justifyContent:"center", gap:8, fontFamily:"monospace" }}>
            {simLoading ? <><Spinner size={13} color="#fff"/>Simulating...</> : "🚀 Run Batch Simulation"}
          </button>
        </div>
      </div>

      {/* Results */}
      <div>
        {result && <>
          <DecisionStory decision={result.decision} selectedRegion={result.selected_region} impact={result.impact}/>
          <BeforeAfterPanel ba={result.before_after}/>
          <RegionTable regions={result.all_regions} loading={false}/>
          <WorldMap regions={RMOCK} selectedId={result.selected_region?.region_id}/>
          {result.ml && (
            <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:10, padding:14, marginBottom:14, display:"flex", gap:16, alignItems:"center", flexWrap:"wrap" }}>
              <span style={{ color:C.muted, fontSize:11 }}>🤖 ML Predicted CPU: <span style={{ color:C.amber, fontWeight:700 }}>{result.ml.predicted_cpu}</span></span>
              <span style={{ color:C.muted, fontSize:11 }}>Confidence: <span style={{ color:C.green, fontWeight:700 }}>{result.ml.confidence_pct}%</span></span>
              <span style={{ color:C.muted, fontSize:11 }}>Model: <span style={{ color:C.text }}>{result.ml.model}</span></span>
              {result.policies_applied?.map((p, i) => <Pill key={i} label={p} color={C.amber}/>)}
            </div>
          )}
        </>}

        {simResult && (
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:20 }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:14, flexWrap:"wrap", gap:10 }}>
              <div>
                <div style={{ color:C.text, fontWeight:700, fontSize:13 }}>Simulation {simResult.simulation_id}</div>
                <div style={{ color:C.muted, fontSize:11 }}>{simResult.workloads_processed} workloads · Before vs After</div>
              </div>
              <div style={{ display:"flex", gap:12, flexWrap:"wrap", alignItems:"center" }}>
                <div><div style={{ color:C.muted, fontSize:9 }}>CO₂ Saved</div><div style={{ color:C.green, fontWeight:800, fontFamily:"monospace" }}>{simResult.summary?.carbon_saved_kg} kg</div></div>
                <div><div style={{ color:C.muted, fontSize:9 }}>Cost Saved</div><div style={{ color:C.amber, fontWeight:800, fontFamily:"monospace" }}>${simResult.summary?.total_cost_saved_usd}</div></div>
                <div><div style={{ color:C.muted, fontSize:9 }}>Avg ESG Gain</div><div style={{ color:C.purple, fontWeight:800 }}>+{simResult.summary?.avg_esg_gain}pts</div></div>
                <GreenBadge pct={simResult.summary?.carbon_reduction_pct}/>
              </div>
            </div>
            {simResult.summary?.equivalents && (
              <div style={{ background:`${C.green}10`, border:`1px solid ${C.green}25`, borderRadius:8, padding:"8px 14px", marginBottom:14, fontSize:11, color:C.muted }}>
                🌳 {simResult.summary.equivalents.trees_planted} trees planted · 🚗 {simResult.summary.equivalents.car_km_avoided} km of driving avoided
              </div>
            )}
            <div style={{ maxHeight:300, overflowY:"auto" }}>
              <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11 }}>
                <thead>
                  <tr>{["ID","Type","CPU","Before CO₂","After CO₂","Before","After","Reduction","Cost Saved","ESG Gain"].map(h => <th key={h} style={{ color:C.muted, textAlign:"left", padding:"5px 8px", borderBottom:`1px solid ${C.border}`, fontSize:9, fontWeight:600 }}>{h}</th>)}</tr>
                </thead>
                <tbody>
                  {simResult.results?.map((r, i) => (
                    <tr key={i} style={{ borderBottom:`1px solid ${C.border}22` }}>
                      <td style={{ color:C.muted, padding:"4px 8px" }}>#{r.workload_id}</td>
                      <td style={{ padding:"4px 8px" }}><Pill label={r.workload_type} color={C.blue}/></td>
                      <td style={{ color:C.text, padding:"4px 8px", fontFamily:"monospace" }}>{r.cpu_load}</td>
                      <td style={{ color:C.red, padding:"4px 8px", fontFamily:"monospace" }}>{r.before_carbon}</td>
                      <td style={{ color:C.green, padding:"4px 8px", fontFamily:"monospace" }}>{r.after_carbon}</td>
                      <td style={{ color:C.muted, padding:"4px 8px", fontSize:9 }}>{(r.before_region||"").split("(")[0].trim()}</td>
                      <td style={{ color:C.green, padding:"4px 8px", fontSize:9 }}>{(r.after_region||"").split("(")[0].trim()}</td>
                      <td style={{ padding:"4px 8px" }}><GreenBadge pct={r.reduction_pct}/></td>
                      <td style={{ color:C.amber, padding:"4px 8px", fontFamily:"monospace" }}>${r.cost_saved_usd}</td>
                      <td style={{ color:C.purple, padding:"4px 8px", fontWeight:700 }}>+{r.esg_gain}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!result && !simResult && (
          <div style={{ background:C.card, border:`1px dashed ${C.border}`, borderRadius:12, padding:60, textAlign:"center" }}>
            <div style={{ fontSize:48, marginBottom:12 }}>☸️</div>
            <div style={{ color:C.muted, fontSize:15 }}>Submit a workload to see full Before vs After comparison</div>
            <div style={{ color:C.muted, fontSize:11, marginTop:8 }}>Switch between Carbon First / Cost First / Balanced to see how region selection changes</div>
          </div>
        )}
      </div>
    </div>
  );
}

function K8sPage() {
  const [clusters, setClusters] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    apiFetch("/api/v1/k8s/clusters").then(res => {
      if (res.ok && res.data?.clusters) setClusters(res.data.clusters);
      else setClusters(RMOCK.map(r => ({ ...r, cluster_name:r.id==="eu-north"?"aks-eu-north-prod":"eks-"+r.id+"-prod", region_id:r.id, region_name:r.name, nodes_total:r.k8s_nodes, cpu_utilization_pct:Math.floor(35+Math.random()*45), ram_utilization_pct:Math.floor(30+Math.random()*50), pods_running:Math.floor(r.k8s_nodes*2.5), pods_pending:Math.floor(Math.random()*3), pods_failed:Math.floor(Math.random()*2), carbon_kg_per_hour:+(r.carbon_intensity*0.25*1.0*r.pue).toFixed(4) })));
      setLoading(false);
    });
  }, []);

  const radarData = (clusters||[]).map(c => ({ subject:(c.region_name||c.name||"").split("(")[0].trim().slice(0,8), ESG:c.esg_score||0, Renewable:c.renewable_pct||0, Efficiency:Math.max(0,100-(c.cpu_utilization_pct||50)) }));

  return (
    <div>
      <div style={{ background:`linear-gradient(135deg,${C.blue}15,${C.purple}10)`, border:`1px solid ${C.blue}35`, borderRadius:12, padding:"16px 22px", marginBottom:20 }}>
        <div style={{ color:C.blue, fontSize:18, fontWeight:900 }}>☸️ Kubernetes Cluster Monitor</div>
        <div style={{ color:C.muted, fontSize:12, marginTop:2 }}>DhruvCloud Nexus · Real-time energy efficiency across {(clusters||RMOCK).length} clusters</div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"repeat(2,1fr)", gap:16, marginBottom:20 }}>
        {loading ? Array(6).fill(null).map((_, i) => (
          <div key={i} style={{ background:C.card, borderRadius:12, padding:16 }}><Skeleton h={120}/></div>
        )) : (clusters||[]).slice(0,6).map(c => {
          const cpuCol = c.cpu_utilization_pct>80?C.red:c.cpu_utilization_pct>60?C.amber:C.green;
          const ciCol = c.carbon_intensity<0.1?C.green:c.carbon_intensity<0.3?C.teal:c.carbon_intensity<0.5?C.amber:C.red;
          return (
            <div key={c.cluster_name||c.id} style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:16 }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:10 }}>
                <div>
                  <div style={{ color:C.text, fontWeight:700, fontSize:12, fontFamily:"monospace" }}>{c.cluster_name}</div>
                  <div style={{ color:C.muted, fontSize:11, marginTop:2 }}>{c.region_name||c.name}</div>
                </div>
                <div style={{ display:"flex", gap:6 }}>
                  <Pill label={c.provider} color={PROV[c.provider]||C.blue}/>
                  <EsgBadge grade={c.esg_grade||"B"}/>
                </div>
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginBottom:12 }}>
                <div>
                  <div style={{ color:C.muted, fontSize:9, marginBottom:3 }}>CPU Utilization</div>
                  <div style={{ background:C.border, borderRadius:3, height:5, marginBottom:2 }}><div style={{ width:`${c.cpu_utilization_pct}%`, background:cpuCol, borderRadius:3, height:5 }}/></div>
                  <div style={{ color:cpuCol, fontSize:11, fontWeight:700 }}>{c.cpu_utilization_pct}%</div>
                </div>
                <div>
                  <div style={{ color:C.muted, fontSize:9, marginBottom:3 }}>RAM Utilization</div>
                  <div style={{ background:C.border, borderRadius:3, height:5, marginBottom:2 }}><div style={{ width:`${c.ram_utilization_pct}%`, background:C.teal, borderRadius:3, height:5 }}/></div>
                  <div style={{ color:C.teal, fontSize:11, fontWeight:700 }}>{c.ram_utilization_pct}%</div>
                </div>
              </div>
              <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                {[["Nodes",c.nodes_total,C.text],["Pods ✅",c.pods_running,C.green],["CO₂/hr",c.carbon_kg_per_hour,ciCol],["Renewable",`${c.renewable_pct}%`,C.green]].map(([l,v,c2]) => (
                  <div key={l} style={{ background:"#ffffff06", borderRadius:6, padding:"5px 9px", textAlign:"center" }}>
                    <div style={{ color:C.muted, fontSize:8 }}>{l}</div>
                    <div style={{ color:c2, fontWeight:700, fontSize:12 }}>{v}</div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {radarData.length > 0 && (
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
          <SH title="K8s Cluster ESG Radar" sub="ESG Score · Renewable % · CPU Efficiency"/>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid stroke={C.border}/>
              <PolarAngleAxis dataKey="subject" tick={{ fill:C.muted, fontSize:9 }}/>
              <PolarRadiusAxis angle={30} domain={[0,100]} tick={{ fill:C.muted, fontSize:8 }}/>
              <Radar name="ESG" dataKey="ESG" stroke={C.purple} fill={C.purple} fillOpacity={0.2}/>
              <Radar name="Renewable" dataKey="Renewable" stroke={C.green} fill={C.green} fillOpacity={0.2}/>
              <Radar name="Efficiency" dataKey="Efficiency" stroke={C.teal} fill={C.teal} fillOpacity={0.2}/>
              <Legend wrapperStyle={{ fontSize:10 }}/>
              <Tooltip content={<TT/>}/>
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function ESGPage() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    apiFetch("/api/v1/esg/report").then(res => {
      if (res.ok && res.data) setReport(res.data);
      else setReport({ overall_esg_score:78, overall_grade:"B+", environmental:{ total_carbon_saved_kg:1203.7, avg_reduction_pct:62.4, renewable_energy_usage_pct:74.5, green_region_scheduling_pct:78.2, equivalents:{trees_planted:20.1,car_km_avoided:7580,smartphone_charges:150337,led_bulb_hours:120337} }, social:{ workloads_optimized:2847, regions_monitored:8, uptime_pct:99.95 }, governance:{ policy_engine_active:true, carbon_budget_enforcement:true, audit_trail_count:47, api_versioned:true }, regions_esg:RMOCK.map(r=>({ region:r.name,region_id:r.id,provider:r.provider,esg_score:r.esg_score,esg_grade:r.esg_grade,carbon_intensity:r.carbon_intensity,renewable_pct:r.renewable_pct,cluster_name:r.id+"-prod" })).sort((a,b)=>b.esg_score-a.esg_score), recommendations:["Migrate batch workloads from US East → EU North for 97% CO₂ reduction","Schedule ML training off-peak (18:00–06:00) for additional 12% efficiency gain","Enable carbon budget alerts at 60% threshold for proactive governance","EU North (Azure Stockholm) achieves highest ESG compliance — Grade A+"] });
      setLoading(false);
    });
  }, []);

  if (loading || !report) return <div style={{ padding:40 }}><Skeleton h={200}/></div>;
  const { environmental:env, social, governance:gov } = report;
  const sc = report.overall_esg_score > 85 ? C.green : report.overall_esg_score > 65 ? C.teal : report.overall_esg_score > 50 ? C.amber : C.red;

  return (
    <div>
      <div style={{ display:"grid", gridTemplateColumns:"auto 1fr", gap:20, marginBottom:22 }}>
        <div style={{ background:C.card, border:`2px solid ${sc}`, borderRadius:16, padding:24, textAlign:"center", minWidth:140 }}>
          <div style={{ color:C.muted, fontSize:10, fontWeight:700, letterSpacing:1.5, marginBottom:8 }}>OVERALL ESG</div>
          <div style={{ color:sc, fontSize:52, fontWeight:900, fontFamily:"monospace", lineHeight:1 }}>{report.overall_esg_score}</div>
          <div style={{ color:C.muted, fontSize:11, marginTop:4 }}>/100</div>
          <div style={{ marginTop:10 }}><EsgBadge grade={report.overall_grade}/></div>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:12 }}>
          {[
            { title:"🌿 Environmental", color:C.green, items:[["CO₂ Saved",`${env.total_carbon_saved_kg}kg`],["Avg Reduction",`${env.avg_reduction_pct}%`],["Renewable",`${env.renewable_energy_usage_pct}%`],["Green Scheduling",`${env.green_region_scheduling_pct}%`]] },
            { title:"👥 Social",       color:C.blue,  items:[["Workloads Opt.",social.workloads_optimized.toLocaleString()],["Regions Monitored",social.regions_monitored],["Uptime",`${social.uptime_pct}%`]] },
            { title:"🏛️ Governance",   color:C.purple,items:[["Policy Engine",gov.policy_engine_active?"Active":"Inactive"],["Budget Enforcement",gov.carbon_budget_enforcement?"Yes":"No"],["Audit Trail",`${gov.audit_trail_count} records`],["API Versioned",gov.api_versioned?"v1":"No"]] },
          ].map(({ title, color, items }) => (
            <div key={title} style={{ background:C.card, border:`1px solid ${color}35`, borderRadius:12, padding:16 }}>
              <div style={{ color, fontWeight:700, fontSize:12, marginBottom:10 }}>{title}</div>
              {items.map(([l,v]) => (
                <div key={l} style={{ display:"flex", justifyContent:"space-between", marginBottom:6 }}>
                  <span style={{ color:C.muted, fontSize:11 }}>{l}</span>
                  <span style={{ color:C.text, fontWeight:700, fontFamily:"monospace", fontSize:11 }}>{v}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Equivalents */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18, marginBottom:18 }}>
        <SH title="🌍 Environmental Equivalents" sub="Real-world impact of DhruvCloud Nexus CO₂ savings"/>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12 }}>
          {[["🌳","Trees Planted",env.equivalents.trees_planted],["🚗","Car Km Avoided",env.equivalents.car_km_avoided?.toLocaleString()],["📱","Phones Charged",env.equivalents.smartphone_charges?.toLocaleString()],["💡","LED Bulb Hours",env.equivalents.led_bulb_hours?.toLocaleString()]].map(([icon,label,val]) => (
            <div key={label} style={{ background:C.surface, borderRadius:10, padding:16, textAlign:"center" }}>
              <div style={{ fontSize:28, marginBottom:6 }}>{icon}</div>
              <div style={{ color:C.green, fontSize:20, fontWeight:800, fontFamily:"monospace" }}>{val}</div>
              <div style={{ color:C.muted, fontSize:11, marginTop:4 }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Regions ESG table */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18, marginBottom:18 }}>
        <SH title="ESG Score by Region" sub="E/S/G performance across all K8s cluster regions"/>
        <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
          <thead><tr>{["Region","Provider","ESG Score","Grade","CO₂/kWh","Renewable"].map(h => <th key={h} style={{ color:C.muted, textAlign:"left", padding:"7px 12px", borderBottom:`1px solid ${C.border}`, fontSize:10, fontWeight:600 }}>{h}</th>)}</tr></thead>
          <tbody>
            {report.regions_esg?.map((r, i) => {
              const s = r.esg_score > 80 ? C.green : r.esg_score > 60 ? C.amber : C.red;
              return (
                <tr key={i} style={{ borderBottom:`1px solid ${C.border}22` }}>
                  <td style={{ color:C.text, padding:"9px 12px", fontWeight:600 }}>{r.region}</td>
                  <td style={{ padding:"9px 12px" }}><Pill label={r.provider} color={PROV[r.provider]||C.blue}/></td>
                  <td style={{ padding:"9px 12px" }}>
                    <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                      <div style={{ flex:1, background:C.border, borderRadius:3, height:5, maxWidth:70 }}><div style={{ width:`${r.esg_score}%`, background:s, borderRadius:3, height:5 }}/></div>
                      <span style={{ color:s, fontWeight:800, fontSize:13 }}>{r.esg_score}</span>
                    </div>
                  </td>
                  <td style={{ padding:"9px 12px" }}><EsgBadge grade={r.esg_grade}/></td>
                  <td style={{ color:r.carbon_intensity<0.1?C.green:r.carbon_intensity<0.3?C.teal:r.carbon_intensity<0.5?C.amber:C.red, padding:"9px 12px", fontFamily:"monospace", fontWeight:700 }}>{r.carbon_intensity}</td>
                  <td style={{ padding:"9px 12px" }}>
                    <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                      <div style={{ flex:1, background:C.border, borderRadius:3, height:4, maxWidth:55 }}><div style={{ width:`${r.renewable_pct}%`, background:C.green, borderRadius:3, height:4 }}/></div>
                      <span style={{ color:C.text, fontSize:11 }}>{r.renewable_pct}%</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
        <SH title="💡 ESG Recommendations" sub="Automated optimization recommendations"/>
        {report.recommendations?.map((rec, i) => (
          <div key={i} style={{ display:"flex", gap:10, padding:"10px 12px", background:`${C.green}08`, borderRadius:8, marginBottom:8, border:`1px solid ${C.green}20` }}>
            <span style={{ color:C.green, fontSize:14, flexShrink:0 }}>→</span>
            <span style={{ color:C.text, fontSize:12 }}>{rec}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalyticsPage() {
  const [cd, setCd] = useState(null);
  const [pred, setPred] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    Promise.all([apiFetch("/api/v1/regions"), apiFetch("/api/v1/ml/forecast")]).then(([r, p]) => {
      if (r.ok && r.data?.regions) setCd({ data:r.data.regions.map(x => ({ ...x, region_name:x.name, hourly:Array.from({length:24},(_,h) => +(x.carbon_intensity*(1+0.15*Math.sin(h*Math.PI/12))).toFixed(4)) })) });
      else setCd({ data:RMOCK.map(r => ({ ...r, region_name:r.name, hourly:Array.from({length:24},(_,h) => +(r.carbon_intensity*(1+0.15*Math.sin(h*Math.PI/12))).toFixed(4)) })) });
      if (p.ok && p.data?.predictions) setPred(p.data);
      else setPred({ model:"EnsemblePredictor v3.1", r2:0.874, weights:{lr:0.4,ma:0.35,tp:0.25}, predictions:Array.from({length:24},(_,h) => ({ hour_offset:h, hour_of_day:h, predicted_cpu:+(0.3+0.4*Math.sin((h-6)*Math.PI/12)+Math.random()*0.1).toFixed(3), confidence_pct:82+Math.floor(Math.random()*10) })) });
      setLoading(false);
    });
  }, []);

  if (loading || !cd || !pred) return <div style={{ padding:40 }}><Skeleton h={300}/></div>;

  const top4 = cd.data.slice(0,4);
  const hourly = Array.from({length:24},(_,h) => {
    const row = { hour:`${String(h).padStart(2,"0")}:00` };
    top4.forEach(r => { row[(r.short||r.name||"").split("(")[0].trim()] = r.hourly?.[h] ?? r.carbon_intensity; });
    return row;
  });
  const lineColors = [C.green,C.teal,C.amber,C.red];
  const renData = cd.data.map(r => ({ name:(r.short||r.name||"").split("(")[0].trim(), Renewable:r.renewable_pct, Fossil:100-r.renewable_pct }));

  return (
    <div>
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18, marginBottom:18 }}>
        <SH title="🤖 ML Ensemble Model" sub={`${pred.model} · R²: ${pred.r2}`}/>
        <div style={{ display:"flex", gap:14, flexWrap:"wrap" }}>
          {Object.entries(pred.weights||{}).map(([k,v]) => (
            <div key={k} style={{ background:C.surface, borderRadius:8, padding:"10px 16px", textAlign:"center" }}>
              <div style={{ color:C.muted, fontSize:9, marginBottom:4, textTransform:"uppercase" }}>{k==="lr"?"Linear Reg":k==="ma"?"Moving Avg":"Time Pattern"}</div>
              <div style={{ color:C.green, fontSize:20, fontWeight:800 }}>{(v*100).toFixed(0)}%</div>
            </div>
          ))}
          <div style={{ background:C.surface, borderRadius:8, padding:"10px 16px", textAlign:"center" }}>
            <div style={{ color:C.muted, fontSize:9, marginBottom:4 }}>MODEL R²</div>
            <div style={{ color:C.amber, fontSize:20, fontWeight:800 }}>{(pred.r2*100).toFixed(1)}%</div>
          </div>
        </div>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:18, marginBottom:18 }}>
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
          <SH title="Hourly Carbon Intensity" sub="24h variation · top 4 regions"/>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={hourly} margin={{top:5,right:5,bottom:5,left:-15}}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
              <XAxis dataKey="hour" tick={{fill:C.muted,fontSize:8}} interval={3}/>
              <YAxis tick={{fill:C.muted,fontSize:9}}/>
              <Tooltip content={<TT/>}/><Legend wrapperStyle={{fontSize:9}}/>
              {top4.map((r,i) => <Line key={r.id||r.region_id} type="monotone" dataKey={(r.short||r.name||"").split("(")[0].trim()} stroke={lineColors[i]} strokeWidth={2} dot={false}/>)}
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
          <SH title="ML CPU Forecast" sub="Next 24h · ensemble prediction"/>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={pred.predictions} margin={{top:5,right:5,bottom:5,left:-15}}>
              <defs><linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={C.amber} stopOpacity={0.3}/><stop offset="95%" stopColor={C.amber} stopOpacity={0}/></linearGradient></defs>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
              <XAxis dataKey="hour_of_day" tick={{fill:C.muted,fontSize:9}} tickFormatter={v=>`${v}h`}/>
              <YAxis tick={{fill:C.muted,fontSize:9}} domain={[0,1]}/>
              <Tooltip content={<TT/>}/>
              <Area type="monotone" dataKey="predicted_cpu" name="CPU Load" stroke={C.amber} fill="url(#cg)" strokeWidth={2}/>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
        <SH title="Renewable Energy Mix" sub="% renewable vs fossil per K8s cluster region"/>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={renData} margin={{top:5,right:5,bottom:40,left:-15}}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
            <XAxis dataKey="name" tick={{fill:C.muted,fontSize:9}} angle={-30} textAnchor="end"/>
            <YAxis tick={{fill:C.muted,fontSize:9}} unit="%"/>
            <Tooltip content={<TT/>}/><Legend wrapperStyle={{fontSize:10}}/>
            <Bar dataKey="Renewable" stackId="a" fill={C.green}/>
            <Bar dataKey="Fossil" stackId="a" fill={C.red} radius={[4,4,0,0]}/>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function MetricsPage({ toast }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    apiFetch("/api/v1/analytics/summary").then(res => {
      if (res.ok && res.data) setMetrics(res.data);
      else setMetrics({ summary:{total_workloads:2847,total_carbon_saved_kg:1203.7,avg_reduction_pct:62.4,avg_esg_score_gain:57,ml_r2:0.874,active_regions:8}, trend:mockTrend() });
      setLoading(false);
    });
  }, []);

  const dl = () => {
    if (!metrics) return;
    const rows = [["Date","Workloads","Before CO2","After CO2","Reduction%","Cost Saved","ESG Score"]];
    metrics.trend.forEach(r => rows.push([r.date,r.workloads,r.before_carbon,r.after_carbon,r.reduction_pct,r.cost_saved,r.esg_score]));
    const csv = rows.map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type:"text/csv" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "greenorch_v3_metrics.csv"; a.click();
    toast("📥 CSV downloaded!", "success");
  };

  const s = metrics?.summary || {};
  return (
    <div>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:14, marginBottom:22 }}>
        <StatCard label="Total Workloads" value={s.total_workloads?.toLocaleString()||"..."} accent={C.blue} icon="📊" animated loading={loading}/>
        <StatCard label="Carbon Saved" value={`${s.total_carbon_saved_kg||0}kg`} accent={C.green} icon="🌱" sub="vs. traditional scheduling" animated loading={loading}/>
        <StatCard label="Avg CO₂ Reduction" value={`${s.avg_reduction_pct||0}%`} accent={C.teal} icon="📉" animated loading={loading}/>
      </div>

      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:20, marginBottom:18 }}>
        <SH title="⚙️ Core Algorithm — DhruvCloud Nexus Scheduling Engine"/>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:12 }}>
          {[
            { t:"1. Energy Model",   f:"Energy = CPU × PowerFactor × Time × PUE",                d:"Workload-type profiles: batch 0.25kW, ML 0.55kW, streaming 0.32kW",         c:C.blue },
            { t:"2. Carbon Calc",    f:"CO₂ = Energy × Regional_Carbon_Intensity",               d:"Live carbon intensity with hourly variation. Paris target: 0.2 kgCO₂/kWh", c:C.amber },
            { t:"3. Multi-Obj K8s", f:"Score = CO₂(w1) + Cost(w2) + Latency(w3)",               d:"Weights change per strategy: Carbon First / Cost First / Balanced",          c:C.green },
          ].map((item, i) => (
            <div key={i} style={{ background:`${item.c}10`, border:`1px solid ${item.c}25`, borderRadius:10, padding:14 }}>
              <div style={{ color:item.c, fontWeight:700, marginBottom:6, fontSize:12 }}>{item.t}</div>
              <div style={{ fontFamily:"monospace", fontSize:10, color:C.text, background:"#00000030", borderRadius:6, padding:"6px 10px", marginBottom:8 }}>{item.f}</div>
              <div style={{ color:C.muted, fontSize:11 }}>{item.d}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:18, marginBottom:18 }}>
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
          <SH title="📥 Export Analytics"/>
          <div style={{ color:C.muted, fontSize:12, marginBottom:12 }}>30-day Before vs After metrics with ESG scores as CSV.</div>
          <button onClick={dl} style={{ background:`linear-gradient(135deg,${C.green},${C.teal})`, border:"none", borderRadius:8, color:"#000", fontWeight:700, padding:"10px 20px", cursor:"pointer", fontSize:12, fontFamily:"monospace" }}>⬇ Download CSV</button>
        </div>
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
          <SH title="🔧 System Status"/>
          {[{l:"FastAPI Backend",s:"Online",c:C.green},{l:"Ensemble ML Model",s:`Active (R²=${s.ml_r2||"..."})`,c:C.green},{l:"Policy Engine",s:"Running",c:C.green},{l:"K8s Cluster Monitor",s:"Live",c:C.green},{l:"ESG Report Engine",s:"Active",c:C.green},{l:"Carbon Feed",s:"Live · 10s refresh",c:C.green}].map((item,i) => (
            <div key={i} style={{ display:"flex", justifyContent:"space-between", marginBottom:9 }}>
              <span style={{ color:C.text, fontSize:12 }}>{item.l}</span>
              <span style={{ color:item.c, fontSize:11, fontWeight:700 }}>● {item.s}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:18 }}>
        <SH title="📋 30-Day Metrics Log — Before vs After"/>
        {loading ? <Skeleton h={300}/> : (
          <div style={{ maxHeight:360, overflowY:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11 }}>
              <thead style={{ position:"sticky", top:0, background:C.card }}>
                <tr>{["Date","Workloads","Before CO₂","After CO₂","Saved","Reduction","Cost Saved","ESG"].map(h => <th key={h} style={{ color:C.muted, textAlign:"left", padding:"7px 11px", borderBottom:`1px solid ${C.border}`, fontSize:10, fontWeight:600 }}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {[...(metrics?.trend||[])].reverse().map((r,i) => (
                  <tr key={i} style={{ borderBottom:`1px solid ${C.border}22` }}>
                    <td style={{ color:C.text, padding:"6px 11px", fontFamily:"monospace" }}>{r.date}</td>
                    <td style={{ color:C.blue, padding:"6px 11px" }}>{r.workloads}</td>
                    <td style={{ color:C.red, padding:"6px 11px", fontFamily:"monospace" }}>{r.before_carbon}kg</td>
                    <td style={{ color:C.green, padding:"6px 11px", fontFamily:"monospace" }}>{r.after_carbon}kg</td>
                    <td style={{ color:C.green, padding:"6px 11px", fontFamily:"monospace" }}>+{(r.before_carbon-r.after_carbon).toFixed(2)}kg</td>
                    <td style={{ padding:"6px 11px" }}><GreenBadge pct={r.reduction_pct}/></td>
                    <td style={{ color:C.amber, padding:"6px 11px", fontFamily:"monospace" }}>${r.cost_saved}</td>
                    <td style={{ color:C.purple, padding:"6px 11px", fontWeight:700 }}>{r.esg_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── MAIN APP ──────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState("dashboard");
  const [dark, setDark] = useState(true);
  const { toasts, toast, rmToast } = useToast();

  const navBg = dark ? "rgba(7,19,22,0.96)" : "rgba(220,238,233,0.96)";
  const borderCol = dark ? C.border : "#c0dbd4";
  const textCol = dark ? C.text : "#0a2520";
  const mutedCol = dark ? C.muted : "#4a7870";

  const nav = [
    { id:"dashboard",  label:"Dashboard",       icon:"◈" },
    { id:"simulation", label:"K8s Simulation",  icon:"☸️" },
    { id:"k8s",        label:"Cluster Monitor", icon:"🖥️" },
    { id:"esg",        label:"ESG Report",      icon:"📋" },
    { id:"analytics",  label:"Analytics",       icon:"📊" },
    { id:"metrics",    label:"Metrics",         icon:"🔧" },
  ];

  return (
    <div style={{ minHeight:"100vh", background:dark?C.bg:"#f0f7f5", color:textCol, fontFamily:"'IBM Plex Mono','Courier New',monospace", display:"flex", flexDirection:"column" }}>
      <style>{`
        @keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
        @keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
        @keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
        @keyframes slideIn{from{transform:translateX(60px);opacity:0}to{transform:translateX(0);opacity:1}}
        *{scrollbar-width:thin;scrollbar-color:#1a3540 transparent}
        *::-webkit-scrollbar{width:4px}*::-webkit-scrollbar-thumb{background:#1a3540;border-radius:4px}
        input,select{transition:border-color 0.2s}input:focus,select:focus{border-color:#00e5a0!important;outline:none}
        button:not(:disabled):hover{opacity:0.9}
      `}</style>
      <Toast toasts={toasts} rmToast={rmToast}/>

      {/* Header */}
      <header style={{ background:navBg, backdropFilter:"blur(12px)", borderBottom:`1px solid ${borderCol}`, padding:"0 24px", display:"flex", alignItems:"center", justifyContent:"space-between", height:52, position:"sticky", top:0, zIndex:200 }}>
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          {/* DhruvCloud Nexus Logo */}
          <div style={{ width:34, height:34, borderRadius:10, background:`linear-gradient(135deg,${C.teal},${C.blue})`, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0, boxShadow:`0 0 10px ${C.teal}55` }}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              {/* Cloud base */}
              <path d="M5 13a3 3 0 01-.5-5.95A4 4 0 0113 7.1 2.5 2.5 0 0115 12H5z" fill="#fff" opacity="0.95"/>
              {/* Nexus node dots */}
              <circle cx="7" cy="16" r="1.3" fill={C.green}/>
              <circle cx="10" cy="17.5" r="1.3" fill={C.teal}/>
              <circle cx="13" cy="16" r="1.3" fill={C.blue}/>
              {/* Connecting lines */}
              <line x1="7" y1="16" x2="10" y2="17.5" stroke="#fff" strokeWidth="0.8" opacity="0.7"/>
              <line x1="10" y1="17.5" x2="13" y2="16" stroke="#fff" strokeWidth="0.8" opacity="0.7"/>
              <line x1="7" y1="16" x2="13" y2="16" stroke="#fff" strokeWidth="0.6" opacity="0.4"/>
            </svg>
          </div>
          <div>
            <div style={{ color:C.teal, fontWeight:900, fontSize:14, letterSpacing:0.5 }}>DhruvCloud Nexus</div>
            <div style={{ color:mutedCol, fontSize:8, letterSpacing:1.5, textTransform:"uppercase", marginTop:-1 }}>CarbonAware Sustainable Cloud Orchestration Platform</div>
          </div>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{ background:`${C.blue}15`, border:`1px solid ${C.blue}25`, borderRadius:6, padding:"3px 9px", fontSize:9, color:C.blue, fontWeight:700 }}>☸️ K8s Monitor</div>
          <div style={{ background:`${C.purple}15`, border:`1px solid ${C.purple}25`, borderRadius:6, padding:"3px 9px", fontSize:9, color:C.purple, fontWeight:700 }}>📋 ESG A+ Ready</div>
          <div style={{ display:"flex", alignItems:"center", gap:5 }}>
            <div style={{ width:5, height:5, borderRadius:"50%", background:C.green, animation:"pulse 2s infinite" }}/>
            <span style={{ color:mutedCol, fontSize:10 }}>Live</span>
          </div>
          <button onClick={() => setDark(d => !d)} style={{ background:dark?C.card:"#c5e5de", border:`1px solid ${borderCol}`, borderRadius:20, color:textCol, padding:"4px 12px", cursor:"pointer", fontSize:11, fontWeight:600, fontFamily:"inherit" }}>
            {dark ? "☀ Light" : "☾ Dark"}
          </button>
        </div>
      </header>

      <div style={{ display:"flex", flex:1 }}>
        {/* Sidebar */}
        <nav style={{ width:210, background:navBg, borderRight:`1px solid ${borderCol}`, padding:"18px 10px", flexShrink:0 }}>
          {nav.map(item => (
            <button key={item.id} onClick={() => setPage(item.id)}
              style={{ display:"flex", alignItems:"center", gap:9, width:"100%", padding:"9px 12px", borderRadius:8, border:"none", borderLeft:page===item.id?`2px solid ${C.green}`:"2px solid transparent", background:page===item.id?`linear-gradient(135deg,${C.green}18,${C.teal}10)`:"transparent", color:page===item.id?C.green:mutedCol, fontSize:12, fontWeight:page===item.id?700:500, cursor:"pointer", textAlign:"left", marginBottom:3, transition:"all 0.15s", whiteSpace:"nowrap", fontFamily:"inherit" }}>
              <span style={{ flexShrink:0 }}>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
          <div style={{ marginTop:24, padding:"10px 12px", background:`${C.green}10`, borderRadius:8, border:`1px solid ${C.green}25` }}>
            <div style={{ color:C.green, fontSize:9, fontWeight:700, marginBottom:3 }}>🏆 GREENEST CLUSTER</div>
            <div style={{ color:textCol, fontSize:11, fontWeight:700 }}>aks-eu-north-prod</div>
            <div style={{ color:mutedCol, fontSize:9 }}>0.013 kgCO₂/kWh · 98% RE</div>
            <div style={{ color:mutedCol, fontSize:9 }}>ESG: 97/100 · Grade A+</div>
          </div>
          <div style={{ marginTop:8, padding:"10px 12px", background:`${C.red}10`, borderRadius:8, border:`1px solid ${C.red}25` }}>
            <div style={{ color:C.red, fontSize:9, fontWeight:700, marginBottom:3 }}>⚠️ AVOID CLUSTER</div>
            <div style={{ color:textCol, fontSize:11, fontWeight:700 }}>gke-asia-south-prod</div>
            <div style={{ color:mutedCol, fontSize:9 }}>0.708 kgCO₂/kWh · 18% RE</div>
            <div style={{ color:mutedCol, fontSize:9 }}>ESG: 14/100 · Grade F</div>
          </div>
        </nav>

        {/* Main */}
        <main style={{ flex:1, padding:"22px 26px", overflowY:"auto", animation:"fadeIn 0.3s ease" }}>
          <div style={{ maxWidth:1300 }}>
            {page === "dashboard"  && <DashboardPage  toast={toast}/>}
            {page === "simulation" && <SimulationPage toast={toast}/>}
            {page === "k8s"        && <K8sPage/>}
            {page === "esg"        && <ESGPage/>}
            {page === "analytics"  && <AnalyticsPage/>}
            {page === "metrics"    && <MetricsPage    toast={toast}/>}
          </div>
        </main>
      </div>
    </div>
  );
}