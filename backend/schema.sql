CREATE TABLE IF NOT EXISTS leagues (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    country     VARCHAR(80),
    logo        VARCHAR(255),
    type        VARCHAR(20),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS seasons (
    id          SERIAL PRIMARY KEY,
    league_id   INTEGER NOT NULL REFERENCES leagues(id),
    year        INTEGER NOT NULL,
    start_date  DATE,
    end_date    DATE,
    is_current  BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (league_id, year)
);

CREATE TABLE IF NOT EXISTS teams (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    code        VARCHAR(10),
    country     VARCHAR(80),
    logo        VARCHAR(255),
    venue_name  VARCHAR(120),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS season_teams (
    season_id   INTEGER NOT NULL REFERENCES seasons(id),
    team_id     INTEGER NOT NULL REFERENCES teams(id),
    PRIMARY KEY (season_id, team_id)
);

CREATE TABLE IF NOT EXISTS fixtures (
    id            INTEGER PRIMARY KEY,
    season_id     INTEGER NOT NULL REFERENCES seasons(id),
    round         VARCHAR(60),
    kickoff       TIMESTAMPTZ NOT NULL,
    status_short  VARCHAR(10) NOT NULL,
    status_long   VARCHAR(60),
    home_team_id  INTEGER NOT NULL REFERENCES teams(id),
    away_team_id  INTEGER NOT NULL REFERENCES teams(id),
    home_goals    INTEGER,
    away_goals    INTEGER,
    venue_name    VARCHAR(120),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (home_team_id <> away_team_id)
);
CREATE INDEX IF NOT EXISTS idx_fixtures_season_kickoff ON fixtures (season_id, kickoff);
CREATE INDEX IF NOT EXISTS idx_fixtures_home ON fixtures (home_team_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_away ON fixtures (away_team_id);

CREATE TABLE IF NOT EXISTS sync_runs (
    id                SERIAL PRIMARY KEY,
    league_id         INTEGER NOT NULL,
    season_year       INTEGER NOT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at       TIMESTAMPTZ,
    status            VARCHAR(20) NOT NULL DEFAULT 'running',  -- running | success | failed
    teams_upserted    INTEGER NOT NULL DEFAULT 0,
    fixtures_inserted INTEGER NOT NULL DEFAULT 0,
    fixtures_updated  INTEGER NOT NULL DEFAULT 0,
    fixtures_skipped  INTEGER NOT NULL DEFAULT 0,
    error_message     TEXT
);

CREATE TABLE IF NOT EXISTS fixture_changes (
    id               SERIAL PRIMARY KEY,
    fixture_id       INTEGER NOT NULL REFERENCES fixtures(id),
    sync_run_id      INTEGER REFERENCES sync_runs(id),
    changed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    old_status       VARCHAR(10),
    new_status       VARCHAR(10),
    old_home_goals   INTEGER,
    new_home_goals   INTEGER,
    old_away_goals   INTEGER,
    new_away_goals   INTEGER,
    old_kickoff      TIMESTAMPTZ,
    new_kickoff      TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_changes_fixture ON fixture_changes (fixture_id);

CREATE TABLE IF NOT EXISTS api_requests (
    id             SERIAL PRIMARY KEY,
    requested_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    endpoint       VARCHAR(60) NOT NULL,
    params         TEXT,
    http_status    INTEGER,          
    ok             BOOLEAN NOT NULL,
    api_remaining  INTEGER,         
    error          TEXT
);
CREATE INDEX IF NOT EXISTS idx_api_requests_time ON api_requests (requested_at);

ALTER TABLE sync_runs
    ADD COLUMN IF NOT EXISTS mode VARCHAR(10) NOT NULL DEFAULT 'full',
    ADD COLUMN IF NOT EXISTS api_calls INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS fixture_stats_fetches (
    fixture_id  INTEGER PRIMARY KEY REFERENCES fixtures(id),
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    has_data    BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS fixture_team_stats (
    fixture_id  INTEGER NOT NULL REFERENCES fixtures(id),
    team_id     INTEGER NOT NULL REFERENCES teams(id),
    stats       JSONB NOT NULL,
    PRIMARY KEY (fixture_id, team_id)
);

ALTER TABLE api_requests ADD COLUMN IF NOT EXISTS state VARCHAR(10) NOT NULL DEFAULT 'completed';