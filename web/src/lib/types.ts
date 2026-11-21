export type Status = "livre" | "stock" | "sain";

export type MapNode = {
  id: string;
  label: string;
  kind: string;
  status: Status;
  x: number;
  y: number;
};

export type Impact = {
  lotId: string;
  summary: string;
  source: string;
  nodes: MapNode[];
  edges: { source: string; target: string }[];
};

export type Decision = {
  lotId: string;
  product: string;
  site: string;
  quantityKg: number;
  delivered: boolean;
  action: "block" | "quarantine" | "redirect" | "recall";
  actionLabel: string;
  costEur: number;
  why: string;
};

export type Plan = {
  lotId: string;
  key?: string;
  labTestsPerDay: number;
  biscuitsDelivered: boolean;
  riskThreshold: number;
  totalEur: number;
  naiveRecallEur: number;
  savingsEur: number;
  decisions: Decision[];
};

export type Catalog = {
  asOf: string;
  defaultLotId: string;
  lots: { id: string; product: string }[];
  reasons: { id: string; fr: string; en: string }[];
  labSteps: number[];
  riskSteps: number[];
  cases: Record<string, { impact: Impact; scenarios: Plan[] }>;
};

export type AuditEntry = {
  id: string;
  at: string;
  lotId: string;
  decision: "approve" | "modify";
  comment: string;
  reason: string;
  totalEur: number;
};
