import type { AuditEvent } from '../api/client';

type Props = {
  events?: AuditEvent[] | null;
};

export default function AuditTable({ events }: Props) {
  const rows = events ?? [];
  return (
    <article className="panel span-2">
      <div className="panel-head">
        <h2>Audit preview</h2>
        <button>Export</button>
      </div>
      {rows.length === 0 ? (
        <p className="empty-state">No audit events recorded.</p>
      ) : (
        <table>
          <tbody>
            {rows.slice(0, 6).map((event) => (
              <tr key={event.id}>
                <td>{event.event_type}</td>
                <td>{JSON.stringify(event.payload)}</td>
                <td>#{event.id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </article>
  );
}
