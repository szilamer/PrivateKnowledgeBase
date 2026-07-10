"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  getGoogleAuthUrl,
  listGoogleAccounts,
  listSources,
  listSyncRuns,
  revokeGoogleAccount,
  sourceTypeLabel,
  startSync,
  syncStatusLabel,
  type GoogleAccount,
  type Source,
  type SyncRun,
} from "@/lib/api";

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [accounts, setAccounts] = useState<GoogleAccount[]>([]);
  const [syncRuns, setSyncRuns] = useState<Record<string, SyncRun[]>>({});
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    const [items, googleAccounts] = await Promise.all([listSources(), listGoogleAccounts()]);
    setSources(items);
    setAccounts(googleAccounts);
    const runs: Record<string, SyncRun[]> = {};
    for (const source of items) {
      runs[source.id] = await listSyncRuns(source.id);
    }
    setSyncRuns(runs);
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSync(sourceId: string) {
    const run = await startSync(sourceId);
    if (!run) {
      setMessage("Nem sikerült elindítani a szinkronizálást.");
      return;
    }
    setMessage("Szinkronizálás elindítva.");
    await refresh();
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
              const latest = (syncRuns[source.id] ?? [])[0];
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
                  {latest && (
                    <p className="run">
                      {syncStatusLabel(latest.status)} — {latest.objects_processed} feldolgozva
                      {latest.objects_failed > 0 ? `, ${latest.objects_failed} hiba` : ""}
                    </p>
                  )}
                  <div className="source-card-actions">
                    <button type="button" onClick={() => void handleSync(source.id)}>
                      Szinkronizálás most
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
