import { api } from "@/lib/api";
import { resolveSelection, seasonLabel } from "@/lib/season";
import { DashboardHeader } from "@/components/dashboard-header";
import { NoData } from "@/components/no-data";

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ season?: string }>;
}) {
  const { season: seasonParam } = await searchParams;
  const leagues = (await api.leagues()).filter((l) => l.seasons.length > 0);
  if (leagues.length === 0) return <NoData />;

  const { league, season } = resolveSelection(leagues, seasonParam);

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
      <p className="mt-2 text-sm text-neutral-600">
        Sezon kimliği: {season.id}
      </p>
    </div>
  );
}
