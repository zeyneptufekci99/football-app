import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "latin-ext"] });

export const metadata: Metadata = {
  title: "Futbol Panosu",
  description: "Lig puan durumu, maçlar ve takım performansları",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body
        className={`${inter.className} min-h-screen bg-neutral-50 text-neutral-900 antialiased`}
      >
        <header className="border-b bg-white">
          <div className="mx-auto max-w-5xl px-4 py-4 text-lg font-semibold">
            Futbol Panosu
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
