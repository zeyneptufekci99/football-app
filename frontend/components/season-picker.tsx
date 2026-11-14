"use client";

import { usePathname, useRouter } from "next/navigation";
import type { League } from "@/lib/types";
import { seasonLabel } from "@/lib/season";
import { Dropdown } from "./dropdown";

type SeasonPickerProps = {
  leagues: League[];
  leagueId: number;
  seasonId: number;
  basePath?: string;
};

export function SeasonPicker({
  leagues,
  leagueId,
  seasonId,
  basePath,
}: SeasonPickerProps) {
  const router = useRouter();
  const pathname = usePathname();
  const league = leagues.find((l) => l.id === leagueId)!;

  // basePath verilmezse bulunulan sayfada kalınır.
  // Sezon değişince filtreler bilerek sıfırlanır: başka sezonun takım ID'leri geçersiz olabilir.
  const go = (id: number | string) =>
    router.push(`${basePath ?? pathname}?season=${id}`);

  const leagueLabel = (l: League) =>
    l.country ? `${l.name} (${l.country})` : l.name;
  const leagueItems = leagues.map((l) => ({
    value: String(l.id),
    label: leagueLabel(l),
  }));
  const seasonItems = league.seasons.map((s) => ({
    value: String(s.id),
    label: seasonLabel(s.year),
  }));

  function onLeagueChange(value: string | null) {
    if (!value) return;
    const next = leagues.find((l) => String(l.id) === value);
    if (next?.seasons[0]) go(next.seasons[0].id); // en güncel sezon
  }

  function onSeasonChange(value: string | null) {
    if (!value) return;
    go(value);
  }

  return (
    <div className="flex flex-wrap gap-3">
      <Dropdown
        items={leagueItems}
        value={String(leagueId)}
        onChange={onLeagueChange}
      />
      <Dropdown
        items={seasonItems}
        value={String(seasonId)}
        onChange={onSeasonChange}
      />
    </div>
  );
}
