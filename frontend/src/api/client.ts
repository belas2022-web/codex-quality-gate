const DASHBOARD_TOKEN_STORAGE_KEY = 'codex_quality_gate.dashboard_token';

type DesktopRequestInit = {
  method?: string;
  headers?: Record<string, string>;
  body?: string;
};

type DesktopApiResponse<T> = {
  ok: boolean;
  status: number;
  payload: T;
};

declare global {
  interface Window {
    __CQG_DESKTOP__?: {
      requestJson?: <T>(path: string, init?: DesktopRequestInit) => Promise<DesktopApiResponse<T>>;
    };
  }
}

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

export class DashboardApiError extends Error {
  constructor(
    public readonly path: string,
    public readonly status: number,
  ) {
    super(`API ${path} failed with ${status}`);
  }
}

let dashboardToken = readStoredDashboardToken();

export function getDashboardToken(): string {
  return dashboardToken;
}

export function setDashboardToken(token: string): void {
  dashboardToken = token.trim();
  const storage = browserSessionStorage();
  if (!storage) return;
  if (dashboardToken) {
    storage.setItem(DASHBOARD_TOKEN_STORAGE_KEY, dashboardToken);
  } else {
    storage.removeItem(DASHBOARD_TOKEN_STORAGE_KEY);
  }
}

export function clearDashboardToken(): void {
  setDashboardToken('');
}

export async function fetchSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>('/summary');
}

export async function fetchProjects(): Promise<ProjectSummary[]> {
  return request<ProjectSummary[]>('/projects');
}

export async function fetchFindings(severity = ''): Promise<Finding[]> {
  const query = severity ? `?severity=${encodeURIComponent(severity)}` : '';
  return request<Finding[]>(`/findings${query}`);
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

export async function scanProject(projectName: string): Promise<{ project: string; status: string }> {
  return request<{ project: string; status: string }>(
    `/projects/${encodeURIComponent(projectName)}/scan`,
    { method: 'POST' },
  );
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const bridge = desktopBridge();
  if (!bridge?.requestJson) {
    throw new DashboardApiError(path, 0);
  }
  const token = getDashboardToken();
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await bridge.requestJson<T>(path, {
    method: init.method,
    headers,
    body: typeof init.body === 'string' ? init.body : undefined,
  });
  if (!response.ok) {
    throw new DashboardApiError(path, response.status);
  }
  return response.payload as T;
}

function readStoredDashboardToken(): string {
  return browserSessionStorage()?.getItem(DASHBOARD_TOKEN_STORAGE_KEY) ?? '';
}

function desktopBridge(): Window['__CQG_DESKTOP__'] | null {
  if (typeof window === 'undefined') return null;
  return window.__CQG_DESKTOP__ ?? null;
}

function browserSessionStorage(): Storage | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}
