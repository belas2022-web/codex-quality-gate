import { fetchRuns } from '../api/client';
import RunTimeline from '../components/RunTimeline';
import ResourcePage from './ResourcePage';

export default function Runs() {
  return (
    <ResourcePage title="Runs" load={fetchRuns} render={(runs) => <RunTimeline runs={runs} />} />
  );
}
