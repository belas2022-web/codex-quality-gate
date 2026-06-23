import { type FormEvent, useCallback, useEffect, useState } from 'react';

import {
  DashboardApiError,
  type AuditEvent,
  type ChatConnector,
  type DashboardSummary,
  type Finding,
  type ProjectSummary,
  type ScanRun,
  type UpdateStatus,
  clearDashboardToken,
  fetchAuditEvents,
  fetchChats,
  fetchFindings,
  fetchProjects,
  fetchRuns,
  fetchSummary,
  fetchUpdates,
  getDashboardToken,
  scanProject,
  setDashboardToken,
} from '../api/client';
import AuditTable from '../components/AuditTable';
import ChatActivityPanel from '../components/ChatActivityPanel';
import FindingsTable from '../components/FindingsTable';
import ProjectStatusTable from '../components/ProjectStatusTable';
import RunTimeline from '../components/RunTimeline';
import SummaryCards from '../components/SummaryCards';
import UpdateStatusPanel from '../components/UpdateStatusPanel';

type DashboardData = {
  summary: DashboardSummary;
  projects: ProjectSummary[];
  findings: Finding[];
  runs: ScanRun[];
  updates: UpdateStatus;
  chats: ChatConnector[];
  audit: AuditEvent[];
};

const DEFAULT_SUMMARY: DashboardSummary = {
  projects: 0,
  runs: 0,
  findings: 0,
  critical_findings: 0,
  updates: 0,
  mode: 'observe',
};

const DEFAULT_UPDATES: UpdateStatus = {
  rules: 'unknown',
  signature: 'unknown',
  history: [],
};

const loadLabels = ['summary', 'projects', 'findings', 'runs', 'updates', 'chats', 'audit'] as const;

type Props = {
  onNavigate: (page: 'projects') => void;
};

type LoadResult = {
  data: DashboardData;
  warnings: string[];
};

export default function Dashboard({ onNavigate }: Props) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string>('');
  const [warnings, setWarnings] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [authRequired, setAuthRequired] = useState<boolean>(false);
  const [tokenInput, setTokenInput] = useState<string>(getDashboardToken());
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanStatus, setScanStatus] = useState<string>('');

  const refreshDashboard = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const loaded = await loadDashboardData();
      setData(loaded.data);
      setWarnings(loaded.warnings);
      setAuthRequired(false);
    } catch (reason: unknown) {
      if (isUnauthorized(reason)) {
        setAuthRequired(true);
        setData(null);
        setWarnings([]);
        setError('Dashboard token is required or invalid.');
      } else {
        setError(reason instanceof Error ? reason.message : 'Dashboard API request failed');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshDashboard();
  }, [refreshDashboard]);

  const handleTokenSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setDashboardToken(tokenInput);
    void refreshDashboard();
  };

  const handleClearToken = () => {
    clearDashboardToken();
    setTokenInput('');
    void refreshDashboard();
  };

  const handleScanAll = async () => {
    if (!data || data.projects.length === 0) return;
    setIsScanning(true);
    setScanStatus('Queueing scans...');
    setError('');
    try {
      const results = await Promise.allSettled(
        data.projects.map((project) => scanProject(project.name)),
      );
      const failed = results.filter((result) => result.status === 'rejected').length;
      setScanStatus(
        failed === 0
          ? `${results.length} scan requests queued.`
          : `${failed} scan requests failed.`,
      );
      await refreshDashboard();
    } catch (reason: unknown) {
      if (isUnauthorized(reason)) {
        setAuthRequired(true);
        setError('Dashboard token is required or invalid.');
      } else {
        setError(reason instanceof Error ? reason.message : 'Scan request failed');
      }
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <section className="workspace">
      <header className="topbar">
        <div>
          <h1>Quality Command Center</h1>
          <p>Local multi-project guardrails for AI and Codex changes.</p>
        </div>
        <div className="topbar-actions">
          <span className="status-dot">127.0.0.1</span>
          <span className="mode-pill">{data?.summary.mode ?? 'observe'}</span>
          <button
            className="primary-button"
            disabled={!data?.projects.length || isScanning || loading}
            onClick={handleScanAll}
            type="button"
          >
            {isScanning ? 'Scanning...' : 'Scan all'}
          </button>
        </div>
      </header>
      {authRequired ? (
        <form className="auth-panel" onSubmit={handleTokenSubmit}>
          <label>
            Dashboard token
            <input
              autoComplete="off"
              onChange={(event) => setTokenInput(event.target.value)}
              type="password"
              value={tokenInput}
            />
          </label>
          <button className="primary-button" type="submit">
            Save token
          </button>
          <button onClick={handleClearToken} type="button">
            Clear
          </button>
        </form>
      ) : null}
      {error ? <section className="state-panel error-state">{error}</section> : null}
      {scanStatus ? <section className="state-panel">{scanStatus}</section> : null}
      {warnings.length > 0 ? (
        <section className="state-panel warning-state">Partial data: {warnings.join('; ')}</section>
      ) : null}
      {loading && !data && !error ? (
        <section className="state-panel">Loading dashboard data...</section>
      ) : null}
      {data ? (
        <>
          <SummaryCards summary={data.summary} />
          <section className="grid">
            <ProjectStatusTable
              findings={data.findings}
              onOpenRegistry={() => onNavigate('projects')}
              projects={data.projects}
            />
            <FindingsTable findings={data.findings} />
            <UpdateStatusPanel updates={data.updates} />
            <RunTimeline runs={data.runs} />
            <ChatActivityPanel chats={data.chats} />
            <AuditTable events={data.audit} />
          </section>
        </>
      ) : null}
    </section>
  );
}

async function loadDashboardData(): Promise<LoadResult> {
  const settled = await Promise.allSettled([
    fetchSummary(),
    fetchProjects(),
    fetchFindings(),
    fetchRuns(),
    fetchUpdates(),
    fetchChats(),
    fetchAuditEvents(),
  ] as const);

  const unauthorized = settled.find(
    (result) => result.status === 'rejected' && isUnauthorized(result.reason),
  );
  if (unauthorized?.status === 'rejected') {
    throw unauthorized.reason;
  }

  return {
    data: {
      summary: valueOrDefault(settled[0], DEFAULT_SUMMARY),
      projects: valueOrDefault<ProjectSummary[]>(settled[1], []),
      findings: valueOrDefault<Finding[]>(settled[2], []),
      runs: valueOrDefault<ScanRun[]>(settled[3], []),
      updates: valueOrDefault(settled[4], DEFAULT_UPDATES),
      chats: valueOrDefault<ChatConnector[]>(settled[5], []),
      audit: valueOrDefault<AuditEvent[]>(settled[6], []),
    },
    warnings: settled.flatMap((result, index) =>
      result.status === 'rejected' ? [`${loadLabels[index]}: ${formatReason(result.reason)}`] : [],
    ),
  };
}

function valueOrDefault<T>(result: PromiseSettledResult<T>, fallback: T): T {
  return result.status === 'fulfilled' ? result.value : fallback;
}

function isUnauthorized(reason: unknown): boolean {
  return reason instanceof DashboardApiError && reason.status === 401;
}

function formatReason(reason: unknown): string {
  return reason instanceof Error ? reason.message : 'request failed';
}
