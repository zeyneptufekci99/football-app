"use client";

import { usePathname, useRouter } from "next/navigation";
import { seasonLabel } from "@/lib/season";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { League } from "@/lib/types";

type Props = { leagues: League[]; leagueId: number; seasonId: number };

export function SeasonPicker({ leagues, leagueId, seasonId }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const league = leagues.find((l) => l.id === leagueId)!;

  // Sezon değişince filtreler bilerek sıfırlanır: başka sezonun takım ID'leri geçersiz olabilir
  const go = (id: number | string) => router.push(`${pathname}?season=${id}`);

  function onLeagueChange(value: string | null) {
    if (!value) return;
    const next = leagues.find((l) => String(l.id) === value);
    if (next?.seasons[0]) go(next.seasons[0].id);
  }

  function onSeasonChange(value: string | null) {
    if (!value) return;
    go(value);
  }

  return (
    <div className="flex flex-wrap gap-3">
      <Select value={String(leagueId)} onValueChange={onLeagueChange}>
        <SelectTrigger className="w-56 bg-white" aria-label="Lig">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {leagues.map((l) => (
            <SelectItem key={l.id} value={String(l.id)}>
              {l.name}
              {l.country ? ` (${l.country})` : ""}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={String(seasonId)} onValueChange={onSeasonChange}>
        <SelectTrigger className="w-36 bg-white" aria-label="Sezon">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {league.seasons.map((s) => (
            <SelectItem key={s.id} value={String(s.id)}>
              {seasonLabel(s.year)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
