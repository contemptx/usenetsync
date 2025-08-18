// Wrapper for Tauri API to handle environments where it's not available

let invoke: any;
let listen: any;

if (typeof window !== 'undefined' && '__TAURI__' in window) {
  // In Tauri environment
  const { invoke: tauriInvoke } = require('@tauri-apps/api/tauri');
  const { listen: tauriListen } = require('@tauri-apps/api/event');
  invoke = tauriInvoke;
  listen = tauriListen;
} else {
  // Fallback for non-Tauri environments
  invoke = async (cmd: string, args?: any) => {
    console.warn(`Tauri not available, mocking command: ${cmd}`, args);
    return Promise.resolve({});
  };
  listen = async (event: string, callback: any) => {
    console.warn(`Tauri not available, mocking event listener: ${event}`);
    return () => {};
  };
}

export { invoke, listen };
