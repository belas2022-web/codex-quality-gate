import { fetchAuditEvents } from '../api/client';
import AuditTable from '../components/AuditTable';
import ResourcePage from './ResourcePage';

export default function AuditLog() {
  return (
    <ResourcePage
      title="Audit"
      load={fetchAuditEvents}
      render={(events) => <AuditTable events={events} />}
    />
  );
}
