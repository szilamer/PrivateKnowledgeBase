"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { FolderBrowser } from "@/components/FolderBrowser";
import { getSyncRun, registerLocalSource, startSync, syncStatusLabel, type SyncRun } from "@/lib/api";

export default function ConnectLocalPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [paths, setPaths] = useState<string[]>([]);
  const [extensions, setExtensions] = useState({ md: true, txt: true, pdf: true });
  const [syncNow, setSyncNow] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncRun, setSyncRun] = useState<SyncRun | null>(null);

  function addPath(path: string) {
    if (!paths.includes(path)) {
      setPaths((current) => [...current, path]);
    }
  }

  function removePath(path: string) {
    setPaths((current) => current.filter((item) => item !== path));
  }

  useEffect(() => {
    if (!syncRun || syncRun.status === "completed" || syncRun.status === "failed" || syncRun.status === "partial") {
      return;
    }

    const interval = window.setInterval(() => {
      void getSyncRun(syncRun.id).then((latest) => {
        if (latest) setSyncRun(latest);
      });
    }, 2000);

    return () => window.clearInterval(interval);
  }, [syncRun]);

  async function handleSubmit() {
    setLoading(true);
    setMessage(null);
    setSyncRun(null);

    const fileExtensions = [
      ...(extensions.md ? [".md"] : []),
      ...(extensions.txt ? [".txt"] : []),
      ...(extensions.pdf ? [".pdf"] : []),
    ];

    try {
      const created = await registerLocalSource({
        name,
        paths,
        file_extensions: fileExtensions,
      });
      if (!created) {
        setMessage("Nem sikerült hozzáadni a forrást. Ellenőrizd, hogy a mappa elérhető és olvasható.");
        return;
      }

      if (syncNow) {
        const run = await startSync(created.id);
        if (!run) {
          setMessage("A forrás létrejött, de a szinkronizálást nem sikerült elindítani. A források oldalon újra próbálhatod.");
          setStep(5);
          return;
        }
        setSyncRun(run);
      }

      setStep(5);
    } catch {
      setMessage("Váratlan hiba történt. Ellenőrizd, hogy az API fut-e (http://localhost:8000).");
    } finally {
      setLoading(false);
    }
  }

  const syncInProgress =
    syncRun !== null && (syncRun.status === "pending" || syncRun.status === "running");

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Helyi mappa — {step === 5 ? "kész" : `${step}. lépés / 4`}</p>
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
            <p className="muted">
              A szinkronizálás a háttérben fut. Nagy mappáknál ez több percig is eltarthat — nem kell várni, a
              források oldalon követheted az állapotot.
            </p>
            <div className="wizard-nav">
              <button type="button" onClick={() => setStep(3)} disabled={loading}>
                Vissza
              </button>
              <button type="button" className="button primary" onClick={() => void handleSubmit()} disabled={loading}>
                {loading ? "Forrás hozzáadása…" : "Forrás hozzáadása"}
              </button>
            </div>
          </>
        )}

        {step === 5 && (
          <>
            <h2>Forrás hozzáadva</h2>
            <p className="muted">
              <strong>{name}</strong> sikeresen csatlakoztatva ({paths.join(", ")}).
            </p>
            {syncRun ? (
              <div className="sync-status-panel">
                <p className="run">
                  {syncStatusLabel(syncRun.status)} — {syncRun.objects_processed} feldolgozva
                  {syncRun.objects_discovered > 0 ? ` / ${syncRun.objects_discovered} fájl` : ""}
                  {syncRun.objects_failed > 0 ? `, ${syncRun.objects_failed} hiba` : ""}
                </p>
                {syncInProgress && (
                  <p className="muted">
                    A szinkronizálás fut a háttérben. Nagy mappáknál ez több percig is eltarthat — nyugodtan menj
                    tovább, az állapot a források oldalon is frissül.
                  </p>
                )}
                {syncRun.status === "failed" && syncRun.error_summary && (
                  <p className="message">{syncRun.error_summary}</p>
                )}
              </div>
            ) : (
              <p className="muted">A szinkronizálást később indíthatod a források oldalról.</p>
            )}
            <div className="wizard-nav">
              <button type="button" className="button primary" onClick={() => router.push("/sources")}>
                Tovább a forrásokhoz
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
