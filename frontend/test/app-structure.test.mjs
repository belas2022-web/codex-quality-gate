import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { test } from 'node:test';
import { URL } from 'node:url';

const indexSource = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const appSource = readFileSync(new URL('../src/App.tsx', import.meta.url), 'utf8');
const clientSource = readFileSync(new URL('../src/api/client.ts', import.meta.url), 'utf8');
const dashboardSource = readFileSync(new URL('../src/pages/Dashboard.tsx', import.meta.url), 'utf8');
const projectStatusSource = readFileSync(
  new URL('../src/components/ProjectStatusTable.tsx', import.meta.url),
  'utf8',
);
const findingsTableSource = readFileSync(
  new URL('../src/components/FindingsTable.tsx', import.meta.url),
  'utf8',
);
const auditTableSource = readFileSync(new URL('../src/components/AuditTable.tsx', import.meta.url), 'utf8');
const cssSource = readFileSync(new URL('../src/styles/app.css', import.meta.url), 'utf8');

const expectedPages = [
  'dashboard',
  'projects',
  'project-details',
  'findings',
  'runs',
  'updates',
  'rules',
  'sources',
  'chat-bridge',
  'audit-log',
  'settings',
];

test('navigation entries have render coverage', () => {
  for (const page of expectedPages) {
    assert.match(appSource, new RegExp(`page: '${page}'`));
    if (page !== 'dashboard') {
      assert.match(appSource, new RegExp(`case '${page}'`));
    }
  }

  assert.match(appSource, /default:\s*\n\s*return <Dashboard onNavigate=\{setPage\} \/>;/);
});

test('api client supports the local api contract with dashboard auth', () => {
  assert.match(clientSource, /__CQG_DESKTOP__/);
  assert.match(clientSource, /requestJson/);
  assert.match(clientSource, /function desktopBridge/);
  assert.match(clientSource, /DASHBOARD_TOKEN_STORAGE_KEY/);
  assert.match(clientSource, /Authorization/);
  assert.match(clientSource, /Bearer \$\{token\}/);
  assert.match(clientSource, /export function setDashboardToken/);
  assert.match(clientSource, /export function clearDashboardToken/);
  assert.match(clientSource, /export async function scanProject/);
  assert.match(clientSource, /if \(!response\.ok\)/);
  assert.match(clientSource, /return response\.payload as T;/);
  assert.doesNotMatch(clientSource, /fetch\(/);
  assert.doesNotMatch(clientSource, /DEFAULT_API_BASE/);
});

test('dashboard wires visible actions to behavior instead of inert buttons', () => {
  assert.match(dashboardSource, /Promise\.allSettled/);
  assert.match(dashboardSource, /getDashboardToken/);
  assert.match(dashboardSource, /setDashboardToken/);
  assert.match(dashboardSource, /handleScanAll/);
  assert.match(dashboardSource, /scanProject\(project\.name\)/);
  assert.match(dashboardSource, /ProjectStatusTable[\s\S]*onOpenRegistry/);
});

test('dashboard components expose filters, export, health, and responsive table wrappers', () => {
  assert.match(projectStatusSource, /type HealthStatus/);
  assert.match(projectStatusSource, /getProjectHealth/);
  assert.match(projectStatusSource, /className=\{`badge \$\{health\.tone\}`\}/);
  assert.match(projectStatusSource, /className="table-scroll"/);
  assert.doesNotMatch(projectStatusSource, />tracked<\/span>/);

  assert.match(findingsTableSource, /<select/);
  assert.match(findingsTableSource, /setSeverity/);
  assert.doesNotMatch(findingsTableSource, />Filter<\/button>/);

  assert.match(auditTableSource, /new Blob/);
  assert.match(auditTableSource, /\.download =/);
  assert.match(auditTableSource, /className="table-scroll"/);

  assert.match(cssSource, /\.table-scroll/);
  assert.match(cssSource, /overflow-x: auto/);
  assert.match(cssSource, /overflow-wrap: anywhere/);
});

test('dashboard shell declares an icon asset to avoid browser favicon 404s', () => {
  assert.match(indexSource, /rel="icon"/);
  assert.match(indexSource, /href="\/favicon\.svg"/);
  assert.equal(existsSync(new URL('../public/favicon.svg', import.meta.url)), true);
});
