import { useEffect, useState } from 'react';

import {
  type AuditEvent,
  type ChatConnector,
  type DashboardSummary,
  type Finding,
  type ProjectSummary,
  type ScanRun,
  type UpdateStatus,
  fetchAuditEvents,
  fetchChats,
  fetchFindings,
  fetchProjects,
  fetchRuns,
  fetchSummary,
  fetchUpdates,
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

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    let active = true;
    Promise.all([
      fetchSummary(),
      fetchProjects(),
      fetchFindings(),
      fetchRuns(),
      fetchUpdates(),
      fetchChats(),
      fetchAuditEvents(),
    ])
      .then(([summary, projects, findings, runs, updates, chats, audit]) => {
        if (active) {
          setData({ summary, projects, findings, runs, updates, chats, audit });
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : 'Dashboard API request failed');
        }
      });
    return () => {
      active = false;
    };
  }, []);

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
          <button className="primary-button" type="button">
            Scan all
          </button>
        </div>
      </header>
      {error ? <section className="state-panel error-state">{error}</section> : null}
      {!data && !error ? <section className="state-panel">Loading dashboard data...</section> : null}
      {data ? (
        <>
          <SummaryCards summary={data.summary} />
          <section className="grid">
            <ProjectStatusTable projects={data.projects} />
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
