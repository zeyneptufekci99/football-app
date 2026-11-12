"use server";

import { api, BASE } from "@/lib/api";
import type { SyncRun } from "@/lib/types";

export async function startSync(leagueId: number, year: number): Promise<{ ok: boolean; message: string }> {
  try {
    const res = await fetch(`${BASE}/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ league_id: leagueId, season: year }),
      cache: "no-store",
    });
    if (res.status === 202) return { ok: true, message: "Güncelleme başlatıldı." };

    const body = await res.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : "";
    if (res.status === 409) {
      return {
        ok: false,
        message: detail.includes("already running")
          ? "Bu lig ve sezon için bir güncelleme zaten çalışıyor."
          : "Bu sezon son 15 dakika içinde güncellendi. Biraz sonra tekrar deneyin.",
      };
    }
    return { ok: false, message: "Güncelleme başlatılamadı." };
  } catch {
    return { ok: false, message: "Backend'e ulaşılamıyor." };
  }
}

export async function getSyncStatus(leagueId: number, year: number): Promise<SyncRun | null> {
  return api.syncStatus(leagueId, year);
}