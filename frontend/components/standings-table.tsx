import Link from "next/link";
import type { StandingRow } from "@/lib/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type StandingsTableProps = {
  rows: StandingRow[];
  seasonId: number;
};
export function StandingsTable({ rows, seasonId }: StandingsTableProps) {
  const num = "text-right tabular-nums";
  const head = "font-semibold text-blue-900";
  return (
    <div className="rounded-lg border overflow-hidden bg-white border-t-4 border-t-blue-400">
      <Table>
        <TableHeader className="bg-blue-100 overflow-hidden">
          <TableRow className="hover:bg-blue-100">
            <TableHead className={`w-10 ${head}`}>#</TableHead>
            <TableHead className={head}>Takım</TableHead>
            <TableHead className={`${num} ${head}`} title="Oynanan">
              O
            </TableHead>
            <TableHead className={`${num} ${head}`} title="Galibiyet">
              G
            </TableHead>
            <TableHead className={`${num} ${head}`} title="Beraberlik">
              B
            </TableHead>
            <TableHead className={`${num} ${head}`} title="Mağlubiyet">
              M
            </TableHead>
            <TableHead
              className={`${num} ${head} hidden sm:table-cell`}
              title="Atılan gol"
            >
              AG
            </TableHead>
            <TableHead
              className={`${num} ${head}  hidden sm:table-cell`}
              title="Yenilen gol"
            >
              YG
            </TableHead>
            <TableHead className={`${num} ${head}`} title="Averaj">
              Av
            </TableHead>
            <TableHead className={`${num} ${head}`} title="Puan">
              P
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((r) => (
            <TableRow
              key={r.team_id}
              className={`text-sm ${
                r.rank === 1
                  ? "bg-green-50 hover:bg-green-100"
                  : "even:bg-blue-50/40 hover:bg-blue-50"
              }`}
            >
              <TableCell className="font-medium tabular-nums ">
                <span className={r.rank === 1 ? "text-green-700" : ""}>
                  {r.rank}
                </span>
              </TableCell>
              <TableCell className="w-full max-w-0 text-xs md:text-sm">
                <Link
                  href={`/teams/${r.team_id}?season=${seasonId}`}
                  className="flex min-w-0 items-center gap-2 hover:underline"
                  title={r.team_name}
                >
                  {r.team_logo && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={r.team_logo}
                      alt=""
                      width={22}
                      height={22}
                      className="h-5.5 w-5.5 shrink-0 object-contain"
                    />
                  )}
                  <span className="truncate">{r.team_name}</span>
                </Link>
              </TableCell>
              <TableCell className={`${num} md:text-sm text-xs`}>
                {r.played}
              </TableCell>
              <TableCell
                className={`${num} text-green-700 md:text-sm text-xs `}
              >
                {r.won}
              </TableCell>
              <TableCell className={`${num} md:text-sm text-xs`}>
                {r.drawn}
              </TableCell>
              <TableCell className={`${num} text-red-700 md:text-sm text-xs`}>
                {r.lost}
              </TableCell>
              <TableCell
                className={`${num} hidden sm:table-cell md:text-sm text-xs`}
              >
                {r.goals_for}
              </TableCell>
              <TableCell
                className={`${num} hidden sm:table-cell md:text-sm text-xs`}
              >
                {r.goals_against}
              </TableCell>
              <TableCell className={`${num} md:text-sm text-xs`}>
                {r.goal_diff > 0 ? `+${r.goal_diff}` : r.goal_diff}
              </TableCell>
              <TableCell
                className={`${num} font-semibold text-blue-700 md:text-sm text-xs`}
              >
                {r.points}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
