// Re-export all API functions
export * from './api';
export * from './backend-api';
export * from './tauri';

// Export backend API as default
import backendAPI from './backend-api';
export { backendAPI };

// Handle ambiguous imports by preferring backend-api versions
import { getSystemStats as getSystemStatsBackend } from './backend-api';
import { getShareDetails as getShareDetailsBackend } from './backend-api';

// Use backend versions as primary to avoid ambiguity
export { getSystemStatsBackend as getSystemStats };
export { getShareDetailsBackend as getShareDetails };