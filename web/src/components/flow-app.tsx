"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ImpactMap } from "@/components/impact-map";
import { fetchImpact, fetchPlan, liveMode, loadCatalog } from "@/lib/api";
import { messages, type Locale } from "@/lib/messages";
import { reportPdf } from "@/lib/pdf";
import type { AuditEntry, Catalog, Impact, Plan } from "@/lib/types";
import { euros } from "@/lib/utils";

const STORAGE = "agritrace-journal";

export function FlowApp() {
  const [locale, setLocale] = useState<Locale>("fr");
  const copy = messages[locale];
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [step, setStep] = useState(0);
  const [lotId, setLotId] = useState("BLE-0457");
  const [reason, setReason] = useState("contamination");
  const [impact, setImpact] = useState<Impact | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [lab, setLab] = useState(2);
  const [delivered, setDelivered] = useState(true);
  const [risk, setRisk] = useState(0.6);
  const [comment, setComment] = useState("");
  const [history, setHistory] = useState<AuditEntry[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadCatalog().then((data) => {
      setCatalog(data);
      setLotId(data.defaultLotId);
    });
    const saved = window.localStorage.getItem(STORAGE);
    if (saved) setHistory(JSON.parse(saved) as AuditEntry[]);
  }, []);

  const reasonLabel = useMemo(() => {
    const row = catalog?.reasons.find((item) => item.id === reason);
    return row ? row[locale] : reason;
  }, [catalog, locale, reason]);

  async function analyze() {
    setError("");
    try {
      const nextImpact = await fetchImpact(lotId);
      const nextPlan = await fetchPlan(lotId, lab, delivered, risk);
      setImpact(nextImpact);
      setPlan(nextPlan);
      setStep(1);
    } catch {
      setError(copy.missing);
    }
  }

  async function recompute(nextLab: number, nextDelivered: boolean, nextRisk: number) {
    setLab(nextLab);
    setDelivered(nextDelivered);
    setRisk(nextRisk);
    const nextPlan = await fetchPlan(lotId, nextLab, nextDelivered, nextRisk);
    setPlan(nextPlan);
  }

  function remember(decision: "approve" | "modify") {
    if (!plan || comment.trim().length < 3) return;
    const entry: AuditEntry = {
      id: crypto.randomUUID(),
      at: new Date().toISOString(),
      lotId,
      decision,
      comment: comment.trim(),
      reason: reasonLabel,
      totalEur: plan.totalEur,
    };
    const next = [entry, ...history];
    setHistory(next);
    window.localStorage.setItem(STORAGE, JSON.stringify(next));
    if (liveMode()) {
      void fetch(`${process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "")}/ui/approve`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ lot_id: lotId, decision, comment: comment.trim(), reason }),
      });
    }
    if (decision === "modify") setStep(2);
  }

  async function download() {
    if (!plan) return;
    const blob = await reportPdf(plan, comment, reasonLabel);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `decision-${plan.lotId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-6 py-12">
      <header className="flex items-start justify-between gap-6">
        <div className="flex flex-col gap-2">
          <p className="text-sm text-muted-foreground">{copy.product}</p>
          <p className="text-xs text-muted-foreground">{liveMode() ? copy.live : copy.demo}</p>
        </div>
        <Button variant="ghost" onClick={() => setLocale(locale === "fr" ? "en" : "fr")}>
          {locale === "fr" ? "EN" : "FR"}
        </Button>
      </header>
      <ol className="flex gap-3">
        {copy.steps.map((label, index) => (
          <li key={label} className="flex items-center gap-2 text-sm">
            <Badge className={index === step ? "bg-primary text-primary-foreground" : ""}>
              {index + 1}
            </Badge>
            <span className={index === step ? "font-medium" : "text-muted-foreground"}>{label}</span>
          </li>
        ))}
      </ol>

      {step === 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-3xl">{copy.alertTitle}</CardTitle>
            <CardDescription>{copy.alertHint}</CardDescription>
          </CardHeader>
          <CardContent>
            <label className="flex flex-col gap-2 text-sm">
              {copy.lot}
              <select className="h-11 rounded-lg border border-border bg-card px-3" value={lotId} onChange={(event) => setLotId(event.target.value)}>
                {catalog?.lots.map((lot) => (
                  <option key={lot.id} value={lot.id}>
                    {lot.id} · {lot.product}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-2 text-sm">
              {copy.reason}
              <select className="h-11 rounded-lg border border-border bg-card px-3" value={reason} onChange={(event) => setReason(event.target.value)}>
                {catalog?.reasons.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item[locale]}
                  </option>
                ))}
              </select>
            </label>
            {error ? <p className="text-sm text-muted-foreground">{error}</p> : null}
            <Button size="lg" onClick={() => void analyze()}>
              {copy.analyze}
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 1 && impact && (
        <section className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <h1 className="text-3xl font-semibold">{copy.impactTitle}</h1>
            <p className="max-w-2xl text-lg">{impact.summary}</p>
            <p className="max-w-2xl text-sm text-muted-foreground">{impact.source}</p>
          </div>
          <div className="flex gap-3 text-sm">
            <Badge className="bg-[#b42318] text-white">{copy.legendDelivered}</Badge>
            <Badge className="bg-[#c2410c] text-white">{copy.legendStock}</Badge>
            <Badge className="bg-[#3f7d4e] text-white">{copy.legendHealthy}</Badge>
          </div>
          <ImpactMap impact={impact} />
          <Button size="lg" onClick={() => setStep(2)}>
            {copy.seePlan}
          </Button>
        </section>
      )}

      {step === 2 && plan && (
        <section className="flex flex-col gap-8">
          <div className="flex flex-col gap-2">
            <h1 className="text-3xl font-semibold">{copy.planTitle}</h1>
            <p className="text-5xl font-semibold tracking-tight">{euros(plan.totalEur)}</p>
            <p className="text-muted-foreground">{copy.total}</p>
            <p>
              {copy.savings} <span className="font-semibold">{euros(plan.savingsEur)}</span>
            </p>
            <p className="text-sm text-muted-foreground">
              {copy.naive} {euros(plan.naiveRecallEur)}
            </p>
          </div>
          <div className="grid gap-4">
            {plan.decisions.map((row) => (
              <Card key={row.lotId}>
                <CardHeader>
                  <CardTitle>
                    {row.product} {row.lotId}
                  </CardTitle>
                  <CardDescription>
                    {row.site} · {row.quantityKg} kg
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-semibold">{row.actionLabel}</p>
                  <p className="text-lg">{euros(row.costEur)}</p>
                  <p className="text-sm text-muted-foreground">{row.why}</p>
                </CardContent>
              </Card>
            ))}
          </div>
          <Card>
            <CardHeader>
              <CardTitle>{copy.lab}</CardTitle>
            </CardHeader>
            <CardContent>
              <input
                aria-label={copy.lab}
                type="range"
                min={0}
                max={Math.max((catalog?.labSteps.length ?? 1) - 1, 0)}
                step={1}
                value={Math.max(catalog?.labSteps.indexOf(lab) ?? 0, 0)}
                onChange={(event) => {
                  const next = catalog?.labSteps[Number(event.target.value)] ?? lab;
                  void recompute(next, delivered, risk);
                }}
              />
              <p>{lab}</p>
              <label className="flex items-center gap-3 text-sm">
                <input type="checkbox" checked={!delivered} onChange={(event) => void recompute(lab, !event.target.checked, risk)} />
                {copy.notDelivered}
              </label>
              <label className="flex flex-col gap-2 text-sm">
                {copy.risk}
                <input
                  aria-label={copy.risk}
                  type="range"
                  min={0.4}
                  max={0.8}
                  step={0.2}
                  value={risk}
                  onChange={(event) => void recompute(lab, delivered, Number(event.target.value))}
                />
                <span>{risk.toFixed(1)}</span>
              </label>
            </CardContent>
          </Card>
          <Button size="lg" onClick={() => setStep(3)}>
            {copy.continue}
          </Button>
        </section>
      )}

      {step === 3 && plan && (
        <section className="flex flex-col gap-8">
          <div className="flex flex-col gap-2">
            <h1 className="text-3xl font-semibold">{copy.validateTitle}</h1>
            <p className="text-5xl font-semibold">{euros(plan.totalEur)}</p>
            <p className="text-sm text-muted-foreground">
              {reasonLabel} · {lotId}
            </p>
          </div>
          <label className="flex flex-col gap-2 text-sm">
            {copy.comment}
            <textarea
              className="min-h-28 rounded-lg border border-border bg-card p-3"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              placeholder={copy.commentHint}
            />
          </label>
          <div className="flex flex-wrap gap-3">
            <Button size="lg" disabled={comment.trim().length < 3} onClick={() => remember("approve")}>
              {copy.approve}
            </Button>
            <Button size="lg" variant="outline" disabled={comment.trim().length < 3} onClick={() => remember("modify")}>
              {copy.modify}
            </Button>
            <Button size="lg" variant="outline" onClick={() => void download()}>
              {copy.download}
            </Button>
          </div>
          <div className="flex flex-col gap-3">
            <h2 className="text-lg font-semibold">{copy.history}</h2>
            {history.length === 0 ? <p className="text-sm text-muted-foreground">{copy.emptyHistory}</p> : null}
            {history.map((entry) => (
              <p key={entry.id} className="text-sm">
                {new Date(entry.at).toLocaleString(locale)} · {entry.lotId} · {euros(entry.totalEur)} · {entry.comment}
              </p>
            ))}
          </div>
          <Button variant="ghost" onClick={() => setStep(2)}>
            {copy.back}
          </Button>
        </section>
      )}
    </main>
  );
}
