const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld(
  '__CQG_DESKTOP__',
  Object.freeze({
    requestJson: (path, init = {}) => ipcRenderer.invoke('cqg-api-request', { path, init }),
  }),
);
