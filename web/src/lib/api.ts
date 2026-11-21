import type { Catalog, Impact, Plan } from "./types";

const api = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

export function liveMode() {
  return api.length > 0;
}

export async function loadCatalog(): Promise<Catalog> {
  const response = await fetch("/data/scenarios.json");
  if (!response.ok) throw new Error("catalog");
  return response.json() as Promise<Catalog>;
}

function nearest(value: number, steps: number[]) {
  return steps.reduce((best, step) => (Math.abs(step - value) < Math.abs(best - value) ? step : best));
}

export function snapPlan(catalog: Catalog, lotId: string, lab: number, delivered: boolean, risk: number): Plan | null {
  const entry = catalog.cases[lotId];
  if (!entry) return null;
  if (lotId !== "BLE-0457") return entry.scenarios[0] ?? null;
  const labStep = nearest(lab, catalog.labSteps);
  const riskStep = nearest(risk, catalog.riskSteps);
  const key = `${labStep}|${delivered ? "true" : "false"}|${riskStep}`;
  return entry.scenarios.find((row) => row.key === key) ?? entry.scenarios[0] ?? null;
}

export async function fetchImpact(lotId: string): Promise<Impact> {
  if (!liveMode()) {
    const catalog = await loadCatalog();
    const impact = catalog.cases[lotId]?.impact;
    if (!impact) throw new Error("missing");
    return impact;
  }
  const response = await fetch(`${api}/ui/impact/${lotId}`);
  if (!response.ok) throw new Error("impact");
  return response.json() as Promise<Impact>;
}

export async function fetchPlan(lotId: string, lab: number, delivered: boolean, risk: number): Promise<Plan> {
  if (!liveMode()) {
    const catalog = await loadCatalog();
    const plan = snapPlan(catalog, lotId, lab, delivered, risk);
    if (!plan) throw new Error("missing");
    return plan;
  }
  const response = await fetch(`${api}/ui/plan`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      lot_id: lotId,
      lab_tests_per_day: lab,
      biscuits_delivered: delivered,
      risk_threshold: risk,
    }),
  });
  if (!response.ok) throw new Error("plan");
  return response.json() as Promise<Plan>;
}
