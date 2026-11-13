import { notFound } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { SplitStats, TeamStats } from "@/lib/types";
import { formatDate, formatNumber, formatPercent } from "@/lib/format";
import { resolveSelection, seasonLabel } from "@/lib/season";
import { DashboardHeader } from "@/components/dashboard-header";
import { StatCardProps } from "@/components/stat-card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PointsChart } from "@/components/points-chart";
import { FormBadges } from "@/components/form-badges";
import { NoData } from "@/components/no-data";
import { CardContainer } from "@/components/card-container";
import { StatCardSection } from "@/components/stat-card-section";

function totalAsSplit(s: TeamStats): SplitStats {
  return {
    played: s.played,
    won: s.won,
    drawn: s.drawn,
    lost: s.lost,
    points: s.points,
    win_rate: s.win_rate,
    goals_for_per_match: s.goals_for_per_match,
    goals_against_per_match: s.goals_against_per_match,
  };
}

const RESULT_LABEL = { W: "G", D: "B", L: "M" } as const;

export default async function TeamPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ season?: string }>;
}) {
  const { id } = await params;
  const { season: seasonParam } = await searchParams;
  if (!/^\d+$/.test(id)) notFound();

  const leagues = (await api.leagues()).filter((l) => l.seasons.length > 0);
  if (leagues.length === 0) return <NoData />;
  const { league, season } = resolveSelection(leagues, seasonParam);

  let stats: TeamStats;
  try {
    stats = await api.teamStats(season.id, id);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }

  const rows: { label: string; pick: (s: SplitStats) => string }[] = [
    { label: "Oynanan maç", pick: (s) => String(s.played) },
    { label: "Galibiyet", pick: (s) => String(s.won) },
    { label: "Beraberlik", pick: (s) => String(s.drawn) },
    { label: "Mağlubiyet", pick: (s) => String(s.lost) },
    { label: "Puan", pick: (s) => String(s.points) },
    { label: "Galibiyet oranı", pick: (s) => formatPercent(s.win_rate) },
    {
      label: "Maç başına atılan gol",
      pick: (s) => formatNumber(s.goals_for_per_match),
    },
    {
      label: "Maç başına yenilen gol",
      pick: (s) => formatNumber(s.goals_against_per_match),
    },
  ];
  const columns = [stats.home, stats.away, totalAsSplit(stats)];

  const statCardsData: StatCardProps[] = [
    {
      label: "Puan",
      value: String(stats.points),
      hint: `${stats.played} maç`,
      tone: "blue",
    },
    {
      label: "Galibiyet oranı",
      value: formatPercent(stats.win_rate),
      tone: "green",
    },
    {
      label: "Maç başına atılan gol",
      value: formatNumber(stats.goals_for_per_match),
      hint: `Toplam ${stats.goals_for}`,
      tone: "sky",
    },
    {
      label: "Maç başına yenilen gol",
      value: formatNumber(stats.goals_against_per_match),
      hint: `Toplam ${stats.goals_against}`,
      tone: "teal",
    },
  ];

  return (
    <div>
      <DashboardHeader
        leagues={leagues}
        leagueId={league.id}
        seasonId={season.id}
        pickerBasePath="/"
      />

      <h1 className="text-2xl font-semibold">{stats.team_name}</h1>
      <p className="mt-1 text-sm text-neutral-600">
        {league.name} {seasonLabel(season.year)}
      </p>
      <StatCardSection
        cards={statCardsData}
        className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4"
        title="Sezon özeti"
      />

      <CardContainer contentClassName="space-y-4" header="Son 5 maç">
        <>
          <div className="flex flex-wrap items-center gap-x-8 gap-y-3 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-neutral-600">Form (eskiden yeniye):</span>
              <FormBadges form={stats.form_last_5} />
            </div>
            <span>
              <span className="text-neutral-600">Galibiyet oranı: </span>
              {formatPercent(stats.last_5_win_rate)}
            </span>
            <span>
              <span className="text-neutral-600">Atılan gol/maç: </span>
              {formatNumber(stats.last_5_goals_for_per_match)}
            </span>
            <span>
              <span className="text-neutral-600">Yenilen gol/maç: </span>
              {formatNumber(stats.last_5_goals_against_per_match)}
            </span>
          </div>

          {stats.last_5_matches.length === 0 ? (
            <p className="text-sm text-neutral-600">
              Henüz tamamlanmış maç yok.
            </p>
          ) : (
            <ul className="divide-y rounded-md border text-sm">
              {stats.last_5_matches.map((m) => (
                <li
                  key={m.fixture_id}
                  className="flex items-center justify-between gap-3 px-3 py-2"
                >
                  <span className="w-28 shrink-0 text-neutral-600">
                    {formatDate(m.kickoff)}
                  </span>
                  <span className="flex-1">
                    {m.is_home ? "Ev" : "Dep"} · {m.opponent}
                  </span>
                  <span className="font-semibold tabular-nums">
                    {m.goals_for} - {m.goals_against}
                  </span>
                  <span className="w-6 text-right font-medium">
                    {RESULT_LABEL[m.result]}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </>
      </CardContainer>

      <CardContainer header="İç saha ve deplasman performansı">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead />
              <TableHead className="text-right tabular-num">İç saha</TableHead>
              <TableHead className="text-right tabular-num">
                Deplasman
              </TableHead>
              <TableHead className="text-right tabular-num">Toplam</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.label}>
                <TableCell>{r.label}</TableCell>
                {columns.map((c, i) => (
                  <TableCell key={i} className="text-right tabular-num">
                    {r.pick(c)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContainer>

      <CardContainer header="Sezon boyunca birikmiş puan">
        <PointsChart data={stats.points_progress} />
      </CardContainer>
    </div>
  );
}
