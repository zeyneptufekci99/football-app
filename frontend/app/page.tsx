import { Suspense } from "react";
import { DashboardHeader } from "@/components/dashboard-header";
import { NoData } from "@/components/no-data";
import { StandingsTable } from "@/components/standings-table";
import { StatCardProps } from "@/components/stat-card";
import { StatCardSection } from "@/components/stat-card-section";
import { SyncButton } from "@/components/sync-button";
import { api } from "@/lib/api";
import { formatDateTime, formatNumber, hoursSince } from "@/lib/format";
import { resolveSelection, seasonLabel } from "@/lib/season";
import { Notice } from "@/components/notice";

type SearchParams = Promise<{ season?: string }>;

async function HomeContent({ searchParams }: { searchParams: SearchParams }) {
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

  const statCardsData: StatCardProps[] = [
    {
      label: "Oynanan maç",
      value: String(overview.played),
      hint: `Toplam ${overview.total_fixtures} maç`,
      tone: "blue",
    },
    {
      label: "Tamamlanmamış maç",
      value: String(overview.unfinished),
      tone: "green",
    },
    {
      label: "Toplam gol",
      value: String(overview.total_goals),
      hint: `Maç başına ${formatNumber(overview.goals_per_match)}`,
      tone: "sky",
    },
    {
      label: "Son veri güncellemesi",
      value: overview.last_sync_at
        ? formatDateTime(overview.last_sync_at)
        : "Henüz yok",
      tone: "teal",
    },
  ];

  return (
    <div className="flex flex-col md:gap-4 gap-6 ">
      <DashboardHeader
        leagues={leagues}
        leagueId={league.id}
        seasonId={season.id}
        active="overview"
      />

      <div className="flex flex-col gap-4 md:gap-6">
        <h1 className="text-2xl font-semibold  text-blue-900">
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
            Bu sezonda tamamlanmamış maçlar var ve veriler 24 saatten uzun
            süredir güncellenmedi. Sonuçlar eski olabilir.
          </Notice>
        )}
        {overview.last_sync_at === null && (
          <Notice>
            Bu lig ve sezon için henüz başarılı bir senkronizasyon kaydı yok.
          </Notice>
        )}

        <StatCardSection
          cards={statCardsData}
          className="grid grid-cols-2 gap-4 lg:grid-cols-4"
          title="Genel görünüm"
        />

        <SyncButton leagueId={league.id} year={season.year} />
      </div>
      <div className="flex flex-col gap-4 md:gap-6 ">
        <h2 className=" border-l-4 border-green-600 pl-3 text-xl font-semibold text-blue-900">
          Puan durumu
        </h2>
        <StandingsTable rows={rows} seasonId={season.id} />
      </div>
    </div>
  );
}

export default function Home({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense
      fallback={<p className="text-sm text-neutral-600">Yükleniyor…</p>}
    >
      <HomeContent searchParams={searchParams} />
    </Suspense>
  );
}
