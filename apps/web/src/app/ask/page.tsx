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
        <p className="eyebrow">Phase 5 — Question answering</p>
        <h1>Ask</h1>
        <p className="lead">Hybrid retrieval with source-backed answers and citations.</p>
      </section>

      <section className="panel">
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Question
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              required
              rows={3}
            />
          </label>
          <label>
            Retrieval mode
            <select value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
              <option value="hybrid">Hybrid</option>
              <option value="keyword">Keyword</option>
              <option value="semantic">Semantic</option>
            </select>
          </label>
          <button type="submit">Ask</button>
        </form>
      </section>

      {answer && (
        <section className="panel">
          <h2>Answer</h2>
          <p className="hit-meta">
            confidence {answer.confidence.toFixed(2)}
            {answer.model ? ` · ${answer.model}` : ""}
            {answer.insufficient_evidence ? " · insufficient evidence" : ""}
          </p>
          <p>{answer.answer}</p>

          <h3>Citations ({answer.citations.length})</h3>
          {answer.citations.map((citation) => (
            <article key={citation.citation_id} className="hit">
              <p className="hit-meta">
                {citation.signal} · score {citation.score.toFixed(3)}
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
