"use client";

import { useEffect, useState } from "react";

import {
  fetchNeighborhood,
  listContradictions,
  listEntities,
  type CanonicalEntity,
  type GraphView,
} from "@/lib/graph";

export default function GraphPage() {
  const [entities, setEntities] = useState<CanonicalEntity[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [graph, setGraph] = useState<GraphView | null>(null);
  const [contradictions, setContradictions] = useState<
    Array<{ id: string; summary: string; status: string }>
  >([]);

  useEffect(() => {
    void (async () => {
      setEntities(await listEntities());
      setContradictions(await listContradictions());
    })();
  }, []);

  async function handleSelect(entityId: string) {
    setSelectedId(entityId);
    setGraph(await fetchNeighborhood(entityId));
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Phase 4 — Knowledge graph</p>
        <h1>Graph browser</h1>
        <p className="lead">
          Explore canonical entities, relationships, and contradiction findings projected to Neo4j.
        </p>
      </section>

      <section className="panel">
        <h2>Entities ({entities.length})</h2>
        {entities.length === 0 ? (
          <p className="muted">No canonical entities yet. Approve entity proposals first.</p>
        ) : (
          <ul>
            {entities.map((entity) => (
              <li key={entity.id}>
                <button type="button" onClick={() => void handleSelect(entity.id)}>
                  {entity.canonical_name} ({entity.entity_type})
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {selectedId && graph && (
        <section className="panel">
          <h2>Neighborhood</h2>
          <p className="hit-meta">
            {graph.nodes.length} nodes · {graph.edges.length} edges
            {graph.truncated ? " · truncated" : ""}
          </p>
          <div className="graph-grid">
            {graph.nodes.map((node) => (
              <article key={node.id} className="hit">
                <p className="hit-meta">{node.node_type}</p>
                <h3>{node.label}</h3>
              </article>
            ))}
          </div>
          <h3>Edges</h3>
          <ul>
            {graph.edges.map((edge) => (
              <li key={edge.id}>
                {edge.source_id} —{edge.edge_type}→ {edge.target_id}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="panel">
        <h2>Open contradictions ({contradictions.length})</h2>
        {contradictions.length === 0 ? (
          <p className="muted">No open contradictions.</p>
        ) : (
          contradictions.map((item) => (
            <article key={item.id} className="hit">
              <p>{item.summary}</p>
            </article>
          ))
        )}
      </section>
    </main>
  );
}
