// Wrapper for Tauri API to handle environments where it's not available

let tauriInvoke: any;
let tauriListen: any;

// Check if we're in a Tauri environment
const isTauri = typeof window !== 'undefined' && (window as any).__TAURI__;

if (isTauri) {
  // We're in Tauri, use the real API
  try {
    const tauriCore = require('@tauri-apps/api/core');
    const tauriEvent = require('@tauri-apps/api/event');
    tauriInvoke = tauriCore.invoke;
    tauriListen = tauriEvent.listen;
  } catch (e) {
    console.warn('Failed to load Tauri API:', e);
  }
}

// Fallback for non-Tauri environments (browser dev mode)
if (!tauriInvoke) {
  tauriInvoke = async (cmd: string, args?: any) => {
    console.log(`[Mock Tauri] invoke('${cmd}', ${JSON.stringify(args)})`);
    
    // Return mock data for common commands
    switch (cmd) {
      case 'check_license':
        return { valid: true, type: 'trial', expires: Date.now() + 86400000 };
      case 'get_system_stats':
        return {
          totalFiles: 0,
          totalSize: 0,
          activeTransfers: 0,
          networkSpeed: { download: 0, upload: 0 },
          storageUsed: 0,
          storageTotal: 100,
          cpuUsage: 0,
          memoryUsage: 0,
          diskUsage: 0
        };
      case 'get_shares':
        return [];
      case 'get_transfers':
        return { uploads: [], downloads: [] };
      default:
        return null;
    }
  };
}

if (!tauriListen) {
  tauriListen = async (event: string, handler: any) => {
    console.log(`[Mock Tauri] listen('${event}')`);
    // Return a mock unsubscribe function
    return () => {};
  };
}

export const invoke = tauriInvoke;
export const listen = tauriListen;