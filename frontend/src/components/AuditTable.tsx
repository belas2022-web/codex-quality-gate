import type { AuditEvent } from '../api/client';

type Props = {
  events?: AuditEvent[] | null;
};

export default function AuditTable({ events }: Props) {
  const rows = events ?? [];
  const exportEvents = () => {
    const blob = new Blob([JSON.stringify(rows, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'codex-quality-gate-audit.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <article className="panel span-2">
      <div className="panel-head">
        <h2>Audit preview</h2>
        <button disabled={rows.length === 0} onClick={exportEvents} type="button">
          Export
        </button>
      </div>
      {rows.length === 0 ? (
        <p className="empty-state">No audit events recorded.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <tbody>
              {rows.slice(0, 6).map((event) => (
                <tr key={event.id}>
                  <td>{event.event_type}</td>
                  <td className="audit-payload">{JSON.stringify(event.payload)}</td>
                  <td>#{event.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}
