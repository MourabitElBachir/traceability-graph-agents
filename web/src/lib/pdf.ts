import { PDFDocument, StandardFonts, rgb } from "pdf-lib";
import type { Plan } from "./types";

export async function reportPdf(plan: Plan, comment: string, reason: string) {
  const pdf = await PDFDocument.create();
  const page = pdf.addPage([595, 842]);
  const font = await pdf.embedFont(StandardFonts.Helvetica);
  const clean = (value: string) => value.replaceAll("’", "'").replaceAll("—", "-").replaceAll("·", "-");
  const lines = [
    "Rapport de decision",
    `Lot ${plan.lotId}`,
    `Motif : ${reason}`,
    `Cout total : ${plan.totalEur} EUR`,
    `Tout rappeler : ${plan.naiveRecallEur} EUR`,
    `Economie : ${plan.savingsEur} EUR`,
    "",
    ...plan.decisions.flatMap((row) => [
      `${row.product} ${row.lotId} — ${row.actionLabel} — ${row.costEur} EUR`,
      row.why,
      "",
    ]),
    "Commentaire",
    comment,
  ];
  lines.forEach((line, index) => {
    page.drawText(clean(line).slice(0, 95), {
      x: 48,
      y: 790 - index * 18,
      size: 11,
      font,
      color: rgb(0.1, 0.16, 0.12),
    });
  });
  const bytes = await pdf.save();
  return new Blob([Uint8Array.from(bytes)], { type: "application/pdf" });
}
