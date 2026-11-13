import type {
  Fixture,
  FixtureFilters,
  League,
  Overview,
  StandingRow,
  SyncRun,
  TeamOption,
  TeamStats,
  Usage,
} from "./types";

export const BASE = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new ApiError(res.status, `API error ${res.status} on ${path}`);
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
  usage: () => get<Usage>("/usage"),
  // Hiç senkronizasyon yoksa backend 404 döner; bu bir hata değil
  syncStatus: async (leagueId: number, year: number): Promise<SyncRun | null> => {
    try {
      return await get<SyncRun>(`/sync/status?league_id=${leagueId}&season=${year}`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) return null;
      throw e;
    }
  },
};