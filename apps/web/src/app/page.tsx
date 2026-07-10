import type { Metadata } from "next";
import "./globals.css";
import { getServerApiUrl } from "@/lib/api-url";

export const metadata: Metadata = {
  title: "Private Knowledge Base",
  description: "AI-powered personal knowledge operations system",
};

async function fetchHealth() {
  const apiUrl = getServerApiUrl();
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
        <p className="eyebrow">Phase 7 — Források és Q&amp;A</p>
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
            <a href="/settings">LLM és embedding beállítások</a>
          </li>
          <li>
            <a href="/sources">Források és szinkronizálás (Phase 7)</a>
          </li>
          <li>
            <a href="/search">Search (Phase 2)</a>
          </li>
          <li>
            <a href="/proposals">Approval queue (Phase 3)</a>
          </li>
          <li>
            <a href="/graph">Graph browser (Phase 4)</a>
          </li>
          <li>
            <a href="/ask">Ask a question (Phase 5)</a>
          </li>
          <li>
            <a href="/projects">Project overview (Phase 5)</a>
          </li>
          <li>Phase 6 — Hardening</li>
        </ul>
      </section>
    </main>
  );
}
