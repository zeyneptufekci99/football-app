const dateTime = new Intl.DateTimeFormat("tr-TR", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Europe/Istanbul",
});

export const formatDateTime = (iso: string) => dateTime.format(new Date(iso));

export const formatNumber = (n: number | null, digits = 2) =>
  n === null ? "–" : n.toLocaleString("tr-TR", { maximumFractionDigits: digits });

export const STATUS_OPTIONS = [
  { value: "FT", label: "Tamamlandı" },
  { value: "NS", label: "Başlamadı" },
  { value: "PST", label: "Ertelendi" },
  { value: "CANC", label: "İptal edildi" },
];

const LIVE = ["1H", "HT", "2H", "ET", "BT", "P", "LIVE", "INT"];

export function statusInfo(code: string): { label: string; tone: "done" | "live" | "idle" } {
  if (code === "FT") return { label: "Bitti", tone: "done" };
  if (code === "AET") return { label: "Uzatmada bitti", tone: "done" };
  if (code === "PEN") return { label: "Penaltılarla bitti", tone: "done" };
  if (code === "NS") return { label: "Başlamadı", tone: "idle" };
  if (code === "PST") return { label: "Ertelendi", tone: "idle" };
  if (code === "CANC") return { label: "İptal", tone: "idle" };
  if (code === "TBD") return { label: "Belirsiz", tone: "idle" };
  if (LIVE.includes(code)) return { label: "Canlı", tone: "live" };
  return { label: code, tone: "idle" };
}

const dateOnly = new Intl.DateTimeFormat("tr-TR", { dateStyle: "medium", timeZone: "Europe/Istanbul" });

export const formatDate = (iso: string) => dateOnly.format(new Date(iso));

export const formatPercent = (n: number | null) =>
  n === null ? "–" : `${(n * 100).toLocaleString("tr-TR", { maximumFractionDigits: 0 })}%`;

export const hoursSince = (iso: string) => (Date.now() - new Date(iso).getTime()) / 3_600_000;

const timeOnly = new Intl.DateTimeFormat("tr-TR", { timeStyle: "short", timeZone: "Europe/Istanbul" });

export const formatTime = (iso: string) => timeOnly.format(new Date(iso));