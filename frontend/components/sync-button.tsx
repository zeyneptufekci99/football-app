"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { getSyncStatus, startSync } from "@/app/action";

const POLL_MS = 3000;
const MAX_POLLS = 40;
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

type SyncButton = {
  leagueId: number;
  year: number;
};
export function SyncButton({ leagueId, year }: SyncButton) {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<{
    text: string;
    error: boolean;
  } | null>(null);

  async function onClick() {
    setRunning(true);
    setMessage(null);
    try {
      const before = await getSyncStatus(leagueId, year);
      const started = await startSync(leagueId, year);
      if (!started.ok) {
        setMessage({ text: started.message, error: true });
        return;
      }

      for (let i = 0; i < MAX_POLLS; i++) {
        await sleep(POLL_MS);
        const run = await getSyncStatus(leagueId, year);
        if (run && run.id > (before?.id ?? 0) && run.status !== "running") {
          if (run.status === "success") {
            setMessage({
              text: `Güncellendi: ${run.fixtures_inserted} yeni, ${run.fixtures_updated} değişen maç · ${run.api_calls} API isteği`,
              error: false,
            });
          } else {
            setMessage({
              text: `Güncelleme başarısız. Mevcut veriler gösterilmeye devam ediyor.${
                run.error_message ? ` Neden: ${run.error_message}` : ""
              }`,
              error: true,
            });
          }
          router.refresh();
          return;
        }
      }
      setMessage({
        text: "Güncelleme sürüyor. Birkaç dakika sonra sayfayı yenileyin.",
        error: false,
      });
    } catch {
      setMessage({ text: "Backend'e ulaşılamıyor.", error: true });
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button onClick={onClick} disabled={running} variant="outline">
        {running ? "Güncelleniyor…" : "Verileri güncelle"}
      </Button>
      <p
        aria-live="polite"
        className={`text-sm ${message?.error ? "text-red-700" : "text-neutral-600"}`}
      >
        {message?.text}
      </p>
    </div>
  );
}
