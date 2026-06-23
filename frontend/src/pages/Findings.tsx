import { fetchFindings } from '../api/client';
import FindingsTable from '../components/FindingsTable';
import ResourcePage from './ResourcePage';

export default function Findings() {
  return (
    <ResourcePage
      title="Findings"
      load={fetchFindings}
      render={(findings) => <FindingsTable findings={findings} />}
    />
  );
}
