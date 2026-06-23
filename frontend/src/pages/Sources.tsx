import { fetchSources } from '../api/client';
import ResourcePage from './ResourcePage';

export default function Sources() {
  return (
    <ResourcePage
      title="Sources"
      load={fetchSources}
      render={(sources) => (
        <article className="panel table-panel">
          {sources.length === 0 ? (
            <p className="empty-state">No update sources configured.</p>
          ) : (
            <table>
              <tbody>
                {sources.map((source) => (
                  <tr key={source.name}>
                    <td>{source.name}</td>
                    <td>{source.enabled ? 'enabled' : 'disabled'}</td>
                    <td>{source.secrets_exposed ? 'review' : 'redacted'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </article>
      )}
    />
  );
}
