import { League, Season } from "./types";

export function resolveSelection(leagues: League[], seasonParam?: string): { league: League; season: Season } {
  const options = leagues.flatMap((league) => league.seasons.map((season) => ({ league, season })));
  return (
    options.find((o) => String(o.season.id) === seasonParam) ?? {
      league: leagues[0],
      season: leagues[0].seasons[0],
    }
  );
}

export const seasonLabel = (year: number) => `${year}/${String(year + 1).slice(2)}`;