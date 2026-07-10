"use client";

import { useEffect, useState } from "react";

import { browseLocalFolder, type LocalBrowseResult } from "@/lib/api";

type FolderBrowserProps = {
  selectedPaths: string[];
  onSelectPath: (path: string) => void;
  onRemovePath: (path: string) => void;
  onSuggestName?: (name: string) => void;
};

export function FolderBrowser({
  selectedPaths,
  onSelectPath,
  onRemovePath,
  onSuggestName,
}: FolderBrowserProps) {
  const [browse, setBrowse] = useState<LocalBrowseResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [manualPath, setManualPath] = useState("");

  async function load(path: string) {
    setLoading(true);
    const result = await browseLocalFolder(path);
    setBrowse(result);
    setLoading(false);
  }

  useEffect(() => {
    void load("~");
  }, []);

  function handleSelectCurrent() {
    if (!browse?.can_select || browse.error) return;
    onSelectPath(browse.path);
    const base = browse.path.split("/").filter(Boolean).pop();
    if (base && onSuggestName) {
      onSuggestName(base);
    }
  }

  function handleManualAdd() {
    const trimmed = manualPath.trim();
    if (!trimmed) return;
    onSelectPath(trimmed);
    const base = trimmed.split("/").filter(Boolean).pop();
    if (base && onSuggestName) {
      onSuggestName(base);
    }
    setManualPath("");
  }

  const crumbs = buildBreadcrumbs(browse?.path ?? "~");

  return (
    <div className="folder-browser">
      <div className="browser-toolbar">
        <button type="button" className="button" onClick={() => void load("~")} disabled={loading}>
          Kezdőlap (~)
        </button>
        {browse?.parent_path && (
          <button
            type="button"
            className="button"
            onClick={() => void load(browse.parent_path!)}
            disabled={loading}
          >
            ↑ Szülő mappa
          </button>
        )}
        <button
          type="button"
          className="button primary"
          onClick={handleSelectCurrent}
          disabled={loading || !browse?.can_select || Boolean(browse?.error)}
        >
          Ezen a mappán kiválasztása
        </button>
      </div>

      <nav className="breadcrumbs" aria-label="Mappa útvonal">
        {crumbs.map((crumb, index) => (
          <span key={crumb.path}>
            {index > 0 && <span className="muted"> / </span>}
            <button type="button" className="crumb" onClick={() => void load(crumb.path)} disabled={loading}>
              {crumb.label}
            </button>
          </span>
        ))}
      </nav>

      {browse?.error && <p className="message">{browse.error}</p>}
      {loading && <p className="muted">Mappák betöltése…</p>}

      <ul className="folder-list">
        {(browse?.entries ?? []).map((entry) => (
          <li key={entry.path}>
            <button type="button" className="folder-item" onClick={() => void load(entry.path)} disabled={loading}>
              <span className="folder-icon">📁</span>
              <span>{entry.name}</span>
              {entry.has_children && <span className="muted">›</span>}
            </button>
          </li>
        ))}
        {!loading && (browse?.entries?.length ?? 0) === 0 && !browse?.error && (
          <li className="muted">Nincs további almappa.</li>
        )}
      </ul>

      {selectedPaths.length > 0 && (
        <div className="chips">
          {selectedPaths.map((path) => (
            <span key={path} className="chip">
              {path}
              <button type="button" onClick={() => onRemovePath(path)} aria-label="Eltávolítás">
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <details className="advanced-panel">
        <summary>Több beállítás — útvonal kézi megadása</summary>
        <div className="chip-row">
          <input
            value={manualPath}
            onChange={(e) => setManualPath(e.target.value)}
            placeholder="~/Projects"
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleManualAdd())}
          />
          <button type="button" onClick={handleManualAdd}>
            Hozzáadás
          </button>
        </div>
      </details>
    </div>
  );
}

function buildBreadcrumbs(path: string): Array<{ label: string; path: string }> {
  if (path === "~") {
    return [{ label: "~", path: "~" }];
  }
  const parts = path.replace(/^~\/?/, "").split("/").filter(Boolean);
  const crumbs: Array<{ label: string; path: string }> = [{ label: "~", path: "~" }];
  let accumulated = "";
  for (const part of parts) {
    accumulated = accumulated ? `${accumulated}/${part}` : part;
    crumbs.push({ label: part, path: `~/${accumulated}` });
  }
  return crumbs;
}
