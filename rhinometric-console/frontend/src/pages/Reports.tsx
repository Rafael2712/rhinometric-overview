import { useState } from "react";
import { useAuthStore } from '../lib/auth/store';
import { Download, RefreshCw, AlertTriangle, CheckCircle, XCircle, Clock, Activity, Shield, TrendingUp} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────
interface KpiData {
  total_incidents: number;
  mttr_human: string;
  uptime: number;
  total_alerts: number;
  active_alerts: number;
}

interface GroupedIncident {
  service: string;
  incident_count: number;
  severity: string;
  avg_duration: string;
  resolution_rate: string;
  last_occurrence: string | null;
  ai_summary?: string;
}

interface ExecutiveReport {
  status: string;
  summary: string;
  kpis: KpiData;
  top_incidents: GroupedIncident[];
  risks: string[];
  recommendations: string[];
  generated_at: string;
  time_range: string;
}

interface IncidentRow {
  entity_name: string;
  severity: string;
  status: string;
  started_at: string;
  resolved_at?: string;
  duration: string;
  summary?: string;
}

interface AlertGroup {
  entity_name: string;
  alert_name: string;
  severity: string;
  count: number;
  last_status: string;
  last_seen?: string;
}

interface AnomalyRow {
  entity_name: string;
  metric_name: string;
  severity: string;
  status: string;
  occurrence_count?: number;
}

interface TimelineEvent {
  timestamp: string;
  type: string;
  entity: string;
  severity?: string;
}

interface TechnicalReport {
  incidents: IncidentRow[];
  grouped_incidents: GroupedIncident[];
  alerts: AlertGroup[];
  total_alert_count: number;
  alert_volume_note?: string;
  anomalies: AnomalyRow[];
  timeline: TimelineEvent[];
  generated_at: string;
  time_range: string;
}

// ─── UI atoms ─────────────────────────────────────────────────────────────────
const SEV_MAP: Record<string, { bg: string; text: string; dot: string }> = {
  critical: { bg: "bg-red-50  border border-red-200",  text: "text-red-700",    dot: "bg-red-500"    },
  warning:  { bg: "bg-amber-50 border border-amber-200",text: "text-amber-700",  dot: "bg-amber-400"  },
  info:     { bg: "bg-sky-50  border border-sky-200",  text: "text-sky-700",    dot: "bg-sky-400"    },
  ok:       { bg: "bg-emerald-50 border border-emerald-200", text: "text-emerald-700", dot: "bg-emerald-400" },
};
const sevKey = (s?: string) => (s?.toLowerCase() || "info") as keyof typeof SEV_MAP;

const SevBadge = ({ sev }: { sev?: string }) => {
  const k = sevKey(sev);
  const c = SEV_MAP[k] ?? SEV_MAP["info"];
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${c.bg} ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {sev ?? "Unknown"}
    </span>
  );
};

const StatusChip = ({ status }: { status?: string }) => {
  const s = (status || "").toLowerCase();
  const cls = s.includes("operational")
    ? "bg-emerald-100 text-emerald-800"
    : s.includes("degraded")
    ? "bg-amber-100 text-amber-800"
    : s.includes("critical") || s.includes("down")
    ? "bg-red-100 text-red-800"
    : "bg-slate-100 text-slate-700";
  return <span className={`px-2 py-0.5 rounded text-xs font-semibold ${cls}`}>{status || "Unknown"}</span>;
};

const fmtTime = (iso?: string | null): string => {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-GB", { dateStyle: "short", timeStyle: "short", hour12: false });
  } catch {
    return iso;
  }
};

// ─── KPI card ─────────────────────────────────────────────────────────────────
type IconComp = React.ElementType;
const KpiCard = ({ label, value, icon: Icon, accent }: { label: string; value: string | number; icon: IconComp; accent?: string }) => (
  <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3 shadow-sm">
    <div className={`p-2 rounded-lg ${accent ?? "bg-slate-100"}`}>
      <Icon className={`w-5 h-5 ${accent ? "text-gray-900" : "text-slate-600"}`} />
    </div>
    <div>
      <p className="text-xs text-slate-500 font-medium">{label}</p>
      <p className="text-xl font-bold text-slate-800 leading-tight">{value}</p>
    </div>
  </div>
);

// ─── Section card ─────────────────────────────────────────────────────────────
const SectionCard = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
    <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
      <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">{title}</h3>
    </div>
    <div className="p-5">{children}</div>
  </div>
);

// ─── Table ────────────────────────────────────────────────────────────────────
const Tbl = ({ headers, rows }: { headers: string[]; rows: (string | React.ReactNode)[][] }) => (
  <div className="overflow-auto rounded-lg border border-slate-200">
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-50 text-left">
          {headers.map(h => (
            <th key={h} className="px-3 py-2.5 text-xs font-semibold text-slate-300 whitespace-nowrap">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-slate-50"}>
            {row.map((cell, j) => (
              <td key={j} className="px-3 py-2 text-slate-700 text-xs align-top">{cell}</td>
            ))}
          </tr>
        ))}
        {rows.length === 0 && (
          <tr><td colSpan={headers.length} className="px-3 py-6 text-center text-slate-400 text-xs">No data available for this period.</td></tr>
        )}
      </tbody>
    </table>
  </div>
);

// ─── Empty state ──────────────────────────────────────────────────────────────
const Empty = ({ msg }: { msg: string }) => (
  <div className="flex flex-col items-center justify-center py-14 text-slate-400 gap-2">
    <Activity className="w-8 h-8 opacity-40" />
    <p className="text-sm">{msg}</p>
  </div>
);

// ─── PDF helpers (pure HTML + print) ─────────────────────────────────────────
const PDF_CSS = `
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:'Segoe UI',Helvetica,Arial,sans-serif;background:#fff;color:#111827;font-size:13px;line-height:1.5;}
  @page{size:A4;margin:16mm 16mm 16mm 16mm;}
  @media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact;}.no-print{display:none!important;}}

  /* Layout */
  .page{max-width:760px;margin:0 auto;padding:24px;}
  .header{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:16px;border-bottom:2px solid #e5e7eb;margin-bottom:24px;}
  .logo{display:flex;align-items:center;gap:10px;}
  .logo-mark{width:34px;height:34px;background:#111827;border-radius:8px;display:flex;align-items:center;justify-content:center;}
  .logo-mark svg{width:20px;height:20px;fill:none;stroke:#fff;stroke-width:2;}
  .logo-name{font-size:17px;font-weight:700;color:#111827;letter-spacing:-0.3px;}
  .logo-sub{font-size:11px;color:#6b7280;margin-top:1px;}
  .header-right{text-align:right;}
  .report-title{font-size:20px;font-weight:700;color:#111827;}
  .report-meta{font-size:11px;color:#6b7280;margin-top:3px;}

  /* Status badge */
  .badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;border:1px solid;}
  .badge-healthy{background:#f0fdf4;color:#166534;border-color:#bbf7d0;}
  .badge-degraded{background:#fffbeb;color:#92400e;border-color:#fde68a;}
  .badge-critical{background:#fef2f2;color:#991b1b;border-color:#fecaca;}
  .badge-dot{width:6px;height:6px;border-radius:50%;}
  .badge-healthy .badge-dot{background:#22c55e;}
  .badge-degraded .badge-dot{background:#f59e0b;}
  .badge-critical .badge-dot{background:#ef4444;}

  /* Summary block */
  .summary-block{background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:14px 16px;margin-bottom:20px;display:flex;align-items:flex-start;gap:12px;}
  .summary-text{font-size:13px;color:#374151;line-height:1.6;}

  /* Section */
  .section{margin-bottom:22px;}
  .section-title{font-size:10px;font-weight:700;color:#6b7280;letter-spacing:1px;text-transform:uppercase;padding-bottom:6px;border-bottom:1px solid #e5e7eb;margin-bottom:12px;}
  h2.section-title{font-size:12px;font-weight:700;color:#374151;letter-spacing:0.5px;}

  /* KPI grid */
  .kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:22px;}
  .kpi-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px 14px;box-shadow:0 1px 3px rgba(0,0,0,.05);}
  .kpi-label{font-size:10px;color:#9ca3af;font-weight:600;letter-spacing:.4px;text-transform:uppercase;margin-bottom:4px;}
  .kpi-value{font-size:20px;font-weight:700;color:#111827;line-height:1.2;}

  /* Bullet lists */
  .bullet-list{list-style:none;display:flex;flex-direction:column;gap:6px;}
  .bullet-list li{display:flex;align-items:flex-start;gap:8px;font-size:12px;color:#374151;}
  .bullet-icon{flex-shrink:0;width:16px;height:16px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;margin-top:1px;}
  .bullet-icon.warn{background:#fef3c7;color:#92400e;}
  .bullet-icon.ok{background:#d1fae5;color:#065f46;}

  /* Two-col layout */
  .two-col{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:22px;}
  .col-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:14px 16px;}

  /* Tables */
  table{width:100%;border-collapse:collapse;font-size:11px;}
  thead tr{background:#f9fafb;}
  th{padding:7px 10px;text-align:left;font-size:10px;font-weight:600;color:#9ca3af;letter-spacing:.4px;text-transform:uppercase;border-bottom:2px solid #e5e7eb;}
  td{padding:7px 10px;border-bottom:1px solid #f3f4f6;color:#374151;vertical-align:top;}
  tr:last-child td{border-bottom:none;}
  tr:nth-child(even) td{background:#fafafa;}
  .tbl-service{font-weight:600;color:#111827;}
  .tbl-number{font-weight:700;color:#111827;}
  .tbl-muted{color:#9ca3af;}

  /* Sev badges */
  .sev{display:inline-flex;align-items:center;gap:4px;padding:2px 7px;border-radius:10px;font-size:10px;font-weight:600;}
  .sev-critical{background:#fef2f2;color:#991b1b;border:1px solid #fecaca;}
  .sev-warning{background:#fffbeb;color:#92400e;border:1px solid #fde68a;}
  .sev-info{background:#eff6ff;color:#1e40af;border:1px solid #bfdbfe;}
  .sev-ok{background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;}
  .sev-dot{width:5px;height:5px;border-radius:50%;}
  .sev-critical .sev-dot{background:#ef4444;}
  .sev-warning .sev-dot{background:#f59e0b;}
  .sev-info .sev-dot{background:#3b82f6;}
  .sev-ok .sev-dot{background:#22c55e;}

  /* Status chip */
  .chip{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;}
  .chip-green{background:#d1fae5;color:#065f46;}
  .chip-amber{background:#fef3c7;color:#92400e;}
  .chip-red{background:#fef2f2;color:#991b1b;}
  .chip-gray{background:#f3f4f6;color:#374151;}

  /* Timeline */
  .timeline{display:flex;flex-direction:column;gap:0;}
  .tl-row{display:flex;align-items:flex-start;gap:10px;padding:6px 0;border-bottom:1px solid #f3f4f6;}
  .tl-time{font-size:10px;color:#9ca3af;min-width:100px;padding-top:1px;}
  .tl-dot{width:8px;height:8px;border-radius:50%;background:#d1d5db;flex-shrink:0;margin-top:3px;}
  .tl-content{flex:1;font-size:11px;color:#374151;}
  .tl-entity{font-weight:600;color:#111827;}

  /* Page break */
  .page-break{page-break-before:always;}
  .table-wrap{border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;}
`;

const formatDt = (iso?: string | null) => {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString("en-GB", { dateStyle: "short", timeStyle: "short", hour12: false }); }
  catch { return iso; }
};

const sevHtml = (s?: string) => {
  const k = (s || "").toLowerCase();
  const cls = k === "critical" ? "sev-critical" : k === "warning" ? "sev-warning" : k === "ok" || k === "resolved" ? "sev-ok" : "sev-info";
  return `<span class="sev ${cls}"><span class="sev-dot"></span>${s || "—"}</span>`;
};

const chipHtml = (s?: string) => {
  const k = (s || "").toLowerCase();
  const cls = k.includes("operational") || k.includes("resolved") ? "chip-green"
    : k.includes("degraded") ? "chip-amber"
    : k.includes("down") || k.includes("critical") || k.includes("open") ? "chip-red"
    : "chip-gray";
  return `<span class="chip ${cls}">${s || "—"}</span>`;
};

const badgeHtml = (status: string) => {
  const k = (status || "").toLowerCase();
  const cls = k.includes("operational") || k.includes("healthy") ? "badge-healthy"
    : k.includes("degraded") ? "badge-degraded"
    : "badge-critical";
  return `<span class="badge ${cls}"><span class="badge-dot"></span>${status}</span>`;
};

const logoSvg = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`;

function openPrint(html: string) {
  const w = window.open("", "_blank");
  if (!w) { alert("Please allow popups to export PDF."); return; }
  w.document.write(html);
  w.document.close();
  setTimeout(() => { w.focus(); w.print(); }, 600);
}

function printExec(data: ExecutiveReport, range: string) {
  const kpiHtml = `
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Incidents</div>
        <div class="kpi-value">${data.kpis.total_incidents}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Total Alerts</div>
        <div class="kpi-value">${data.kpis.total_alerts}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Platform Uptime</div>
        <div class="kpi-value">${data.kpis.uptime}%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">MTTR</div>
        <div class="kpi-value" style="font-size:15px;padding-top:3px;">${data.kpis.mttr_human}</div>
      </div>
    </div>`;

  const incRows = data.top_incidents.map(g => `
    <tr>
      <td class="tbl-service">${g.service}</td>
      <td class="tbl-number">${g.incident_count}</td>
      <td>${sevHtml(g.severity)}</td>
      <td>${g.avg_duration}</td>
      <td>${g.resolution_rate}</td>
      <td class="tbl-muted">${formatDt(g.last_occurrence)}</td>
    </tr>`).join("") || `<tr><td colspan="6" style="text-align:center;color:#9ca3af;padding:14px;">No incidents recorded in this period.</td></tr>`;

  const risksHtml = (data.risks || []).slice(0, 3).map(r =>
    `<li><span class="bullet-icon warn">!</span><span>${r}</span></li>`).join("") || "<li><span class='tbl-muted'>No risks identified.</span></li>";

  const recsHtml = (data.recommendations || []).slice(0, 3).map(r =>
    `<li><span class="bullet-icon ok">✓</span><span>${r}</span></li>`).join("") || "<li><span class='tbl-muted'>No recommendations at this time.</span></li>";

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Rhinometric Executive Report</title>
  <style>${PDF_CSS}</style></head><body><div class="page">

  <div class="header">
    <div class="logo">
      <div class="logo-mark">${logoSvg}</div>
      <div>
        <div class="logo-name">Rhinometric</div>
        <div class="logo-sub">Observability Platform</div>
      </div>
    </div>
    <div class="header-right">
      <div class="report-title">Executive Report</div>
      <div class="report-meta">Time range: ${range} &nbsp;|&nbsp; Generated: ${formatDt(data.generated_at)}</div>
      <div style="margin-top:6px;">${badgeHtml(data.status)}</div>
    </div>
  </div>

  <!-- Summary -->
  <div class="section">
    <div class="section-title">Executive Summary</div>
    <div class="summary-block">
      <div class="summary-text">${data.summary || "No summary available."}</div>
    </div>
  </div>

  <!-- KPIs -->
  <div class="section">
    <div class="section-title">Key Performance Indicators</div>
    ${kpiHtml}
  </div>

  <!-- Top Affected Services -->
  <div class="section">
    <div class="section-title">Top Affected Services</div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Service</th><th>Incidents</th><th>Severity</th>
          <th>Avg Duration</th><th>Resolution Rate</th><th>Last Occurrence</th>
        </tr></thead>
        <tbody>${incRows}</tbody>
      </table>
    </div>
  </div>

  <!-- Risks + Recommendations -->
  <div class="two-col">
    <div class="col-card">
      <div class="section-title" style="margin-bottom:10px;">Identified Risks</div>
      <ul class="bullet-list">${risksHtml}</ul>
    </div>
    <div class="col-card">
      <div class="section-title" style="margin-bottom:10px;">Recommendations</div>
      <ul class="bullet-list">${recsHtml}</ul>
    </div>
  </div>

  <div style="margin-top:32px;padding-top:12px;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;font-size:10px;color:#9ca3af;">
    <span>Rhinometric &mdash; Confidential</span>
    <span>rhinometric.com</span>
  </div>
  </div></body></html>`;

  openPrint(html);
}

function printTech(data: TechnicalReport, range: string) {
  const incGroupRows = (data.grouped_incidents || []).map(g => `
    <tr>
      <td class="tbl-service">${g.service}</td>
      <td class="tbl-number">${g.incident_count}</td>
      <td>${sevHtml(g.severity)}</td>
      <td>${g.avg_duration}</td>
      <td>${g.resolution_rate}</td>
    </tr>`).join("") || `<tr><td colspan="5" style="text-align:center;color:#9ca3af;padding:14px;">No incidents recorded.</td></tr>`;

  const incDetailRows = (data.incidents || []).slice(0, 40).map(i => `
    <tr>
      <td class="tbl-service">${i.entity_name}</td>
      <td>${sevHtml(i.severity)}</td>
      <td>${chipHtml(i.status)}</td>
      <td class="tbl-muted">${formatDt(i.started_at)}</td>
      <td>${i.duration}</td>
    </tr>`).join("") || `<tr><td colspan="5" style="text-align:center;color:#9ca3af;padding:14px;">No incident detail available.</td></tr>`;

  const alertRows = (data.alerts || []).map(a => `
    <tr>
      <td class="tbl-service">${a.entity_name}</td>
      <td>${a.alert_name}</td>
      <td>${sevHtml(a.severity)}</td>
      <td class="tbl-number">${a.count}</td>
      <td>${chipHtml(a.last_status)}</td>
      <td class="tbl-muted">${formatDt(a.last_seen)}</td>
    </tr>`).join("") || `<tr><td colspan="6" style="text-align:center;color:#9ca3af;padding:14px;">No alerts recorded.</td></tr>`;

  const tlRows = (data.timeline || []).slice(0, 60).map(t => `
    <div class="tl-row">
      <div class="tl-time">${formatDt(t.timestamp)}</div>
      <div class="tl-dot"></div>
      <div class="tl-content">
        <span style="margin-right:6px;">${sevHtml(t.severity)}</span>
        <span class="tl-entity">${t.entity}</span>
        <span style="color:#6b7280;margin-left:6px;">${(t.type || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</span>
      </div>
    </div>`).join("") || `<p style="color:#9ca3af;font-size:11px;padding:8px 0;">No timeline events.</p>`;

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Rhinometric Technical Report</title>
  <style>${PDF_CSS}</style></head><body><div class="page">

  <div class="header">
    <div class="logo">
      <div class="logo-mark">${logoSvg}</div>
      <div>
        <div class="logo-name">Rhinometric</div>
        <div class="logo-sub">Observability Platform</div>
      </div>
    </div>
    <div class="header-right">
      <div class="report-title">Technical Report</div>
      <div class="report-meta">Time range: ${range} &nbsp;|&nbsp; Generated: ${formatDt(data.generated_at)}</div>
    </div>
  </div>

  <!-- Incidents by Service -->
  <div class="section">
    <div class="section-title">Incidents by Service</div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Service</th><th>Count</th><th>Severity</th><th>Avg Duration</th><th>Resolution Rate</th></tr></thead>
        <tbody>${incGroupRows}</tbody>
      </table>
    </div>
  </div>

  <!-- Incident Detail Log -->
  <div class="section">
    <div class="section-title">Incident Detail Log${data.incidents.length > 40 ? ` — showing 40 of ${data.incidents.length}` : ""}</div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Service</th><th>Severity</th><th>Status</th><th>Started</th><th>Duration</th></tr></thead>
        <tbody>${incDetailRows}</tbody>
      </table>
    </div>
  </div>

  <!-- Alert Groups -->
  <div class="section page-break">
    <div class="section-title">Alert Groups${data.total_alert_count > 0 ? ` — ${data.total_alert_count.toLocaleString()} total` : ""}</div>
    ${data.alert_volume_note ? `<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:8px 12px;margin-bottom:10px;font-size:11px;color:#92400e;">${data.alert_volume_note}</div>` : ""}
    <div class="table-wrap">
      <table>
        <thead><tr><th>Service</th><th>Alert</th><th>Severity</th><th>Occurrences</th><th>Last Status</th><th>Last Seen</th></tr></thead>
        <tbody>${alertRows}</tbody>
      </table>
    </div>
  </div>

  <!-- Event Timeline -->
  <div class="section">
    <div class="section-title">Event Timeline${data.timeline.length > 0 ? ` — ${data.timeline.length} events` : ""}</div>
    <div class="timeline">${tlRows}</div>
  </div>

  <div style="margin-top:32px;padding-top:12px;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;font-size:10px;color:#9ca3af;">
    <span>Rhinometric &mdash; Confidential</span>
    <span>rhinometric.com</span>
  </div>
  </div></body></html>`;

  openPrint(html);
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function Reports() {
  const token = useAuthStore((s) => s.token);
  const [tab, setTab] = useState<"executive" | "technical">("executive");
  const [range, setRange] = useState("24h");
  const [loading, setLoading] = useState(false);
  const [execData, setExecData] = useState<ExecutiveReport | null>(null);
  const [techData, setTechData] = useState<TechnicalReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const [execRes, techRes] = await Promise.all([
        fetch(`/api/reports/executive?range=${range}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`/api/reports/technical?range=${range}`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (!execRes.ok) throw new Error(`Executive report: ${execRes.status}`);
      if (!techRes.ok) throw new Error(`Technical report: ${techRes.status}`);
      setExecData(await execRes.json());
      setTechData(await techRes.json());
    } catch (e: any) {
      setError(e.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  // ─── Client-side HTML → print/PDF renderer ─────────────────────────────────
  const downloadPdf = () => {
    if (tab === "executive" && execData) { printExec(execData, range); }
    else if (tab === "technical" && techData) { printTech(techData, range); }
  };

  const hasData = tab === "executive" ? !!execData : !!techData;

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Observability Reports</h1>
        <p className="text-sm text-slate-500 mt-0.5">Infrastructure health summary — production data only</p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        {/* Tab toggle */}
        <div className="flex rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
          {(["executive", "technical"] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                tab === t ? "bg-gray-50 text-gray-900" : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              {t === "executive" ? "Executive" : "Technical"}
            </button>
          ))}
        </div>

        {/* Range */}
        <div className="flex rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
          {["24h", "7d", "30d"].map(r => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-3 py-2 text-sm font-medium transition-colors ${
                range === r ? "bg-gray-100 text-gray-900" : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {/* Generate */}
        <button
          onClick={generate}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-50 hover:bg-gray-100 disabled:opacity-50 text-gray-900 text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          {loading ? "Generating…" : "Generate"}
        </button>

        {/* Download PDF */}
        {hasData && (
          <button
            onClick={downloadPdf}
            className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-lg border border-slate-200 shadow-sm transition-colors"
          >
            <Download className="w-4 h-4" />
            Export / Print PDF
          </button>
        )}

        {/* Status */}
        {execData && (
          <div className="ml-auto flex items-center gap-2">
            <StatusChip status={execData.status} />
            <span className="text-xs text-slate-400">Generated {fmtTime(execData.generated_at)}</span>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
          <XCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Empty state */}
      {!hasData && !loading && !error && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
          <Empty msg="Click Generate to load the report." />
        </div>
      )}

      {/* ─── Executive tab ─────────────────────────────────────────────────── */}
      {tab === "executive" && execData && (
        <div className="space-y-5">
          {/* Summary */}
          <SectionCard title="Executive Summary">
            <p className="text-sm text-slate-700 leading-relaxed">{execData.summary}</p>
          </SectionCard>

          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Total Incidents"  value={execData.kpis.total_incidents} icon={AlertTriangle} accent="bg-red-500" />
            <KpiCard label="MTTR"             value={execData.kpis.mttr_human}       icon={Clock}         accent="bg-slate-600" />
            <KpiCard label="Platform Uptime"  value={`${execData.kpis.uptime}%`}     icon={TrendingUp}    accent="bg-emerald-500" />
            <KpiCard label="Active Alerts"    value={execData.kpis.active_alerts}    icon={Shield}        accent="bg-amber-500" />
          </div>

          {/* Top affected services */}
          <SectionCard title="Top Affected Services">
            {execData.top_incidents.length > 0 ? (
              <Tbl
                headers={["Service", "Incidents", "Severity", "Avg Duration", "Resolution Rate", "Last Occurrence"]}
                rows={execData.top_incidents.map(g => [
                  <span className="font-medium text-slate-800">{g.service}</span>,
                  <span className="font-semibold">{g.incident_count}</span>,
                  <SevBadge sev={g.severity} />,
                  g.avg_duration,
                  g.resolution_rate,
                  fmtTime(g.last_occurrence),
                ])}
              />
            ) : (
              <p className="text-sm text-slate-400">No incidents recorded in this period.</p>
            )}
          </SectionCard>

          {/* Risks + Recommendations side-by-side */}
          <div className="grid md:grid-cols-2 gap-5">
            <SectionCard title="Identified Risks">
              <ul className="space-y-2">
                {execData.risks.map((r, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-700">
                    <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                    {r}
                  </li>
                ))}
              </ul>
            </SectionCard>
            <SectionCard title="Recommendations">
              <ul className="space-y-2">
                {execData.recommendations.map((r, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-700">
                    <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    {r}
                  </li>
                ))}
              </ul>
            </SectionCard>
          </div>
        </div>
      )}

      {/* ─── Technical tab ─────────────────────────────────────────────────── */}
      {tab === "technical" && techData && (
        <div className="space-y-5">
          {/* Grouped incidents */}
          <SectionCard title="Incidents by Service">
            <Tbl
              headers={["Service", "Count", "Severity", "Avg Duration", "Resolution Rate"]}
              rows={(techData.grouped_incidents || []).map(g => [
                <span className="font-medium text-slate-800">{g.service}</span>,
                <span className="font-semibold">{g.incident_count}</span>,
                <SevBadge sev={g.severity} />,
                g.avg_duration,
                g.resolution_rate,
              ])}
            />
          </SectionCard>

          {/* Incident detail */}
          <SectionCard title="Incident Detail Log">
            {techData.incidents.length > 30 && (
              <p className="text-xs text-slate-400 mb-2">Showing first 30 of {techData.incidents.length} incidents.</p>
            )}
            <Tbl
              headers={["Service", "Severity", "Status", "Started", "Duration"]}
              rows={techData.incidents.slice(0, 30).map(i => [
                i.entity_name,
                <SevBadge sev={i.severity} />,
                <StatusChip status={i.status} />,
                fmtTime(i.started_at),
                i.duration,
              ])}
            />
          </SectionCard>

          {/* Alert volume notice */}
          {techData.alert_volume_note && (
            <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 rounded-lg">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {techData.alert_volume_note}
            </div>
          )}

          {/* Alert groups */}
          <SectionCard title={`Alert Groups ${techData.total_alert_count > 0 ? `— ${techData.total_alert_count.toLocaleString()} total` : ""}`}>
            <Tbl
              headers={["Service", "Alert", "Severity", "Occurrences", "Last Status", "Last Seen"]}
              rows={(techData.alerts || []).map(a => [
                a.entity_name,
                a.alert_name,
                <SevBadge sev={a.severity} />,
                <span className="font-semibold">{a.count}</span>,
                <StatusChip status={a.last_status} />,
                fmtTime(a.last_seen),
              ])}
            />
          </SectionCard>

          {/* Anomalies */}
          <SectionCard title="Anomalies">
            {techData.anomalies.length > 0 ? (
              <Tbl
                headers={["Service", "Metric", "Severity", "Status", "Occurrences"]}
                rows={techData.anomalies.map(a => [
                  a.entity_name,
                  a.metric_name,
                  <SevBadge sev={a.severity} />,
                  <StatusChip status={a.status} />,
                  a.occurrence_count ?? "—",
                ])}
              />
            ) : (
              <p className="text-sm text-slate-400">No anomalies detected in this period.</p>
            )}
          </SectionCard>

          {/* Timeline */}
          <SectionCard title={`Event Timeline ${techData.timeline.length > 0 ? `— ${techData.timeline.length} events` : ""}`}>
            {techData.timeline.length > 0 ? (
              <div className="max-h-72 overflow-y-auto">
                <Tbl
                  headers={["Time", "Event", "Service", "Severity"]}
                  rows={techData.timeline.slice(0, 50).map(t => [
                    fmtTime(t.timestamp),
                    (t.type || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
                    t.entity,
                    <SevBadge sev={t.severity} />,
                  ])}
                />
              </div>
            ) : (
              <p className="text-sm text-slate-400">No timeline events to display.</p>
            )}
          </SectionCard>
        </div>
      )}
    </div>
  );
}
export { Reports as ReportsPage }
