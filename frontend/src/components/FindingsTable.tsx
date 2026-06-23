import type { Finding } from '../api/client';

type Props = {
  findings?: Finding[] | null;
};

export default function FindingsTable({ findings }: Props) {
  const rows = findings ?? [];
  return (
    <article className="panel">
      <div className="panel-head">
        <h2>Findings needing attention</h2>
        <button>Filter</button>
      </div>
      <div className="finding-list">
        {rows.length === 0 ? (
          <p className="empty-state">No findings recorded.</p>
        ) : (
          rows.slice(0, 6).map((finding) => (
            <div className="finding-row" key={finding.id}>
              <span className={`severity ${finding.severity}`}>{finding.severity}</span>
              <strong>{finding.rule_id}</strong>
              <small>{finding.path}</small>
            </div>
          ))
        )}
      </div>
    </article>
  );
}
