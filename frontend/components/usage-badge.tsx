import { api } from "@/lib/api";
import { formatTime } from "@/lib/format";

export async function UsageBadge() {
  const usage = await api.usage().catch(() => null);
  if (!usage)
    return (
      <span className="text-xs text-blue-100">API kullanımı: bilinmiyor</span>
    );

  const ratio = Math.min(usage.used_today / usage.daily_limit, 1);
  const high = ratio >= 0.8;
  const title =
    `Kendi kayıtlarımıza göre bugün ${usage.used_today} istek atıldı (${usage.failed_today} başarısız).` +
    (usage.resets_at
      ? ` Sayaç ${formatTime(usage.resets_at)} saatinde sıfırlanır.`
      : "") +
    (usage.api_reported_remaining !== null
      ? ` API'nin bildirdiği kalan: ${usage.api_reported_remaining}.`
      : "");

  return (
    <div
      className="flex items-center gap-2 text-xs text-blue-100"
      title={title}
    >
      <span>API istekleri</span>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={usage.daily_limit}
        aria-valuenow={usage.used_today}
        aria-label="Günlük API kullanımı"
        className="h-1.5 w-14  md:w-20 overflow-hidden rounded bg-blue-900/50"
      >
        <div
          className={`h-full ${high ? "bg-red-400" : "bg-green-400"}`}
          style={{ width: `${ratio * 100}%` }}
        />
      </div>
      <span
        className={`tabular-nums ${high ? "font-medium text-red-200" : "text-white"}`}
      >
        {usage.used_today} / {usage.daily_limit}
      </span>
    </div>
  );
}
