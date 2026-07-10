"use client";

import { useEffect, useState } from "react";

import {
  listSources,
  listSyncRuns,
  registerLocalSource,
  startSync,
  type Source,
  type SyncRun,
} from "@/lib/api";

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [syncRuns, setSyncRuns] = useState<Record<string, SyncRun[]>>({});
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    const items = await listSources();
    setSources(items);
    const runs: Record<string, SyncRun[]> = {};
    for (const source of items) {
      runs[source.id] = await listSyncRuns(source.id);
    }
    setSyncRuns(runs);
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleRegister(event: React.FormEvent) {
    event.preventDefault();
    const created = await registerLocalSource(name, path);
    if (!created) {
      setMessage("Failed to register source.");
      return;
    }
    setMessage(`Registered source: ${created.name}`);
    setName("");
    setPath("");
    await refresh();
  }

  async function handleSync(sourceId: string) {
    const run = await startSync(sourceId);
    if (!run) {
      setMessage("Failed to start sync.");
      return;
    }
    setMessage(`Sync started: ${run.id} (${run.status})`);
    await refresh();
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">MVP-01 / MVP-02</p>
        <h1>Sources</h1>
        <p className="lead">Register local folders and trigger synchronization runs.</p>
      </section>

      {message && <p className="message">{message}</p>}

      <section className="panel">
        <h2>Register local folder</h2>
        <form className="form" onSubmit={handleRegister}>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Path
            <input value={path} onChange={(e) => setPath(e.target.value)} required />
          </label>
          <button type="submit">Register</button>
        </form>
      </section>

      <section className="panel">
        <h2>Registered sources</h2>
        {sources.length === 0 ? (
          <p className="muted">No sources yet.</p>
        ) : (
          <ul className="source-list">
            {sources.map((source) => (
              <li key={source.id}>
                <div className="source-row">
                  <div>
                    <strong>{source.name}</strong>
                    <span className="muted"> ({source.type})</span>
                  </div>
                  <button type="button" onClick={() => void handleSync(source.id)}>
                    Sync
                  </button>
                </div>
                <pre className="config">{JSON.stringify(source.configuration, null, 2)}</pre>
                {(syncRuns[source.id] ?? []).slice(0, 3).map((run) => (
                  <p key={run.id} className="run">
                    {run.status} — discovered {run.objects_discovered}, processed{" "}
                    {run.objects_processed}, failed {run.objects_failed}
                    {run.error_summary ? ` — ${run.error_summary}` : ""}
                  </p>
                ))}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
