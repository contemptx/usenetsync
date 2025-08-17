import { vi } from 'vitest';

// Mock invoke function that returns realistic data
export const invoke = vi.fn(async (command: string, args?: any) => {
  console.log(`Mock Tauri invoke: ${command}`, args);
  
  switch (command) {
    case 'activate_license':
      return { success: true, message: 'License activated successfully' };
    
    case 'check_license':
      return {
        activated: true,
        genuine: true,
        trial: false,
        hardwareId: 'MOCK-HARDWARE-ID',
        tier: 'pro',
        features: {
          maxFileSize: 10737418240,
          maxConnections: 50,
          maxShares: 500,
        }
      };
    
    case 'start_trial':
      return { success: true, trialDays: 30 };
    
    case 'deactivate_license':
      return { success: true };
    
    case 'select_files':
      return [
        {
          id: 'file-1',
          name: 'test-file.txt',
          type: 'file',
          size: 1024,
          path: '/mock/path/test-file.txt',
          modifiedAt: new Date(),
          selected: false,
        }
      ];
    
    case 'index_folder':
      return {
        id: 'folder-1',
        name: 'test-folder',
        type: 'folder',
        size: 0,
        path: '/mock/path/test-folder',
        modifiedAt: new Date(),
        selected: false,
        children: []
      };
    
    case 'create_share':
      return {
        shareId: 'MOCK-SHARE-ID',
        success: true,
        url: 'https://mock.share/MOCK-SHARE-ID'
      };
    
    case 'download_share':
      return { success: true, path: '/downloads/mock-file' };
    
    case 'get_share_details':
      return {
        id: args?.shareId || 'MOCK-SHARE-ID',
        name: 'Mock Share',
        size: 1048576,
        fileCount: 5,
        folderCount: 2,
        createdAt: new Date(),
        type: 'public'
      };
    
    case 'pause_transfer':
    case 'resume_transfer':
    case 'cancel_transfer':
      return { success: true };
    
    case 'test_server_connection':
      return { success: true, latency: 50 };
    
    case 'save_server_config':
      return { success: true };
    
    case 'get_system_stats':
      return {
        cpuUsage: 45.5,
        memoryUsage: 62.3,
        diskUsage: 78.9,
        networkSpeed: {
          upload: 1024000,
          download: 5120000
        },
        activeTransfers: 2,
        totalShares: 15
      };
    
    case 'open_folder':
      return { success: true };
    
    case 'get_logs':
      return [
        {
          id: 'log-1',
          timestamp: new Date(),
          level: 'info',
          category: 'system',
          message: 'Mock log entry',
          source: 'frontend'
        }
      ];
    
    case 'set_bandwidth_limit':
      return { success: true };
    
    case 'get_bandwidth_limit':
      return {
        uploadKbps: 1000,
        downloadKbps: 5000,
        enabled: true
      };
    
    case 'get_statistics':
      return {
        totalUploads: 100,
        totalDownloads: 250,
        totalShares: 50,
        totalBandwidth: 1073741824
      };
    
    case 'export_data':
      return 'MOCK_EXPORT_DATA_BASE64';
    
    case 'import_data':
      return true;
    
    case 'clear_cache':
      return { success: true };
    
    case 'get_system_info':
      return {
        os: 'Linux',
        version: '5.15.0',
        arch: 'x64',
        cpuCores: 8,
        totalMemory: 16777216,
        freeMemory: 8388608
      };
    
    case 'restart_services':
      return { success: true };
    
    default:
      console.warn(`Unhandled Tauri command: ${command}`);
      return null;
  }
});