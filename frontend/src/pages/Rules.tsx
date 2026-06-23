import { fetchSummary } from '../api/client';
import ResourcePage from './ResourcePage';

export default function Rules() {
  return (
    <ResourcePage
      title="Rules"
      load={fetchSummary}
      render={(summary) => (
        <article className="panel">
          <dl>
            <div>
              <dt>Findings</dt>
              <dd>{summary.findings}</dd>
            </div>
            <div>
              <dt>Critical</dt>
              <dd>{summary.critical_findings}</dd>
            </div>
            <div>
              <dt>Mode</dt>
              <dd>{summary.mode}</dd>
            </div>
          </dl>
        </article>
      )}
    />
  );
}
