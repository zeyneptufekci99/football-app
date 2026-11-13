"use client";

import { useState } from "react";
import Link from "next/link";
import type { TeamOption } from "@/lib/types";
import { STATUS_OPTIONS } from "@/lib/format";
import { Button } from "@/components/ui/button";

type FixturesFilterFormProps = {
  seasonId: number;
  seasonYear: number;
  teams: TeamOption[];
  values: {
    team_id?: string;
    status?: string;
    date_from?: string;
    date_to?: string;
  };
};

const field = "h-9 rounded-md border bg-white px-2 text-sm";

export function FixturesFilterForm({
  seasonId,
  seasonYear,
  teams,
  values,
}: FixturesFilterFormProps) {
  const [from, setFrom] = useState(values.date_from ?? "");
  const [to, setTo] = useState(values.date_to ?? "");

  // Seçilebilir aralık: sezonun başladığı yaz ile bittiği yaz
  const min = `${seasonYear}-06-01`;
  const max = `${seasonYear + 1}-07-31`;

  function onFromChange(value: string) {
    setFrom(value);
    // Bitiş, yeni başlangıçtan önceyse bitiş de başlangıca çekilir
    if (value && to && to < value) setTo(value);
  }

  return (
    <form
      method="get"
      className="shadow-sm flex flex-wrap items-end gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4 border-t-4 border-t-blue-400"
    >
      <input type="hidden" name="season" value={seasonId} />

      <label className="flex flex-col gap-1 text-sm">
        Takım
        <select
          name="team_id"
          defaultValue={values.team_id ?? ""}
          className={`${field} w-48`}
        >
          <option value="">Tümü</option>
          {teams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Durum
        <select
          name="status"
          defaultValue={values.status ?? ""}
          className={`${field} w-40`}
        >
          <option value="">Tümü</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Başlangıç tarihi
        <input
          type="date"
          name="date_from"
          value={from}
          min={min}
          max={to || max}
          onChange={(e) => onFromChange(e.target.value)}
          className={field}
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        Bitiş tarihi
        <input
          type="date"
          name="date_to"
          value={to}
          min={from || min}
          max={max}
          onChange={(e) => setTo(e.target.value)}
          className={field}
        />
      </label>

      <Button type="submit">Filtrele</Button>
      <Link
        href={`/fixtures?season=${seasonId}`}
        className="py-2 text-sm underline"
      >
        Temizle
      </Link>
    </form>
  );
}
