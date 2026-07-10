"use client";

import { useEffect, useState } from "react";

import {
  fetchProjectOverview,
  generateStatusReport,
  type ProjectDashboard,
  type StatusReport,
} from "@/lib/projects";

export default function ProjectsPage() {
  const [dashboard, setDashboard] = useState<ProjectDashboard | null>(null);
  const [report, setReport] = useState<StatusReport | null>(null);

  useEffect(() => {
    void fetchProjectOverview().then(setDashboard);
  }, []);

  async function handleReport() {
    setReport(await generateStatusReport());
  }

  if (!dashboard) {
    return (
      <main className="page">
        <p className="muted">Loading project overview…</p>
      </main>
    );
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Phase 5 — Project intelligence</p>
        <h1>Projects</h1>
        <p className="lead">{dashboard.summary}</p>
      </section>

      <section className="panel">
        <h2>Processing health</h2>
        <ul>
          <li>Sources: {dashboard.processing_health.sources_enabled} / {dashboard.processing_health.sources_total} enabled</li>
          <li>Open contradictions: {dashboard.processing_health.open_contradictions}</li>
          <li>Pending graph projection events: {dashboard.processing_health.pending_outbox_events}</li>
        </ul>
        <button type="button" onClick={() => void handleReport()}>
          Generate status report
        </button>
      </section>

      <section className="panel">
        <h2>Repositories</h2>
        <ul>{dashboard.repositories.map((item) => <li key={item.id}>{item.name}</li>)}</ul>
        <h2>Technologies</h2>
        <ul>{dashboard.technologies.map((item) => <li key={item.id}>{item.name}</li>)}</ul>
        <h2>Open tasks</h2>
        <ul>{dashboard.open_tasks.map((task) => <li key={task}>{task}</li>)}</ul>
        <h2>Recent decisions</h2>
        <ul>{dashboard.decisions.map((item) => <li key={item}>{item}</li>)}</ul>
      </section>

      {report && (
        <section className="panel">
          <h2>{report.title}</h2>
          <p>{report.summary}</p>
          <pre>{JSON.stringify(report, null, 2)}</pre>
        </section>
      )}
    </main>
  );
}
