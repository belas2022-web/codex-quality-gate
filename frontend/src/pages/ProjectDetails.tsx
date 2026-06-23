import { fetchProjects } from '../api/client';
import ProjectStatusTable from '../components/ProjectStatusTable';
import ResourcePage from './ResourcePage';

export default function ProjectDetails() {
  return (
    <ResourcePage
      title="Project Details"
      load={fetchProjects}
      render={(projects) => <ProjectStatusTable projects={projects.slice(0, 1)} />}
    />
  );
}
