export function NoData() {
  return (
    <p className="rounded-lg border bg-white p-6">
      Veritabanında henüz veri yok. Önce şu komutu çalıştırın:{" "}
      <code className="rounded bg-neutral-100 px-1">
        docker compose run --rm backend python -m app.sync --league 203 --season
        2024
      </code>
    </p>
  );
}
