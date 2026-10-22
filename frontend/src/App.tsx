import { useEffect, useState } from "react";

type Health = {
  status: string;
  service: string;
};

export function App() {
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    fetch("/api/v1/health")
      .then((response) => response.json() as Promise<Health>)
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <main>
      <p className="eyebrow">Incident console</p>
      <h1>On-call assistant</h1>
      <p>Baseline runtime is ready for the incident workflow.</p>
      <output aria-live="polite">
        API: {health ? `${health.status} (${health.service})` : "checking"}
      </output>
    </main>
  );
}
