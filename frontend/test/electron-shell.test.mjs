import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { test } from 'node:test';
import { URL } from 'node:url';

const packageJson = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const mainPath = new URL('../electron/main.cjs', import.meta.url);
const preloadPath = new URL('../electron/preload.cjs', import.meta.url);

test('frontend exposes Electron desktop entrypoints', () => {
  assert.equal(packageJson.main, 'electron/main.cjs');
  assert.equal(packageJson.scripts.desktop, 'electron electron/main.cjs');
  assert.equal(packageJson.scripts['desktop:package'], 'electron-builder --win portable');
  assert.equal(packageJson.scripts.dev, undefined);
  assert.equal(packageJson.scripts['desktop:dev'], undefined);
  assert.match(packageJson.devDependencies.electron, /^\^/);
  assert.match(packageJson.devDependencies['electron-builder'], /^\^/);
  assert.equal(packageJson.build.appId, 'io.codex-quality-gate.desktop');
  assert.equal(packageJson.build.productName, 'codex-quality-gate');
  assert.equal(existsSync(mainPath), true);
  assert.equal(existsSync(preloadPath), true);
});

test('Electron main process starts the local dashboard API without shell execution', () => {
  const mainSource = readFileSync(mainPath, 'utf8');

  assert.match(mainSource, /BrowserWindow/);
  assert.match(mainSource, /ipcMain/);
  assert.match(mainSource, /spawn\(/);
  assert.match(mainSource, /shell: false/);
  assert.match(mainSource, /windowsHide: true/);
  assert.doesNotMatch(mainSource, /exec\(/);
  assert.doesNotMatch(mainSource, /execFile\(/);
  assert.match(mainSource, /'-m',\s*'codex_quality_gate',\s*'dashboard-api'/);
  assert.match(mainSource, /process\.resourcesPath/);
  assert.match(mainSource, /cqg-dashboard-api\.exe/);
  assert.match(mainSource, /\/api\/health/);
  assert.match(mainSource, /CQG_DESKTOP_BACKEND_PORT/);
  assert.match(mainSource, /PYTHONUTF8: '1'/);
  assert.match(mainSource, /PYTHONIOENCODING: 'utf-8'/);
});

test('Electron renderer is isolated and receives only the dashboard API base URL', () => {
  const mainSource = readFileSync(mainPath, 'utf8');
  const preloadSource = readFileSync(preloadPath, 'utf8');

  assert.match(mainSource, /contextIsolation: true/);
  assert.match(mainSource, /sandbox: true/);
  assert.match(mainSource, /nodeIntegration: false/);
  assert.match(mainSource, /cqg-api-request/);
  assert.match(mainSource, /requestBackendJson/);
  assert.match(mainSource, /loadFile\(/);
  assert.doesNotMatch(mainSource, /loadURL\(/);
  assert.doesNotMatch(mainSource, /VITE_DEV_URL/);

  assert.match(preloadSource, /contextBridge\.exposeInMainWorld\(\s*'__CQG_DESKTOP__'/);
  assert.match(preloadSource, /requestJson/);
  assert.match(preloadSource, /ipcRenderer\.invoke\('cqg-api-request'/);
  assert.doesNotMatch(preloadSource, /apiBaseUrl/);
});
