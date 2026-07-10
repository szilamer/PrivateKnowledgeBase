async function fetchHealth() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${apiUrl}/api/v1/health`, { cache: "no-store" });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const health = await fetchHealth();

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Phase 0 — Platform Foundation</p>
        <h1>Private Knowledge Base</h1>
        <p className="lead">
          Development environment for the AI-powered personal knowledge operations system.
        </p>
      </section>

      <section className="panel">
        <h2>API Health</h2>
        {health ? (
          <pre>{JSON.stringify(health, null, 2)}</pre>
        ) : (
          <p className="muted">API unreachable. Start services with <code>make up</code>.</p>
        )}
      </section>

      <section className="panel">
        <h2>Next steps</h2>
        <ul>
          <li>
            <a href="/sources">Sources &amp; synchronization (Phase 1)</a>
          </li>
          <li>Phase 2 — Parsing and retrieval foundation</li>
          <li>Phase 3 — Knowledge proposals</li>
        </ul>
      </section>
    </main>
  );
}
