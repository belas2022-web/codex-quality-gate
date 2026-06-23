import type { Finding, ProjectSummary } from '../api/client';

type HealthStatus = {
  label: 'blocked' | 'risk' | 'watching' | 'healthy';
  tone: 'blocked' | 'risk' | 'watching' | 'healthy';
};

type Props = {
  findings?: Finding[] | null;
  onOpenRegistry?: () => void;
  projects?: ProjectSummary[] | null;
};

export default function ProjectStatusTable({ findings, onOpenRegistry, projects }: Props) {
  const rows = projects ?? [];
  const projectFindings = findings ?? [];
  return (
    <article className="panel table-panel span-2">
      <div className="panel-head">
        <h2>Project health</h2>
        <button disabled={!onOpenRegistry} onClick={onOpenRegistry} type="button">
          Open registry
        </button>
      </div>
      {rows.length === 0 ? (
        <p className="empty-state">No projects have been scanned yet.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Runs</th>
                <th>Status</th>
                <th>Last scan</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((project) => {
                const health = getProjectHealth(project, projectFindings);
                return (
                  <tr key={project.name}>
                    <td>{project.name}</td>
                    <td>{project.runs}</td>
                    <td>
                      <span className={`badge ${health.tone}`}>{health.label}</span>
                    </td>
                    <td>{project.last_scan}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}

function getProjectHealth(project: ProjectSummary, findings: Finding[]): HealthStatus {
  const severities = findings
    .filter((finding) => finding.project === project.name)
    .map((finding) => finding.severity.toLowerCase());
  if (severities.some((severity) => severity === 'critical' || severity === 'error')) {
    return { label: 'blocked', tone: 'blocked' };
  }
  if (severities.includes('warning')) {
    return { label: 'risk', tone: 'risk' };
  }
  if (project.runs === 0) {
    return { label: 'watching', tone: 'watching' };
  }
  return { label: 'healthy', tone: 'healthy' };
}
