"use client";

import { Button } from "@/components/ui/button";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div role="alert" className="rounded-lg border bg-white p-6">
      <h1 className="text-xl font-semibold">Veriler yüklenemedi</h1>
      <p className="mt-2 text-sm text-neutral-600">
        Backend&apos;e ulaşılamıyor. <code>docker compose ps</code> ile
        servislerin çalıştığını kontrol edin.
      </p>
      <Button onClick={reset} className="mt-4">
        Tekrar dene
      </Button>
    </div>
  );
}
