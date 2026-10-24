import { useEffect, useRef, useState } from "react";
import { activeAction, activePage, workflowStates } from "../lib/incidentSelection";
import type { Action, Incident, IncidentDetail, Investigation, Page, TimelineEvent } from "../domain/types";

const scenarioServices: Record<string, string> = { deployment_regression: "payments-api", disk_pressure: "orders-worker", third_party_outage: "checkout-api" };
const serviceScenarios = Object.fromEntries(Object.entries(scenarioServices).map(([scenario, service]) => [service, scenario]));
const scenarioLabels: Record<string, string> = { deployment_regression: "Deployment regression", disk_pressure: "Disk pressure", third_party_outage: "Third-party outage" };
const actionTypes: Record<string, string | null> = { deployment_regression: "rollback", disk_pressure: "clear_disk", third_party_outage: null };

const titleCase = (value: string) => value.replace(/_/g, " ").replace(/\b\w/g, (letter: string) => letter.toUpperCase());
const readableValue = (value: unknown) => typeof value === "string" ? value : JSON.stringify(value);
const objectRows = (value: unknown) => value && typeof value === "object" && !Array.isArray(value)
  ? Object.entries(value as Record<string, unknown>).map(([key, item]) => [titleCase(key), readableValue(item)] as const)
  : [["Value", readableValue(value)] as const];

function eventSummary(event: TimelineEvent) {
  const payload = event.payload;
  const actionType = typeof payload.action_type === "string" ? titleCase(payload.action_type) : null;
  const responder = typeof payload.responder === "string" ? payload.responder : null;
  const status = typeof payload.status === "string" ? payload.status : null;
  if (event.event_type === "alert_received") return "A new alert was accepted into this incident.";
  if (event.event_type === "investigation_started") return "Investigation started for the selected scenario.";
  if (event.event_type === "investigation_completed") return "Investigation completed and its finding was recorded.";
  if (event.event_type === "incident_unfixable") return "The evidence points to an external dependency; no local fix was proposed.";
  if (event.event_type === "incident_resolved") return "The verified action returned the service to a healthy state.";
  if (event.event_type === "page_delivered") return `Responder page delivered${responder ? ` to ${responder}` : ""}.`;
  if (event.event_type === "page_response") return `Responder sent a ${String(payload.response_type ?? "response")}.`;
  if (event.event_type === "action_proposed") return `${actionType ?? "An action"} was proposed for approval.`;
  if (event.event_type === "action_decision") return `Human decision: ${status ?? "updated"}.`;
  if (event.event_type === "action_result") return `The ${actionType ?? "approved action"} returned ${status ?? "a result"}.`;
  if (event.event_type === "action_verified") return `Post-action verification ${payload.verified === true ? "passed" : "needs review"}.`;
  if (event.event_type === "page_timeout") return "The primary responder timed out.";
  if (event.event_type === "page_escalated") return "The incident escalated to the fallback responder.";
  return titleCase(event.event_type);
}

export function App() {
  const incidentFromUrl = new URLSearchParams(window.location.search).get("incident");
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<IncidentDetail | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(incidentFromUrl);
  const [pages, setPages] = useState<Page[]>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [scenarioId, setScenarioId] = useState("deployment_regression");
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [responseText, setResponseText] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const detailRequest = useRef(0);

  useEffect(() => {
    if (!error) return;
    const timer = window.setTimeout(() => setError(null), 6000);
    return () => window.clearTimeout(timer);
  }, [error]);

  useEffect(() => {
    if (!feedback) return;
    const timer = window.setTimeout(() => setFeedback(null), 4500);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  const responseError = async (response: Response) => {
    try {
      const payload = await response.json() as { detail?: string };
      return new Error(payload.detail ?? "");
    } catch {
      return new Error("");
    }
  };

  const getJson = <T,>(path: string) => fetch(path).then((response) => {
    if (!response.ok) return responseError(response).then((error) => Promise.reject(error));
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
      if (requestId === detailRequest.current) {
        setSelected(incident);
        setPages(pageItems);
        setActions(actionItems);
        setInvestigation(investigationResult);
        setScenarioId(serviceScenarios[incident.service] ?? "deployment_regression");
      }
    }).catch(() => {
      if (requestId === detailRequest.current) setError("The incident detail is unavailable.");
    });
  };

  const loadIncidents = () => getJson<Incident[]>("/api/v1/incidents")
    .then((items) => {
      setIncidents(items);
      if (selectedId) loadIncident(selectedId);
      else if (items[0]) loadIncident(items[0].id);
    })
    .catch(() => setError("The incident list is unavailable."));

  useEffect(() => {
    loadIncidents();
    const timer = window.setInterval(loadIncidents, 5000);
    return () => window.clearInterval(timer);
  }, [selectedId]);

  const post = (path: string, body?: object) => fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  }).then((response) => {
    if (!response.ok) return responseError(response).then((error) => Promise.reject(error));
    return response.json();
  });

  const successMessages: Record<string, string> = { investigate: "Investigation started. The finding will update when the worker finishes.", page: "Responder page sent.", acknowledge: "Responder acknowledged the incident.", reply: "Reply sent to the responder.", investigate_reply: "More investigation requested from the responder.", propose: "Action proposed for human approval.", approve: "Action approved and ready to queue.", reject: "Action rejected.", execute: "Action queued for execution.", verify: "Action verified and the incident is closed.", reconcile: "Action result reconciled." };
  const perform = (name: string, request: Promise<unknown>, onSuccess: (result?: unknown) => Promise<unknown> | void, message: string) => {
    setPending(name);
    setError(null);
    return request.then((result) => {
      setFeedback(successMessages[name] ?? "Update completed.");
      Promise.resolve(onSuccess(result)).catch(() => setError(message));
    }).catch((caught) => setError(caught instanceof Error && caught.message ? caught.message : message)).finally(() => setPending(null));
  };

  const currentPage = activePage(pages);
  const pageOpen = ["delivered", "acknowledged", "replied"].includes(currentPage?.status ?? "");
  const scenarioMatchesIncident = Boolean(selected && scenarioServices[scenarioId] === selected.service);
  const currentAction = activeAction(actions, selected ? { scenarioId, target: selected.service } : undefined);
  const actionType = actionTypes[scenarioId];
  const investigationComplete = Boolean(investigation && (investigation.status === "completed" || investigation.findings.length > 0));
  const investigationBusy = ["queued", "running"].includes(investigation?.status ?? "");
  const finding = investigation?.findings[0];
  const noLocalAction = finding?.suggested_next_step === "unfixable";
  const workflow = workflowStates(investigation, currentPage, currentAction, noLocalAction);
  const evidenceLabels = new Map((investigation?.evidence ?? []).map((item, index) => [item.id, `${titleCase(item.source_type)} ${index + 1}`]));

  const createPage = () => selected && !currentPage && perform("page", post(`/api/v1/incidents/${selected.id}/page`, { responder: "primary-oncall", fallback_responder: "secondary-oncall", deadline_seconds: 300 }), () => loadIncident(selected.id), "The responder page could not be created.");
  const acknowledge = () => currentPage && selected && perform("acknowledge", post(`/api/v1/pages/${currentPage.id}/respond`, { response_type: "acknowledge", response_text: "Investigating", expected_version: selected.version }), () => loadIncident(selected.id), "The responder response failed.");
  const reply = () => currentPage && selected && responseText.trim() && perform("reply", post(`/api/v1/pages/${currentPage.id}/respond`, { response_type: "reply", response_text: responseText.trim(), expected_version: selected.version }), () => { setResponseText(""); return loadIncident(selected.id); }, "The responder reply failed.");
  const requestMoreInvestigation = () => currentPage && selected && perform("investigate_reply", post(`/api/v1/pages/${currentPage.id}/respond`, { response_type: "investigate", response_text: "Please investigate further", expected_version: selected.version }), () => loadIncident(selected.id), "The follow-up investigation request failed.");
  const proposeAction = () => selected && investigationComplete && scenarioMatchesIncident && actionType && perform("propose", post(`/api/v1/incidents/${selected.id}/actions`, { scenario_id: scenarioId, action_type: actionType, target: selected.service, parameters: {}, idempotency_key: `ui-${selected.id}-${actionType}`, approval_seconds: 300 }), () => loadIncident(selected.id), "The action proposal failed.");
  const decideAction = (approved: boolean) => currentAction && selected && perform(approved ? "approve" : "reject", post(`/api/v1/actions/${currentAction.id}/decision`, { approved, responder: "primary-oncall", expected_version: selected.version }), () => loadIncident(selected.id), "The action decision failed.");
  const executeAction = () => currentAction && perform("execute", post(`/api/v1/actions/${currentAction.id}/execute`), () => selected ? loadIncident(selected.id) : undefined, "The action execution failed.");
  const verifyAction = () => currentAction && perform("verify", post(`/api/v1/actions/${currentAction.id}/verify`), () => selected ? loadIncident(selected.id) : undefined, "The action verification failed.");
  const reconcileAction = () => currentAction && perform("reconcile", post(`/api/v1/actions/${currentAction.id}/reconcile`), () => selected ? loadIncident(selected.id) : undefined, "The action reconciliation failed.");
  const investigate = () => selected && scenarioMatchesIncident && perform("investigate", post(`/api/v1/incidents/${selected.id}/investigate`, { scenario_id: scenarioId }), (result) => { setInvestigation(result as Investigation); return loadIncident(selected.id); }, "The investigation could not be started.");

  return (
    <main>
      <header className="page-header"><div><p className="product-name">Incident console</p><h1>On-call assistant</h1><p className="muted">Find the cause, decide the next safe action, and keep the audit trail.</p></div><div className="header-actions"><a href="http://localhost:8003">Open demo store</a><span className="status-dot">Live workspace</span></div></header>
      {(error || feedback) && <div className="toast-region" aria-live="polite" aria-atomic="true">{error ? <div className="toast" role="alert"><span>{error}</span><button type="button" className="toast-dismiss" onClick={() => setError(null)}>Dismiss</button></div> : <div className="toast success-toast" role="status"><span>{feedback}</span><button type="button" className="toast-dismiss" onClick={() => setFeedback(null)}>Dismiss</button></div>}</div>}
      <section className="layout" aria-label="Incidents">
        <aside className="panel incident-panel"><div className="section-heading"><h2>Incidents</h2><span className="count">{incidents.length}</span></div>{incidents.length === 0 ? <p className="muted">No incidents yet.</p> : <div className="incident-list">{incidents.map((incident) => <button type="button" className={`incident ${selectedId === incident.id ? "selected" : ""}`} key={incident.id} onClick={() => loadIncident(incident.id)}><span><strong>{incident.service}</strong><small>{incident.summary}</small><small>{incident.alert_count} alerts · Updated {new Date(incident.updated_at).toLocaleString()}</small></span><span className="badge">{incident.status}</span></button>)}</div>}</aside>
        <article className="panel detail-panel">
          {selected ? <>
            <div className="detail-heading"><div><p className="product-name">Selected incident</p><h2>{selected.service}</h2><p className="muted">{selected.summary}</p></div><span className="severity">{selected.severity}</span></div>
            <div className="summary-strip"><span><strong>{selected.alert_count}</strong> alerts</span><span><strong>{titleCase(selected.status)}</strong></span><span>Updated {new Date(selected.updated_at).toLocaleString()}</span></div>
            <section className="next-step" aria-labelledby="next-step-heading"><div><h3 id="next-step-heading">What happens next</h3><p className="muted">Work from left to right. Each step unlocks the next safe decision.</p></div><ol className="workflow-steps"><li className={workflow.investigation}><span className="step-number">1</span><span><strong>Investigate</strong><small>{investigationComplete ? "Finding ready" : investigationBusy ? "Investigation running" : "Ready to run"}</small></span></li><li className={workflow.response}><span className="step-number">2</span><span><strong>Respond</strong><small>{workflow.response === "locked" ? "Waiting for finding" : currentPage ? titleCase(currentPage.status) : "Page the owner"}</small></span></li><li className={workflow.action}><span className="step-number">3</span><span><strong>{noLocalAction ? "No local fix" : "Act safely"}</strong><small>{workflow.action === "locked" ? "Waiting for acknowledgement" : currentAction ? titleCase(currentAction.status) : noLocalAction ? "Escalate externally" : "Propose a fix"}</small></span></li></ol></section>
            <section className="workflow-section" aria-labelledby="workflow-heading"><div className="section-heading"><div><h3 id="workflow-heading">1. Find the cause</h3><p className="section-help">Ask the system to inspect the matching signals.</p></div><span className="step-state">{investigationComplete ? "Complete" : investigation?.status ?? "Not started"}</span></div><label className="field-label" htmlFor="scenario">Choose the matching scenario</label><select id="scenario" value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>{Object.entries(scenarioLabels).map(([id, label]) => <option value={id} key={id}>{label}</option>)}</select><div className="button-row"><button type="button" className="primary" disabled={!scenarioMatchesIncident || investigationBusy || pending !== null} onClick={investigate}>{pending === "investigate" ? "Starting…" : investigationBusy ? "Investigation running…" : investigationComplete ? "Run investigation again" : "Start investigation"}</button></div>{investigationBusy && <p className="progress-note" role="status">Investigation is running in the background. This panel will update when the finding is ready.</p>}{!scenarioMatchesIncident && <p className="hint">This incident belongs to the {serviceScenarios[selected.service] ? scenarioLabels[serviceScenarios[selected.service]] : "matching"} scenario.</p>}</section>
            {finding && <section className="finding-panel" aria-labelledby="finding-heading"><div className="finding-heading"><div><h3 id="finding-heading">{finding.statement}</h3></div><span className="confidence">{Math.round(finding.confidence * 100)}% confidence</span></div><div className="finding-summary"><span><small>Category</small><strong>{titleCase(finding.category)}</strong></span><span><small>Recommended next step</small><strong>{titleCase(finding.suggested_next_step)}</strong></span></div>{finding.uncertainty && <p className="hint">Uncertainty: {finding.uncertainty}</p>}<p className="citation-line"><strong>Based on:</strong> {finding.evidence_ids.map((id) => evidenceLabels.get(id) ?? "evidence").join(" · ")}</p></section>}
            {investigation?.model_analysis && <section className="model-panel" aria-labelledby="model-heading"><div className="section-heading"><div><h3 id="model-heading">Model readout</h3><p className="section-help">A structured model response checked against the collected evidence.</p></div><span className="badge">{Math.round(investigation.model_analysis.confidence * 100)}% confidence</span></div><div className="finding-summary"><span><small>Current condition</small><strong>{investigation.model_analysis.current_condition}</strong></span><span><small>Likely cause</small><strong>{investigation.model_analysis.likely_cause}</strong></span><span><small>Suggested next step</small><strong>{titleCase(investigation.model_analysis.suggested_next_step)}</strong></span></div>{investigation.model_analysis.uncertainty && <p className="hint">Model uncertainty: {investigation.model_analysis.uncertainty}</p>}<p className="citation-line"><strong>Model citations:</strong> {investigation.model_analysis.evidence_ids.map((id) => evidenceLabels.get(id) ?? "evidence").join(" · ")}</p></section>}
            {investigationComplete && <section className="workflow-section" aria-labelledby="responder-heading"><div className="section-heading"><div><h3 id="responder-heading">2. Keep the owner informed</h3><p className="section-help">Page the service owner and record their response.</p></div><span className="step-state">{currentPage?.status ? titleCase(currentPage.status) : "Not paged"}</span></div>{!currentPage && <><p className="muted">Send the finding and suggested next step to the service owner.</p><button type="button" className="primary" disabled={pending !== null} onClick={createPage}>{pending === "page" ? "Paging…" : "Page service owner"}</button></>}{currentPage?.status === "delivered" && <div className="response-card"><p><strong>Waiting for acknowledgement</strong><small>The primary responder has been paged.</small></p><button type="button" className="primary" disabled={pending !== null} onClick={acknowledge}>{pending === "acknowledge" ? "Acknowledging…" : "Acknowledge"}</button></div>}{currentPage?.status === "acknowledged" && <div className="response-card"><p><strong>Responder acknowledged</strong><small>They are investigating this incident.</small></p></div>}{currentPage?.status === "replied" && <div className="response-card"><p><strong>Responder has replied</strong><small>The response is recorded in the audit trail.</small></p></div>}{pageOpen && <div className="reply-row"><input value={responseText} onChange={(event) => setResponseText(event.target.value)} placeholder="Add a reply for the responder" aria-label="Reply to responder" /><button type="button" className="primary" disabled={!responseText.trim() || pending !== null} onClick={reply}>{pending === "reply" ? "Sending…" : "Send reply"}</button><button type="button" disabled={pending !== null} onClick={requestMoreInvestigation}>{pending === "investigate_reply" ? "Requesting…" : "Request more investigation"}</button></div>}</section>}
            {noLocalAction && investigationComplete && <section className="workflow-section" aria-labelledby="no-local-fix-heading"><div className="section-heading"><div><h3 id="no-local-fix-heading">3. No local fix available</h3><p className="section-help">The evidence points to an external dependency. Keep the incident visible for human follow-up.</p></div><span className="step-state">Escalate externally</span></div></section>}
            {actionType && investigationComplete && ["acknowledged", "replied"].includes(currentPage?.status ?? "") && <section className="workflow-section" aria-labelledby="action-heading"><div className="section-heading"><div><h3 id="action-heading">3. Decide and verify the fix</h3><p className="section-help">Approve the suggested remediation, then check the service state.</p></div><span className="step-state">{currentAction?.status ? titleCase(currentAction.status) : "Not proposed"}</span></div>{!currentAction && <button type="button" className="primary" disabled={pending !== null} onClick={proposeAction}>Propose {titleCase(actionType)}</button>}{currentAction?.status === "pending_approval" && <div className="button-row"><button type="button" className="primary" disabled={pending !== null} onClick={() => decideAction(true)}>{pending === "approve" ? "Approving…" : "Approve action"}</button><button type="button" disabled={pending !== null} onClick={() => decideAction(false)}>{pending === "reject" ? "Rejecting…" : "Reject"}</button></div>}{currentAction?.status === "approved" && <button type="button" className="primary" disabled={pending !== null} onClick={executeAction}>{pending === "execute" ? "Queueing…" : "Queue action"}</button>}{currentAction?.status === "queued" && <p className="hint">The worker has the action and will update this panel when it finishes.</p>}{currentAction?.status === "running" && <p className="hint">The action is running. Keep this incident open for the result.</p>}{currentAction?.status === "unknown" && <button type="button" className="primary" disabled={pending !== null} onClick={reconcileAction}>Reconcile result</button>}{["completed", "timed_out"].includes(currentAction?.status ?? "") && <><p className="action-result">{currentAction?.status === "completed" ? "Action completed. Verify the service state before closing the loop." : "Action timed out. Verify the service state before deciding what to do next."}</p><button type="button" className="primary" disabled={pending !== null} onClick={verifyAction}>{pending === "verify" ? "Verifying…" : "Verify service state"}</button></>}</section>}
            {investigation && <details className="secondary-section"><summary><span><strong>Evidence used</strong><small>{investigation.evidence.length} sources · Model {titleCase(investigation.model_status)}</small></span><span className="count">Review</span></summary><div className="secondary-content" aria-labelledby="evidence-heading"><div className="section-heading"><div><h3 id="evidence-heading">What the system checked</h3></div><span className="badge">Model: {titleCase(investigation.model_status)}</span></div>{investigation.model_error && <p className="hint">Model note: {investigation.model_error}</p>}<div className="evidence-grid">{investigation.evidence.map((item, index) => <article className={`evidence-card ${item.availability !== "available" ? "degraded" : ""}`} key={item.id}><div className="evidence-card-heading"><div><strong>{titleCase(item.source_type)}</strong><small>{item.availability === "available" ? "Source available" : "Source degraded"}</small></div><span className="badge">Evidence {index + 1}</span></div><div className="evidence-fields">{item.items.flatMap((entry) => objectRows(entry)).map(([key, value]) => <div className="evidence-field" key={`${item.id}-${key}`}><span>{key}</span><strong>{value}</strong></div>)}</div><details><summary>View raw payload</summary><pre>{JSON.stringify(item.items, null, 2)}</pre></details></article>)}</div></div></details>}
            <details className="secondary-section"><summary><span><strong>Audit trail</strong><small>{selected.timeline.length} events · alerts, pages, decisions, and actions</small></span><span className="count">Review</span></summary><div className="secondary-content" aria-labelledby="timeline-heading"><div className="section-heading"><div><h3 id="timeline-heading">What happened</h3></div><span className="count">{selected.timeline.length} events</span></div><ol className="timeline">{selected.timeline.map((event) => <li key={event.id}><div className="timeline-event"><span className="event-marker" /><div><strong>{titleCase(event.event_type)}</strong><p>{eventSummary(event)}</p><time>{new Date(event.event_time).toLocaleString()}</time><details><summary>View event data</summary><pre>{JSON.stringify(event.payload, null, 2)}</pre></details></div></div></li>)}</ol></div></details>
          </> : <div className="empty-state"><h2>Select an incident</h2><p className="muted">Choose an incident from the inbox to see what happened and what to do next.</p></div>}
        </article>
      </section>
    </main>
  );
}
