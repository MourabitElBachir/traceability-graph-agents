import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Décision de retrait",
  description: "Choisir quoi faire d’un lot signalé.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
