import type { DashboardSummary } from '../api/client';

type Props = {
  summary?: DashboardSummary | null;
};

export default function SummaryCards({ summary }: Props) {
  const safeSummary = summary ?? {
    projects: 0,
    runs: 0,
    findings: 0,
    critical_findings: 0,
    updates: 0,
    mode: 'observe',
  };
  const cards = [
    { label: 'Projects under guard', value: safeSummary.projects, tone: 'neutral' },
    { label: 'Critical findings', value: safeSummary.critical_findings, tone: 'danger' },
    { label: 'Scan runs', value: safeSummary.runs, tone: 'good' },
    { label: 'Update events', value: safeSummary.updates, tone: 'warn' },
  ];

  return (
    <section className="summary-grid">
      {cards.map((card) => (
        <article className={`summary-card ${card.tone}`} key={card.label}>
          <span>{card.label}</span>
          <strong>{card.value}</strong>
        </article>
      ))}
    </section>
  );
}
