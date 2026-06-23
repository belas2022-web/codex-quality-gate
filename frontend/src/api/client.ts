const API_BASE = '/api';

export type DashboardSummary = {
  projects: number;
  runs: number;
  findings: number;
  critical_findings: number;
  updates: number;
  mode: string;
};

export type ProjectSummary = {
  name: string;
  runs: number;
  latest_run_id: number;
  last_scan: string;
};

export type Finding = {
  id: number;
  project: string;
  run_id: number;
  rule_id: string;
  path: string;
  severity: string;
  message: string;
};

export type ScanRun = {
  id: number;
  project: string;
  created_at: string;
};

export type UpdateHistory = {
  id: number;
  version: string;
  status: string;
};

export type UpdateStatus = {
  rules: string;
  signature: string;
  history: UpdateHistory[];
};

export type SourceStatus = {
  name: string;
  type: string;
  enabled: boolean;
  status: string;
  last_sync_at: string | null;
  last_error: string | null;
  secrets_exposed: boolean;
};

export type ChatConnector = {
  name: string;
  type: string;
  enabled: boolean;
  status: string;
  last_sync_at: string | null;
  last_error: string | null;
  allowed_read_count: number;
  allowed_write_count: number;
  secrets_exposed: boolean;
};

export type AuditEvent = {
  id: number;
  event_type: string;
  payload: Record<string, unknown>;
};

export async function fetchSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>('/summary');
}

export async function fetchProjects(): Promise<ProjectSummary[]> {
  return request<ProjectSummary[]>('/projects');
}

export async function fetchFindings(): Promise<Finding[]> {
  return request<Finding[]>('/findings');
}

export async function fetchRuns(): Promise<ScanRun[]> {
  return request<ScanRun[]>('/runs');
}

export async function fetchUpdates(): Promise<UpdateStatus> {
  return request<UpdateStatus>('/updates');
}

export async function fetchSources(): Promise<SourceStatus[]> {
  return request<SourceStatus[]>('/sources');
}

export async function fetchChats(): Promise<ChatConnector[]> {
  return request<ChatConnector[]>('/chats');
}

export async function fetchAuditEvents(): Promise<AuditEvent[]> {
  return request<AuditEvent[]>('/audit');
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`API ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}
