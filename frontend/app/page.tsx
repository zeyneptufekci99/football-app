import { api } from "@/lib/api";
import { formatDateTime, formatNumber, hoursSince } from "@/lib/format";
import { resolveSelection, seasonLabel } from "@/lib/season";
import { DashboardHeader } from "@/components/dashboard-header";
import { NoData } from "@/components/no-data";
import { StandingsTable } from "@/components/standings-table";
import { SyncButton } from "@/components/sync-button";
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

function Notice({ children }: { children: React.ReactNode }) {
  return (
    <p
      role="alert"
      className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm"
    >
      {children}
    </p>
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

  const failed = overview.last_sync_status === "failed";
  const stale =
    !failed &&
    overview.unfinished > 0 &&
    overview.last_sync_at !== null &&
    hoursSince(overview.last_sync_at) > 24;

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

      {failed && (
        <Notice>
          Son veri güncellemesi başarısız oldu. Gösterilen bilgiler
          veritabanındaki son başarılı güncellemeye aittir.
        </Notice>
      )}
      {stale && (
        <Notice>
          Bu sezonda tamamlanmamış maçlar var ve veriler 24 saatten uzun süredir
          güncellenmedi. Sonuçlar eski olabilir.
        </Notice>
      )}
      {overview.last_sync_at === null && (
        <Notice>
          Bu lig ve sezon için henüz başarılı bir senkronizasyon kaydı yok.
        </Notice>
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

      <div className="mt-4">
        <SyncButton leagueId={league.id} year={season.year} />
      </div>

      <h2 className="mb-3 mt-8 text-xl font-semibold">Puan durumu</h2>
      <StandingsTable rows={rows} seasonId={season.id} />
    </div>
  );
}
