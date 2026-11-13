import Link from "next/link";
import { api } from "@/lib/api";
import type { Fixture } from "@/lib/types";
import { formatDateTime, statusInfo } from "@/lib/format";
import { resolveSelection, seasonLabel } from "@/lib/season";
import { DashboardHeader } from "@/components/dashboard-header";
import { NoData } from "@/components/no-data";
import { Badge } from "@/components/ui/badge";
import { FixturesFilterForm } from "@/components/fixtures-filter-form";

import { MdOutlineChevronLeft, MdOutlineChevronRight } from "react-icons/md";

const PAGE_SIZE = 25;

type SearchParams = {
  season?: string;
  team_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: string;
};

const TONE = {
  done: "border-transparent bg-green-100 text-green-900",
  live: "border-transparent bg-amber-100 text-amber-900",
  idle: "border-transparent bg-neutral-100 text-neutral-600",
};

function TeamLink({
  team,
  seasonId,
  align,
}: {
  team: Fixture["home"];
  seasonId: number;
  align: "left" | "right";
}) {
  return (
    <Link
      href={`/teams/${team.id}?season=${seasonId}`}
      className={`flex items-center gap-2 hover:underline ${align === "right" ? "flex-row-reverse text-right" : ""}`}
    >
      {team.logo && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={team.logo}
          alt=""
          width={22}
          height={22}
          className="h-5.5 w-5.5 shrink-0 object-contain"
        />
      )}
      <span>{team.name}</span>
    </Link>
  );
}

export default async function FixturesPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const sp = await searchParams;
  const leagues = (await api.leagues()).filter((l) => l.seasons.length > 0);
  if (leagues.length === 0) return <NoData />;

  const { league, season } = resolveSelection(leagues, sp.season);
  const page = Math.max(Number(sp.page) || 1, 1);

  const [teams, rows] = await Promise.all([
    api.teams(season.id),
    api.fixtures(season.id, {
      team_id: sp.team_id,
      status: sp.status,
      date_from: sp.date_from,
      date_to: sp.date_to,
      limit: PAGE_SIZE + 1, // fazladan 1 kayıt: sonraki sayfa var mı?
      offset: (page - 1) * PAGE_SIZE,
    }),
  ]);
  const hasNext = rows.length > PAGE_SIZE;
  const items = rows.slice(0, PAGE_SIZE);

  const pageHref = (p: number) => {
    const q = new URLSearchParams({ season: String(season.id) });
    for (const key of ["team_id", "status", "date_from", "date_to"] as const) {
      const value = sp[key];
      if (value) q.set(key, value);
    }
    q.set("page", String(p));
    return `/fixtures?${q}`;
  };

  return (
    <div className="flex flex-col md:gap-4 gap-6 ">
      <DashboardHeader
        leagues={leagues}
        leagueId={league.id}
        seasonId={season.id}
        active="fixtures"
      />

      <div className="flex flex-col gap-4 md:gap-6">
        <h1 className="text-2xl font-semibold">
          Maçlar · {league.name} {seasonLabel(season.year)}
        </h1>

        <FixturesFilterForm
          key={season.id}
          seasonId={season.id}
          seasonYear={season.year}
          teams={teams}
          values={{
            team_id: sp.team_id,
            status: sp.status,
            date_from: sp.date_from,
            date_to: sp.date_to,
          }}
        />
      </div>

      {items.length === 0 ? (
        <p className="text-neutral-600">Bu filtrelere uyan maç bulunamadı.</p>
      ) : (
        <ul className="divide-y rounded-lg border bg-white">
          {items.map((f) => {
            const info = statusInfo(f.status_short);
            const hasScore = f.home_goals !== null && f.away_goals !== null;
            return (
              <li key={f.id} className="px-4 py-3">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs text-neutral-600">
                  <span>
                    {formatDateTime(f.kickoff)}
                    {f.round ? ` · ${f.round}` : ""}
                  </span>
                  <Badge
                    variant="outline"
                    className={TONE[info.tone]}
                    title={f.status_long ?? undefined}
                  >
                    {info.label}
                  </Badge>
                </div>
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 text-sm">
                  <div className="flex justify-end">
                    <TeamLink
                      team={f.home}
                      seasonId={season.id}
                      align="right"
                    />
                  </div>
                  <div className="min-w-16 rounded-md bg-blue-100 px-2 py-1 text-center text-lg font-semibold tabular-nums text-blue-900">
                    {hasScore ? `${f.home_goals} - ${f.away_goals}` : "–"}
                  </div>
                  <div>
                    <TeamLink team={f.away} seasonId={season.id} align="left" />
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <div className="flex items-center justify-between text-sm">
        {page > 1 ? (
          <Link href={pageHref(page - 1)} className="underline">
            <div className="flex p-2 rounded-md items-center border border-primary">
              <MdOutlineChevronLeft color="oklch(0.488 0.2 264)" size={20} />
            </div>
          </Link>
        ) : (
          <span />
        )}
        <span className="text-neutral-600">Sayfa {page}</span>
        {hasNext ? (
          <Link href={pageHref(page + 1)} className="underline">
            <div className="flex p-2 rounded-md items-center border border-primary">
              <MdOutlineChevronRight color="oklch(0.488 0.2 264)" size={20} />
            </div>
          </Link>
        ) : (
          <span />
        )}
      </div>
    </div>
  );
}
