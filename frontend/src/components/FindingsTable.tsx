import { useState } from 'react';

import type { Finding } from '../api/client';

type Props = {
  findings?: Finding[] | null;
};

export default function FindingsTable({ findings }: Props) {
  const rows = findings ?? [];
  const [severity, setSeverity] = useState<string>('all');
  const visibleRows =
    severity === 'all'
      ? rows
      : rows.filter((finding) => finding.severity.toLowerCase() === severity);

  return (
    <article className="panel">
      <div className="panel-head">
        <h2>Findings needing attention</h2>
        <label className="select-control">
          <span className="sr-only">Finding severity</span>
          <select onChange={(event) => setSeverity(event.target.value)} value={severity}>
            <option value="all">All</option>
            <option value="critical">Critical</option>
            <option value="error">Error</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
        </label>
      </div>
      <div className="finding-list">
        {visibleRows.length === 0 ? (
          <p className="empty-state">No findings recorded.</p>
        ) : (
          visibleRows.slice(0, 6).map((finding) => (
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
