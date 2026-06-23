import type { ScanRun } from '../api/client';

type Props = {
  runs?: ScanRun[] | null;
};

export default function RunTimeline({ runs }: Props) {
  const rows = runs ?? [];
  return (
    <article className="panel">
      <h2>Daemon timeline</h2>
      {rows.length === 0 ? (
        <p className="empty-state">No scan runs recorded.</p>
      ) : (
        <ol className="timeline">
          {rows.slice(0, 6).map((run) => (
            <li key={run.id}>
              {run.project} scan #{run.id} at {run.created_at}
            </li>
          ))}
        </ol>
      )}
    </article>
  );
}
