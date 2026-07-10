"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  getAppSettings,
  getLlmHealth,
  putAppSettings,
  type AppSettings,
  type LlmHealth,
} from "@/lib/settings";

const defaultSettings: AppSettings = {
  version: "1",
  llm: {
    enabled: true,
    base_url: "http://localhost:11434/v1",
    api_key_env: "LLM_API_KEY",
    extraction_model: "gpt-4o-mini",
    synthesis_model: "gpt-4o-mini",
    embedding: {
      provider: "auto",
      model: "text-embedding-3-small",
      dimension: 1536,
    },
  },
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [health, setHealth] = useState<LlmHealth | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function refresh() {
    const [loaded, llmHealth] = await Promise.all([getAppSettings(), getLlmHealth()]);
    if (loaded) {
      setSettings({
        version: loaded.version ?? "1",
        llm: { ...defaultSettings.llm, ...loaded.llm },
      });
    }
    setHealth(llmHealth);
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    const ok = await putAppSettings(settings);
    setSaving(false);
    if (!ok) {
      setMessage("Nem sikerült menteni a beállításokat.");
      return;
    }
    setMessage("Beállítások mentve.");
    await refresh();
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Beállítások</p>
        <h1>LLM és embedding</h1>
        <p className="lead">
          Itt állíthatod be a kivonás, válaszgenerálás és keresés modelljeit. Az API kulcs a{" "}
          <code>.env</code> fájlban marad.
        </p>
      </section>

      {message && <p className="message">{message}</p>}

      {health && (
        <section className="panel">
          <h2>Állapot</h2>
          <p>
            <strong>{health.status}</strong>
            {health.message ? ` — ${health.message}` : ""}
          </p>
          <p className="muted">
            API kulcs: {health.api_key_configured ? "beállítva" : "nincs beállítva"} · Embedding:{" "}
            {health.embedding_provider}
          </p>
        </section>
      )}

      <section className="panel wizard">
        <form className="form" onSubmit={(e) => void handleSave(e)}>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={settings.llm.enabled}
              onChange={(e) =>
                setSettings((s) => ({ ...s, llm: { ...s.llm, enabled: e.target.checked } }))
              }
            />
            LLM engedélyezve (kikapcsolva: heurisztikus kivonás és válasz)
          </label>

          <label>
            Szolgáltatás URL
            <input
              value={settings.llm.base_url}
              onChange={(e) =>
                setSettings((s) => ({ ...s, llm: { ...s.llm, base_url: e.target.value } }))
              }
              placeholder="http://localhost:11434/v1"
            />
          </label>

          <label>
            API kulcs környezeti változó
            <input
              value={settings.llm.api_key_env}
              onChange={(e) =>
                setSettings((s) => ({ ...s, llm: { ...s.llm, api_key_env: e.target.value } }))
              }
              placeholder="LLM_API_KEY"
            />
          </label>

          <label>
            Kivonás modell
            <input
              value={settings.llm.extraction_model}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  llm: { ...s.llm, extraction_model: e.target.value },
                }))
              }
            />
          </label>

          <label>
            Válasz modell
            <input
              value={settings.llm.synthesis_model}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  llm: { ...s.llm, synthesis_model: e.target.value },
                }))
              }
            />
          </label>

          <label>
            Embedding mód
            <select
              value={settings.llm.embedding.provider}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  llm: {
                    ...s.llm,
                    embedding: {
                      ...s.llm.embedding,
                      provider: e.target.value as "auto" | "hash" | "api",
                    },
                  },
                }))
              }
            >
              <option value="auto">Automatikus (API kulcs nélkül offline)</option>
              <option value="hash">Offline hash embedding</option>
              <option value="api">API embedding (kulcs szükséges)</option>
            </select>
          </label>

          <label>
            Embedding modell
            <input
              value={settings.llm.embedding.model}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  llm: {
                    ...s.llm,
                    embedding: { ...s.llm.embedding, model: e.target.value },
                  },
                }))
              }
            />
          </label>

          <label>
            Embedding dimenzió
            <input
              type="number"
              value={settings.llm.embedding.dimension}
              onChange={(e) =>
                setSettings((s) => ({
                  ...s,
                  llm: {
                    ...s.llm,
                    embedding: {
                      ...s.llm.embedding,
                      dimension: Number(e.target.value),
                    },
                  },
                }))
              }
            />
          </label>

          <button type="submit" className="button primary" disabled={saving}>
            {saving ? "Mentés…" : "Beállítások mentése"}
          </button>
        </form>
      </section>

      <p className="muted back-link">
        <Link href="/">← Vissza a főoldalra</Link>
        {" · "}
        <Link href="/sources">Források</Link>
      </p>
    </main>
  );
}
