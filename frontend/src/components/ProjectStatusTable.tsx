import type { ProjectSummary } from '../api/client';

type Props = {
  projects?: ProjectSummary[] | null;
};

export default function ProjectStatusTable({ projects }: Props) {
  const rows = projects ?? [];
  return (
    <article className="panel table-panel span-2">
      <div className="panel-head">
        <h2>Project health</h2>
        <button>Open registry</button>
      </div>
      {rows.length === 0 ? (
        <p className="empty-state">No projects have been scanned yet.</p>
      ) : (
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
            {rows.map((project) => (
              <tr key={project.name}>
                <td>{project.name}</td>
                <td>{project.runs}</td>
                <td>
                  <span className="badge healthy">tracked</span>
                </td>
                <td>{project.last_scan}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </article>
  );
}
