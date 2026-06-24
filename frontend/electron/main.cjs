const { spawn } = require('node:child_process');
const http = require('node:http');
const path = require('node:path');
const { app, BrowserWindow } = require('electron');

const BACKEND_HOST = '127.0.0.1';
const DEFAULT_BACKEND_PORT = 8765;
const HEALTH_PATH = '/api/health';
const VITE_DEV_URL = 'http://127.0.0.1:5173';
const BACKEND_READY_TIMEOUT_MS = 15_000;
const BACKEND_READY_INTERVAL_MS = 250;

let backendProcess = null;
let mainWindow = null;

function isDevMode() {
  return process.argv.includes('--dev') || process.env.CQG_DESKTOP_DEV === '1';
}

function backendPort() {
  const rawPort = process.env.CQG_DESKTOP_BACKEND_PORT;
  const port = rawPort ? Number.parseInt(rawPort, 10) : DEFAULT_BACKEND_PORT;
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    return DEFAULT_BACKEND_PORT;
  }
  return port;
}

function desktopApiBaseUrl(port) {
  return `http://${BACKEND_HOST}:${port}/api`;
}

function pythonCommand() {
  return process.env.CQG_DESKTOP_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
}

function backendArgs(port) {
  return ['-m', 'codex_quality_gate', 'dashboard', '--host', BACKEND_HOST, '--port', String(port)];
}

function startBackend(port) {
  if (process.env.CQG_DESKTOP_SKIP_BACKEND === '1') {
    return null;
  }

  const child = spawn(pythonCommand(), backendArgs(port), {
    cwd: path.resolve(__dirname, '..', '..'),
    env: {
      ...process.env,
      PYTHONUTF8: '1',
      PYTHONIOENCODING: 'utf-8',
    },
    stdio: 'ignore',
    windowsHide: true,
    shell: false,
  });

  backendProcess = child;
  child.on('exit', () => {
    if (backendProcess === child) {
      backendProcess = null;
    }
  });
  return child;
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
  backendProcess = null;
}

function checkBackend(port, timeoutMs = 1_000) {
  return new Promise((resolve) => {
    const request = http.get(
      {
        host: BACKEND_HOST,
        port,
        path: HEALTH_PATH,
        timeout: timeoutMs,
      },
      (response) => {
        response.resume();
        resolve(Boolean(response.statusCode && response.statusCode >= 200 && response.statusCode < 500));
      },
    );

    request.on('timeout', () => {
      request.destroy();
      resolve(false);
    });
    request.on('error', () => resolve(false));
  });
}

async function waitForBackend(port, timeoutMs = BACKEND_READY_TIMEOUT_MS) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await checkBackend(port)) {
      return;
    }
    await new Promise((resolve) => {
      setTimeout(resolve, BACKEND_READY_INTERVAL_MS);
    });
  }
  throw new Error(`Dashboard API did not become ready on ${BACKEND_HOST}:${port}`);
}

async function ensureBackend(port) {
  if (await checkBackend(port, 500)) {
    return;
  }
  startBackend(port);
  await waitForBackend(port);
}

async function createWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 720,
    title: 'codex-quality-gate',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      additionalArguments: [`--cqg-api-base=${desktopApiBaseUrl(port)}`],
    },
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  if (isDevMode()) {
    await mainWindow.loadURL(VITE_DEV_URL);
    return;
  }
  await mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
}

app
  .whenReady()
  .then(async () => {
    app.setName('codex-quality-gate');
    const port = backendPort();
    await ensureBackend(port);
    await createWindow(port);
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        void createWindow(port);
      }
    });
  })
  .catch((error) => {
    console.error(error);
    app.quit();
  });

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', stopBackend);

module.exports = {
  backendArgs,
  backendPort,
  desktopApiBaseUrl,
  isDevMode,
  startBackend,
  stopBackend,
};
