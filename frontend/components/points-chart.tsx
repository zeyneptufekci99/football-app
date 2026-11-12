"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PointsPoint } from "@/lib/types";
import { formatDate } from "@/lib/format";

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: PointsPoint }[];
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-md border bg-white px-3 py-2 text-xs shadow">
      <p className="font-medium">
        {p.match_no}. maç · {p.opponent}
      </p>
      <p className="text-neutral-600">{formatDate(p.kickoff)}</p>
      <p className="mt-1 tabular-nums">{p.cumulative_points} puan</p>
    </div>
  );
}

export function PointsChart({ data }: { data: PointsPoint[] }) {
  if (data.length === 0) {
    return (
      <p className="text-sm text-neutral-600">
        Bu takım için henüz tamamlanmış maç yok.
      </p>
    );
  }
  return (
    <div
      className="h-64 w-full"
      role="img"
      aria-label="Maç maç birikmiş puan grafiği"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 8, right: 16, bottom: 0, left: -16 }}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="match_no" tickLine={false} />
          <YAxis allowDecimals={false} tickLine={false} />
          <Tooltip content={<ChartTooltip />} />
          <Line
            type="monotone"
            dataKey="cumulative_points"
            stroke="#166534"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
