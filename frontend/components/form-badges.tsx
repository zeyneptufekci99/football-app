const STYLE: Record<
  string,
  { label: string; className: string; name: string }
> = {
  W: { label: "G", className: "bg-green-700 text-white", name: "Galibiyet" },
  D: {
    label: "B",
    className: "bg-neutral-300 text-neutral-900",
    name: "Beraberlik",
  },
  L: { label: "M", className: "bg-red-700 text-white", name: "Mağlubiyet" },
};

type FormBadgesProps = {
  form: string;
};

export function FormBadges({ form }: FormBadgesProps) {
  if (!form) return <span className="text-sm text-neutral-600">–</span>;
  return (
    <span className="flex gap-1" aria-label={`Son ${form.length} maç`}>
      {form.split("").map((c, i) => {
        const s = STYLE[c];
        return (
          <span
            key={i}
            title={s?.name}
            className={`inline-flex h-7 w-7 items-center justify-center rounded text-xs font-semibold ${s?.className}`}
          >
            {s?.label ?? c}
          </span>
        );
      })}
    </span>
  );
}
