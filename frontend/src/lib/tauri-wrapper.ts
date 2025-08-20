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

// Mock data generators
const generateMockFolder = (name: string = 'Mock Folder') => ({
  id: `folder-${Date.now()}`,
  name,
  type: 'folder',
  path: `/mock/path/${name}`,
  size: Math.floor(Math.random() * 1000000),
  children: [
    {
      id: `file-${Date.now()}-1`,
      name: 'document.pdf',
      type: 'file',
      path: `/mock/path/${name}/document.pdf`,
      size: 245678,
      modifiedAt: new Date()
    },
    {
      id: `file-${Date.now()}-2`,
      name: 'image.jpg',
      type: 'file',
      path: `/mock/path/${name}/image.jpg`,
      size: 1456789,
      modifiedAt: new Date()
    }
  ],
  modifiedAt: new Date()
});

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
      
      case 'select_files':
        return [
          {
            id: `file-${Date.now()}`,
            name: 'selected-file.txt',
            type: 'file',
            path: '/mock/selected-file.txt',
            size: 1024,
            modifiedAt: new Date()
          }
        ];
      
      case 'select_folder':
        return generateMockFolder('Selected Folder');
      
      case 'select_folder_dialog':
        return '/mock/path/to/folder';
      
      case 'get_folders':
        return {
          folders: [
            {
              folder_id: 'mock-1',
              name: 'Documents',
              path: '/home/user/Documents',
              state: 'indexed',
              total_files: 42,
              total_size: 10485760,
              total_segments: 15,
              uploaded_segments: 15,
              access_type: 'private',
              share_id: null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            },
            {
              folder_id: 'mock-2',
              name: 'Pictures',
              path: '/home/user/Pictures',
              state: 'segmented',
              total_files: 128,
              total_size: 524288000,
              total_segments: 200,
              uploaded_segments: 0,
              access_type: 'public',
              share_id: null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
          ]
        };
      
      case 'add_folder':
        return {
          folder_id: `folder-${Date.now()}`,
          name: args?.name || 'New Folder',
          path: args?.path || '/mock/new/folder',
          state: 'added'
        };
      
      case 'index_folder':
      case 'index_folder_full':
        return {
          success: true,
          folder_id: args?.folder_id,
          indexed_files: 10,
          total_size: 1048576
        };
      
      case 'segment_folder':
        return {
          success: true,
          folder_id: args?.folder_id,
          total_segments: 20
        };
      
      case 'upload_folder':
        return {
          success: true,
          folder_id: args?.folder_id,
          uploaded_segments: 20
        };
      
      case 'publish_folder':
        return {
          success: true,
          share_id: `share-${Date.now()}`,
          access_string: 'MOCK-ACCESS-STRING-123'
        };
      
      case 'create_share':
        return {
          id: `share-${Date.now()}`,
          shareId: `SHARE-${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
          type: args?.shareType || 'public',
          files: args?.files || [],
          createdAt: new Date(),
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
          downloadCount: 0,
          maxDownloads: 100
        };
      
      case 'check_database_status':
        return {
          connected: true,
          type: 'sqlite',
          tables: ['folders', 'files', 'segments', 'shares', 'users'],
          version: '1.0.0'
        };
      
      case 'get_authorized_users':
        return { users: [] };
      
      case 'set_folder_access':
        return { success: true };
      
      case 'get_folder_info':
        return {
          folder_id: args?.folder_id,
          name: 'Folder Info',
          path: '/mock/folder/path',
          total_files: 5,
          total_size: 2097152,
          state: 'indexed'
        };
      
      case 'resync_folder':
        return { success: true, changes_detected: 2 };
      
      case 'delete_folder':
        return { success: true };
      
      case 'start_trial':
        return { 
          success: true, 
          license: { 
            type: 'trial', 
            expires: Date.now() + 14 * 24 * 60 * 60 * 1000 
          } 
        };
      
      case 'activate_license':
        return { 
          success: true, 
          license: { 
            type: 'pro', 
            expires: Date.now() + 365 * 24 * 60 * 60 * 1000 
          } 
        };
      
      default:
        console.warn(`[Mock Tauri] Unhandled command: ${cmd}`);
        return null;
    }
  };
}

if (!tauriListen) {
  tauriListen = async (event: string, handler: any) => {
    console.log(`[Mock Tauri] listen('${event}')`);
    
    // Simulate some events for testing
    if (event === 'transfer-progress') {
      // Simulate progress updates
      setTimeout(() => {
        handler({
          payload: {
            id: 'mock-transfer',
            progress: 25,
            speed: 1048576,
            eta: 300
          }
        });
      }, 1000);
    }
    
    // Return a mock unsubscribe function
    return () => {};
  };
}

export const invoke = tauriInvoke;
export const listen = tauriListen;