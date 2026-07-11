"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  fetchNeighborhood,
  listContradictions,
  listEntities,
  type CanonicalEntity,
  type Contradiction,
  type GraphView,
} from "@/lib/graph";

const ENTITY_TYPE_LABELS: Record<string, string> = {
  technology: "technológia",
  concept: "fogalom",
  person: "személy",
  organization: "szervezet",
  project: "projekt",
  document: "dokumentum",
};

function entityTypeLabel(type: string): string {
  return ENTITY_TYPE_LABELS[type] ?? type;
}

export default function GraphPage() {
  const [entities, setEntities] = useState<CanonicalEntity[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [graph, setGraph] = useState<GraphView | null>(null);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [contradictions, setContradictions] = useState<Contradiction[]>([]);

  async function loadEntity(entityId: string) {
    setSelectedId(entityId);
    setLoadingGraph(true);
    setGraph(await fetchNeighborhood(entityId));
    setLoadingGraph(false);
  }

  useEffect(() => {
    void (async () => {
      const [items, openContradictions] = await Promise.all([
        listEntities(),
        listContradictions(),
      ]);
      setEntities(items);
      setContradictions(openContradictions);
      if (items.length > 0) {
        await loadEntity(items[0].id);
      }
    })();
  }, []);

  const edgeCount = graph?.edges.length ?? 0;
  const nodeCount = graph?.nodes.length ?? 0;

  return (
    <main className="page graph-page">
      <section className="hero">
        <p className="eyebrow">Tudásgráf</p>
        <h1>Mit tanult meg a rendszer?</h1>
        <p className="lead">
          A dokumentumaidból kinyert és jóváhagyott fogalmak itt jelennek meg. A vonalak (kapcsolatok)
          akkor látszanak, ha a rendszer összefüggéseket is elfogadott.
        </p>
      </section>

      <section className="panel graph-guide">
        <h2>Hogyan működik?</h2>
        <ol className="guide-list">
          <li>
            <strong>80%+ bizonyosságú</strong> javaslatokat a rendszer <strong>automatikusan
            jóváhagyja</strong> — nem kell egyenként bólogatnod.
          </li>
          <li>A jóváhagyott fogalmak megjelennek itt, a gráf oldalon.</li>
          <li>Kattints egy fogalomra — alul látod a közvetlen kapcsolatait.</li>
        </ol>
        <p className="muted">
          Ha üres: szinkronizáld a forrásokat, várj pár percet, majd frissítsd ezt az oldalt.
        </p>
      </section>

      <section className="panel">
        <h2>Ellentmondások ({contradictions.length})</h2>
        {contradictions.length === 0 ? (
          <p className="muted">
            Nincs nyitott ellentmondás. Ha két jóváhagyott állítás ütközik ugyanarra a predikátumra,
            itt jelenik meg — csak tájékoztató, nem dönt helyetted.
          </p>
        ) : (
          <ul className="contradiction-list">
            {contradictions.map((item) => (
              <li key={item.id} className="contradiction-card">
                <p className="hit-meta">
                  {item.predicate ? `Predikátum: ${item.predicate}` : "Állítás ütközés"}
                </p>
                <p>
                  <strong>Korábbi:</strong> {item.existing_value ?? "—"}
                </p>
                <p>
                  <strong>Új:</strong> {item.conflicting_value ?? "—"}
                </p>
                <p className="muted">{item.summary}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="panel">
        <h2>Fogalmak ({entities.length})</h2>
        {entities.length === 0 ? (
          <div className="empty-state">
            <p>Még nincs jóváhagyott fogalom a tudásbázisban.</p>
            <p className="muted">
              A rendszer a szinkronizálás után automatikusan jóváhagyja a magabiztos (80%+) találatokat.
              A bizonytalanabbakat a <Link href="/proposals">Javaslatok</Link> oldalon döntheted el.
            </p>
          </div>
        ) : (
          <div className="entity-cloud">
            {entities.map((entity) => (
              <button
                key={entity.id}
                type="button"
                className={`entity-chip ${selectedId === entity.id ? "entity-chip-active" : ""}`}
                onClick={() => void loadEntity(entity.id)}
              >
                <span className="entity-chip-name">{entity.canonical_name}</span>
                <span className="entity-chip-type">{entityTypeLabel(entity.entity_type)}</span>
              </button>
            ))}
          </div>
        )}
      </section>

      {selectedId && (
        <section className="panel">
          <h2>Kiválasztott fogalom</h2>
          {loadingGraph ? (
            <p className="muted">Betöltés…</p>
          ) : graph ? (
            <>
              <p className="hit-meta">
                {nodeCount} elem · {edgeCount} kapcsolat
                {graph.truncated ? " · részleges nézet" : ""}
              </p>
              {edgeCount === 0 ? (
                <p className="muted">
                  Ez a fogalom még önmagában áll — nincs jóváhagyott kapcsolata más fogalmakhoz. Ez normális,
                  ha csak a neveket automatikusan hagytad jóvá.
                </p>
              ) : null}
              <div className="graph-grid">
                {graph.nodes.map((node) => (
                  <article key={node.id} className="graph-node-card">
                    <p className="hit-meta">{entityTypeLabel(node.node_type)}</p>
                    <h3>{node.label}</h3>
                  </article>
                ))}
              </div>
              {graph.edges.length > 0 && (
                <>
                  <h3>Kapcsolatok</h3>
                  <ul className="graph-edge-list">
                    {graph.edges.map((edge) => {
                      const source = graph.nodes.find((n) => n.id === edge.source_id);
                      const target = graph.nodes.find((n) => n.id === edge.target_id);
                      return (
                        <li key={edge.id}>
                          {source?.label ?? edge.source_id} → {target?.label ?? edge.target_id}
                          <span className="muted"> ({edge.edge_type})</span>
                        </li>
                      );
                    })}
                  </ul>
                </>
              )}
            </>
          ) : (
            <p className="muted">Nem sikerült betölteni a gráfot.</p>
          )}
        </section>
      )}
    </main>
  );
}
