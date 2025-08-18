/**
 * API integration for backend communication
 * Provides functions for all backend operations
 */

import { invoke } from '@tauri-apps/api/tauri';

// File operations
export async function uploadFile(filePath: string, shareId: string, password?: string) {
  return invoke('upload_file', { 
    filePath, 
    shareId, 
    password 
  });
}

export async function downloadFile(shareId: string, destination: string, password?: string) {
  return invoke('download_file', { 
    shareId, 
    destination, 
    password 
  });
}

// Share management
export async function createShare(files: string[], type: 'public' | 'private' | 'protected', password?: string) {
  return invoke('create_share', { 
    files, 
    shareType: type, 
    password 
  });
}

export async function getShares() {
  return invoke('get_shares');
}

export async function deleteShare(shareId: string) {
  return invoke('delete_share', { shareId });
}

export async function getShareDetails(shareId: string) {
  return invoke('get_share_details', { shareId });
}

// Settings management
export async function getSettings() {
  return invoke('get_settings');
}

export async function updateSettings(settings: Record<string, any>) {
  return invoke('update_settings', { settings });
}

// Server management
export async function getServerStatus() {
  return invoke('get_server_status');
}

export async function addServer(server: {
  host: string;
  port: number;
  username: string;
  password: string;
  ssl: boolean;
}) {
  return invoke('add_server', { server });
}

export async function removeServer(serverId: string) {
  return invoke('remove_server', { serverId });
}

export async function testServerConnection(serverId: string) {
  return invoke('test_server_connection', { serverId });
}

// System operations
export async function getSystemStats() {
  return invoke('get_system_stats');
}

export async function clearCache() {
  return invoke('clear_cache');
}

export async function exportData(options: { format: string; includeSettings: boolean }) {
  return invoke('export_data', { options });
}

export async function importData(data: string) {
  return invoke('import_data', { data });
}

// Bandwidth control
export async function setBandwidthLimit(uploadMbps: number, downloadMbps: number) {
  return invoke('set_bandwidth_limit', { 
    uploadMbps, 
    downloadMbps 
  });
}

export async function getBandwidthStats() {
  return invoke('get_bandwidth_stats');
}

// Logging
export async function getLogs(level?: string, limit?: number) {
  return invoke('get_logs', { level, limit });
}

export async function clearLogs() {
  return invoke('clear_logs');
}

// License management
export async function activateLicense(key: string) {
  return invoke('activate_license', { key });
}

export async function deactivateLicense() {
  return invoke('deactivate_license');
}

export async function getLicenseStatus() {
  return invoke('get_license_status');
}

// Version control
export async function getFileVersions(filePath: string) {
  return invoke('get_file_versions', { filePath });
}

export async function restoreVersion(filePath: string, versionId: string) {
  return invoke('restore_version', { filePath, versionId });
}

export async function deleteVersion(filePath: string, versionId: string) {
  return invoke('delete_version', { filePath, versionId });
}

// Export all functions as default
export default {
  // File operations
  uploadFile,
  downloadFile,
  
  // Share management
  createShare,
  getShares,
  deleteShare,
  getShareDetails,
  
  // Settings
  getSettings,
  updateSettings,
  
  // Server management
  getServerStatus,
  addServer,
  removeServer,
  testServerConnection,
  
  // System
  getSystemStats,
  clearCache,
  exportData,
  importData,
  
  // Bandwidth
  setBandwidthLimit,
  getBandwidthStats,
  
  // Logging
  getLogs,
  clearLogs,
  
  // License
  activateLicense,
  deactivateLicense,
  getLicenseStatus,
  
  // Version control
  getFileVersions,
  restoreVersion,
  deleteVersion
};