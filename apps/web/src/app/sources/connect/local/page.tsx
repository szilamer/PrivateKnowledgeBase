"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { putSourcesConfig, registerLocalSource } from "@/lib/api";

export default function ConnectLocalPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [pathInput, setPathInput] = useState("");
  const [paths, setPaths] = useState<string[]>([]);
  const [extensions, setExtensions] = useState({ md: true, txt: true, pdf: true });
  const [syncNow, setSyncNow] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function addPath() {
    const trimmed = pathInput.trim();
    if (!trimmed) return;
    if (!paths.includes(trimmed)) {
      setPaths((current) => [...current, trimmed]);
      if (!name) {
        const base = trimmed.split("/").filter(Boolean).pop() ?? "Forrás";
        setName(base);
      }
    }
    setPathInput("");
  }

  function removePath(path: string) {
    setPaths((current) => current.filter((item) => item !== path));
  }

  async function handleSubmit() {
    setLoading(true);
    setMessage(null);
    const fileExtensions = [
      ...(extensions.md ? [".md"] : []),
      ...(extensions.txt ? [".txt"] : []),
      ...(extensions.pdf ? [".pdf"] : []),
    ];
    const created = await registerLocalSource({
      name,
      paths,
      file_extensions: fileExtensions,
    });
    if (!created) {
      setMessage("Nem sikerült hozzáadni a forrást. Ellenőrizd az elérési utakat.");
      setLoading(false);
      return;
    }

    const configId = `local-${Date.now()}`;
    await putSourcesConfig({
      version: "1",
      sync: { on_startup: syncNow, interval_minutes: 60 },
      sources: [
        {
          id: configId,
          type: "local_folder",
          name,
          enabled: true,
          paths,
          include_extensions: fileExtensions,
          exclude_globs: ["**/node_modules/**", "**/.git/**"],
        },
      ],
    });

    setMessage("Forrás hozzáadva.");
    setLoading(false);
    router.push("/sources");
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Helyi mappa — {step}. lépés / 4</p>
        <h1>Helyi mappa csatlakoztatása</h1>
      </section>

      {message && <p className="message">{message}</p>}

      <section className="panel wizard">
        {step === 1 && (
          <>
            <h2>Megjelenő név</h2>
            <p className="muted">Ezt a nevet látod a forráslistában.</p>
            <label>
              Név
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <button type="button" className="button primary" onClick={() => setStep(2)} disabled={!name}>
              Tovább
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <h2>Mappák kiválasztása</h2>
            <p className="muted">Add meg a mappa elérési útját (pl. ~/Projects).</p>
            <div className="chip-row">
              <input
                value={pathInput}
                onChange={(e) => setPathInput(e.target.value)}
                placeholder="~/Projects"
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addPath())}
              />
              <button type="button" onClick={addPath}>
                Hozzáadás
              </button>
            </div>
            <div className="chips">
              {paths.map((path) => (
                <span key={path} className="chip">
                  {path}
                  <button type="button" onClick={() => removePath(path)} aria-label="Eltávolítás">
                    ×
                  </button>
                </span>
              ))}
            </div>
            <div className="wizard-nav">
              <button type="button" onClick={() => setStep(1)}>
                Vissza
              </button>
              <button type="button" className="button primary" onClick={() => setStep(3)} disabled={paths.length === 0}>
                Tovább
              </button>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <h2>Fájltípusok</h2>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={extensions.md}
                onChange={(e) => setExtensions((s) => ({ ...s, md: e.target.checked }))}
              />
              Markdown
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={extensions.txt}
                onChange={(e) => setExtensions((s) => ({ ...s, txt: e.target.checked }))}
              />
              Szöveg
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={extensions.pdf}
                onChange={(e) => setExtensions((s) => ({ ...s, pdf: e.target.checked }))}
              />
              PDF
            </label>
            <div className="wizard-nav">
              <button type="button" onClick={() => setStep(2)}>
                Vissza
              </button>
              <button type="button" className="button primary" onClick={() => setStep(4)}>
                Tovább
              </button>
            </div>
          </>
        )}

        {step === 4 && (
          <>
            <h2>Összegzés</h2>
            <pre>{JSON.stringify({ name, paths, extensions }, null, 2)}</pre>
            <label className="checkbox">
              <input type="checkbox" checked={syncNow} onChange={(e) => setSyncNow(e.target.checked)} />
              Szinkronizálás azonnal
            </label>
            <div className="wizard-nav">
              <button type="button" onClick={() => setStep(3)}>
                Vissza
              </button>
              <button type="button" className="button primary" onClick={() => void handleSubmit()} disabled={loading}>
                {loading ? "Mentés…" : "Forrás hozzáadása"}
              </button>
            </div>
          </>
        )}
      </section>

      <p className="muted back-link">
        <Link href="/sources/connect">← Vissza</Link>
      </p>
    </main>
  );
}
