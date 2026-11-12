import { StatCard, StatCardProps } from "./stat-card";

type StatCardSectionProps = {
  title: string;
  cards: StatCardProps[];
  className?: string;
};

export function StatCardSection({
  title,
  className,
  cards,
}: StatCardSectionProps) {
  return (
    <section aria-label={title} className={className}>
      {cards.length > 0 &&
        cards.map((card, index) => <StatCard key={index} {...card} />)}
    </section>
  );
}
