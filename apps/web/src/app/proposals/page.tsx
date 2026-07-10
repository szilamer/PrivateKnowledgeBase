"use client";

import { useEffect, useState } from "react";

import {
  approveProposal,
  deferProposal,
  listProposals,
  rejectProposal,
  type Proposal,
} from "@/lib/proposals";

export default function ProposalsPage() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    const items = await listProposals("pending");
    setProposals(items);
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleAction(
    id: string,
    action: "approve" | "reject" | "defer",
  ) {
    setMessage(null);
    const fn = {
      approve: approveProposal,
      reject: rejectProposal,
      defer: deferProposal,
    }[action];
    const result = await fn(id);
    if (!result) {
      setMessage(`Failed to ${action} proposal.`);
      return;
    }
    setMessage(`Proposal ${action}d.`);
    await refresh();
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Phase 3 — Knowledge proposals</p>
        <h1>Approval queue</h1>
        <p className="lead">
          Review AI-generated entities, tasks, decisions, and relationships before they enter
          canonical knowledge.
        </p>
      </section>

      {message && <p className="message">{message}</p>}

      <section className="panel">
        <h2>Pending ({proposals.length})</h2>
        {proposals.length === 0 ? (
          <p className="muted">
            No pending proposals. Sync sources and wait for knowledge extraction to complete.
          </p>
        ) : (
          proposals.map((proposal) => (
            <article key={proposal.id} className="hit">
              <p className="hit-meta">
                {proposal.proposal_type} · {proposal.risk_level} risk · confidence{" "}
                {proposal.confidence.toFixed(2)}
              </p>
              <h3>{proposal.title}</h3>
              <pre>{JSON.stringify(proposal.payload, null, 2)}</pre>
              <div className="actions">
                <button type="button" onClick={() => void handleAction(proposal.id, "approve")}>
                  Approve
                </button>
                <button type="button" onClick={() => void handleAction(proposal.id, "reject")}>
                  Reject
                </button>
                <button type="button" onClick={() => void handleAction(proposal.id, "defer")}>
                  Defer
                </button>
              </div>
            </article>
          ))
        )}
      </section>
    </main>
  );
}
