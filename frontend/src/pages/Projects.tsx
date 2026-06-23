import { fetchProjects } from '../api/client';
import ProjectStatusTable from '../components/ProjectStatusTable';
import ResourcePage from './ResourcePage';

export default function Projects() {
  return (
    <ResourcePage title="Projects" load={fetchProjects} render={(projects) => <ProjectStatusTable projects={projects} />} />
  );
}
