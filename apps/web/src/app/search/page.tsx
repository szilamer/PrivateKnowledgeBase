"use client";

import { useState } from "react";

import { searchKnowledge, type SearchHit } from "@/lib/search";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"hybrid" | "keyword" | "semantic">("hybrid");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    setMessage(null);
    const results = await searchKnowledge(query, mode);
    setHits(results);
    if (results.length === 0) {
      setMessage("No results. Ensure sources are synced and processed.");
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Phase 2 — Retrieval</p>
        <h1>Search</h1>
        <p className="lead">Keyword, semantic, and hybrid search over ingested content.</p>
      </section>

      <section className="panel">
        <form className="form" onSubmit={handleSearch}>
          <label>
            Query
            <input value={query} onChange={(e) => setQuery(e.target.value)} required />
          </label>
          <label>
            Mode
            <select value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
              <option value="hybrid">Hybrid</option>
              <option value="keyword">Keyword</option>
              <option value="semantic">Semantic</option>
            </select>
          </label>
          <button type="submit">Search</button>
        </form>
      </section>

      {message && <p className="message">{message}</p>}

      <section className="panel">
        <h2>Results ({hits.length})</h2>
        {hits.map((hit) => (
          <article key={hit.chunk_id} className="hit">
            <p className="hit-meta">
              {hit.external_id} · {hit.match_type} · score {hit.score.toFixed(3)}
            </p>
            <p>{hit.text}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
