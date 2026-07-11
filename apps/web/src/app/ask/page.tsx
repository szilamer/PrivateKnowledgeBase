"use client";

import { useState } from "react";

import { askQuestion, type QuestionAnswer } from "@/lib/questions";

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<"hybrid" | "keyword" | "semantic">("hybrid");
  const [answer, setAnswer] = useState<QuestionAnswer | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const result = await askQuestion(question, mode);
    setAnswer(result);
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Kérdezés</p>
        <h1>Kérdezz a tudásbázisról</h1>
        <p className="lead">
          Hibrid keresés forrás-alapú válasszal és hivatkozásokkal. A rendszer jelzi, ha kevés a
          bizonyíték vagy ellentmondás van.
        </p>
      </section>

      <section className="panel">
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Kérdés
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              required
              rows={3}
            />
          </label>
          <label>
            Keresési mód
            <select value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
              <option value="hybrid">Hibrid</option>
              <option value="keyword">Kulcsszó</option>
              <option value="semantic">Szemantikus</option>
            </select>
          </label>
          <button type="submit">Kérdezés</button>
        </form>
      </section>

      {answer && (
        <section className="panel">
          <h2>Válasz</h2>
          <p className="hit-meta">
            bizonyosság {answer.confidence.toFixed(2)}
            {answer.model ? ` · ${answer.model}` : ""}
            {answer.insufficient_evidence ? " · kevés bizonyíték" : ""}
          </p>
          <p>{answer.answer}</p>

          {answer.warnings.length > 0 && (
            <>
              <h3>Figyelmeztetések</h3>
              <ul className="guide-list">
                {answer.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </>
          )}

          {answer.conflicts.length > 0 && (
            <>
              <h3>Ellentmondások a bizonyítékban</h3>
              <ul className="guide-list">
                {answer.conflicts.map((conflict) => (
                  <li key={conflict}>{conflict}</li>
                ))}
              </ul>
            </>
          )}

          <h3>Hivatkozások ({answer.citations.length})</h3>
          {answer.citations.map((citation) => (
            <article key={citation.citation_id} className="hit">
              <p className="hit-meta">
                {citation.signal} · pontszám {citation.score.toFixed(3)}
                {citation.external_id ? ` · ${citation.external_id}` : ""}
              </p>
              <p>{citation.excerpt}</p>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
