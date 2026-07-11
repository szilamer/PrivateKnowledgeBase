import type { Proposal } from "./proposals";

const TYPE_ORDER: Record<string, number> = {
  entity: 0,
  task: 1,
  decision: 2,
  event: 3,
  claim: 4,
  relationship: 5,
};

export function sortProposalsForDisplay(proposals: Proposal[]): Proposal[] {
  return [...proposals].sort((a, b) => {
    const orderA = TYPE_ORDER[a.proposal_type] ?? 99;
    const orderB = TYPE_ORDER[b.proposal_type] ?? 99;
    if (orderA !== orderB) return orderA - orderB;
    return b.confidence - a.confidence;
  });
}

export function proposalTypeLabel(type: string): string {
  switch (type) {
    case "entity":
      return "Fogalom";
    case "task":
      return "Feladat";
    case "decision":
      return "Döntés";
    case "event":
      return "Esemény";
    case "claim":
      return "Állítás";
    case "relationship":
      return "Kapcsolat";
    default:
      return type;
  }
}

export function riskLevelLabel(level: string): string {
  switch (level) {
    case "low":
      return "alacsony kockázat";
    case "medium":
      return "közepes kockázat";
    case "high":
      return "magas kockázat";
    default:
      return level;
  }
}

function entityTypeLabel(type: string | undefined): string {
  switch (type) {
    case "technology":
      return "technológia";
    case "person":
      return "személy";
    case "organization":
      return "szervezet";
    case "project":
      return "projekt";
    case "concept":
      return "fogalom";
    default:
      return type ?? "egyéb";
  }
}

function readString(payload: Record<string, unknown>, key: string): string | null {
  const value = payload[key];
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

export function proposalHeadline(proposal: Proposal): string {
  const payload = proposal.payload;

  switch (proposal.proposal_type) {
    case "entity": {
      const name = readString(payload, "name") ?? proposal.title;
      const kind = entityTypeLabel(readString(payload, "entity_type") ?? undefined);
      return `„${name}” — ${kind}`;
    }
    case "task":
      return readString(payload, "title") ?? proposal.title;
    case "decision":
      return readString(payload, "title") ?? proposal.title;
    case "event":
      return readString(payload, "title") ?? proposal.title;
    case "claim":
      return readString(payload, "predicate") ?? proposal.title;
    case "relationship": {
      const rel = readString(payload, "relationship_type") ?? proposal.title;
      if (rel === "MENTIONS") return "Két dolog össze van említve ugyanabban a szövegben";
      return `Kapcsolat: ${rel}`;
    }
    default:
      return proposal.title;
  }
}

export function proposalExplanation(proposal: Proposal): string {
  const payload = proposal.payload;

  switch (proposal.proposal_type) {
    case "entity":
      return "A dokumentumaidból kinyert fogalom. Ha jóváhagyod, a rendszer megjegyzi, és később kereshető lesz.";
    case "task":
      return "Feladatot talált a szövegben. Jóváhagyás után a tudásbázis része lesz.";
    case "decision":
      return "Döntést talált a szövegben — pl. valamit elhatároztak vagy választottak.";
    case "event":
      return "Eseményt talált — pl. találkozó, határidő vagy esemény dátummal.";
    case "claim":
      return "Állítást talált — valaki vagy valami valamiről állít valamit a dokumentumban.";
    case "relationship":
      return "Két fogalom közötti összefüggés. Ha nem érted vagy nem fontos, nyugodtan utasítsd el.";
    default:
      return "Automatikusan kinyert információ a dokumentumaidból.";
  }
}

export function proposalDetail(proposal: Proposal): string | null {
  const payload = proposal.payload;
  const description = readString(payload, "description");
  if (description) return description;

  if (proposal.proposal_type === "task" || proposal.proposal_type === "decision") {
    return readString(payload, "summary");
  }

  if (proposal.proposal_type === "claim") {
    const subject = readString(payload, "subject");
    const object = readString(payload, "object");
    if (subject && object) return `${subject} → ${object}`;
  }

  return null;
}

export function confidenceLabel(confidence: number): string {
  return `${Math.round(confidence * 100)}% bizonyosság`;
}
