import { Suspense } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Fixture } from "@/lib/types";
import { formatDateTime, formatRound, statusInfo } from "@/lib/format";
import { StatComparison } from "@/components/stat-comparison";
import { CardContainer } from "@/components/card-container";

function Team({
  team,
  align,
}: {
  team: Fixture["home"];
  align: "left" | "right";
}) {
  return (
    <Link
      href={`/teams/${team.id}`}
      className={`flex items-center gap-2 text-lg font-semibold hover:underline ${align === "right" ? "flex-row-reverse text-right" : ""}`}
    >
      {team.logo && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={team.logo}
          alt=""
          width={36}
          height={36}
          className="h-9 w-9 shrink-0 object-contain"
        />
      )}
      <span>{team.name}</span>
    </Link>
  );
}

function Notice({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-neutral-600">{children}</p>;
}

async function MatchContent({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ season?: string }>;
}) {
  const { id } = await params;
  const { season } = await searchParams;
  if (!/^\d+$/.test(id)) notFound();

  let fixture: Fixture;
  try {
    fixture = await api.fixture(id);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }
  const stats = await api.matchStats(id);

  const info = statusInfo(fixture.status_short);
  const hasScore = fixture.home_goals !== null && fixture.away_goals !== null;
  const backHref =
    season && /^\d+$/.test(season) ? `/fixtures?season=${season}` : "/fixtures";

  return (
    <div className="flex flex-col gap-6">
      <Link href={backHref} className="text-sm text-blue-700 underline">
        ← Maçlara dön
      </Link>

      <div className="rounded-lg border bg-white p-4">
        <p className="mb-3 text-center text-xs text-neutral-600">
          {formatDateTime(fixture.kickoff)}
          {fixture.round ? ` · ${formatRound(fixture.round)}` : ""}
          {fixture.venue_name ? ` · ${fixture.venue_name}` : ""}
        </p>
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          <div className="flex justify-end">
            <Team team={fixture.home} align="right" />
          </div>
          <div className="min-w-20 rounded-md bg-blue-100 px-3 py-2 text-center text-2xl font-semibold tabular-nums text-blue-900">
            {hasScore ? `${fixture.home_goals} - ${fixture.away_goals}` : "–"}
          </div>
          <div>
            <Team team={fixture.away} align="left" />
          </div>
        </div>
        <p className="mt-3 text-center text-xs text-neutral-600">
          {info.label}
        </p>
      </div>

      <CardContainer header="Maç istatistikleri">
        {!stats.ok ? (
          <Notice>
            {stats.status === 503
              ? "Günlük API istek bütçesi doldu. Bu maçın istatistikleri henüz kaydedilmediği için gösterilemiyor, yarın tekrar deneyin."
              : "İstatistikler şu anda API-Football'dan alınamadı. Daha sonra tekrar deneyin."}
          </Notice>
        ) : !stats.data.available ? (
          <Notice>
            {stats.data.reason === "not_finished"
              ? "Maç tamamlanmadığı için istatistik yok."
              : "Bu maç için API-Football istatistik sağlamıyor."}
          </Notice>
        ) : (
          stats.data.home &&
          stats.data.away && (
            <StatComparison home={stats.data.home} away={stats.data.away} />
          )
        )}
      </CardContainer>
    </div>
  );
}

export default function MatchPage(props: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ season?: string }>;
}) {
  return (
    <Suspense
      fallback={<p className="text-sm text-neutral-600">Yükleniyor…</p>}
    >
      <MatchContent {...props} />
    </Suspense>
  );
}
