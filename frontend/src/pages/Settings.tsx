import { fetchSummary } from '../api/client';
import ResourcePage from './ResourcePage';

export default function Settings() {
  return (
    <ResourcePage
      title="Settings"
      load={fetchSummary}
      render={(summary) => (
        <article className="panel">
          <dl>
            <div>
              <dt>Mode</dt>
              <dd>{summary.mode}</dd>
            </div>
            <div>
              <dt>Projects</dt>
              <dd>{summary.projects}</dd>
            </div>
            <div>
              <dt>Runs</dt>
              <dd>{summary.runs}</dd>
            </div>
          </dl>
        </article>
      )}
    />
  );
}
