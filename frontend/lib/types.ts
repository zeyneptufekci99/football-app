export type Season = { id: number; year: number; is_current: boolean };

export type League = {
  id: number;
  name: string;
  country: string | null;
  logo: string | null;
  seasons: Season[];
};

export type TeamRef = { id: number; name: string; logo: string | null };
export type TeamOption = TeamRef & { code: string | null; venue_name: string | null };

export type Fixture = {
  id: number;
  round: string | null;
  kickoff: string;
  status_short: string;
  status_long: string | null;
  home: TeamRef;
  away: TeamRef;
  home_goals: number | null;
  away_goals: number | null;
  venue_name: string | null;
};

export type FixtureFilters = {
  team_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
};

export type StandingRow = {
  rank: number;
  team_id: number;
  team_name: string;
  team_logo: string | null;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
};

export type Overview = {
  season_id: number;
  league_id: number;
  league_name: string;
  year: number;
  total_fixtures: number;
  played: number;
  unfinished: number;
  total_goals: number;
  goals_per_match: number | null;
  last_sync_at: string | null;
  last_sync_status: "success" | "failed" | "running" | null;
};

export type SplitStats = {
  played: number;
  won: number;
  drawn: number;
  lost: number;
  points: number;
  win_rate: number | null;
  goals_for_per_match: number | null;
  goals_against_per_match: number | null;
};

export type RecentMatch = {
  fixture_id: number;
  kickoff: string;
  opponent: string;
  is_home: boolean;
  goals_for: number;
  goals_against: number;
  result: "W" | "D" | "L";
};

export type PointsPoint = {
  match_no: number;
  kickoff: string;
  opponent: string;
  cumulative_points: number;
};

export type TeamStats = {
  team_id: number;
  team_name: string;
  season_id: number;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  points: number;
  win_rate: number | null;
  goals_for: number;
  goals_against: number;
  goals_for_per_match: number | null;
  goals_against_per_match: number | null;
  form_last_5: string;
  last_5_win_rate: number | null;
  last_5_goals_for_per_match: number | null;
  last_5_goals_against_per_match: number | null;
  last_5_matches: RecentMatch[];
  home: SplitStats;
  away: SplitStats;
  points_progress: PointsPoint[];
};

export type SyncRun = {
  id: number;
  league_id: number;
  season_year: number;
  started_at: string;
  finished_at: string | null;
  status: "running" | "success" | "failed";
  teams_upserted: number;
  fixtures_inserted: number;
  fixtures_updated: number;
  fixtures_skipped: number;
  error_message: string | null;
  mode: string;
  api_calls: number;
};

export type Usage = {
  daily_limit: number;
  used_today: number;
  failed_today: number;
  remaining: number;
  api_reported_remaining: number | null;
  last_request_at: string | null;
  resets_at: string | null;
};