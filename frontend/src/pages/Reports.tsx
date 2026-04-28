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
      <Icon className={`w-5 h-5 ${accent ? "text-white" : "text-slate-600"}`} />
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
        <tr className="bg-slate-800 text-left">
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
        fetch(`/api/reports/executive?time_range=${range}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`/api/reports/technical?time_range=${range}`, { headers: { Authorization: `Bearer ${token}` } }),
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

  const downloadPdf = async () => {
    const payload = tab === "executive" ? execData : techData;
    if (!payload) return;
    const endpoint = tab === "executive" ? "executive" : "technical";
    try {
      const res = await fetch(`/api/reports/${endpoint}/pdf?time_range=${range}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ range }),
      });
      if (!res.ok) throw new Error(`PDF error: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rhinometric-${endpoint}-${range}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(`PDF download failed: ${e.message}`);
    }
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
                tab === t ? "bg-slate-800 text-white" : "text-slate-600 hover:bg-slate-50"
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
                range === r ? "bg-slate-700 text-white" : "text-slate-600 hover:bg-slate-50"
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
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
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
            Export PDF
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
