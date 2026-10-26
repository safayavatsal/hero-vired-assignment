import { useEffect, useRef, useState } from "react";
import { activeAction, activePage, scenarioForService, workflowStates } from "../lib/incidentSelection";
import type { Action, ActionPreview, Incident, IncidentDetail, Investigation, Page, ResourceAnalysis, ScenarioInfo, TimelineEvent } from "../domain/types";

const fallbackScenarios: ScenarioInfo[] = [
  { id: "deployment_regression", name: "Deployment regression", service: "payments-api", severity: "critical", alert_type: "p99_latency_high", allowed_actions: ["rollback", "restart"], finding: { metric: "p99_latency_ms", category: "deployment_regression", suggested_next_step: "rollback" } },
  { id: "disk_pressure", name: "Disk pressure", service: "orders-worker", severity: "high", alert_type: "disk_usage_high", allowed_actions: ["clear_disk", "restart", "scale"], finding: { metric: "disk_usage_percent", category: "disk_pressure", suggested_next_step: "clear_disk" } },
  { id: "third_party_outage", name: "Third-party outage", service: "checkout-api", severity: "high", alert_type: "dependency_errors_high", allowed_actions: [], finding: { metric: "provider_error_rate", category: "third_party_outage", suggested_next_step: "unfixable" } },
];

const scenarioMaps = (definitions: ScenarioInfo[]) => ({
  scenarioServices: Object.fromEntries(definitions.map((scenario) => [scenario.id, scenario.service])),
  scenarioLabels: Object.fromEntries(definitions.map((scenario) => [scenario.id, scenario.name])),
  actionTypes: Object.fromEntries(definitions.map((scenario) => [scenario.id,
    scenario.finding && scenario.finding.suggested_next_step !== "unfixable" ? scenario.finding.suggested_next_step : scenario.allowed_actions[0] ?? null])),
});

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
  const [actionPreview, setActionPreview] = useState<ActionPreview | null>(null);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [scenarioId, setScenarioId] = useState("deployment_regression");
  const [showScenarioOverride, setShowScenarioOverride] = useState(false);
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>(fallbackScenarios);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [responseText, setResponseText] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [resourceScan, setResourceScan] = useState<ResourceAnalysis | null>(null);
  const [resourceScanPending, setResourceScanPending] = useState(false);
  const [activeView, setActiveView] = useState<"incidents" | "kubernetes">("incidents");
  const detailRequest = useRef(0);

  useEffect(() => {
    if (!error) return;
    const timer = window.setTimeout(() => setError(null), 6000);
    return () => window.clearTimeout(timer);
  }, [error]);

  useEffect(() => {
    getJson<ScenarioInfo[]>("/api/v1/simulator/scenarios")
      .then((items) => { if (items.length) setScenarios(items); })
      .catch(() => undefined);
  }, []);

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
    window.history.replaceState({}, "", `/?incident=${encodeURIComponent(id)}`);
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
        setActionPreview(null);
        setInvestigation(investigationResult);
        setScenarioId(serviceScenarios[incident.service] ?? "deployment_regression");
        setShowScenarioOverride(false);
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

  const successMessages: Record<string, string> = { investigate: "Investigation started. The finding will update when the worker finishes.", deeper_investigate: "A deeper investigation started. The result will replace the current finding when the worker finishes.", page: "Responder page sent to the service owner.", acknowledge: "Service owner acknowledged the incident.", reply: "Reply recorded for the service owner.", preview: "Sandbox preview ready. No live change was made.", propose: "Action proposed for human approval.", approve: "Action approved and ready to queue.", reject: "Action rejected.", execute: "Action queued for execution.", verify: "Action verified and the incident is closed.", reconcile: "Action result reconciled." };
  const perform = (name: string, request: Promise<unknown>, onSuccess: (result?: unknown) => Promise<unknown> | void, message: string) => {
    setPending(name);
    setError(null);
    return request.then((result) => {
      setFeedback(successMessages[name] ?? "Update completed.");
      return Promise.resolve(onSuccess(result)).catch(() => setError(message));
    }).catch((caught) => setError(caught instanceof Error && caught.message ? caught.message : message)).finally(() => setPending(null));
  };

  const currentPage = activePage(pages);
  const pageOpen = currentPage?.status === "delivered";
  const { scenarioServices, scenarioLabels, actionTypes } = scenarioMaps(scenarios);
  const selectedScenario = scenarios.find((scenario) => scenario.id === scenarioId);
  const serviceScenarios = Object.fromEntries(Object.entries(scenarioServices).map(([scenario, service]) => [service, scenario]));
  useEffect(() => {
    if (!selected) return;
    const matchingScenario = scenarioForService(scenarios, selected.service);
    if (matchingScenario && matchingScenario !== scenarioId) setScenarioId(matchingScenario);
  }, [scenarios, selected?.service]);
  const scenarioMatchesIncident = Boolean(selected && scenarioServices[scenarioId] === selected.service);
  const currentAction = activeAction(actions, selected ? { scenarioId, target: selected.service } : undefined);
  const actionType = actionPreview ? null : actionTypes[scenarioId];
  const investigationComplete = Boolean(investigation && (investigation.status === "completed" || investigation.findings.length > 0));
  const investigationBusy = ["queued", "running"].includes(investigation?.status ?? "");
  const finding = investigation?.findings[0];
  const noLocalAction = finding?.suggested_next_step === "unfixable";
  const workflow = workflowStates(investigation, currentPage, currentAction, noLocalAction);
  const evidenceLabels = new Map((investigation?.evidence ?? []).map((item, index) => [item.id, `${titleCase(item.source_type)} ${index + 1}`]));
  const similarEvidence = investigation?.evidence.find((item) => item.source_type === "similar_incidents");

  const createPage = () => selected && !currentPage && perform("page", post(`/api/v1/incidents/${selected.id}/page`, { deadline_seconds: 300 }), () => loadIncident(selected.id), "The responder page could not be created.");
  const acknowledge = () => currentPage && selected && perform("acknowledge", post(`/api/v1/pages/${currentPage.id}/respond`, { response_type: "acknowledge", response_text: "Investigating", expected_version: selected.version }), () => loadIncident(selected.id), "The responder response failed.");
  const reply = () => currentPage && selected && responseText.trim() && perform("reply", post(`/api/v1/pages/${currentPage.id}/respond`, { response_type: "reply", response_text: responseText.trim(), expected_version: selected.version }), () => { setResponseText(""); return loadIncident(selected.id); }, "The responder reply failed.");
  const previewAction = () => selected && investigationComplete && scenarioMatchesIncident && actionType && perform("preview", post(`/api/v1/incidents/${selected.id}/actions/preview`, { scenario_id: scenarioId, action_type: actionType, target: selected.service, parameters: {} }), (result) => { setActionPreview(result as ActionPreview); return undefined; }, "The sandbox preview failed.");
  const proposeAction = previewAction;
  const submitPreviewDecision = (approved: boolean) => selected && actionPreview && perform(approved ? "approve" : "reject", post(`/api/v1/incidents/${selected.id}/actions`, { scenario_id: actionPreview.scenario_id, action_type: actionPreview.action_type, target: actionPreview.target, parameters: {}, idempotency_key: `ui-${selected.id}-${actionPreview.action_type}`, approval_seconds: 300 }), async (result) => { const proposal = result as Action; await post(`/api/v1/actions/${proposal.id}/decision`, { approved, responder: currentPage?.responder ?? "primary-oncall", expected_version: selected.version }); await loadIncident(selected.id); }, "The action decision failed.");
  const decideAction = (approved: boolean) => currentAction && selected && perform(approved ? "approve" : "reject", post(`/api/v1/actions/${currentAction.id}/decision`, { approved, responder: currentPage?.responder ?? "primary-oncall", expected_version: selected.version }), () => loadIncident(selected.id), "The action decision failed.");
  const executeAction = () => currentAction && perform("execute", post(`/api/v1/actions/${currentAction.id}/execute`), () => selected ? loadIncident(selected.id) : undefined, "The action execution failed.");
  const verifyAction = () => currentAction && perform("verify", post(`/api/v1/actions/${currentAction.id}/verify`), () => selected ? loadIncident(selected.id) : undefined, "The action verification failed.");
  const reconcileAction = () => currentAction && perform("reconcile", post(`/api/v1/actions/${currentAction.id}/reconcile`), () => selected ? loadIncident(selected.id) : undefined, "The action reconciliation failed.");
  const investigate = (mode: "standard" | "deeper" = "standard") => selected && scenarioMatchesIncident && perform(mode === "deeper" ? "deeper_investigate" : "investigate", post(`/api/v1/incidents/${selected.id}/investigate`, { scenario_id: scenarioId, mode }), (result) => { setInvestigation(result as Investigation); return loadIncident(selected.id); }, "The investigation could not be started.");
  const runResourceScan = () => {
    setResourceScanPending(true);
    setError(null);
    return post("/api/v1/kubernetes/analyze", {
      resources: [
        { kind: "Pod", metadata: { name: "checkout-api-7f", namespace: "shop", labels: { app: "checkout-api" } }, status: { phase: "Pending", containerStatuses: [{ name: "api", state: { waiting: { reason: "CrashLoopBackOff", message: "container keeps restarting" } } }] } },
        { kind: "Deployment", metadata: { name: "checkout-api", namespace: "shop", labels: { app: "checkout-api" } }, spec: { replicas: 3 }, status: { readyReplicas: 1, conditions: [{ type: "Progressing", status: "False", reason: "ProgressDeadlineExceeded", message: "ReplicaSet did not become ready" }] } },
      ],
      namespace: "shop",
    }).then((result) => {
      setResourceScan(result as ResourceAnalysis);
      setFeedback("Resource scan completed. No cluster changes were made.");
    }).catch((caught) => setError(caught instanceof Error && caught.message ? caught.message : "The resource scan failed.")).finally(() => setResourceScanPending(false));
  };
  const recommendationReason = investigation?.model_analysis?.likely_cause ?? finding?.statement ?? "The evidence does not yet support a specific remediation.";
  const recommendationCondition = investigation?.model_analysis?.current_condition ?? finding?.statement;

  return (
    <main>
      <header className="page-header"><div><p className="product-name">Incident console</p><h1>On-call assistant</h1><p className="muted">Find the cause, decide the next safe action, and keep the audit trail.</p></div><div className="header-actions"><a href="http://localhost:8003">Open demo store</a><span className="status-dot">Live workspace</span></div></header>
      {(error || feedback) && <div className="toast-region" aria-live="polite" aria-atomic="true">{error ? <div className="toast" role="alert"><span>{error}</span><button type="button" className="toast-dismiss" onClick={() => setError(null)}>Dismiss</button></div> : <div className="toast success-toast" role="status"><span>{feedback}</span><button type="button" className="toast-dismiss" onClick={() => setFeedback(null)}>Dismiss</button></div>}</div>}
      <nav className="view-tabs" aria-label="Console views" role="tablist">
        <button type="button" role="tab" aria-selected={activeView === "incidents"} className={`view-tab ${activeView === "incidents" ? "active" : ""}`} onClick={() => setActiveView("incidents")}>Incidents <span>{incidents.length}</span></button>
        <button type="button" role="tab" aria-selected={activeView === "kubernetes"} className={`view-tab ${activeView === "kubernetes" ? "active" : ""}`} onClick={() => setActiveView("kubernetes")}>Kubernetes health</button>
      </nav>
      {activeView === "incidents" && <section className="layout" aria-label="Incidents">
        <aside className="panel incident-panel"><div className="section-heading"><h2>Incidents</h2><span className="count">{incidents.length}</span></div>{incidents.length === 0 ? <p className="muted">No incidents yet.</p> : <div className="incident-list">{incidents.map((incident) => <button type="button" className={`incident ${selectedId === incident.id ? "selected" : ""}`} key={incident.id} onClick={() => loadIncident(incident.id)}><span><strong>{incident.service}</strong><small>{incident.summary}</small><small>{incident.alert_count} alerts · Updated {new Date(incident.updated_at).toLocaleString()}</small></span><span className="badge">{incident.status}</span></button>)}</div>}</aside>
        <article className="panel detail-panel">
          {selected ? <>
            <div className="detail-heading"><div><p className="product-name">Selected incident</p><h2>{selected.service}</h2><p className="muted">{selected.summary}</p></div><span className="severity">{selected.severity}</span></div>
            <div className="summary-strip"><span><strong>{selected.alert_count}</strong> alerts</span><span><strong>{titleCase(selected.status)}</strong></span><span>Updated {new Date(selected.updated_at).toLocaleString()}</span></div>
            {selectedScenario?.runbook?.length ? <section className="runbook" aria-label="Investigation checklist"><div><strong>Investigation checklist</strong><p className="section-help">These bounded checks explain what the assistant will verify for this incident.</p></div><ol className="runbook-list">{selectedScenario.runbook.map((step) => <li className={investigationComplete ? "complete" : investigationBusy ? "active" : ""} key={step.id}><span className="runbook-marker">{investigationComplete ? "✓" : "·"}</span><span><strong>{step.title}</strong><small>{step.purpose}</small></span></li>)}</ol></section> : null}
            <section className="next-step" aria-labelledby="next-step-heading"><div><h3 id="next-step-heading">What happens next</h3><p className="muted">The system finds the cause first, then a human owns the response, then a human approves the fix.</p></div><ol className="workflow-steps"><li className={workflow.investigation}><span className="step-number">1</span><span><strong>Investigate</strong><small>{investigationComplete ? "Cause found" : investigationBusy ? "Checking signals" : "Find the likely cause"}</small></span></li><li className={workflow.response}><span className="step-number">2</span><span><strong>Notify owner</strong><small>{workflow.response === "locked" ? "Waiting for finding" : currentPage ? titleCase(currentPage.status) : "Confirm human ownership"}</small></span></li><li className={workflow.action}><span className="step-number">3</span><span><strong>{noLocalAction ? "Escalate" : "Approve and verify"}</strong><small>{workflow.action === "locked" ? "Waiting for acknowledgement" : currentAction ? titleCase(currentAction.status) : noLocalAction ? "No local fix" : "Control the remediation"}</small></span></li></ol></section>
            <section className="workflow-section" aria-labelledby="workflow-heading"><div className="section-heading"><div><h3 id="workflow-heading">1. Find the cause</h3><p className="section-help">The context is selected from the incident service. The system then checks its evidence sources.</p></div><span className="step-state">{investigationComplete ? "Complete" : investigation?.status ?? "Not started"}</span></div><div className="scenario-context"><div><span className="field-label">Investigation context</span><strong>{scenarioLabels[scenarioId] ?? "Automatic context"}</strong><small>Matched to {selected.service}</small></div><button type="button" className="context-toggle" onClick={() => setShowScenarioOverride((visible) => !visible)}>{showScenarioOverride ? "Hide advanced options" : "Change context"}</button></div>{showScenarioOverride && <div className="scenario-override"><label className="field-label" htmlFor="scenario">Change context for a controlled demo run</label><select id="scenario" value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>{Object.entries(scenarioLabels).map(([id, label]) => <option value={id} key={id}>{label}</option>)}</select><p className="hint">Use this only to test another registered scenario. The incident’s matching context remains the default.</p></div>}{!investigationComplete && <div className="button-row"><button type="button" className="primary" disabled={!scenarioMatchesIncident || investigationBusy || pending !== null} onClick={() => investigate()}>{pending === "investigate" ? "Starting…" : investigationBusy ? "Investigation running…" : "Start investigation"}</button></div>}{investigationBusy && <p className="progress-note" role="status">Investigation is running in the background. This panel will update when the finding is ready.</p>}{!scenarioMatchesIncident && <p className="hint">This context does not match this incident’s service. Choose the matching context before running.</p>}</section>
            {finding && <section className="finding-panel" aria-labelledby="finding-heading"><div className="finding-heading"><div><h3 id="finding-heading">{finding.statement}</h3></div><span className="confidence">{Math.round(finding.confidence * 100)}% confidence</span></div><div className="finding-summary"><span><small>Category</small><strong>{titleCase(finding.category)}</strong></span><span><small>Recommended next step</small><strong>{titleCase(finding.suggested_next_step)}</strong></span></div>{finding.uncertainty && <p className="hint">Uncertainty: {finding.uncertainty}</p>}<p className="citation-line"><strong>Based on:</strong> {finding.evidence_ids.map((id) => evidenceLabels.get(id) ?? "evidence").join(" · ")}</p><div className="button-row"><button type="button" className="secondary-action" disabled={investigationBusy || pending !== null} onClick={() => investigate("deeper")}>{pending === "deeper_investigate" ? "Starting deeper review…" : "Request deeper investigation"}</button></div></section>}
            {investigation?.model_analysis && <section className="model-panel" aria-labelledby="model-heading"><div className="section-heading"><div><p className="product-name">Structured investigation</p><h3 id="model-heading">Model readout</h3><p className="section-help">A structured response checked against the collected evidence.</p></div><span className="badge">{Math.round(investigation.model_analysis.confidence * 100)}% confidence</span></div><div className="analysis-brief"><article><small>What is happening</small><strong>{investigation.model_analysis.current_condition}</strong></article><article><small>Most likely cause</small><strong>{investigation.model_analysis.likely_cause}</strong></article><article><small>Suggested next step</small><strong>{titleCase(investigation.model_analysis.suggested_next_step)}</strong></article></div>{investigation.model_analysis.uncertainty && <p className="hint">Model uncertainty: {investigation.model_analysis.uncertainty}</p>}<p className="citation-line"><strong>Model citations:</strong> {investigation.model_analysis.evidence_ids.map((id) => evidenceLabels.get(id) ?? "evidence").join(" · ")}</p>{investigation.model_telemetry && <div className="investigation-meta"><span><small>Provider status</small><strong>{titleCase(investigation.model_telemetry.status)}</strong></span><span><small>Model</small><strong>{investigation.model_telemetry.model ?? "Not configured"}</strong></span><span><small>Response time</small><strong>{investigation.model_telemetry.duration_ms} ms</strong></span></div>}</section>}
            {investigationComplete && <section className="workflow-section" aria-labelledby="responder-heading"><div className="section-heading"><div><h3 id="responder-heading">2. Notify the service owner</h3><p className="section-help">Send the finding to the responsible human and record whether they have taken ownership.</p></div><span className="step-state">{currentPage?.status ? titleCase(currentPage.status) : "Not notified"}</span></div>{!currentPage && <><p className="muted">This sends a responder page to the resolved service owner. Acknowledgement means ownership, not resolution.</p><button type="button" className="primary" disabled={pending !== null} onClick={createPage}>{pending === "page" ? "Notifying…" : "Notify service owner"}</button></>}{currentPage?.status === "delivered" && <div className="response-card"><p><strong>Waiting for acknowledgement</strong><small>The service owner has been notified and must accept ownership. An optional reply records a note but does not investigate or resolve the incident.</small></p><button type="button" className="primary" disabled={pending !== null} onClick={acknowledge}>{pending === "acknowledge" ? "Acknowledging…" : "Acknowledge ownership"}</button></div>}{currentPage?.status === "replied" && <div className="response-card"><p><strong>Owner note recorded</strong><small>Ownership is still pending. Acknowledge the incident to open the remediation step.</small></p><button type="button" className="primary" disabled={pending !== null} onClick={acknowledge}>{pending === "acknowledge" ? "Acknowledging…" : "Acknowledge ownership"}</button></div>}{currentPage?.status === "acknowledged" && <div className="response-card"><p><strong>Owner acknowledged</strong><small>Ownership is recorded. Step 2 is closed; the remediation review is now available.</small></p></div>}{pageOpen && <div className="reply-row"><input value={responseText} onChange={(event) => setResponseText(event.target.value)} placeholder="Optional note to the service owner" aria-label="Reply to service owner" /><button type="button" className="primary" disabled={!responseText.trim() || pending !== null} onClick={reply}>{pending === "reply" ? "Sending…" : "Send owner note"}</button></div>}</section>}
            {noLocalAction && investigationComplete && <section className="workflow-section" aria-labelledby="no-local-fix-heading"><div className="section-heading"><div><h3 id="no-local-fix-heading">3. No local fix available</h3><p className="section-help">The evidence points to an external dependency. Keep the incident visible for human follow-up.</p></div><span className="step-state">Escalate externally</span></div></section>}
            {actionPreview && investigationComplete && currentPage?.status === "acknowledged" && <section className="workflow-section" aria-labelledby="sandbox-review-heading"><div className="section-heading"><div><h3 id="sandbox-review-heading">3. Review the proposed remediation</h3><p className="section-help">This read-only sandbox shows the projected service state before any approval is recorded.</p></div><span className="step-state">Sandbox preview</span></div><div className="action-preview"><div className="preview-grid"><div><small>Before</small><pre>{JSON.stringify(actionPreview.state_before, null, 2)}</pre></div><div><small>After approval</small><pre>{JSON.stringify(actionPreview.state_after, null, 2)}</pre></div></div><p className="citation-line"><strong>Projected changes:</strong> {Object.keys(actionPreview.changes).length ? Object.entries(actionPreview.changes).map(([key, value]) => `${titleCase(key)} ${readableValue(value.before)} → ${readableValue(value.after)}`).join(" · ") : "No state changes"}</p><p className="hint">No live service state has changed. Choose whether to create and approve the audited action.</p><div className="button-row"><button type="button" className="primary" disabled={pending !== null} onClick={() => submitPreviewDecision(true)}>{pending === "approve" ? "Approving…" : `Approve ${titleCase(actionPreview.action_type)}`}</button><button type="button" disabled={pending !== null} onClick={() => submitPreviewDecision(false)}>{pending === "reject" ? "Rejecting…" : "Reject recommendation"}</button></div></div></section>}
            {actionType && investigationComplete && currentPage?.status === "acknowledged" && <section className="workflow-section" aria-labelledby="action-heading"><div className="section-heading"><div><h3 id="action-heading">3. Approve and verify remediation</h3><p className="section-help">Review the recommended action, approve it, then verify what changed in the service.</p></div><span className="step-state">{currentAction?.status ? titleCase(currentAction.status) : "Not proposed"}</span></div><details className="recommendation-explanation" open><summary>Why is {titleCase(actionType)} suggested?</summary><p>{recommendationReason}</p>{recommendationCondition && <p className="hint">Current condition: {recommendationCondition}</p>}<p className="citation-line"><strong>Evidence:</strong> {finding?.evidence_ids.map((id) => evidenceLabels.get(id) ?? "evidence").join(" · ") || "The collected evidence is shown below."}</p></details>{!currentAction && <><p className="muted">The system recommends {titleCase(actionType)}. Nothing runs until a human approves it.</p><button type="button" className="primary" disabled={pending !== null} onClick={proposeAction}>Review {titleCase(actionType)} in sandbox</button></>}{currentAction?.status === "pending_approval" && <div className="button-row"><button type="button" className="primary" disabled={pending !== null} onClick={() => decideAction(true)}>{pending === "approve" ? "Approving…" : `Approve ${titleCase(actionType)}`}</button><button type="button" disabled={pending !== null} onClick={() => decideAction(false)}>{pending === "reject" ? "Rejecting…" : "Reject recommendation"}</button></div>}{currentAction?.status === "approved" && <button type="button" className="primary" disabled={pending !== null} onClick={executeAction}>{pending === "execute" ? "Queueing…" : `Queue ${titleCase(actionType)}`}</button>}{currentAction?.status === "queued" && <p className="hint">The approved action is queued. The worker will execute it and update this panel.</p>}{currentAction?.status === "running" && <p className="hint">The approved action is running. Keep this incident open for the result.</p>}{currentAction?.status === "unknown" && <button type="button" className="primary" disabled={pending !== null} onClick={reconcileAction}>Reconcile action result</button>}{["completed", "timed_out"].includes(currentAction?.status ?? "") && <><p className="action-result">{currentAction?.status === "completed" ? "The action finished. Verify the service state before closing the incident." : "The action timed out. Verify the service state before deciding what to do next."}</p><button type="button" className="primary" disabled={pending !== null} onClick={verifyAction}>{pending === "verify" ? "Verifying…" : "Verify service state"}</button></>}</section>}
            {investigation && <details className="secondary-section"><summary><span><strong>Evidence used</strong><small>{investigation.evidence.length} sources · Model {titleCase(investigation.model_status)}</small></span><span className="count">Review</span></summary><div className="secondary-content" aria-labelledby="evidence-heading"><div className="section-heading"><div><h3 id="evidence-heading">What the system checked</h3><p className="section-help">Every source query is bounded, named, and linked to the finding.</p></div><span className="badge">Model: {titleCase(investigation.model_status)}</span></div>{investigation.model_error && <p className="hint">Model note: {investigation.model_error}</p>}{similarEvidence && <section className={`similar-incidents-panel ${similarEvidence.availability !== "available" ? "degraded" : ""}`} aria-labelledby="similar-incidents-heading"><div className="section-heading"><div><h3 id="similar-incidents-heading">Similar past incidents</h3><p className="section-help">Related completed findings are context only; they do not change the deterministic finding.</p></div><span className={similarEvidence.availability === "available" ? "trace-status" : "trace-status degraded"}>{titleCase(similarEvidence.availability)}</span></div>{similarEvidence.availability === "available" ? <div className="similar-incidents-list">{similarEvidence.items.map((entry, index) => { const item = entry as Record<string, unknown>; return <article className="similar-incident" key={`${String(item.incident_id ?? index)}-${index}`}><strong>{String(item.statement ?? "Related finding")}</strong><span>{titleCase(String(item.category ?? "unknown"))} · Resolution: {titleCase(String(item.resolution ?? "review"))}</span></article>; })}</div> : <p className="hint">{similarEvidence.error ?? "No similar incident context is available."}</p>}</section>}{investigation.tool_trace?.length ? <details className="trace-section"><summary>View tool trace ({investigation.tool_trace.length} queries)</summary><div className="trace-list">{investigation.tool_trace.map((trace) => <div className="trace-row" key={trace.evidence_id}><span><strong>{titleCase(trace.source_type)}</strong><small>{trace.purpose ?? trace.tool}</small><small>{trace.tool}</small></span><span className={trace.status === "available" ? "trace-status" : "trace-status degraded"}>{titleCase(trace.status)} · {trace.duration_ms ?? "—"} ms</span></div>)}</div></details> : null}<div className="evidence-grid">{investigation.evidence.map((item, index) => <article className={`evidence-card ${item.availability !== "available" ? "degraded" : ""}`} id={`evidence-${item.id}`} key={item.id}><div className="evidence-card-heading"><div><strong>{titleCase(item.source_type)}</strong><small>{item.availability === "available" ? "Source available" : "Source degraded"}</small><small>Query: {item.query} · {item.duration_ms ?? "—"} ms</small></div><span className="badge">Evidence {index + 1}</span></div><div className="evidence-fields"><div className="evidence-field"><span>Parameters</span><strong>{readableValue(item.parameters)}</strong></div>{item.items.flatMap((entry) => objectRows(entry)).map(([key, value]) => <div className="evidence-field" key={`${item.id}-${key}`}><span>{key}</span><strong>{value}</strong></div>)}</div>{item.error && <p className="hint">Source note: {item.error}</p>}<details><summary>View raw payload</summary><pre>{JSON.stringify(item.items, null, 2)}</pre></details></article>)}</div></div></details>}
            <details className="secondary-section"><summary><span><strong>Audit trail</strong><small>{selected.timeline.length} events · alerts, pages, decisions, and actions</small></span><span className="count">Review</span></summary><div className="secondary-content" aria-labelledby="timeline-heading"><div className="section-heading"><div><h3 id="timeline-heading">What happened</h3></div><span className="count">{selected.timeline.length} events</span></div><ol className="timeline">{selected.timeline.map((event) => <li key={event.id}><div className="timeline-event"><span className="event-marker" /><div><strong>{titleCase(event.event_type)}</strong><p>{eventSummary(event)}</p><time>{new Date(event.event_time).toLocaleString()}</time><details><summary>View event data</summary><pre>{JSON.stringify(event.payload, null, 2)}</pre></details></div></div></li>)}</ol></div></details>
          </> : <div className="empty-state"><h2>Select an incident</h2><p className="muted">Choose an incident from the inbox to see what happened and what to do next.</p></div>}
        </article>
      </section>}
      {activeView === "kubernetes" && <section className="resource-analysis-panel" aria-labelledby="resource-health-heading">
        <div className="resource-analysis-header"><div><p className="product-name">Read-only resource analysis</p><h2 id="resource-health-heading">Kubernetes resource health</h2><p className="muted">Scan a captured workload snapshot for actionable problems without changing the cluster.</p></div><button type="button" className="resource-scan-button" onClick={runResourceScan} disabled={resourceScanPending}>{resourceScanPending ? "Scanning…" : "Run sample scan"}</button></div>
        {!resourceScan ? <p className="resource-empty muted">No scan yet. Run the sample to see the same evidence-first workflow used by the incident console.</p> : <><div className="resource-analysis-summary"><span><small>Status</small><strong>{titleCase(resourceScan.status)}</strong></span><span><small>Problems</small><strong>{resourceScan.problems}</strong></span><span><small>Resources scanned</small><strong>{resourceScan.resources_scanned}</strong></span><span><small>Analyzers</small><strong>{resourceScan.analyzers.filter((analyzer) => analyzer.read_only).length} read-only</strong></span></div><div className="resource-analysis-findings">{resourceScan.findings.map((item) => <article className="resource-finding" key={item.id}><div className="resource-finding-meta"><span>{titleCase(item.analyzer)}</span><span>{titleCase(item.severity)}</span></div><h3>{item.name}</h3><p>{item.reason}</p><small>Next: {titleCase(item.suggested_next_step)}</small></article>)}</div><p className="resource-read-only-note">Read-only scan: {resourceScan.analyzers.filter((analyzer) => analyzer.read_only).length} analyzers ran; no cluster changes were made.</p></>}
      </section>}
    </main>
  );
}
