import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { User, Share, Transfer, FileNode, LicenseStatus, ServerConfig } from '../types';

interface AppState {
  // User & License
  user: User | null;
  licenseStatus: LicenseStatus | null;
  
  // Shares
  shares: Share[];
  activeShare: Share | null;
  
  // Transfers
  uploads: Transfer[];
  downloads: Transfer[];
  
  // Files
  selectedFiles: FileNode[];
  currentPath: string;
  
  // Server Config
  serverConfig: ServerConfig | null;
  
  // UI State
  sidebarOpen: boolean;
  darkMode: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  setLicenseStatus: (status: LicenseStatus) => void;
  addShare: (share: Share) => void;
  removeShare: (id: string) => void;
  setActiveShare: (share: Share | null) => void;
  
  // Transfer Actions
  addUpload: (transfer: Transfer) => void;
  addDownload: (transfer: Transfer) => void;
  updateTransfer: (id: string, update: Partial<Transfer>) => void;
  removeTransfer: (id: string, type: 'upload' | 'download') => void;
  
  // File Actions
  setSelectedFiles: (files: FileNode[]) => void;
  toggleFileSelection: (file: FileNode) => void;
  clearSelection: () => void;
  
  // Settings
  setServerConfig: (config: ServerConfig) => void;
  toggleSidebar: () => void;
  toggleDarkMode: () => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        // Initial State
        user: null,
        licenseStatus: null,
        shares: [],
        activeShare: null,
        uploads: [],
        downloads: [],
        selectedFiles: [],
        currentPath: '/',
        serverConfig: null,
        sidebarOpen: true,
        darkMode: true,
        
        // User Actions
        setUser: (user) => set({ user }),
        setLicenseStatus: (licenseStatus) => set({ licenseStatus }),
        
        // Share Actions
        addShare: (share) => set((state) => ({ 
          shares: [...state.shares, share] 
        })),
        removeShare: (id) => set((state) => ({
          shares: state.shares.filter(s => s.id !== id)
        })),
        setActiveShare: (activeShare) => set({ activeShare }),
        
        // Transfer Actions
        addUpload: (transfer) => set((state) => ({
          uploads: [...state.uploads, transfer]
        })),
        addDownload: (transfer) => set((state) => ({
          downloads: [...state.downloads, transfer]
        })),
        updateTransfer: (id, update) => set((state) => ({
          uploads: state.uploads.map(u => 
            u.id === id ? { ...u, ...update } : u
          ),
          downloads: state.downloads.map(d => 
            d.id === id ? { ...d, ...update } : d
          ),
        })),
        removeTransfer: (id, type) => set((state) => ({
          ...(type === 'upload' 
            ? { uploads: state.uploads.filter(u => u.id !== id) }
            : { downloads: state.downloads.filter(d => d.id !== id) }
          )
        })),
        
        // File Actions
        setSelectedFiles: (selectedFiles) => set({ selectedFiles }),
        toggleFileSelection: (file) => set((state) => {
          const exists = state.selectedFiles.find(f => f.id === file.id);
          return {
            selectedFiles: exists
              ? state.selectedFiles.filter(f => f.id !== file.id)
              : [...state.selectedFiles, file]
          };
        }),
        clearSelection: () => set({ selectedFiles: [] }),
        
        // Settings
        setServerConfig: (serverConfig) => set({ serverConfig }),
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
      }),
      {
        name: 'usenet-sync-storage',
        partialize: (state) => ({
          user: state.user,
          serverConfig: state.serverConfig,
          darkMode: state.darkMode,
        }),
      }
    )
  )
);