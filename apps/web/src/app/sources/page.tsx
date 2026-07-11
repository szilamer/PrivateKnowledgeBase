"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  deleteSource,
  formatProcessingSummary,
  getSourceProcessingStats,
  getGoogleAuthUrl,
  listGoogleAccounts,
  listSources,
  listSyncRuns,
  revokeGoogleAccount,
  sourceTypeLabel,
  startSync,
  syncStatusLabel,
  pickDisplaySyncRun,
  hasStuckPendingSync,
  isSyncInFlight,
  type GoogleAccount,
  type Source,
  type SourceProcessingStats,
  type SyncRun,
} from "@/lib/api";

function isActiveSync(run: SyncRun | undefined): boolean {
  return run?.status === "pending" || run?.status === "running";
}

function anySyncInFlight(syncRuns: Record<string, SyncRun[]>): boolean {
  return Object.values(syncRuns).some((runs) => isSyncInFlight(runs));
}

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [accounts, setAccounts] = useState<GoogleAccount[]>([]);
  const [syncRuns, setSyncRuns] = useState<Record<string, SyncRun[]>>({});
  const [processingStats, setProcessingStats] = useState<Record<string, SourceProcessingStats>>(
    {},
  );
  const [message, setMessage] = useState<string | null>(null);
  const [syncingSourceId, setSyncingSourceId] = useState<string | null>(null);
  const [removingSourceId, setRemovingSourceId] = useState<string | null>(null);

  async function refresh() {
    const [items, googleAccounts] = await Promise.all([listSources(), listGoogleAccounts()]);
    setSources(items);
    setAccounts(googleAccounts);
    const runs: Record<string, SyncRun[]> = {};
    const stats: Record<string, SourceProcessingStats> = {};
    for (const source of items) {
      runs[source.id] = await listSyncRuns(source.id);
      const processing = await getSourceProcessingStats(source.id);
      if (processing) stats[source.id] = processing;
    }
    setSyncRuns(runs);
    setProcessingStats(stats);
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (!anySyncInFlight(syncRuns)) return;

    const interval = window.setInterval(() => {
      void refresh();
    }, 3000);

    return () => window.clearInterval(interval);
  }, [syncRuns]);

  async function handleSync(sourceId: string) {
    setSyncingSourceId(sourceId);
    setMessage(null);
    try {
      const run = await startSync(sourceId);
      if (!run) {
        setMessage("Nem sikerült elindítani a szinkronizálást.");
        return;
      }
      setMessage("Szinkronizálás elindítva — a háttérben fut, nagy mappáknál ez több percig is eltarthat.");
      await refresh();
    } finally {
      setSyncingSourceId(null);
    }
  }

  async function handleRemove(source: Source) {
    const hostPaths = Array.isArray(source.configuration.host_paths)
      ? (source.configuration.host_paths as string[]).join(", ")
      : "";
    const confirmed = window.confirm(
      `Eltávolítod a „${source.name}” forrást?\n\n` +
        "A forrás leáll, a jövőbeli szinkronizálás megszűnik. " +
        "A már jóváhagyott tudás a rendszerben megmarad.\n\n" +
        (hostPaths ? `Mappa: ${hostPaths}` : ""),
    );
    if (!confirmed) return;

    setRemovingSourceId(source.id);
    setMessage(null);
    try {
      const ok = await deleteSource(source.id);
      if (!ok) {
        setMessage("Nem sikerült eltávolítani a forrást.");
        return;
      }
      setMessage(`„${source.name}” forrás eltávolítva.`);
      await refresh();
    } finally {
      setRemovingSourceId(null);
    }
  }

  async function handleRevoke(alias: string) {
    const ok = await revokeGoogleAccount(alias);
    setMessage(ok ? "Google kapcsolat bontva." : "Nem sikerült bontani a kapcsolatot.");
    await refresh();
  }

  return (
    <main className="page sources-page">
      <section className="hero">
        <p className="eyebrow">Phase 7 — Források</p>
        <div className="hero-row">
          <div>
            <h1>Forrásaim</h1>
            <p className="lead">
              Mappák, Google Drive, email és naptár — egy helyen, egyszerűen.
            </p>
          </div>
          <div className="hero-actions">
            <Link className="button primary" href="/sources/connect">
              Forrás hozzáadása
            </Link>
            <Link className="button" href="/settings">
              LLM beállítások
            </Link>
          </div>
        </div>
      </section>

      {message && <p className="message">{message}</p>}

      {accounts.length > 0 && (
        <section className="panel account-strip">
          <h2>Csatlakoztatott fiókok</h2>
          {accounts.map((account) => (
            <div key={account.id} className="account-row">
              <div>
                <strong>{account.email ?? account.account_alias}</strong>
                <span className="muted"> — Csatlakoztatva</span>
              </div>
              <button type="button" onClick={() => void handleRevoke(account.account_alias)}>
                Kapcsolat bontása
              </button>
            </div>
          ))}
        </section>
      )}

      <section className="panel">
        {sources.length === 0 ? (
          <div className="empty-state">
            <p>
              Még nincs csatlakoztatott forrás. Add meg, honnan gyűjtse a rendszer a tudásodat —
              mappák, Drive, email vagy naptár.
            </p>
            <Link className="button primary" href="/sources/connect">
              Első forrás hozzáadása
            </Link>
          </div>
        ) : (
          <div className="source-grid">
            {sources.map((source) => {
              const runs = syncRuns[source.id] ?? [];
              const newest = runs[0];
              const display = pickDisplaySyncRun(runs);
              const processing = processingStats[source.id];
              const inFlight = isSyncInFlight(runs);
              const busy = syncingSourceId === source.id || inFlight;
              const stuckQueue = hasStuckPendingSync(runs);
              return (
                <article key={source.id} className="source-card">
                  <div className="source-card-head">
                    <div>
                      <h3>{source.name}</h3>
                      <p className="muted">{sourceTypeLabel(source.type)}</p>
                    </div>
                    <span className={`pill ${source.enabled ? "pill-ok" : "pill-muted"}`}>
                      {source.enabled ? "Aktív" : "Szüneteltetve"}
                    </span>
                  </div>
                  {display ? (
                    <p className={`run ${inFlight || isActiveSync(newest) ? "run-active" : ""}`}>
                      {syncStatusLabel(display.status)} — {display.objects_processed} feldolgozva
                      {display.objects_discovered > 0 ? ` / ${display.objects_discovered} fájl` : ""}
                      {display.objects_failed > 0 ? `, ${display.objects_failed} hiba` : ""}
                    </p>
                  ) : (
                    <p className="run muted">Még nem volt szinkronizálás.</p>
                  )}
                  {processing && (
                    <p className="run muted">{formatProcessingSummary(processing)}</p>
                  )}
                  {processing && processing.extraction_failed > 0 && (
                    <p className="muted sync-hint">
                      {processing.extraction_failed} fájl feldolgozási hibával —{" "}
                      {processing.recent_extraction_errors[0]?.external_id ?? "részletek az API-ban"}
                    </p>
                  )}
                  {stuckQueue && (
                    <p className="muted sync-hint">
                      Egy korábbi szinkron beragadt a sorban — nyomd meg újra a „Szinkronizálás most” gombot.
                    </p>
                  )}
                  {inFlight && (
                    <p className="muted sync-hint">
                      Szinkronizálás folyamatban — nagy mappáknál ez több percig is eltarthat.
                    </p>
                  )}
                  <div className="source-card-actions">
                    <button
                      type="button"
                      className="button primary"
                      onClick={() => void handleSync(source.id)}
                      disabled={busy || removingSourceId === source.id}
                    >
                      {busy ? "Szinkronizálás…" : "Szinkronizálás most"}
                    </button>
                    <button
                      type="button"
                      className="button danger"
                      onClick={() => void handleRemove(source)}
                      disabled={busy || removingSourceId === source.id}
                    >
                      {removingSourceId === source.id ? "Eltávolítás…" : "Forrás eltávolítása"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
