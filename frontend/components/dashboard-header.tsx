import Link from "next/link";
import { SeasonPicker } from "@/components/season-picker";
import { League } from "@/lib/types";

type Props = {
  leagues: League[];
  leagueId: number;
  seasonId: number;
  active: "overview" | "fixtures";
};

export function DashboardHeader({
  leagues,
  leagueId,
  seasonId,
  active,
}: Props) {
  const tab = (isActive: boolean) =>
    `rounded-md px-3 py-1.5 text-sm font-medium ${
      isActive ? "bg-neutral-900 text-white" : "hover:bg-neutral-200"
    }`;

  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
      <nav className="flex gap-1" aria-label="Sayfalar">
        <Link
          href={`/?season=${seasonId}`}
          className={tab(active === "overview")}
        >
          Genel görünüm
        </Link>
        <Link
          href={`/fixtures?season=${seasonId}`}
          className={tab(active === "fixtures")}
        >
          Maçlar
        </Link>
      </nav>
      <SeasonPicker leagues={leagues} leagueId={leagueId} seasonId={seasonId} />
    </div>
  );
}
