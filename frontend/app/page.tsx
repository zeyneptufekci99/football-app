import { api } from "@/lib/api";
import { formatDateTime, formatNumber } from "@/lib/format";
import { resolveSelection, seasonLabel } from "@/lib/season";
import { DashboardHeader } from "@/components/dashboard-header";
import { NoData } from "@/components/no-data";
import { StandingsTable } from "@/components/standings-table";
import { Card, CardContent } from "@/components/ui/card";

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <Card className="bg-white">
      <CardContent className="p-4">
        <p className="text-sm text-neutral-600">{label}</p>
        <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
        {hint && <p className="mt-1 text-xs text-neutral-500">{hint}</p>}
      </CardContent>
    </Card>
  );
}

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ season?: string }>;
}) {
  const { season: seasonParam } = await searchParams;
  const leagues = (await api.leagues()).filter((l) => l.seasons.length > 0);
  if (leagues.length === 0) return <NoData />;

  const { league, season } = resolveSelection(leagues, seasonParam);
  const [overview, rows] = await Promise.all([
    api.overview(season.id),
    api.standings(season.id),
  ]);

  return (
    <div>
      <DashboardHeader
        leagues={leagues}
        leagueId={league.id}
        seasonId={season.id}
        active="overview"
      />

      <h1 className="text-2xl font-semibold">
        {league.name} {seasonLabel(season.year)}
      </h1>

      {overview.last_sync_status === "failed" && (
        <p
          role="alert"
          className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm"
        >
          Son veri güncellemesi başarısız oldu. Gösterilen bilgiler
          veritabanındaki son başarılı güncellemeye aittir.
        </p>
      )}

      <section
        className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4"
        aria-label="Genel görünüm"
      >
        <StatCard
          label="Oynanan maç"
          value={String(overview.played)}
          hint={`Toplam ${overview.total_fixtures} maç`}
        />
        <StatCard
          label="Tamamlanmamış maç"
          value={String(overview.unfinished)}
        />
        <StatCard
          label="Toplam gol"
          value={String(overview.total_goals)}
          hint={`Maç başına ${formatNumber(overview.goals_per_match)}`}
        />
        <StatCard
          label="Son veri güncellemesi"
          value={
            overview.last_sync_at
              ? formatDateTime(overview.last_sync_at)
              : "Henüz yok"
          }
        />
      </section>

      <h2 className="mb-3 mt-8 text-xl font-semibold">Puan durumu</h2>
      <StandingsTable rows={rows} seasonId={season.id} />
    </div>
  );
}
