import { fetchUpdates } from '../api/client';
import UpdateStatusPanel from '../components/UpdateStatusPanel';
import ResourcePage from './ResourcePage';

export default function Updates() {
  return (
    <ResourcePage
      title="Updates"
      load={fetchUpdates}
      render={(updates) => <UpdateStatusPanel updates={updates} />}
    />
  );
}
