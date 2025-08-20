// Re-export API functions (excluding conflicting ones)
export { 
  uploadFile,
  downloadFile,
  createShare as createShareAPI,
  getShares,
  deleteShare,
  getShareDetails as getShareDetailsAPI,
  getSettings,
  updateSettings,
  getServerStatus,
  addServer,
  removeServer,
  testServerConnection,
  getSystemStats as getSystemStatsAPI,
  clearCache,
  exportData,
  importData,
  setBandwidthLimit,
  getBandwidthStats,
  getLogs,
  clearLogs,
  // Skip activateLicense, deactivateLicense, getLicenseStatus - use tauri.ts versions
  getFileVersions,
  restoreVersion,
  deleteVersion
} from './api';

// Re-export backend API functions
export * from './backend-api';

// Re-export Tauri functions (these take precedence for conflicts)
export * from './tauri';

// Export backend API as default
import backendAPI from './backend-api';
export { backendAPI };

// Handle specific conflicts by preferring certain versions
import { getSystemStats as getSystemStatsBackend } from './backend-api';
import { getShareDetails as getShareDetailsBackend } from './backend-api';

// Use backend versions as primary for these specific functions
export { getSystemStatsBackend as getSystemStats };
export { getShareDetailsBackend as getShareDetails };