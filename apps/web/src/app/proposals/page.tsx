"use client";

import { useEffect, useState } from "react";

import {
  confidenceLabel,
  proposalDetail,
  proposalExplanation,
  proposalHeadline,
  proposalTypeLabel,
  riskLevelLabel,
  sortProposalsForDisplay,
} from "@/lib/proposal-labels";
import {
  approveProposal,
  autoApproveConfident,
  deferProposal,
  listProposals,
  rejectProposal,
  type Proposal,
} from "@/lib/proposals";

export default function ProposalsPage() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [actingId, setActingId] = useState<string | null>(null);

  async function refresh() {
    const [items, autoResult] = await Promise.all([
      listProposals("pending"),
      autoApproveConfident(),
    ]);
    const needsReview = items.filter((p) => p.requires_review);
    setProposals(sortProposalsForDisplay(needsReview));
    if (autoResult && autoResult.approved_count > 0) {
      setMessage(autoResult.message);
      const refreshed = await listProposals("pending");
      setProposals(sortProposalsForDisplay(refreshed.filter((p) => p.requires_review)));
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleAction(id: string, action: "approve" | "reject" | "defer") {
    setActingId(id);
    setMessage(null);
    const fn = {
      approve: approveProposal,
      reject: rejectProposal,
      defer: deferProposal,
    }[action];
    const result = await fn(id);
    setActingId(null);
    if (!result) {
      setMessage(
        action === "approve"
          ? "Nem sikerült jóváhagyni."
          : action === "reject"
            ? "Nem sikerült elutasítani."
            : "Nem sikerült későbbre halasztani.",
      );
      return;
    }
    setMessage(
      action === "approve"
        ? "Jóváhagyva — bekerült a tudásbázisba."
        : action === "reject"
          ? "Elutasítva."
          : "Későbbre halasztva.",
    );
    await refresh();
  }

  return (
    <main className="page proposals-page">
      <section className="hero">
        <p className="eyebrow">Javaslatok</p>
        <h1>Mit talált a rendszer?</h1>
        <p className="lead">
          A dokumentumaidból kinyert, de még bizonytalan információk. A{" "}
          <strong>80%+ bizonyosságú</strong> javaslatokat a rendszer automatikusan jóváhagyja — itt csak
          azok maradnak, amiket te döntesz el.
        </p>
      </section>

      <section className="panel proposal-guide">
        <h2>Hogyan használd?</h2>
        <ul className="guide-list">
          <li>
            <strong>Automatikus (80%+):</strong> pl. „Celery”, „PostgreSQL” — ezek már bekerültek, nem
            kell foglalkoznod velük.
          </li>
          <li>
            <strong>Itt látható:</strong> bizonytalan fogalmak és kapcsolatok — jóváhagyás vagy elutasítás.
          </li>
          <li>
            <strong>Kapcsolatok:</strong> ha nem érted, utasítsd el — a gráf így is működik a
            fogalmakkal.
          </li>
        </ul>
      </section>

      {message && <p className="message">{message}</p>}

      <section className="panel">
        <h2>Te döntesz ({proposals.length})</h2>
        {proposals.length === 0 ? (
          <p className="muted">
            Nincs olyan javaslat, amihez a te döntésed kellene — a magabiztos találatok automatikusan
            bekerültek. Nézd meg a <a href="/graph">Tudásgráf</a> oldalt.
          </p>
        ) : (
          proposals.map((proposal) => {
            const detail = proposalDetail(proposal);
            const busy = actingId === proposal.id;
            return (
              <article key={proposal.id} className="proposal-card">
                <div className="proposal-card-head">
                  <span className="proposal-type">{proposalTypeLabel(proposal.proposal_type)}</span>
                  <span className="proposal-meta">
                    {riskLevelLabel(proposal.risk_level)} · {confidenceLabel(proposal.confidence)}
                  </span>
                </div>
                <h3>{proposalHeadline(proposal)}</h3>
                <p className="proposal-explanation">{proposalExplanation(proposal)}</p>
                {detail && <p className="proposal-detail">{detail}</p>}
                <div className="proposal-actions">
                  <button
                    type="button"
                    className="button primary"
                    disabled={busy}
                    onClick={() => void handleAction(proposal.id, "approve")}
                  >
                    {busy ? "…" : "Jóváhagyás"}
                  </button>
                  <button
                    type="button"
                    className="button"
                    disabled={busy}
                    onClick={() => void handleAction(proposal.id, "reject")}
                  >
                    Elutasítás
                  </button>
                  <button
                    type="button"
                    className="button"
                    disabled={busy}
                    onClick={() => void handleAction(proposal.id, "defer")}
                  >
                    Később
                  </button>
                </div>
              </article>
            );
          })
        )}
      </section>
    </main>
  );
}
