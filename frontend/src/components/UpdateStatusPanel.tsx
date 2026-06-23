import type { UpdateStatus } from '../api/client';

type Props = {
  updates?: UpdateStatus | null;
};

export default function UpdateStatusPanel({ updates }: Props) {
  const safeUpdates = updates ?? { rules: 'unknown', signature: 'unknown', history: [] };
  const latest = safeUpdates.history[0];
  return (
    <article className="panel update-panel">
      <h2>Update verification</h2>
      <p className="signal">HTTPS + allowlist + SHA-256 + Ed25519</p>
      <dl>
        <div>
          <dt>Rules</dt>
          <dd>{safeUpdates.rules}</dd>
        </div>
        <div>
          <dt>Signature</dt>
          <dd>{safeUpdates.signature}</dd>
        </div>
        <div>
          <dt>Latest event</dt>
          <dd>{latest ? `${latest.version} ${latest.status}` : 'none recorded'}</dd>
        </div>
      </dl>
    </article>
  );
}
