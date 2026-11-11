from datetime import datetime

from pydantic import BaseModel, Field


class SeasonOut(BaseModel):
    id: int
    year: int
    is_current: bool


class LeagueOut(BaseModel):
    id: int
    name: str
    country: str | None
    logo: str | None
    seasons: list[SeasonOut]


class TeamOut(BaseModel):
    id: int
    name: str
    code: str | None
    logo: str | None
    venue_name: str | None


class TeamRef(BaseModel):
    id: int
    name: str
    logo: str | None


class FixtureOut(BaseModel):
    id: int
    round: str | None
    kickoff: datetime
    status_short: str
    status_long: str | None
    home: TeamRef
    away: TeamRef
    home_goals: int | None
    away_goals: int | None
    venue_name: str | None


class StandingRow(BaseModel):
    rank: int
    team_id: int
    team_name: str
    team_logo: str | None
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int


class RecentMatch(BaseModel):
    fixture_id: int
    kickoff: datetime
    opponent: str
    is_home: bool
    goals_for: int
    goals_against: int
    result: str  # W | D | L


class TeamStats(BaseModel):
    team_id: int
    team_name: str
    season_id: int
    played: int
    won: int
    drawn: int
    lost: int
    points: int
    win_rate: float | None
    goals_for: int
    goals_against: int
    goals_for_per_match: float | None
    goals_against_per_match: float | None
    # Son 5 maç: en sağdaki harf en son oynanan maç
    form_last_5: str
    last_5_win_rate: float | None
    last_5_goals_for_per_match: float | None
    last_5_goals_against_per_match: float | None
    last_5_matches: list[RecentMatch]  # en yeni maç ilk sırada


class SyncRequest(BaseModel):
    league_id: int = Field(gt=0)
    season: int = Field(ge=2000, le=2100)


class SyncRunOut(BaseModel):
    id: int
    league_id: int
    season_year: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    teams_upserted: int
    fixtures_inserted: int
    fixtures_updated: int
    fixtures_skipped: int
    error_message: str | None

class UsageOut(BaseModel):
    daily_limit: int
    used_today: int
    failed_today: int
    remaining: int
    api_reported_remaining: int | None
    last_request_at: datetime | None
    resets_at: datetime | None