const { spawn } = require('node:child_process');
const http = require('node:http');
const path = require('node:path');
const { app, BrowserWindow, ipcMain } = require('electron');

const BACKEND_HOST = '127.0.0.1';
const DEFAULT_BACKEND_PORT = 8765;
const HEALTH_PATH = '/api/health';
const BACKEND_READY_TIMEOUT_MS = 15_000;
const BACKEND_READY_INTERVAL_MS = 250;
const API_IPC_CHANNEL = 'cqg-api-request';
const API_PATH_PREFIX = '/api';

let backendProcess = null;
let mainWindow = null;
let apiBridgePort = null;

function backendPort() {
  const rawPort = process.env.CQG_DESKTOP_BACKEND_PORT;
  const port = rawPort ? Number.parseInt(rawPort, 10) : DEFAULT_BACKEND_PORT;
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    return DEFAULT_BACKEND_PORT;
  }
  return port;
}

function pythonCommand() {
  return process.env.CQG_DESKTOP_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
}

function packagedBackendPath() {
  if (!app.isPackaged) {
    return null;
  }
  const executableName = process.platform === 'win32' ? 'cqg-dashboard-api.exe' : 'cqg-dashboard-api';
  return path.join(process.resourcesPath, 'desktop-backend', executableName);
}

function backendCommand(port) {
  const packagedBackend = packagedBackendPath();
  if (packagedBackend) {
    return {
      command: packagedBackend,
      args: ['--host', BACKEND_HOST, '--port', String(port)],
      cwd: path.dirname(packagedBackend),
    };
  }
  return {
    command: pythonCommand(),
    args: ['-m', 'codex_quality_gate', 'dashboard-api', '--host', BACKEND_HOST, '--port', String(port)],
    cwd: path.resolve(__dirname, '..', '..'),
  };
}

function startBackend(port) {
  if (process.env.CQG_DESKTOP_SKIP_BACKEND === '1') {
    return null;
  }

  const backend = backendCommand(port);
  const child = spawn(backend.command, backend.args, {
    cwd: backend.cwd,
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

function safeRendererPath(value) {
  if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//')) {
    throw new Error('Invalid dashboard API path');
  }
  if (value.includes('\r') || value.includes('\n')) {
    throw new Error('Invalid dashboard API path');
  }
  return `${API_PATH_PREFIX}${value}`;
}

function safeRendererMethod(value) {
  const method = typeof value === 'string' && value ? value.toUpperCase() : 'GET';
  if (!['GET', 'POST'].includes(method)) {
    throw new Error('Unsupported dashboard API method');
  }
  return method;
}

function safeRendererHeaders(headers) {
  const safeHeaders = { Accept: 'application/json' };
  if (!headers || typeof headers !== 'object') {
    return safeHeaders;
  }
  for (const [key, value] of Object.entries(headers)) {
    if (typeof value !== 'string') {
      continue;
    }
    const normalized = key.toLowerCase();
    if (normalized === 'accept' || normalized === 'authorization' || normalized === 'content-type') {
      safeHeaders[key] = value;
    }
  }
  return safeHeaders;
}

function requestBackendJson(port, rendererPath, init = {}) {
  return new Promise((resolve, reject) => {
    const requestBody = typeof init.body === 'string' ? init.body : undefined;
    const request = http.request(
      {
        host: BACKEND_HOST,
        port,
        path: safeRendererPath(rendererPath),
        method: safeRendererMethod(init.method),
        headers: safeRendererHeaders(init.headers),
        timeout: 15_000,
      },
      (response) => {
        const chunks = [];
        response.on('data', (chunk) => {
          chunks.push(chunk);
        });
        response.on('end', () => {
          const text = Buffer.concat(chunks).toString('utf8');
          let payload;
          try {
            payload = text ? JSON.parse(text) : null;
          } catch (error) {
            reject(error);
            return;
          }
          resolve({
            ok: Boolean(response.statusCode && response.statusCode >= 200 && response.statusCode < 300),
            status: response.statusCode || 0,
            payload,
          });
        });
      },
    );

    request.on('timeout', () => {
      request.destroy(new Error('Dashboard API request timed out'));
    });
    request.on('error', reject);
    if (requestBody) {
      request.write(requestBody);
    }
    request.end();
  });
}

function registerApiBridge(port) {
  if (apiBridgePort !== null) {
    ipcMain.removeHandler(API_IPC_CHANNEL);
  }
  ipcMain.handle(API_IPC_CHANNEL, (_event, payload) => {
    return requestBackendJson(port, payload?.path, payload?.init || {});
  });
  apiBridgePort = port;
}

async function createWindow() {
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
    },
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  await mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
}

app
  .whenReady()
  .then(async () => {
    app.setName('codex-quality-gate');
    const port = backendPort();
    await ensureBackend(port);
    registerApiBridge(port);
    await createWindow();
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        void createWindow();
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
  backendCommand,
  backendPort,
  packagedBackendPath,
  requestBackendJson,
  startBackend,
  stopBackend,
};
