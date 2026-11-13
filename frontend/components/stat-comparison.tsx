import type { MatchStatsTeam } from "@/lib/types";

type Row = {
  key: string;
  label: string;
  suffix?: string;
  digits?: number;
  bar?: boolean;
};

const ROWS: Row[] = [
  { key: "Ball Possession", label: "Topa sahip olma", suffix: "%", bar: true },
  { key: "expected_goals", label: "Beklenen gol (xG)", digits: 2, bar: true },
  { key: "Total Shots", label: "Toplam şut", bar: true },
  { key: "Shots on Goal", label: "İsabetli şut", bar: true },
  { key: "Shots off Goal", label: "İsabetsiz şut", bar: true },
  { key: "Blocked Shots", label: "Engellenen şut", bar: true },
  { key: "Corner Kicks", label: "Korner", bar: true },
  { key: "Fouls", label: "Faul", bar: true },
  { key: "Offsides", label: "Ofsayt", bar: true },
  { key: "Yellow Cards", label: "Sarı kart", bar: true },
  { key: "Red Cards", label: "Kırmızı kart", bar: true },
  { key: "Goalkeeper Saves", label: "Kurtarış", bar: true },
  { key: "Total passes", label: "Toplam pas", bar: true },
  { key: "Passes %", label: "Pas isabeti", suffix: "%" },
];

function fmt(v: number | null | undefined, row: Row) {
  if (v === null || v === undefined) return "–";
  const text = v.toLocaleString("tr-TR", {
    maximumFractionDigits: row.digits ?? 0,
    minimumFractionDigits: row.digits ?? 0,
  });
  return `${text}${row.suffix ?? ""}`;
}
type StatComparisonProps = {
  home: MatchStatsTeam;
  away: MatchStatsTeam;
};

export function StatComparison({ home, away }: StatComparisonProps) {
  const rows = ROWS.filter((r) => r.key in home.stats || r.key in away.stats);

  return (
    <div className="space-y-4">
      <div className="flex justify-between text-sm font-semibold">
        <span className="text-blue-800">{home.name}</span>
        <span className="text-green-800">{away.name}</span>
      </div>
      {rows.map((row) => {
        const h = home.stats[row.key] ?? null;
        const a = away.stats[row.key] ?? null;
        const total = (h ?? 0) + (a ?? 0);
        const homeShare = total > 0 ? ((h ?? 0) / total) * 100 : 0;
        return (
          <div key={row.key}>
            <div className="mb-1 grid grid-cols-[1fr_auto_1fr] items-baseline gap-3 text-sm">
              <span className="font-semibold tabular-nums">{fmt(h, row)}</span>
              <span className="text-center text-xs text-neutral-600">
                {row.label}
              </span>
              <span className="text-right font-semibold tabular-nums">
                {fmt(a, row)}
              </span>
            </div>
            {row.bar && (
              <div
                className="flex h-2 overflow-hidden rounded bg-neutral-200"
                aria-hidden="true"
              >
                {total > 0 && (
                  <>
                    <div
                      className="bg-blue-600"
                      style={{ width: `${homeShare}%` }}
                    />
                    <div
                      className="bg-green-600"
                      style={{ width: `${100 - homeShare}%` }}
                    />
                  </>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
