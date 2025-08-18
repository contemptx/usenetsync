import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import { PrivateShareManager } from '../components/PrivateShareManager';
import { 
  getFolders, 
  addFolder, 
  indexFolderFull, 
  segmentFolder, 
  uploadFolder, 
  publishFolder as publishFolderApi,
  getAuthorizedUsers,
  checkDatabaseStatus 
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
  Settings
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
}

interface FolderOperation {
  operation: 'indexing' | 'segmenting' | 'uploading' | 'publishing';
  progress: number;
  current_item?: string;
  speed_mbps?: number;
  eta_seconds?: number;
}

export const FolderManagement: React.FC = () => {
  const [folders, setFolders] = useState<ManagedFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<ManagedFolder | null>(null);
  const [activeOperations, setActiveOperations] = useState<Record<string, FolderOperation>>({});
  const [activeTab, setActiveTab] = useState<'overview' | 'access' | 'files' | 'actions'>('overview');
  const [loading, setLoading] = useState(false);
  const [dbError, setDbError] = useState<string | null>(null);
  const [databaseType, setDatabaseType] = useState<'sqlite' | 'postgresql' | null>(null);
  
  // Access control state
  const [selectedAccessType, setSelectedAccessType] = useState<'public' | 'private' | 'protected'>('public');
  const [authorizedUsers, setAuthorizedUsers] = useState<string[]>([]);
  const [protectedPassword, setProtectedPassword] = useState('');

  // Load folders on mount
  useEffect(() => {
    loadFolders();
    // Set up interval to refresh folders (only if no error)
    const interval = setInterval(() => {
      // Only refresh if not loading and no error
      if (!dbError && !loading) {
        loadFolders();
      }
    }, 30000); // Increased to 30 seconds to reduce database load
    return () => clearInterval(interval);
  }, []); // Remove dbError dependency to avoid re-creating interval

  // Load authorized users when folder is selected
  useEffect(() => {
    if (selectedFolder && selectedFolder.access_type === 'private') {
      loadAuthorizedUsers(selectedFolder.folder_id);
      setSelectedAccessType('private');
    } else if (selectedFolder) {
      setSelectedAccessType(selectedFolder.access_type || 'public');
      setAuthorizedUsers([]);
    }
  }, [selectedFolder]);

  const loadFolders = async () => {
    try {
      // First check database status
      try {
        const dbStatus = await checkDatabaseStatus();
        if (dbStatus?.type) {
          setDatabaseType(dbStatus.type);
        }
      } catch (dbError) {
        console.log('Could not check database status:', dbError);
      }
      
      const result = await getFolders();
      setFolders(result as ManagedFolder[]);
      setDbError(null); // Clear any previous errors
    } catch (error: any) {
      console.error('Failed to load folders:', error);
      
      // Don't show error popup, just log it
      // The UI will show an appropriate message based on the database type
      
      // Set empty folders array to prevent undefined errors
      setFolders([]);
      
      // Still set database type if possible
      try {
        const dbStatus = await checkDatabaseStatus();
        if (dbStatus?.type) {
          setDatabaseType(dbStatus.type);
        }
      } catch (dbError) {
        console.log('Could not check database status:', dbError);
      }
    }
  };

  const loadAuthorizedUsers = async (folderId: string) => {
    try {
      const result = await getAuthorizedUsers(folderId);
      const userIds = result.users.map((u: any) => u.user_id || u);
      setAuthorizedUsers(userIds);
    } catch (error) {
      console.error('Failed to load authorized users:', error);
      setAuthorizedUsers([]);
    }
  };

  const handleAddFolder = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: 'Select Folder to Manage'
      });

      if (selected) {
        setLoading(true);
        const result = await addFolder(
          selected,
          selected.split('/').pop() || 'Unnamed Folder'
        );
        
        toast.success('Folder added successfully');
        await loadFolders();
      }
    } catch (error) {
      toast.error(`Failed to add folder: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const handleIndexFolder = async (folderId: string) => {
    try {
      setActiveOperations(prev => ({
        ...prev,
        [folderId]: { operation: 'indexing', progress: 0 }
      }));

      const result = await indexFolderFull(folderId);
      
      toast.success('Indexing completed');
      await loadFolders();
    } catch (error) {
      toast.error(`Indexing failed: ${error}`);
    } finally {
      setActiveOperations(prev => {
        const ops = { ...prev };
        delete ops[folderId];
        return ops;
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
      
      toast.success('Segmentation completed');
      await loadFolders();
    } catch (error) {
      toast.error(`Segmentation failed: ${error}`);
    } finally {
      setActiveOperations(prev => {
        const ops = { ...prev };
        delete ops[folderId];
        return ops;
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
      
      toast.success('Upload completed');
      await loadFolders();
    } catch (error) {
      toast.error(`Upload failed: ${error}`);
    } finally {
      setActiveOperations(prev => {
        const ops = { ...prev };
        delete ops[folderId];
        return ops;
      });
    }
  };

  const publishFolder = async (
    folderId: string, 
    accessType: string = 'public',
    userIds?: string[],
    password?: string
  ) => {
    try {
      setActiveOperations(prev => ({
        ...prev,
        [folderId]: { operation: 'publishing', progress: 0 }
      }));

      const params: any = { folderId, accessType };
      
      // Add user IDs for private shares
      if (accessType === 'private' && userIds && userIds.length > 0) {
        params.userIds = userIds;
      }
      
      // Add password for protected shares
      if (accessType === 'protected' && password) {
        params.password = password;
      }

      const result = await publishFolderApi(
        folderId,
        accessType,
        userIds,
        password
      );
      
      toast.success('Publishing completed');
      await loadFolders();
    } catch (error) {
      toast.error(`Publishing failed: ${error}`);
    } finally {
      setActiveOperations(prev => {
        const ops = { ...prev };
        delete ops[folderId];
        return ops;
      });
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'added': return <Folder className="w-4 h-4 text-gray-500" />;
      case 'indexing': return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'indexed': return <FileText className="w-4 h-4 text-green-500" />;
      case 'segmenting': return <Package className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'segmented': return <Layers className="w-4 h-4 text-green-500" />;
      case 'uploading': return <Upload className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'uploaded': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'publishing': return <Share2 className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'published': return <Share2 className="w-4 h-4 text-green-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Folder className="w-4 h-4 text-gray-500" />;
    }
  };

  const getNextAction = (folder: ManagedFolder) => {
    switch (folder.state) {
      case 'added':
        return { label: 'Index', action: () => indexFolder(folder.folder_id), icon: <FileText className="w-4 h-4" /> };
      case 'indexed':
        return { label: 'Segment', action: () => segmentFolder(folder.folder_id), icon: <Package className="w-4 h-4" /> };
      case 'segmented':
        return { label: 'Upload', action: () => uploadFolder(folder.folder_id), icon: <Upload className="w-4 h-4" /> };
      case 'uploaded':
        return { label: 'Publish', action: () => publishFolder(folder.folder_id, selectedAccessType, authorizedUsers, protectedPassword), icon: <Share2 className="w-4 h-4" /> };
      case 'published':
        return { label: 'Re-sync', action: () => indexFolder(folder.folder_id), icon: <RefreshCw className="w-4 h-4" /> };
      default:
        return null;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="flex h-full">
      {/* Database Error Alert */}
      {dbError && (
        <div className="absolute top-4 right-4 left-4 z-50 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
          <div className="flex-1">
            <p className="text-red-800 dark:text-red-200 font-medium">{dbError}</p>
            <button
              onClick={() => {
                setDbError(null);
                loadFolders();
              }}
              className="mt-2 text-sm text-red-700 dark:text-red-300 hover:underline"
            >
              Retry
            </button>
          </div>
          <button
            onClick={() => setDbError(null)}
            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
          >
            ✕
          </button>
        </div>
      )}

      {/* Folder List */}
      <div className="w-1/3 border-r border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface">
        <div className="p-4 border-b border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Managed Folders</h2>
              {databaseType && (
                <span className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                  {databaseType === 'postgresql' ? 'PostgreSQL' : 'SQLite'}
                </span>
              )}
            </div>
            <button
              onClick={handleAddFolder}
              disabled={loading}
              className="px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FolderOpen className="w-4 h-4" />
              Add Folder
            </button>
          </div>
        </div>

        <div className="overflow-y-auto" style={{ height: 'calc(100% - 88px)' }}>
          {folders.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Folder className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No folders added yet</p>
              <p className="text-sm mt-2">Click "Add Folder" to get started</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-dark-border">
              {folders.map(folder => {
                const operation = activeOperations[folder.folder_id];
                const nextAction = getNextAction(folder);
                
                return (
                  <div
                    key={folder.folder_id}
                    onClick={() => setSelectedFolder(folder)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-dark-hover transition-colors ${
                      selectedFolder?.folder_id === folder.folder_id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {getStateIcon(folder.state)}
                          <h3 className="font-medium text-gray-900 dark:text-white truncate">
                            {folder.name}
                          </h3>
                        </div>
                        
                        <p className="text-xs text-gray-500 truncate mb-2">{folder.path}</p>
                        
                        <div className="flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
                          <span className="flex items-center gap-1">
                            <Files className="w-3 h-3" />
                            {folder.total_files || 0} files
                          </span>
                          <span className="flex items-center gap-1">
                            <HardDrive className="w-3 h-3" />
                            {formatBytes(folder.total_size || 0)}
                          </span>
                          {folder.total_segments > 0 && (
                            <span className="flex items-center gap-1">
                              <Layers className="w-3 h-3" />
                              {folder.total_segments} segments
                            </span>
                          )}
                        </div>

                        {operation && (
                          <div className="mt-2">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-blue-600 capitalize">{operation.operation}...</span>
                              <span>{operation.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-1.5">
                              <div 
                                className="bg-blue-600 h-1.5 rounded-full transition-all"
                                style={{ width: `${operation.progress}%` }}
                              />
                            </div>
                          </div>
                        )}

                        {folder.published && folder.share_id && (
                          <div className="mt-2 px-2 py-1 bg-green-100 dark:bg-green-900/20 rounded text-xs text-green-700 dark:text-green-400">
                            Share ID: {folder.share_id}
                          </div>
                        )}
                      </div>

                      {nextAction && !operation && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            nextAction.action();
                          }}
                          className="ml-2 px-2 py-1 bg-primary text-white rounded text-xs hover:bg-primary-dark transition-colors flex items-center gap-1"
                        >
                          {nextAction.icon}
                          {nextAction.label}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Folder Details */}
      <div className="flex-1 bg-gray-50 dark:bg-dark-bg">
        {selectedFolder ? (
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {selectedFolder.name}
                  </h2>
                  <p className="text-sm text-gray-500 mt-1">{selectedFolder.path}</p>
                </div>
                <div className="flex items-center gap-2">
                  {getStateIcon(selectedFolder.state)}
                  <span className="text-sm font-medium capitalize">{selectedFolder.state}</span>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-4 mt-4 border-b border-gray-200 dark:border-dark-border -mb-4">
                {(['overview', 'access', 'files', 'actions'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`pb-2 px-1 text-sm font-medium capitalize transition-colors ${
                      activeTab === tab
                        ? 'text-primary border-b-2 border-primary'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    {tab === 'access' ? 'Access Control' : tab === 'files' ? 'Files & Segments' : tab}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white dark:bg-dark-surface rounded-lg p-4">
                      <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Statistics</h3>
                      <dl className="space-y-2">
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-500">Total Files:</dt>
                          <dd className="text-sm font-medium">{selectedFolder.total_files || 0}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-500">Total Size:</dt>
                          <dd className="text-sm font-medium">{formatBytes(selectedFolder.total_size || 0)}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-500">Segments:</dt>
                          <dd className="text-sm font-medium">{selectedFolder.total_segments || 0}</dd>
                        </div>
                      </dl>
                    </div>

                    <div className="bg-white dark:bg-dark-surface rounded-lg p-4">
                      <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Status</h3>
                      <dl className="space-y-2">
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-500">State:</dt>
                          <dd className="text-sm font-medium capitalize">{selectedFolder.state}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-500">Published:</dt>
                          <dd className="text-sm font-medium">{selectedFolder.published ? 'Yes' : 'No'}</dd>
                        </div>
                        {selectedFolder.share_id && (
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500">Share ID:</dt>
                            <dd className="text-sm font-medium font-mono">{selectedFolder.share_id.slice(0, 8)}...</dd>
                          </div>
                        )}
                      </dl>
                    </div>
                  </div>

                  {/* Workflow Progress */}
                  <div className="bg-white dark:bg-dark-surface rounded-lg p-4">
                    <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-4">Workflow Progress</h3>
                    <div className="flex items-center justify-between">
                      {['added', 'indexed', 'segmented', 'uploaded', 'published'].map((step, index) => {
                        const states = ['added', 'indexed', 'segmented', 'uploaded', 'published'];
                        const currentIndex = states.indexOf(selectedFolder.state);
                        const isComplete = currentIndex >= index;
                        const isCurrent = currentIndex === index;
                        
                        return (
                          <React.Fragment key={step}>
                            <div className="flex flex-col items-center">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                isComplete 
                                  ? 'bg-green-500 text-white' 
                                  : isCurrent 
                                    ? 'bg-blue-500 text-white animate-pulse' 
                                    : 'bg-gray-200 text-gray-400'
                              }`}>
                                {isComplete ? '✓' : index + 1}
                              </div>
                              <span className="text-xs mt-1 capitalize">{step}</span>
                            </div>
                            {index < 4 && (
                              <div className={`flex-1 h-0.5 ${
                                currentIndex > index ? 'bg-green-500' : 'bg-gray-200'
                              }`} />
                            )}
                          </React.Fragment>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'access' && (
                <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                  <h3 className="text-lg font-medium mb-4">Access Control Settings</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Access Type
                      </label>
                      <div className="flex gap-4">
                        <label className="flex items-center">
                          <input 
                            type="radio" 
                            name="access" 
                            value="public" 
                            checked={selectedAccessType === 'public'}
                            onChange={() => setSelectedAccessType('public')}
                            className="mr-2" 
                          />
                          <Unlock className="w-4 h-4 mr-1" />
                          Public
                        </label>
                        <label className="flex items-center">
                          <input 
                            type="radio" 
                            name="access" 
                            value="private" 
                            checked={selectedAccessType === 'private'}
                            onChange={() => setSelectedAccessType('private')}
                            className="mr-2" 
                          />
                          <Lock className="w-4 h-4 mr-1" />
                          Private
                        </label>
                        <label className="flex items-center">
                          <input 
                            type="radio" 
                            name="access" 
                            value="protected" 
                            checked={selectedAccessType === 'protected'}
                            onChange={() => setSelectedAccessType('protected')}
                            className="mr-2" 
                          />
                          <Users className="w-4 h-4 mr-1" />
                          Protected
                        </label>
                      </div>
                    </div>

                    {/* Show PrivateShareManager for private access */}
                    {selectedAccessType === 'private' && (
                      <PrivateShareManager
                        authorizedUsers={authorizedUsers}
                        onUsersChange={setAuthorizedUsers}
                        disabled={!selectedFolder || selectedFolder.state !== 'uploaded'}
                      />
                    )}

                    {/* Show password field for protected access */}
                    {selectedAccessType === 'protected' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Password
                        </label>
                        <input
                          type="password"
                          value={protectedPassword}
                          onChange={(e) => setProtectedPassword(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-bg"
                          placeholder="Enter password for protected access"
                        />
                      </div>
                    )}

                    <div className="flex gap-3">
                      <button 
                        onClick={() => {
                          if (selectedFolder) {
                            publishFolder(
                              selectedFolder.folder_id, 
                              selectedAccessType,
                              selectedAccessType === 'private' ? authorizedUsers : undefined,
                              selectedAccessType === 'protected' ? protectedPassword : undefined
                            );
                          }
                        }}
                        disabled={!selectedFolder || selectedFolder.state !== 'uploaded'}
                        className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {selectedFolder?.published ? 'Update Access & Re-publish' : 'Publish with Access Settings'}
                      </button>
                      
                      {selectedFolder?.published && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 self-center">
                          Re-publishing only updates access control, not files
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'files' && (
                <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                  <h3 className="text-lg font-medium mb-4">Files & Segments</h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    File listing and segment details will appear here once the folder is indexed.
                  </p>
                  {selectedFolder.state === 'added' && (
                    <button
                      onClick={() => handleIndexFolder(selectedFolder.folder_id)}
                      className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
                    >
                      Index Folder to View Files
                    </button>
                  )}
                </div>
              )}

              {activeTab === 'actions' && (
                <div className="bg-white dark:bg-dark-surface rounded-lg p-6">
                  <h3 className="text-lg font-medium mb-4">Actions</h3>
                  <div className="space-y-3">
                    <button
                      onClick={() => handleIndexFolder(selectedFolder.folder_id)}
                      className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Re-index Folder
                    </button>

                    {selectedFolder.published && (
                      <button
                        onClick={() => publishFolder(selectedFolder.folder_id)}
                        className="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center gap-2"
                      >
                        <Share2 className="w-4 h-4" />
                        Re-publish Share
                      </button>
                    )}

                    <button
                      className="w-full px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center justify-center gap-2"
                    >
                      <Settings className="w-4 h-4" />
                      Advanced Settings
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <Folder className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p className="text-lg">Select a folder to view details</p>
              <p className="text-sm mt-2">Add folders to manage them through the complete workflow</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};