// Re-export all mocks from specific modules
export * from './tauri';
export * from './event';

// Additional Tauri API mocks can be added here
export const app = {
  getVersion: () => Promise.resolve('1.0.0'),
  getName: () => Promise.resolve('UsenetSync'),
  getTauriVersion: () => Promise.resolve('2.0.0'),
};

export const window = {
  appWindow: {
    minimize: () => Promise.resolve(),
    maximize: () => Promise.resolve(),
    close: () => Promise.resolve(),
    setTitle: (title: string) => Promise.resolve(),
  }
};

export const dialog = {
  open: () => Promise.resolve('/mock/selected/path'),
  save: () => Promise.resolve('/mock/save/path'),
  message: (message: string) => Promise.resolve(),
  ask: (message: string) => Promise.resolve(true),
  confirm: (message: string) => Promise.resolve(true),
};

export const fs = {
  readTextFile: (path: string) => Promise.resolve('mock file content'),
  writeTextFile: (path: string, content: string) => Promise.resolve(),
  readBinaryFile: (path: string) => Promise.resolve(new Uint8Array([1, 2, 3])),
  writeBinaryFile: (path: string, content: Uint8Array) => Promise.resolve(),
  exists: (path: string) => Promise.resolve(true),
  createDir: (path: string) => Promise.resolve(),
  removeFile: (path: string) => Promise.resolve(),
  removeDir: (path: string) => Promise.resolve(),
};

export const path = {
  appDataDir: () => Promise.resolve('/mock/app/data'),
  appConfigDir: () => Promise.resolve('/mock/app/config'),
  appCacheDir: () => Promise.resolve('/mock/app/cache'),
  appLogDir: () => Promise.resolve('/mock/app/logs'),
  downloadDir: () => Promise.resolve('/mock/downloads'),
  documentDir: () => Promise.resolve('/mock/documents'),
  homeDir: () => Promise.resolve('/mock/home'),
};