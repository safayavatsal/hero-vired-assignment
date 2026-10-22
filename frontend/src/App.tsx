import { useEffect, useState } from "react";

type Incident = { id: string; service: string; severity: string; status: string; summary: string; alert_count: number; updated_at: string };
type TimelineEvent = { id: string; event_type: string; event_time: string };
type IncidentDetail = Incident & { timeline: TimelineEvent[] };

export function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<IncidentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadIncident = (id: string) => fetch(`/api/v1/incidents/${id}`)
    .then((response) => response.json() as Promise<IncidentDetail>)
    .then(setSelected)
    .catch(() => setError("The incident detail is unavailable."));

  const loadIncidents = () => fetch("/api/v1/incidents")
    .then((response) => response.json() as Promise<Incident[]>)
    .then((items) => { setIncidents(items); if (!selected && items[0]) loadIncident(items[0].id); })
    .catch(() => setError("The incident list is unavailable."));

  useEffect(() => { loadIncidents(); const timer = window.setInterval(loadIncidents, 5000); return () => window.clearInterval(timer); }, []);

  return (
    <main>
      <header><p className="eyebrow">Incident console</p><h1>On-call assistant</h1><p className="muted">A durable view of alerts, decisions, and actions.</p></header>
      {error && <p role="alert">{error}</p>}
      <section className="layout" aria-label="Incidents">
        <div className="panel"><h2>Incidents</h2>{incidents.length === 0 ? <p className="muted">No incidents yet.</p> : incidents.map((incident) => (
          <button className={`incident ${selected?.id === incident.id ? "selected" : ""}`} key={incident.id} onClick={() => loadIncident(incident.id)}>
            <span><strong>{incident.service}</strong><small>{incident.summary}</small></span><span className="badge">{incident.status}</span>
          </button>
        ))}</div>
        <div className="panel"><h2>{selected ? selected.service : "Select an incident"}</h2>{selected ? <><p>{selected.summary}</p><p className="muted">{selected.severity} · {selected.alert_count} alert(s) · {selected.status}</p><ol className="timeline">{selected.timeline.map((event) => <li key={event.id}><strong>{event.event_type}</strong><time>{new Date(event.event_time).toLocaleString()}</time></li>)}</ol></> : <p className="muted">Create an alert to see its timeline.</p>}</div>
      </section>
    </main>
  );
}
