import { useEffect, useRef, useState } from "react";
import { activeAction, activePage } from "./incidentSelection";

type Incident = { id: string; service: string; severity: string; status: string; summary: string; alert_count: number; version: number; updated_at: string };
type TimelineEvent = { id: string; event_type: string; event_time: string };
type IncidentDetail = Incident & { timeline: TimelineEvent[] };
type Page = { id: string; status: string; responder: string; level: string; response_type: string | null; incident_version: number };
type Action = { id: string; status: string; action_type: string; target: string; scenario_id: string; incident_version: number };
type Evidence = { id: string; source_type: string; availability: string; observed_at: string; items: unknown[] };
type Finding = { id: string; category: string; statement: string; confidence: number; suggested_next_step: string; evidence_ids: string[]; uncertainty: string | null };
type Investigation = { status?: string; model_status: string; model_error?: string; findings: Finding[]; evidence: Evidence[] };
const scenarioServices: Record<string, string> = { deployment_regression: "payments-api", disk_pressure: "orders-worker", third_party_outage: "checkout-api" };

export function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<IncidentDetail | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [pages, setPages] = useState<Page[]>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [scenarioId, setScenarioId] = useState("deployment_regression");
  const [error, setError] = useState<string | null>(null);
  const [responseText, setResponseText] = useState("");
  const detailRequest = useRef(0);

  const getJson = <T,>(path: string) => fetch(path).then((response) => {
    if (!response.ok) throw new Error("request failed");
    return response.json() as Promise<T>;
  });

  const loadIncident = (id: string) => {
    const requestId = ++detailRequest.current;
    setSelectedId(id);
    return Promise.all([
    getJson<IncidentDetail>(`/api/v1/incidents/${id}`),
    getJson<Page[]>(`/api/v1/incidents/${id}/pages`),
    getJson<Action[]>(`/api/v1/incidents/${id}/actions`),
    getJson<Investigation>(`/api/v1/incidents/${id}/evidence`).catch(() => null),
  ]).then(([incident, pageItems, actionItems, investigationResult]) => {
      if (requestId === detailRequest.current) { setSelected(incident); setPages(pageItems); setActions(actionItems); setInvestigation(investigationResult); }
    })
    .catch(() => { if (requestId === detailRequest.current) setError("The incident detail is unavailable."); });
  };

  const loadIncidents = () => getJson<Incident[]>("/api/v1/incidents")
    .then((items) => { setIncidents(items); if (selectedId) loadIncident(selectedId); else if (items[0]) loadIncident(items[0].id); })
    .catch(() => setError("The incident list is unavailable."));

  useEffect(() => { loadIncidents(); const timer = window.setInterval(loadIncidents, 5000); return () => window.clearInterval(timer); }, [selectedId]);

  const post = (path: string, body?: object) => fetch(path, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined,
  }).then((response) => { if (!response.ok) throw new Error("request failed"); return response.json(); });

  const currentPage = activePage(pages);
  const scenarioMatchesIncident = Boolean(selected && scenarioServices[scenarioId] === selected.service);
  const currentAction = activeAction(actions, selected ? { scenarioId, target: selected.service } : undefined);
  const createPage = () => selected && post(`/api/v1/incidents/${selected.id}/page`, { responder: "primary-oncall", fallback_responder: "secondary-oncall", deadline_seconds: 300 }).then(() => loadIncident(selected.id)).catch(() => setError("The page could not be created."));
  const acknowledge = () => currentPage && selected && post(`/api/v1/pages/${currentPage.id}/respond`, { response_type: "acknowledge", response_text: "Investigating", expected_version: selected.version }).then(() => loadIncident(selected.id)).catch(() => setError("The page response failed."));
  const reply = () => currentPage && selected && responseText.trim() && post(`/api/v1/pages/${currentPage.id}/respond`, { response_type: "reply", response_text: responseText.trim(), expected_version: selected.version }).then(() => { setResponseText(""); return loadIncident(selected.id); }).catch(() => setError("The page response failed."));
  const actionTypes: Record<string, string | null> = { deployment_regression: "rollback", disk_pressure: "clear_disk", third_party_outage: null };
  const actionType = actionTypes[scenarioId];
  const investigationComplete = Boolean(investigation && (investigation.status === "completed" || investigation.findings.length > 0));
  const proposeAction = () => selected && investigationComplete && scenarioMatchesIncident && actionType && post(`/api/v1/incidents/${selected.id}/actions`, { scenario_id: scenarioId, action_type: actionType, target: selected.service, parameters: {}, idempotency_key: `ui-${selected.id}-${actionType}`, approval_seconds: 300 }).then(() => loadIncident(selected.id)).catch(() => setError("The action proposal failed."));
  const decideAction = (approved: boolean) => currentAction && selected && post(`/api/v1/actions/${currentAction.id}/decision`, { approved, responder: "primary-oncall", expected_version: selected.version }).then(() => loadIncident(selected.id)).catch(() => setError("The action decision failed."));
  const executeAction = () => currentAction && post(`/api/v1/actions/${currentAction.id}/execute`).then(() => selected && loadIncident(selected.id)).catch(() => setError("The action execution failed."));
  const verifyAction = () => currentAction && post(`/api/v1/actions/${currentAction.id}/verify`).then(() => selected && loadIncident(selected.id)).catch(() => setError("The action verification failed."));
  const reconcileAction = () => currentAction && post(`/api/v1/actions/${currentAction.id}/reconcile`).then(() => selected && loadIncident(selected.id)).catch(() => setError("The action reconciliation failed."));
  const investigate = () => selected && scenarioMatchesIncident && post(`/api/v1/incidents/${selected.id}/investigate`, { scenario_id: scenarioId }).then(() => loadIncident(selected.id)).catch(() => setError("The investigation could not be started."));

  return (
    <main>
      <header><p className="eyebrow">Incident console</p><h1>On-call assistant</h1><p className="muted">A durable view of alerts, decisions, and actions.</p></header>
      {error && <p role="alert">{error}</p>}
      <section className="layout" aria-label="Incidents">
        <div className="panel"><h2>Incidents</h2>{incidents.length === 0 ? <p className="muted">No incidents yet.</p> : incidents.map((incident) => (
          <button className={`incident ${selectedId === incident.id ? "selected" : ""}`} key={incident.id} onClick={() => loadIncident(incident.id)}>
            <span><strong>{incident.service}</strong><small>{incident.summary}</small></span><span className="badge">{incident.status}</span>
          </button>
        ))}</div>
        <div className="panel"><h2>{selected ? selected.service : "Select an incident"}</h2>{selected ? <>
          <p>{selected.summary}</p><p className="muted">{selected.severity} · {selected.alert_count} alert(s) · {selected.status} · updated {new Date(selected.updated_at).toLocaleString()}</p>
          <div className="controls"><button onClick={createPage}>Page responder</button>{currentPage?.status === "delivered" && <><button onClick={acknowledge}>Acknowledge</button><input value={responseText} onChange={(event) => setResponseText(event.target.value)} placeholder="Reply to responder" aria-label="Reply to responder" /><button disabled={!responseText.trim()} onClick={reply}>Reply</button></>}<select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)} aria-label="Scenario"><option value="deployment_regression">Deployment regression</option><option value="disk_pressure">Disk pressure</option><option value="third_party_outage">Third-party outage</option></select><button disabled={!scenarioMatchesIncident} onClick={investigate}>Investigate</button>{!scenarioMatchesIncident && <span className="muted">Choose the scenario for {selected.service}.</span>}{actionType && scenarioMatchesIncident && investigation ? <button onClick={proposeAction}>Propose {actionType}</button> : actionType && <span className="muted">Investigate the matching scenario before proposing an action.</span>}{currentAction?.status === "pending_approval" && <><button onClick={() => decideAction(true)}>Approve</button><button onClick={() => decideAction(false)}>Reject</button></>}{currentAction?.status === "approved" && <button onClick={executeAction}>Queue execution</button>}{currentAction?.status === "queued" && <span className="muted">Action queued for the worker.</span>}{currentAction?.status === "running" && <span className="muted">Action is running.</span>}{currentAction?.status === "unknown" && <button onClick={reconcileAction}>Reconcile</button>}{["completed", "timed_out"].includes(currentAction?.status ?? "") && <button onClick={verifyAction}>Verify</button>}{actions.length > 0 && !currentAction && <span className="muted">Older action records belong to another scenario or service.</span>}</div>
          {investigation && <section className="evidence" aria-label="Investigation evidence"><div className="evidence-header"><h3>Investigation</h3><span className="badge">model: {investigation.model_status}</span></div>{investigation.model_error && <p className="muted">{investigation.model_error}</p>}{investigation.findings.map((finding) => <article className="finding" key={finding.id}><strong>{finding.statement}</strong><p className="muted">{finding.category} · confidence {(finding.confidence * 100).toFixed(0)}% · next step: {finding.suggested_next_step}</p>{finding.uncertainty && <p className="muted">{finding.uncertainty}</p>}<small>Cites: {finding.evidence_ids.join(", ")}</small></article>)}<div className="evidence-grid">{investigation.evidence.map((item) => <article className={`evidence-card ${item.availability !== "available" ? "degraded" : ""}`} key={item.id}><div><strong>{item.source_type}</strong><span className="badge">{item.availability}</span></div><small>{new Date(item.observed_at).toLocaleString()}</small><pre>{JSON.stringify(item.items, null, 2)}</pre></article>)}</div></section>}
          <ol className="timeline">{selected.timeline.map((event) => <li key={event.id}><strong>{event.event_type}</strong><time>{new Date(event.event_time).toLocaleString()}</time></li>)}</ol>
        </> : <p className="muted">Create an alert to see its timeline.</p>}</div>
      </section>
    </main>
  );
}
