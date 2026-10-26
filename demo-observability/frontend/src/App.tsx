import { useEffect, useMemo, useState } from "react";

type DashboardCard = { dashboard_id: string; service: string; name: string; description: string; metric_count: number };
type Metric = { id: string; label: string; unit: string; before: number; current: number; target: string; direction: "higher" | "lower"; points: number[]; outcome: "blocked" | "steady" | "improved" | "regressed" };
type Snapshot = { dashboard_id: string; name: string; description: string; service: string; state: string; incident?: { id: string; summary: string; severity: string; status: string; updated_at: string }; metrics: Metric[]; action: { status: string; verification: string }; observed_at: string; links: { incident: string; store: string } };

const titleCase = (value: string) => value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const formatValue = (value: number, unit: string) => `${value}${unit === "%" ? "%" : ` ${unit}`}`;

function MetricCard({ metric }: { metric: Metric }) {
  const peak = Math.max(...metric.points, 1);
  return <article className="metric-card">
    <div className="metric-heading"><div><span>{metric.label}</span><strong>{formatValue(metric.current, metric.unit)}</strong></div><span className={`metric-status ${metric.outcome}`}>{titleCase(metric.outcome)}</span></div>
    <div className="metric-chart" aria-label={`${metric.label} trend`} role="img">{metric.points.map((point, index) => <span key={`${metric.id}-${index}`} style={{ height: `${Math.max(10, point / peak * 100)}%` }} />)}</div>
    <div className="metric-footer"><span>Before {formatValue(metric.before, metric.unit)}</span><span>Target {metric.target}</span></div>
  </article>;
}

export function App() {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const incidentId = params.get("incident");
  const dashboardId = params.get("dashboard");
  const [dashboards, setDashboards] = useState<DashboardCard[]>([]);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/observability/dashboards")
      .then((response) => response.json() as Promise<{ dashboards: DashboardCard[] }>)
      .then((payload) => setDashboards(payload.dashboards))
      .catch(() => setError("The monitoring catalog is unavailable."));
  }, []);

  useEffect(() => {
    const path = incidentId
      ? `/api/observability/incidents/${encodeURIComponent(incidentId)}`
      : dashboardId
        ? `/api/observability/dashboards/${encodeURIComponent(dashboardId)}`
        : null;
    if (!path) return;
    fetch(path).then(async (response) => {
      if (!response.ok) throw new Error((await response.json().catch(() => ({})) as { detail?: string }).detail ?? "The monitoring view is unavailable.");
      return response.json() as Promise<Snapshot>;
    }).then(setSnapshot).catch((caught) => setError(caught instanceof Error ? caught.message : "The monitoring view is unavailable."));
  }, [dashboardId, incidentId]);

  return <main className="observability-shell">
    <header className="topbar"><div><p className="eyebrow">Demo observability</p><h1>Service monitoring</h1></div><nav><a href="http://localhost:8000">Incident console</a><a href="http://localhost:8003">Demo store</a></nav></header>
    {error && <div className="error-banner" role="alert">{error}</div>}
    <section className="intro"><div><p className="eyebrow">Local monitoring feasibility</p><h2>See what changed after the incident action.</h2><p>These read-only dashboards use the incident state and persisted action result to make service health changes visible without adding a monitoring dependency.</p></div><span className="scope-badge">Synthetic local data · read only</span></section>
    {!snapshot && <section className="dashboard-picker" aria-labelledby="dashboard-picker-title"><div><p className="eyebrow">Dashboard pages</p><h2 id="dashboard-picker-title">Choose a service view</h2></div><div className="dashboard-grid">{dashboards.map((dashboard) => <a className="dashboard-card" href={`/?dashboard=${dashboard.dashboard_id}`} key={dashboard.dashboard_id}><span>{dashboard.service}</span><strong>{dashboard.name}</strong><small>{dashboard.description}</small><em>{dashboard.metric_count} panels · Open view →</em></a>)}</div></section>}
    {snapshot && <>
      <section className="dashboard-heading"><div><div className="breadcrumb"><a href="/">Dashboards</a><span>/</span><span>{snapshot.service}</span></div><h2>{snapshot.name}</h2><p>{snapshot.description}</p>{snapshot.incident && <p className="incident-context"><strong>{snapshot.incident.summary}</strong><span>{snapshot.incident.severity} · {titleCase(snapshot.incident.status)}</span></p>}</div><div className={`overall-state ${snapshot.state}`}><span>Overall state</span><strong>{titleCase(snapshot.state)}</strong><small>Observed {new Date(snapshot.observed_at).toLocaleTimeString()}</small></div></section>
      <section className="metric-grid" aria-label={`${snapshot.service} metrics`}>{snapshot.metrics.map((metric) => <MetricCard metric={metric} key={metric.id} />)}</section>
      <section className="evidence-layout"><article className="change-panel"><div className="panel-heading"><div><p className="eyebrow">Before and after</p><h2>What changed</h2></div><span className={`metric-status ${snapshot.state === "healthy" ? "improved" : snapshot.state === "external_dependency" ? "blocked" : "steady"}`}>{snapshot.state === "healthy" ? "Fix reflected" : snapshot.state === "external_dependency" ? "Dependency blocked" : "Awaiting fix"}</span></div><div className="change-table"><div className="change-row change-header"><span>Signal</span><span>Before</span><span>Now</span><span>Outcome</span></div>{snapshot.metrics.map((metric) => <div className="change-row" key={metric.id}><strong>{metric.label}</strong><span>{formatValue(metric.before, metric.unit)}</span><span>{formatValue(metric.current, metric.unit)}</span><span className={`outcome-text ${metric.outcome}`}>{titleCase(metric.outcome)}</span></div>)}</div></article><aside className="action-panel"><p className="eyebrow">Verification thesis</p><h2>Monitoring follows the durable workflow</h2><p>{snapshot.action.verification}. This page is evidence for review, not a source of incident truth.</p><div className="action-state"><span>Action status</span><strong>{titleCase(snapshot.action.status)}</strong></div><div className="link-stack"><a className="primary-link" href={snapshot.links.incident}>Open incident remediation ↗</a><a href={snapshot.links.store}>Open demo store ↗</a></div></aside></section>
    </>}
  </main>;
}
