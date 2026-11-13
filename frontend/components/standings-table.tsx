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
    <div className="rounded-lg border bg-white">
      <Table>
        <TableHeader className="bg-blue-100">
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
              className={
                r.rank === 1
                  ? "bg-green-50 hover:bg-green-100"
                  : "even:bg-blue-50/40 hover:bg-blue-50"
              }
            >
              <TableCell className="font-medium tabular-nums">
                <span className={r.rank === 1 ? "text-green-700" : ""}>
                  {r.rank}
                </span>
              </TableCell>
              <TableCell>
                <Link
                  href={`/teams/${r.team_id}?season=${seasonId}`}
                  className="flex items-center gap-2 hover:underline"
                >
                  {r.team_logo && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={r.team_logo}
                      alt=""
                      width={22}
                      height={22}
                      className="h-5.5 w-5.5 object-contain"
                    />
                  )}
                  {r.team_name}
                </Link>
              </TableCell>
              <TableCell className={num}>{r.played}</TableCell>
              <TableCell className={`${num} text-green-700`}>{r.won}</TableCell>
              <TableCell className={num}>{r.drawn}</TableCell>
              <TableCell className={`${num} text-red-700`}>{r.lost}</TableCell>
              <TableCell className={`${num} hidden sm:table-cell`}>
                {r.goals_for}
              </TableCell>
              <TableCell className={`${num} hidden sm:table-cell`}>
                {r.goals_against}
              </TableCell>
              <TableCell className={num}>
                {r.goal_diff > 0 ? `+${r.goal_diff}` : r.goal_diff}
              </TableCell>
              <TableCell className={`${num} font-semibold text-blue-700`}>
                {r.points}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
