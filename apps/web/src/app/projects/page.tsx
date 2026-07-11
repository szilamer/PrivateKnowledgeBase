"use client";

import { useEffect, useState } from "react";

import {
  createProjectReport,
  fetchProjectOverview,
  generateStatusReport,
  getProjectReport,
  type ProjectDashboard,
  type ProjectReport,
  type StatusReport,
} from "@/lib/projects";

export default function ProjectsPage() {
  const [dashboard, setDashboard] = useState<ProjectDashboard | null>(null);
  const [report, setReport] = useState<StatusReport | null>(null);
  const [projectReport, setProjectReport] = useState<ProjectReport | null>(null);
  const [reportMessage, setReportMessage] = useState<string | null>(null);

  useEffect(() => {
    void fetchProjectOverview().then(setDashboard);
  }, []);

  async function handleReport() {
    setReport(await generateStatusReport());
  }

  async function handleProjectReport(projectId: string) {
    setReportMessage(null);
    const created = await createProjectReport(projectId);
    if (!created) {
      setReportMessage("Nem sikerült elindítani a projektjelentést.");
      return;
    }
    setProjectReport(created);
    if (created.status === "completed" && created.markdown) {
      setReportMessage("Projektjelentés elkészült.");
      return;
    }
    for (let attempt = 0; attempt < 8; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 1500));
      const latest = await getProjectReport(projectId, created.id);
      if (!latest) continue;
      setProjectReport(latest);
      if (latest.status === "completed" || latest.status === "failed") {
        setReportMessage(
          latest.status === "completed"
            ? "Projektjelentés elkészült."
            : latest.error_summary ?? "A jelentés generálása sikertelen.",
        );
        return;
      }
    }
    setReportMessage("A jelentés még készül a háttérben — frissíts később.");
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
        {dashboard.projects.length > 0 && (
          <button
            type="button"
            onClick={() => void handleProjectReport(dashboard.projects[0].id)}
          >
            Projektjelentés generálása ({dashboard.projects[0].name})
          </button>
        )}
        {reportMessage && <p className="muted">{reportMessage}</p>}
      </section>

      <section className="panel">
        <h2>Projects</h2>
        <ul>
          {dashboard.projects.map((item) => (
            <li key={item.id}>
              {item.name}{" "}
              <button type="button" onClick={() => void handleProjectReport(item.id)}>
                Jelentés
              </button>
            </li>
          ))}
        </ul>
        <h2>Repositories</h2>
        <ul>{dashboard.repositories.map((item) => <li key={item.id}>{item.name}</li>)}</ul>
        <h2>Technologies</h2>
        <ul>{dashboard.technologies.map((item) => <li key={item.id}>{item.name}</li>)}</ul>
        <h2>Open tasks</h2>
        <ul>{dashboard.open_tasks.map((task) => <li key={task}>{task}</li>)}</ul>
        <h2>Recent decisions</h2>
        <ul>{dashboard.decisions.map((item) => <li key={item}>{item}</li>)}</ul>
      </section>

      {projectReport?.markdown && (
        <section className="panel">
          <h2>{projectReport.title}</h2>
          <pre>{projectReport.markdown}</pre>
        </section>
      )}

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
