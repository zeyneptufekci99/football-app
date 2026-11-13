import { Suspense } from "react";
import { UsageBadge } from "./usage-badge";

export function Header() {
  return (
    <header className="bg-blue-700 text-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-4">
        <span className="text-lg font-semibold">Futbol Panosu</span>
        <Suspense
          fallback={
            <span className="text-xs text-blue-100">
              API kullanımı yükleniyor…
            </span>
          }
        >
          <UsageBadge />
        </Suspense>
      </div>
    </header>
  );
}
