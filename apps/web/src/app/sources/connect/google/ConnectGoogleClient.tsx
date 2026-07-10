"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getGoogleAuthUrl, listGoogleAccounts, putSourcesConfig } from "@/lib/api";

export default function ConnectGooglePage() {
  const searchParams = useSearchParams();
  const mode = searchParams.get("mode") ?? "drive";
  const connected = searchParams.get("connected") === "1";
  const [accounts, setAccounts] = useState<{ email: string | null; account_alias: string }[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [driveFolders, setDriveFolders] = useState("");
  const [gmailQuery, setGmailQuery] = useState("label:important newer_than:365d");
  const [calendarIds, setCalendarIds] = useState("primary");

  useEffect(() => {
    void listGoogleAccounts().then(setAccounts);
    if (connected) {
      setMessage("Google fiók sikeresen csatlakoztatva.");
    }
  }, [connected]);

  async function handleConnect() {
    const url = await getGoogleAuthUrl();
    if (!url) {
      setMessage(
        "Google csatlakozás nem elérhető. Állítsd be a GOOGLE_CLIENT_ID és GOOGLE_CLIENT_SECRET értékeket.",
      );
      return;
    }
    window.location.href = url;
  }

  async function handleSave() {
    const configId = `google-${mode}-${Date.now()}`;
    let source: Record<string, unknown>;
    if (mode === "gmail") {
      source = {
        id: configId,
        type: "gmail",
        name: "Fontos emailek",
        enabled: true,
        account: "google:primary",
        query: gmailQuery,
      };
    } else if (mode === "calendar") {
      source = {
        id: configId,
        type: "google_calendar",
        name: "Saját naptár",
        enabled: true,
        account: "google:primary",
        calendar_ids: calendarIds.split(",").map((item) => item.trim()).filter(Boolean),
      };
    } else {
      source = {
        id: configId,
        type: "google_drive",
        name: "Google Drive mappa",
        enabled: true,
        account: "google:primary",
        folder_ids: driveFolders.split(",").map((item) => item.trim()).filter(Boolean),
        include_google_docs: true,
      };
    }

    const ok = await putSourcesConfig({
      version: "1",
      sync: { on_startup: true, interval_minutes: 60 },
      sources: [source],
    });
    setMessage(ok ? "Google forrás mentve." : "Nem sikerült menteni a forrást.");
  }

  const hasAccount = accounts.length > 0;

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Google</p>
        <h1>
          {mode === "gmail" ? "Gmail" : mode === "calendar" ? "Google Naptár" : "Google Drive"}
        </h1>
        <p className="lead">
          Csak olvasási hozzáférés. A rendszer nem módosítja a fájljaidat vagy leveleidet.
        </p>
      </section>

      {message && <p className="message">{message}</p>}

      <section className="panel wizard">
        {!hasAccount ? (
          <>
            <h2>Bejelentkezés Google-lel</h2>
            <button type="button" className="button primary" onClick={() => void handleConnect()}>
              Bejelentkezés Google-lel
            </button>
          </>
        ) : (
          <>
            <p className="muted">Csatlakoztatva: {accounts[0]?.email}</p>
            {mode === "gmail" && (
              <label>
                Gmail szűrő
                <input value={gmailQuery} onChange={(e) => setGmailQuery(e.target.value)} />
              </label>
            )}
            {mode === "calendar" && (
              <label>
                Naptár azonosítók (vesszővel)
                <input value={calendarIds} onChange={(e) => setCalendarIds(e.target.value)} />
              </label>
            )}
            {mode === "drive" && (
              <label>
                Drive mappa azonosítók (vesszővel)
                <input
                  value={driveFolders}
                  onChange={(e) => setDriveFolders(e.target.value)}
                  placeholder="1A2B3C..."
                />
              </label>
            )}
            <button type="button" className="button primary" onClick={() => void handleSave()}>
              Forrás mentése
            </button>
          </>
        )}
      </section>

      <p className="muted back-link">
        <Link href="/sources/connect">← Vissza</Link>
      </p>
    </main>
  );
}
