import { Card, CardContent } from "./ui/card";

export type StatTone = "blue" | "green" | "sky" | "teal";

const TONES: Record<StatTone, { card: string; value: string }> = {
  blue: { card: "border-t-blue-600 bg-blue-50", value: "text-blue-800" },
  green: { card: "border-t-green-600 bg-green-50", value: "text-green-800" },
  sky: { card: "border-t-sky-500 bg-sky-50", value: "text-sky-800" },
  teal: {
    card: "border-t-teal-500 bg-teal-50",
    value: "text-teal-800",
  },
};

export type StatCardProps = {
  label: string;
  value: string;
  tone?: StatTone;
  hint?: string;
};

export function StatCard({ label, value, tone = "blue", hint }: StatCardProps) {
  const { card, value: valueClass } = TONES[tone];
  return (
    <Card className={`border-t-4 ${card} shadow-sm`}>
      <CardContent className="md:p-4">
        <p className="text-sm text-neutral-600">{label}</p>
        <p
          className={`mt-1 text-xl md:text-2xl font-semibold tabular-nums ${valueClass}`}
        >
          {value}
        </p>
        {hint && <p className="mt-1 text-xs text-neutral-500">{hint}</p>}
      </CardContent>
    </Card>
  );
}
