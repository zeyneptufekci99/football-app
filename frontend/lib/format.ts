const dateTime = new Intl.DateTimeFormat("tr-TR", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Europe/Istanbul",
});

export const formatDateTime = (iso: string) => dateTime.format(new Date(iso));

export const formatNumber = (n: number | null, digits = 2) =>
  n === null ? "–" : n.toLocaleString("tr-TR", { maximumFractionDigits: digits });