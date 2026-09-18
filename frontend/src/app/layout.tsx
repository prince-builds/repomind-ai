import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RepoMind AI — Repository Intelligence Platform",
  description:
    "Understand any GitHub repository: clone, index, map architecture, browse file intelligence, and ask natural language questions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen flex flex-col">{children}</body>
    </html>
  );
}
