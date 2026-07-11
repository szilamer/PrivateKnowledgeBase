"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  clearLlmApiKey,
  getAppSettings,
  getLlmHealth,
  putAppSettings,
  putLlmApiKey,
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
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [savingApiKey, setSavingApiKey] = useState(false);

  const apiKeyConfigured = settings.effective?.llm.api_key_configured ?? health?.api_key_configured ?? false;
  const apiKeyPreview = settings.effective?.llm.api_key_preview ?? null;

  async function refresh() {
    const [loaded, llmHealth] = await Promise.all([getAppSettings(), getLlmHealth()]);
    if (loaded) {
      setSettings({
        version: loaded.version ?? "1",
        llm: { ...defaultSettings.llm, ...loaded.llm },
        effective: loaded.effective,
      });
    }
    setHealth(llmHealth);
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSaveApiKey(event: React.FormEvent) {
    event.preventDefault();
    if (!apiKeyInput.trim()) {
      setMessage("Írd be az API kulcsot a mentéshez.");
      return;
    }
    setSavingApiKey(true);
    setMessage(null);
    const result = await putLlmApiKey(apiKeyInput.trim());
    setSavingApiKey(false);
    if (!result) {
      setMessage("Nem sikerült menteni az API kulcsot.");
      return;
    }
    setApiKeyInput("");
    setMessage(result.message);
    await refresh();
  }

  async function handleClearApiKey() {
    if (!window.confirm("Biztosan törlöd a mentett API kulcsot?")) return;
    setSavingApiKey(true);
    setMessage(null);
    const ok = await clearLlmApiKey();
    setSavingApiKey(false);
    if (!ok) {
      setMessage("Nem sikerült törölni az API kulcsot.");
      return;
    }
    setMessage("API kulcs törölve.");
    await refresh();
  }

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
          Itt állíthatod be a modellt és a szolgáltatás címét. Az API kulcsot az alábbi űrlapon add meg —
          a rendszer automatikusan, biztonságosan eltárolja.
        </p>
      </section>

      {message && <p className="message">{message}</p>}

      <section className="panel api-key-panel">
        <h2>API kulcs</h2>
        <p>
          Illeszd be az OpenAI (vagy más kompatibilis) API kulcsodat. A kulcs a szerveren tárolódik, nem a
          böngészőben, és soha nem jelenik meg újra teljes egészében.
        </p>
        <form className="form" onSubmit={(e) => void handleSaveApiKey(e)}>
          <label>
            API kulcs
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder="sk-proj-..."
              autoComplete="off"
            />
            <span className="field-hint">
              {apiKeyConfigured
                ? `Jelenleg beállítva: ${apiKeyPreview ?? "••••"} — új kulcs felülírja a régit.`
                : "Még nincs mentett kulcs."}
            </span>
          </label>
          <div className="form-actions">
            <button type="submit" className="button primary" disabled={savingApiKey}>
              {savingApiKey ? "Mentés…" : "API kulcs mentése"}
            </button>
            {apiKeyConfigured && (
              <button type="button" className="button danger" onClick={() => void handleClearApiKey()} disabled={savingApiKey}>
                Kulcs törlése
              </button>
            )}
          </div>
        </form>
        <p className={`api-key-status ${apiKeyConfigured ? "ok" : "missing"}`}>
          Állapot:{" "}
          <strong>{apiKeyConfigured ? "API kulcs beállítva" : "API kulcs nincs beállítva"}</strong>
          {apiKeyConfigured ? " — azonnal használható, újraindítás nem kell." : " — add meg fent, majd mentsd."}
        </p>
      </section>

      {health && (
        <section className="panel">
          <h2>Szolgáltatás állapota</h2>
          <p>
            <strong>{health.status}</strong>
            {health.message ? ` — ${health.message}` : ""}
          </p>
          <p className="muted">
            Embedding: {health.embedding_provider} · URL: {health.base_url}
          </p>
        </section>
      )}

      <section className="panel wizard">
        <h2>Modell beállítások</h2>
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
              placeholder="https://api.openai.com/v1"
            />
            <span className="field-hint">OpenAI-hoz: https://api.openai.com/v1 · Ollama-hoz: http://localhost:11434/v1</span>
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
              <option value="auto">Automatikus (kulcs nélkül offline)</option>
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
        <Link href="/sources">← Források</Link>
      </p>
    </main>
  );
}
