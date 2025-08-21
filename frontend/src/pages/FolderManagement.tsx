import React, { useState, useEffect } from 'react';
// @ts-ignore
import { invoke } from '../lib/tauri-wrapper';
import { PrivateShareManager } from '../components/PrivateShareManager';
import { 
  getFolders, 
  addFolder, 
  indexFolderFull, 
  segmentFolder, 
  uploadFolder, 
  publishFolder as publishFolderApi,
  getAuthorizedUsers,
  checkDatabaseStatus,
  setFolderAccess,
  getFolderInfo,
  resyncFolder,
  deleteFolder
} from '../lib/tauri';
import { 
  Folder, 
  FolderOpen, 
  FileText, 
  Package, 
  Upload, 
  Share2, 
  RefreshCw,
  Play,
  Pause,
  CheckCircle,
  AlertCircle,
  Clock,
  HardDrive,
  Files,
  Layers,
  Lock,
  Unlock,
  Users,
  Settings,
  ChevronRight,
  ChevronDown,
  File,
  Database,
  Activity,
  Download,
  Trash2,
  Eye,
  Copy,
  Shield,
  Globe,
  Key,
  Hash,
  Server
} from 'lucide-react';
import toast from 'react-hot-toast';

interface ManagedFolder {
  folder_id: string;
  name: string;
  path: string;
  state: 'added' | 'indexing' | 'indexed' | 'segmenting' | 'segmented' | 'uploading' | 'uploaded' | 'publishing' | 'published' | 'error';
  total_files: number;
  total_size: number;
  total_segments: number;
  share_id?: string;
  published: boolean;
  created_at: string;
  access_type?: 'public' | 'private' | 'protected';
  file_count?: number;
}

interface FileInfo {
  file_id: string;
  name: string;
  path: string;
  size: number;
  hash?: string;
  segments?: SegmentInfo[];
  indexed_at?: string;
}

interface SegmentInfo {
  segment_id: string;
  sequence: number;
  size: number;
  hash: string;
  uploaded: boolean;
  message_ids?: string[];
}

interface FolderOperation {
  operation: 'indexing' | 'segmenting' | 'uploading' | 'publishing';
  progress: number;
  current_item?: string;
  speed_mbps?: number;
  eta_seconds?: number;
}

interface ShareInfo {
  share_id: string;
  share_type: 'public' | 'private' | 'protected';
  access_string?: string;
  created_at: string;
  expires_at?: string;
  download_count?: number;
}

export const FolderManagement: React.FC = () => {
  const [folders, setFolders] = useState<ManagedFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<ManagedFolder | null>(null);
  const [activeOperations, setActiveOperations] = useState<Record<string, FolderOperation>>({});
  const [activeTab, setActiveTab] = useState<'overview' | 'files' | 'segments' | 'shares' | 'actions'>('overview');
  const [loading, setLoading] = useState(false);
  const [dbError, setDbError] = useState<string | null>(null);
  const [databaseType, setDatabaseType] = useState<'sqlite' | 'postgresql' | null>(null);
  
  // File tree state
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  
  // Share management state
  const [shares, setShares] = useState<ShareInfo[]>([]);
  const [shareType, setShareType] = useState<'public' | 'private' | 'protected'>('public');
  const [authorizedUsers, setAuthorizedUsers] = useState<string[]>([]);
  const [sharePassword, setSharePassword] = useState('');
  const [showShareDialog, setShowShareDialog] = useState(false);
  
  // Load folders on mount
  useEffect(() => {
    loadFolders();
    checkDatabase();
    const interval = setInterval(() => {
      if (!dbError && !loading) {
        loadFolders();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load folder details when selected
  useEffect(() => {
    if (selectedFolder) {
      loadFolderDetails(selectedFolder.folder_id);
    }
  }, [selectedFolder]);

  const checkDatabase = async () => {
    try {
      const status = await checkDatabaseStatus();
      setDatabaseType(status.type || 'sqlite');
    } catch (error) {
      console.error('Failed to check database:', error);
    }
  };

  const loadFolders = async () => {
    if (loading) return;
    
    try {
      setLoading(true);
      const result = await getFolders();
      
      if (Array.isArray(result)) {
        setFolders(result as ManagedFolder[]);
      } else {
        console.warn('getFolders returned non-array:', result);
        setFolders([]);
      }
      setDbError(null);
    } catch (error: any) {
      console.error('Failed to load folders:', error);
      if (error?.message?.includes('database') || error?.message?.includes('table')) {
        setDbError(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadFolderDetails = async (folderId: string) => {
    try {
      // Load files for this folder
      const folderInfo = await getFolderInfo(folderId);
      if (folderInfo?.files) {
        setFiles(folderInfo.files);
      }
      
      // Load shares for this folder
      // TODO: Implement getShares API call
      // const folderShares = await getShares(folderId);
      // setShares(folderShares);
    } catch (error) {
      console.error('Failed to load folder details:', error);
    }
  };

  const handleAddFolder = async () => {
    try {
      const folderPath = await invoke('select_folder_dialog', { title: 'Select Folder to Manage' });
      
      if (folderPath) {
        const result = await addFolder(folderPath);
        toast.success(`Folder added: ${folderPath}`);
        await loadFolders();
      }
    } catch (error: any) {
      toast.error(`Failed to add folder: ${error.message || error}`);
    }
  };

  const handleIndexFolder = async (folderId: string) => {
    try {
      setActiveOperations(prev => ({
        ...prev,
        [folderId]: { operation: 'indexing', progress: 0 }
      }));

      const result = await indexFolderFull(folderId);
      
      toast.success(`Indexed ${result.files_indexed || 0} files`);
      await loadFolders();
      await loadFolderDetails(folderId);
    } catch (error: any) {
      toast.error(`Indexing failed: ${error.message || error}`);
    } finally {
      setActiveOperations(prev => {
        const newOps = { ...prev };
        delete newOps[folderId];
        return newOps;
      });
    }
  };

  const handleSegmentFolder = async (folderId: string) => {
    try {
      setActiveOperations(prev => ({
        ...prev,
        [folderId]: { operation: 'segmenting', progress: 0 }
      }));

      const result = await segmentFolder(folderId);
      
      toast.success(`Created ${result.segments_created || 0} segments`);
      await loadFolders();
      await loadFolderDetails(folderId);
    } catch (error: any) {
      toast.error(`Segmentation failed: ${error.message || error}`);
    } finally {
      setActiveOperations(prev => {
        const newOps = { ...prev };
        delete newOps[folderId];
        return newOps;
      });
    }
  };

  const handleUploadFolder = async (folderId: string) => {
    try {
      setActiveOperations(prev => ({
        ...prev,
        [folderId]: { operation: 'uploading', progress: 0 }
      }));

      const result = await uploadFolder(folderId);
      
      toast.success('Upload started');
      await loadFolders();
    } catch (error: any) {
      toast.error(`Upload failed: ${error.message || error}`);
    } finally {
      setActiveOperations(prev => {
        const newOps = { ...prev };
        delete newOps[folderId];
        return newOps;
      });
    }
  };

  const handleCreateShare = async () => {
    if (!selectedFolder) return;

    try {
      const shareData = {
        folderId: selectedFolder.folder_id,
        shareType: shareType,
        password: shareType === 'protected' ? sharePassword : undefined,
        allowedUsers: shareType === 'private' ? authorizedUsers : undefined
      };

      const result = await publishFolderApi(
        selectedFolder.folder_id,
        shareType,
        shareType === 'private' ? authorizedUsers : undefined,
        shareType === 'protected' ? sharePassword : undefined
      );

      toast.success(`Share created: ${result.share_id}`);
      setShowShareDialog(false);
      await loadFolders();
      // TODO: Reload shares
    } catch (error: any) {
      toast.error(`Failed to create share: ${error.message || error}`);
    }
  };

  const handleDeleteFolder = async (folderId: string) => {
    if (!confirm('Are you sure you want to delete this folder? This will remove all indexed data.')) {
      return;
    }

    try {
      await deleteFolder(folderId);
      toast.success('Folder deleted');
      setSelectedFolder(null);
      await loadFolders();
    } catch (error: any) {
      toast.error(`Failed to delete folder: ${error.message || error}`);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'added': return <Folder className="w-4 h-4 text-gray-500" />;
      case 'indexing': return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'indexed': return <FileText className="w-4 h-4 text-green-500" />;
      case 'segmenting': return <Package className="w-4 h-4 text-yellow-500 animate-pulse" />;
      case 'segmented': return <Layers className="w-4 h-4 text-purple-500" />;
      case 'uploading': return <Upload className="w-4 h-4 text-cyan-500 animate-pulse" />;
      case 'uploaded': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'publishing': return <Share2 className="w-4 h-4 text-indigo-500 animate-pulse" />;
      case 'published': return <Globe className="w-4 h-4 text-green-700" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const toggleFileExpanded = (fileId: string) => {
    setExpandedFiles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(fileId)) {
        newSet.delete(fileId);
      } else {
        newSet.add(fileId);
      }
      return newSet;
    });
  };

  return (
    <div className="h-full flex">
      {/* Database Error Alert */}
      {dbError && (
        <div className="absolute top-4 right-4 max-w-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3 z-50">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-medium text-red-800 dark:text-red-200">Database Error</h4>
            <p className="text-sm text-red-600 dark:text-red-400 mt-1">{dbError}</p>
          </div>
          <button
            onClick={() => setDbError(null)}
            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
          >
            ✕
          </button>
        </div>
      )}

      {/* Left Sidebar - Folder List */}
      <div className="w-80 border-r border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Folders</h2>
              {databaseType && (
                <span className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                  {databaseType === 'postgresql' ? <><Database className="w-3 h-3 inline mr-1" />PostgreSQL</> : 'SQLite'}
                </span>
              )}
            </div>
            <button
              onClick={handleAddFolder}
              disabled={loading}
              className="p-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50"
              title="Add Folder"
            >
              <FolderOpen className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {folders.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Folder className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No folders added yet</p>
              <p className="text-sm mt-2">Click the + button to add a folder</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-dark-border">
              {folders.map(folder => {
                const operation = activeOperations[folder.folder_id];
                
                return (
                  <div
                    key={folder.folder_id}
                    onClick={() => setSelectedFolder(folder)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                      selectedFolder?.folder_id === folder.folder_id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-1">{getStateIcon(folder.state)}</div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-gray-900 dark:text-white truncate">
                          {folder.name}
                        </h3>
                        <p className="text-xs text-gray-500 truncate mt-1">{folder.path}</p>
                        
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-600 dark:text-gray-400">
                          <span className="flex items-center gap-1">
                            <Files className="w-3 h-3" />
                            {folder.file_count || folder.total_files || 0}
                          </span>
                          <span className="flex items-center gap-1">
                            <HardDrive className="w-3 h-3" />
                            {formatBytes(folder.total_size || 0)}
                          </span>
                          {folder.total_segments > 0 && (
                            <span className="flex items-center gap-1">
                              <Layers className="w-3 h-3" />
                              {folder.total_segments}
                            </span>
                          )}
                        </div>

                        {operation && (
                          <div className="mt-2">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-blue-600 capitalize">{operation.operation}...</span>
                              <span>{operation.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-1">
                              <div 
                                className="bg-blue-600 h-1 rounded-full transition-all"
                                style={{ width: `${operation.progress}%` }}
                              />
                            </div>
                          </div>
                        )}

                        {folder.published && (
                          <div className="mt-2 flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                            <Share2 className="w-3 h-3" />
                            Published
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 bg-gray-50 dark:bg-dark-bg flex flex-col">
        {selectedFolder ? (
          <>
            {/* Header */}
            <div className="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border">
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStateIcon(selectedFolder.state)}
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                        {selectedFolder.name}
                      </h2>
                      <p className="text-sm text-gray-500">{selectedFolder.path}</p>
                    </div>
                  </div>
                  
                  {/* Quick Actions */}
                  <div className="flex items-center gap-2">
                    {selectedFolder.state === 'added' && (
                      <button
                        onClick={() => handleIndexFolder(selectedFolder.folder_id)}
                        className="px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2 text-sm"
                      >
                        <FileText className="w-4 h-4" />
                        Index
                      </button>
                    )}
                    {selectedFolder.state === 'indexed' && (
                      <button
                        onClick={() => handleSegmentFolder(selectedFolder.folder_id)}
                        className="px-3 py-1.5 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors flex items-center gap-2 text-sm"
                      >
                        <Package className="w-4 h-4" />
                        Segment
                      </button>
                    )}
                    {selectedFolder.state === 'segmented' && (
                      <button
                        onClick={() => handleUploadFolder(selectedFolder.folder_id)}
                        className="px-3 py-1.5 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors flex items-center gap-2 text-sm"
                      >
                        <Upload className="w-4 h-4" />
                        Upload
                      </button>
                    )}
                    {selectedFolder.state === 'uploaded' && !selectedFolder.published && (
                      <button
                        onClick={() => setShowShareDialog(true)}
                        className="px-3 py-1.5 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2 text-sm"
                      >
                        <Share2 className="w-4 h-4" />
                        Share
                      </button>
                    )}
                    <button
                      onClick={async () => {
                        try {
                          const result = await resyncFolder(selectedFolder.folder_id);
                          toast.success('Folder resynced');
                          await loadFolders();
                        } catch (error: any) {
                          toast.error(`Resync failed: ${error.message || error}`);
                        }
                      }}
                      className="px-3 py-1.5 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2 text-sm"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Resync
                    </button>
                    <button
                      onClick={() => handleDeleteFolder(selectedFolder.folder_id)}
                      className="px-3 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2 text-sm"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-6 mt-4 border-b border-gray-200 dark:border-dark-border -mb-4">
                  {(['overview', 'files', 'segments', 'shares', 'actions'] as const).map(tab => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`pb-3 px-1 text-sm font-medium capitalize transition-colors ${
                        activeTab === tab
                          ? 'text-primary border-b-2 border-primary'
                          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="grid grid-cols-3 gap-6">
                  <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                    <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                      <Database className="w-5 h-5 text-gray-500" />
                      Folder Statistics
                    </h3>
                    <dl className="space-y-3">
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Total Files:</dt>
                        <dd className="font-medium">{selectedFolder.file_count || selectedFolder.total_files || 0}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Total Size:</dt>
                        <dd className="font-medium">{formatBytes(selectedFolder.total_size || 0)}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Segments:</dt>
                        <dd className="font-medium">{selectedFolder.total_segments || 0}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Created:</dt>
                        <dd className="font-medium text-sm">
                          {new Date(selectedFolder.created_at).toLocaleDateString()}
                        </dd>
                      </div>
                    </dl>
                  </div>

                  <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                    <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                      <Activity className="w-5 h-5 text-gray-500" />
                      Processing Status
                    </h3>
                    <dl className="space-y-3">
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Current State:</dt>
                        <dd className="font-medium capitalize flex items-center gap-2">
                          {getStateIcon(selectedFolder.state)}
                          {selectedFolder.state}
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Indexed:</dt>
                        <dd className="font-medium">
                          {['indexed', 'segmented', 'uploaded', 'published'].includes(selectedFolder.state) ? 'Yes' : 'No'}
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Segmented:</dt>
                        <dd className="font-medium">
                          {['segmented', 'uploaded', 'published'].includes(selectedFolder.state) ? 'Yes' : 'No'}
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Uploaded:</dt>
                        <dd className="font-medium">
                          {['uploaded', 'published'].includes(selectedFolder.state) ? 'Yes' : 'No'}
                        </dd>
                      </div>
                    </dl>
                  </div>

                  <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                    <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                      <Share2 className="w-5 h-5 text-gray-500" />
                      Sharing Status
                    </h3>
                    <dl className="space-y-3">
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Published:</dt>
                        <dd className="font-medium">{selectedFolder.published ? 'Yes' : 'No'}</dd>
                      </div>
                      {selectedFolder.share_id && (
                        <>
                          <div className="flex justify-between">
                            <dt className="text-gray-500">Share ID:</dt>
                            <dd className="font-mono text-xs">{selectedFolder.share_id.slice(0, 12)}...</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-500">Access Type:</dt>
                            <dd className="font-medium capitalize">
                              {selectedFolder.access_type || 'Public'}
                            </dd>
                          </div>
                        </>
                      )}
                      {!selectedFolder.published && (
                        <button
                          onClick={() => setShowShareDialog(true)}
                          disabled={selectedFolder.state !== 'uploaded'}
                          className="w-full mt-2 px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                          <Share2 className="w-4 h-4" />
                          Create Share
                        </button>
                      )}
                    </dl>
                  </div>
                </div>
              )}

              {/* Files Tab */}
              {activeTab === 'files' && (
                <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                    <Files className="w-5 h-5 text-gray-500" />
                    Files in Folder
                  </h3>
                  
                  {files.length === 0 ? (
                    <div className="text-center py-8">
                      <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <p className="text-gray-500">
                        {selectedFolder.state === 'added' 
                          ? 'Folder not indexed yet. Click "Index" to scan files.'
                          : 'No files found in this folder.'}
                      </p>
                      {selectedFolder.state === 'added' && (
                        <button
                          onClick={() => handleIndexFolder(selectedFolder.folder_id)}
                          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                        >
                          Index Folder
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {files.map(file => (
                        <div key={file.file_id} className="border border-gray-200 dark:border-gray-700 rounded-lg">
                          <div
                            onClick={() => toggleFileExpanded(file.file_id)}
                            className="p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                {expandedFiles.has(file.file_id) ? (
                                  <ChevronDown className="w-4 h-4 text-gray-500" />
                                ) : (
                                  <ChevronRight className="w-4 h-4 text-gray-500" />
                                )}
                                <File className="w-4 h-4 text-blue-500" />
                                <span className="font-medium">{file.name}</span>
                              </div>
                              <div className="flex items-center gap-4 text-sm text-gray-500">
                                <span>{formatBytes(file.size)}</span>
                                {file.segments && (
                                  <span className="flex items-center gap-1">
                                    <Layers className="w-3 h-3" />
                                    {file.segments.length} segments
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          {expandedFiles.has(file.file_id) && (
                            <div className="border-t border-gray-200 dark:border-gray-700 p-3 bg-gray-50 dark:bg-gray-900">
                              <dl className="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                  <dt className="text-gray-500">Path:</dt>
                                  <dd className="font-mono text-xs">{file.path}</dd>
                                </div>
                                <div>
                                  <dt className="text-gray-500">Size:</dt>
                                  <dd>{formatBytes(file.size)}</dd>
                                </div>
                                {file.hash && (
                                  <div>
                                    <dt className="text-gray-500">Hash:</dt>
                                    <dd className="font-mono text-xs">{file.hash.slice(0, 16)}...</dd>
                                  </div>
                                )}
                                {file.indexed_at && (
                                  <div>
                                    <dt className="text-gray-500">Indexed:</dt>
                                    <dd>{new Date(file.indexed_at).toLocaleString()}</dd>
                                  </div>
                                )}
                              </dl>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Segments Tab */}
              {activeTab === 'segments' && (
                <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                  <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                    <Layers className="w-5 h-5 text-gray-500" />
                    Segments
                  </h3>
                  
                  {selectedFolder.total_segments === 0 ? (
                    <div className="text-center py-8">
                      <Package className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <p className="text-gray-500">
                        {selectedFolder.state === 'indexed' 
                          ? 'Folder not segmented yet. Click "Segment" to create segments.'
                          : selectedFolder.state === 'added'
                          ? 'Index the folder first before creating segments.'
                          : 'No segments created for this folder.'}
                      </p>
                      {selectedFolder.state === 'indexed' && (
                        <button
                          onClick={() => handleSegmentFolder(selectedFolder.folder_id)}
                          className="mt-4 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
                        >
                          Create Segments
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4 mb-6">
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                          <div className="text-2xl font-bold text-gray-900 dark:text-white">
                            {selectedFolder.total_segments}
                          </div>
                          <div className="text-sm text-gray-500">Total Segments</div>
                        </div>
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                          <div className="text-2xl font-bold text-gray-900 dark:text-white">
                            {formatBytes((selectedFolder.total_size || 0) / (selectedFolder.total_segments || 1))}
                          </div>
                          <div className="text-sm text-gray-500">Avg Segment Size</div>
                        </div>
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                          <div className="text-2xl font-bold text-gray-900 dark:text-white">
                            {selectedFolder.state === 'uploaded' || selectedFolder.state === 'published' ? '100%' : '0%'}
                          </div>
                          <div className="text-sm text-gray-500">Uploaded</div>
                        </div>
                      </div>

                      {selectedFile && selectedFile.segments && (
                        <div>
                          <h4 className="font-medium mb-2">Segments for {selectedFile.name}</h4>
                          <div className="space-y-2">
                            {selectedFile.segments.map(segment => (
                              <div key={segment.segment_id} className="flex items-center justify-between p-2 border border-gray-200 dark:border-gray-700 rounded">
                                <div className="flex items-center gap-2">
                                  <Hash className="w-4 h-4 text-gray-500" />
                                  <span className="font-mono text-sm">Segment {segment.sequence}</span>
                                </div>
                                <div className="flex items-center gap-4 text-sm text-gray-500">
                                  <span>{formatBytes(segment.size)}</span>
                                  {segment.uploaded && (
                                    <CheckCircle className="w-4 h-4 text-green-500" />
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Shares Tab */}
              {activeTab === 'shares' && (
                <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium flex items-center gap-2">
                      <Share2 className="w-5 h-5 text-gray-500" />
                      Shares
                    </h3>
                    <button
                      onClick={() => setShowShareDialog(true)}
                      disabled={selectedFolder.state !== 'uploaded'}
                      className="px-3 py-1.5 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm"
                    >
                      <Plus className="w-4 h-4" />
                      New Share
                    </button>
                  </div>

                  {shares.length === 0 ? (
                    <div className="text-center py-8">
                      <Share2 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <p className="text-gray-500">
                        {selectedFolder.state !== 'uploaded' 
                          ? 'Upload the folder first before creating shares.'
                          : 'No shares created for this folder.'}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {shares.map(share => (
                        <div key={share.share_id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              {share.share_type === 'public' && <Globe className="w-5 h-5 text-green-500" />}
                              {share.share_type === 'private' && <Lock className="w-5 h-5 text-yellow-500" />}
                              {share.share_type === 'protected' && <Shield className="w-5 h-5 text-blue-500" />}
                              <div>
                                <div className="font-medium capitalize">{share.share_type} Share</div>
                                <div className="text-sm text-gray-500">
                                  Created {new Date(share.created_at).toLocaleDateString()}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => {
                                  navigator.clipboard.writeText(share.share_id);
                                  toast.success('Share ID copied');
                                }}
                                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                                title="Copy Share ID"
                              >
                                <Copy className="w-4 h-4" />
                              </button>
                              <button
                                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                                title="View Share"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-500">Share ID:</span>
                              <span className="font-mono text-xs">{share.share_id}</span>
                            </div>
                            {share.expires_at && (
                              <div className="flex items-center justify-between text-sm mt-1">
                                <span className="text-gray-500">Expires:</span>
                                <span>{new Date(share.expires_at).toLocaleDateString()}</span>
                              </div>
                            )}
                            {share.download_count !== undefined && (
                              <div className="flex items-center justify-between text-sm mt-1">
                                <span className="text-gray-500">Downloads:</span>
                                <span>{share.download_count}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Actions Tab */}
              {activeTab === 'actions' && (
                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                    <h3 className="text-lg font-medium mb-4">Processing Actions</h3>
                    <div className="space-y-3">
                      <button
                        onClick={() => handleIndexFolder(selectedFolder.folder_id)}
                        className="w-full px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
                      >
                        <FileText className="w-5 h-5" />
                        {selectedFolder.state === 'added' ? 'Index Folder' : 'Re-index Folder'}
                      </button>

                      <button
                        onClick={() => handleSegmentFolder(selectedFolder.folder_id)}
                        disabled={!['indexed', 'segmented', 'uploaded', 'published'].includes(selectedFolder.state)}
                        className="w-full px-4 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <Package className="w-5 h-5" />
                        {selectedFolder.total_segments > 0 ? 'Re-segment Folder' : 'Create Segments'}
                      </button>

                      <button
                        onClick={() => handleUploadFolder(selectedFolder.folder_id)}
                        disabled={!['segmented', 'uploaded', 'published'].includes(selectedFolder.state)}
                        className="w-full px-4 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <Upload className="w-5 h-5" />
                        {['uploaded', 'published'].includes(selectedFolder.state) ? 'Re-upload to Usenet' : 'Upload to Usenet'}
                      </button>

                      <button
                        onClick={() => setShowShareDialog(true)}
                        disabled={selectedFolder.state !== 'uploaded'}
                        className="w-full px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <Share2 className="w-5 h-5" />
                        {selectedFolder.published ? 'Create New Share' : 'Publish Folder'}
                      </button>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                    <h3 className="text-lg font-medium mb-4">Maintenance Actions</h3>
                    <div className="space-y-3">
                      <button
                        onClick={async () => {
                          try {
                            const result = await resyncFolder(selectedFolder.folder_id);
                            toast.success('Folder resynced successfully');
                            await loadFolders();
                            await loadFolderDetails(selectedFolder.folder_id);
                          } catch (error: any) {
                            toast.error(`Resync failed: ${error.message || error}`);
                          }
                        }}
                        className="w-full px-4 py-3 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors flex items-center justify-center gap-2"
                      >
                        <RefreshCw className="w-5 h-5" />
                        Resync for Changes
                      </button>

                      <button
                        onClick={() => {
                          // TODO: Implement republish
                          toast.info('Republish functionality coming soon');
                        }}
                        disabled={!selectedFolder.published}
                        className="w-full px-4 py-3 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <Server className="w-5 h-5" />
                        Republish to Usenet
                      </button>

                      <button
                        onClick={() => {
                          // TODO: Implement download
                          toast.info('Download functionality coming soon');
                        }}
                        disabled={!selectedFolder.published}
                        className="w-full px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <Download className="w-5 h-5" />
                        Test Download
                      </button>

                      <button
                        onClick={() => handleDeleteFolder(selectedFolder.folder_id)}
                        className="w-full px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
                      >
                        <Trash2 className="w-5 h-5" />
                        Delete Folder
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Folder className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Select a Folder
              </h3>
              <p className="text-gray-500">
                Choose a folder from the list to view details and manage it
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Share Dialog */}
      {showShareDialog && selectedFolder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">Create Share</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Share Type</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      value="public"
                      checked={shareType === 'public'}
                      onChange={(e) => setShareType(e.target.value as any)}
                    />
                    <Globe className="w-4 h-4 text-green-500" />
                    <span>Public - Anyone can access</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      value="private"
                      checked={shareType === 'private'}
                      onChange={(e) => setShareType(e.target.value as any)}
                    />
                    <Lock className="w-4 h-4 text-yellow-500" />
                    <span>Private - Specific users only</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      value="protected"
                      checked={shareType === 'protected'}
                      onChange={(e) => setShareType(e.target.value as any)}
                    />
                    <Shield className="w-4 h-4 text-blue-500" />
                    <span>Protected - Password required</span>
                  </label>
                </div>
              </div>

              {shareType === 'private' && (
                <PrivateShareManager
                  authorizedUsers={authorizedUsers}
                  onUsersChange={setAuthorizedUsers}
                  disabled={false}
                />
              )}

              {shareType === 'protected' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Password</label>
                  <input
                    type="password"
                    value={sharePassword}
                    onChange={(e) => setSharePassword(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
                    placeholder="Enter password"
                  />
                </div>
              )}

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleCreateShare}
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                >
                  Create Share
                </button>
                <button
                  onClick={() => setShowShareDialog(false)}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Add Plus icon since it's not imported
const Plus = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
);