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
  return (
    <div className="rounded-lg border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">#</TableHead>
            <TableHead>Takım</TableHead>
            <TableHead className={num} title="Oynanan">
              O
            </TableHead>
            <TableHead className={num} title="Galibiyet">
              G
            </TableHead>
            <TableHead className={num} title="Beraberlik">
              B
            </TableHead>
            <TableHead className={num} title="Mağlubiyet">
              M
            </TableHead>
            <TableHead
              className={`${num} hidden sm:table-cell`}
              title="Atılan gol"
            >
              AG
            </TableHead>
            <TableHead
              className={`${num} hidden sm:table-cell`}
              title="Yenilen gol"
            >
              YG
            </TableHead>
            <TableHead className={num} title="Averaj">
              Av
            </TableHead>
            <TableHead className={num} title="Puan">
              P
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((r) => (
            <TableRow key={r.team_id}>
              <TableCell className="font-medium tabular-nums">
                {r.rank}
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
                      className="h-[22px] w-[22px] object-contain"
                    />
                  )}
                  {r.team_name}
                </Link>
              </TableCell>
              <TableCell className={num}>{r.played}</TableCell>
              <TableCell className={num}>{r.won}</TableCell>
              <TableCell className={num}>{r.drawn}</TableCell>
              <TableCell className={num}>{r.lost}</TableCell>
              <TableCell className={`${num} hidden sm:table-cell`}>
                {r.goals_for}
              </TableCell>
              <TableCell className={`${num} hidden sm:table-cell`}>
                {r.goals_against}
              </TableCell>
              <TableCell className={num}>
                {r.goal_diff > 0 ? `+${r.goal_diff}` : r.goal_diff}
              </TableCell>
              <TableCell className={`${num} font-semibold`}>
                {r.points}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
