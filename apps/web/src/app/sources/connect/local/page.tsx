"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { FolderBrowser } from "@/components/FolderBrowser";
import { putSourcesConfig, registerLocalSource } from "@/lib/api";

export default function ConnectLocalPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [paths, setPaths] = useState<string[]>([]);
  const [extensions, setExtensions] = useState({ md: true, txt: true, pdf: true });
  const [syncNow, setSyncNow] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function addPath(path: string) {
    if (!paths.includes(path)) {
      setPaths((current) => [...current, path]);
    }
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
      setMessage("Nem sikerült hozzáadni a forrást. Ellenőrizd, hogy a mappa elérhető és olvasható.");
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
            <p className="muted">Böngéssz a mappák között, majd kattints a „Ezen a mappán kiválasztása” gombra.</p>
            <FolderBrowser
              selectedPaths={paths}
              onSelectPath={addPath}
              onRemovePath={removePath}
              onSuggestName={(suggested) => {
                if (!name) setName(suggested);
              }}
            />
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
            <ul>
              <li>
                <strong>Név:</strong> {name}
              </li>
              <li>
                <strong>Mappák:</strong> {paths.join(", ")}
              </li>
            </ul>
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
