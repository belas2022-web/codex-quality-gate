import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { URL } from 'node:url';

const appSource = readFileSync(new URL('../src/App.tsx', import.meta.url), 'utf8');
const clientSource = readFileSync(new URL('../src/api/client.ts', import.meta.url), 'utf8');

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

  assert.match(appSource, /default:\s*\n\s*return <Dashboard \/>;/);
});

test('api client keeps the dashboard behind the local api contract', () => {
  assert.match(clientSource, /const API_BASE = '\/api';/);
  assert.match(clientSource, /headers: \{ Accept: 'application\/json' \}/);
  assert.match(clientSource, /if \(!response\.ok\)/);
  assert.match(clientSource, /return response\.json\(\) as Promise<T>;/);
});
