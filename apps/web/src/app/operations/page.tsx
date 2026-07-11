"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  fetchOperationsStatus,
  rebuildProjection,
  runMaintenanceRecovery,
  type MaintenanceRunResult,
  type OperationsStatus,
} from "@/lib/operations";

export default function OperationsPage() {
  const [status, setStatus] = useState<OperationsStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setStatus(await fetchOperationsStatus());
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleMaintenance() {
    setBusy(true);
    setMessage(null);
    try {
      const result: MaintenanceRunResult | null = await runMaintenanceRecovery();
      if (!result) {
        setMessage("A karbantartási futás nem indult el.");
        return;
      }
      setMessage(
        result.pipeline_recovery_enqueued
          ? "Pipeline helyreállítás elindítva."
          : "Karbantartás lefutott — nincs új pipeline teendő.",
      );
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function handleRebuild() {
    setBusy(true);
    setMessage(null);
    try {
      const ok = await rebuildProjection(true);
      setMessage(ok ? "Graf projekció újraépítés háttérben elindítva." : "Nem sikerült elindítani.");
    } finally {
      setBusy(false);
    }
  }

  if (!status) {
    return (
      <main className="page">
        <p className="muted">Rendszerállapot betöltése…</p>
      </main>
    );
  }

  return (
    <main className="page operations-page">
      <section className="hero">
        <p className="eyebrow">Phase I — Üzemeltetés</p>
        <h1>Rendszerállapot</h1>
        <p className="lead">{status.status_summary_hu}</p>
      </section>

      {message && <p className="message">{message}</p>}

      <section className="panel">
        <h2>Pipeline</h2>
        <ul>
          <li>Feldolgozás várakozó: {status.pipeline.extraction_pending}</li>
          <li>Feldolgozási hibák: {status.pipeline.extraction_failed}</li>
          <li>Tudás várakozó: {status.pipeline.knowledge_pending}</li>
          <li>Besorolás várakozó: {status.pipeline.triage_pending}</li>
          <li>
            Embedding modell eltérés: {status.pipeline.embedding_model_mismatch_versions}
          </li>
        </ul>
        <h2>Outbox / kanonikus tudás</h2>
        <ul>
          <li>Outbox várakozó: {status.pending_outbox_events}</li>
          <li>Outbox hibás: {status.failed_outbox_events}</li>
          <li>Kanonikus entitások: {status.canonical_entities}</li>
          <li>Kanonikus állítások: {status.canonical_claims}</li>
        </ul>
        {status.maintenance_recommended && (
          <p className="muted sync-hint">
            A rendszer karbantartást javasol — indíts helyreállítást vagy ellenőrizd a worker logokat.
          </p>
        )}
        <div className="source-card-actions">
          <button type="button" className="button primary" disabled={busy} onClick={() => void handleMaintenance()}>
            {busy ? "Fut…" : "Karbantartás futtatása"}
          </button>
          <button type="button" className="button" disabled={busy} onClick={() => void handleRebuild()}>
            Graf újraépítés
          </button>
          <Link className="button" href="/sources">
            Források
          </Link>
        </div>
      </section>
    </main>
  );
}
