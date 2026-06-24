const { contextBridge } = require('electron');

const API_ARG_PREFIX = '--cqg-api-base=';
const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8765/api';

function readApiBaseUrl() {
  const argument = process.argv.find((value) => value.startsWith(API_ARG_PREFIX));
  if (!argument) {
    return DEFAULT_API_BASE_URL;
  }
  return argument.slice(API_ARG_PREFIX.length).trim() || DEFAULT_API_BASE_URL;
}

contextBridge.exposeInMainWorld(
  '__CQG_DESKTOP__',
  Object.freeze({
    apiBaseUrl: readApiBaseUrl(),
  }),
);
