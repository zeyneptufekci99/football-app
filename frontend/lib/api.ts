import type {
  Fixture,
  FixtureFilters,
  League,
  Overview,
  StandingRow,
  TeamOption,
  TeamStats,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`);
  return res.json();
}

export const api = {
  leagues: () => get<League[]>("/leagues"),
  overview: (seasonId: number) => get<Overview>(`/seasons/${seasonId}/overview`),
  standings: (seasonId: number) => get<StandingRow[]>(`/seasons/${seasonId}/standings`),
  teams: (seasonId: number) => get<TeamOption[]>(`/seasons/${seasonId}/teams`),
  teamStats: (seasonId: number, teamId: number | string) =>
    get<TeamStats>(`/seasons/${seasonId}/teams/${teamId}/stats`),
  fixtures: (seasonId: number, filters: FixtureFilters = {}) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== "") params.set(key, String(value));
    }
    return get<Fixture[]>(`/seasons/${seasonId}/fixtures?${params}`);
  },
};