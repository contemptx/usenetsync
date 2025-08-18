// @ts-ignore
import { invoke } from './tauri-wrapper';
// @ts-ignore
import { listen } from './tauri-wrapper';
import { LicenseStatus, Share, Transfer, FileNode } from '../types';

// License Commands
export async function activateLicense(key: string): Promise<boolean> {
  return await invoke('activate_license', { key });
}

export async function checkLicense(): Promise<LicenseStatus> {
  return await invoke('check_license');
}

export async function startTrial(): Promise<number> {
  return await invoke('start_trial');
}

export async function deactivateLicense(): Promise<void> {
  return await invoke('deactivate_license');
}

// File Operations
export async function selectFiles(): Promise<FileNode[]> {
  return await invoke('select_files');
}

export async function selectFolder(): Promise<FileNode> {
  return await invoke('select_folder');
}

export async function indexFolder(path: string): Promise<FileNode> {
  return await invoke('index_folder', { path });
}

// Share Operations
export async function createShare(
  files: string[],
  shareType: 'public' | 'private' | 'protected',
  password?: string
): Promise<Share> {
  return await invoke('create_share', { files, shareType, password });
}

export async function downloadShare(
  shareId: string,
  destination: string,
  selectedFiles?: string[]
): Promise<void> {
  return await invoke('download_share', { shareId, destination, selectedFiles });
}

export async function getShareDetails(shareId: string): Promise<Share> {
  return await invoke('get_share_details', { shareId });
}

// Transfer Operations
export async function pauseTransfer(transferId: string): Promise<void> {
  return await invoke('pause_transfer', { transferId });
}

export async function resumeTransfer(transferId: string): Promise<void> {
  return await invoke('resume_transfer', { transferId });
}

export async function cancelTransfer(transferId: string): Promise<void> {
  return await invoke('cancel_transfer', { transferId });
}

// Server Configuration
export async function testServerConnection(config: any): Promise<boolean> {
  return await invoke('test_server_connection', { config });
}

export async function saveServerConfig(config: any): Promise<void> {
  return await invoke('save_server_config', { config });
}

// System Operations
export async function getSystemStats(): Promise<any> {
  return await invoke('get_system_stats');
}

export async function openFolder(path: string): Promise<void> {
  return await invoke('open_folder', { path });
}

// New System Commands
export async function getLogs(filter?: any): Promise<any[]> {
  return await invoke('get_logs', { filter });
}

export async function setBandwidthLimit(uploadKbps: number, downloadKbps: number, enabled: boolean): Promise<void> {
  return await invoke('set_bandwidth_limit', { uploadKbps, downloadKbps, enabled });
}

export async function getBandwidthLimit(): Promise<any> {
  return await invoke('get_bandwidth_limit');
}

export async function getStatistics(): Promise<any> {
  return await invoke('get_statistics');
}

export async function exportData(options: any): Promise<string> {
  return await invoke('export_data', { options });
}

export async function importData(data: string, options: any): Promise<boolean> {
  return await invoke('import_data', { data, options });
}

export async function clearCache(): Promise<void> {
  return await invoke('clear_cache');
}

export async function getSystemInfo(): Promise<any> {
  return await invoke('get_system_info');
}

export async function restartServices(): Promise<void> {
  return await invoke('restart_services');
}

// Event Listeners
export function onTransferProgress(callback: (progress: any) => void) {
  return listen('transfer-progress', (event) => {
    callback(event.payload);
  });
}

export function onTransferComplete(callback: (transfer: Transfer) => void) {
  return listen('transfer-complete', (event) => {
    callback(event.payload as Transfer);
  });
}

export function onTransferError(callback: (error: any) => void) {
  return listen('transfer-error', (event) => {
    callback(event.payload);
  });
}

export function onLicenseExpired(callback: () => void) {
  return listen('license-expired', () => {
    callback();
  });
}
// Additional API functions for full integration
export async function uploadFile(filePath: string, shareId: string, password?: string): Promise<boolean> {
  // @ts-ignore
  return await invoke('upload_file', { filePath, shareId, password });
}

export async function downloadFile(shareId: string, destination: string, password?: string): Promise<boolean> {
  // @ts-ignore
  return await invoke('download_file', { shareId, destination, password });
}

export async function getShares(): Promise<any[]> {
  // @ts-ignore
  return await invoke('get_shares');
}

export async function deleteShare(shareId: string): Promise<boolean> {
  // @ts-ignore
  return await invoke('delete_share', { shareId });
}

export async function getSettings(): Promise<any> {
  // @ts-ignore
  return await invoke('get_settings');
}

export async function updateSettings(settings: any): Promise<boolean> {
  // @ts-ignore
  return await invoke('update_settings', { settings });
}

export async function getServerStatus(): Promise<any> {
  // @ts-ignore
  return await invoke('get_server_status');
}
