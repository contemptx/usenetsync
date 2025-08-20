// Re-export all API functions
export * from './api';
export * from './backend-api';
export * from './tauri';

// Export backend API as default
import backendAPI from './backend-api';
export { backendAPI };

// Mock functions for missing exports (to be implemented)
export async function checkLicense() {
  // Check with backend or return mock for now
  return { valid: true, expires: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) };
}

export function onTransferProgress(callback: (progress: any) => void) {
  // Register progress callback
  console.log('Transfer progress listener registered');
}

export function onTransferComplete(callback: (result: any) => void) {
  // Register completion callback
  console.log('Transfer complete listener registered');
}

export function onTransferError(callback: (error: any) => void) {
  // Register error callback
  console.log('Transfer error listener registered');
}

export function onLicenseExpired(callback: () => void) {
  // Register license expiry callback
  console.log('License expiry listener registered');
}

export async function isUserInitialized(): Promise<boolean> {
  // Check if user is initialized
  try {
    const response = await fetch('http://localhost:8000/api/v1/user/status');
    return response.ok;
  } catch {
    return false;
  }
}

export async function initializeUser(username: string, email?: string) {
  // Initialize user
  const response = await fetch('http://localhost:8000/api/v1/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email })
  });
  return response.json();
}

export async function pauseTransfer(transferId: string) {
  console.log('Pausing transfer:', transferId);
  // TODO: Implement actual pause logic
  return { paused: true };
}

export async function resumeTransfer(transferId: string) {
  console.log('Resuming transfer:', transferId);
  // TODO: Implement actual resume logic
  return { resumed: true };
}

export async function cancelTransfer(transferId: string) {
  console.log('Cancelling transfer:', transferId);
  // TODO: Implement actual cancel logic
  return { cancelled: true };
}

export async function downloadShare(shareId: string, destination?: string) {
  console.log('Downloading share:', shareId);
  // TODO: Implement actual download
  return { downloading: true, shareId };
}

export async function saveServerConfig(config: any) {
  console.log('Saving server config:', config);
  // TODO: Implement actual save
  return { saved: true };
}

export async function selectFolder(): Promise<string | null> {
  // Use Tauri dialog to select folder
  try {
    const { open } = await import('@tauri-apps/api/dialog');
    const selected = await open({
      directory: true,
      multiple: false,
    });
    return selected as string | null;
  } catch (error) {
    console.error('Failed to select folder:', error);
    return null;
  }
}

export async function startTrial() {
  console.log('Starting trial');
  return { trial: true, expires: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) };
}

// Re-export specific functions that might have conflicts
// (prefer backend-api versions for actual functionality)
import { getSystemStats as getSystemStatsBackend } from './backend-api';
import { getShareDetails as getShareDetailsBackend } from './backend-api';

// Use backend versions as primary
export { getSystemStatsBackend as getSystemStats };
export { getShareDetailsBackend as getShareDetails };