import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileTree } from '../components/FileTree';
import { useAppStore } from '../stores/useAppStore';
import { selectFiles, indexFolder, createShare } from '../lib/tauri';
import { FileNode, Transfer } from '../types';
import { 
  Upload as UploadIcon, 
  FolderOpen, 
  File,
  X,
  Share2,
  Lock,
  Globe,
  Shield,
  AlertCircle
} from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';

export const Upload: React.FC = () => {
  const [files, setFiles] = useState<FileNode | null>(null);
  const [shareType, setShareType] = useState<'public' | 'private' | 'protected'>('public');
  const [password, setPassword] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  
  const { selectedFiles, addUpload, clearSelection } = useAppStore();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // Convert File objects to FileNode structure
    const rootNode: FileNode = {
      id: 'root',
      name: 'Selected Files',
      type: 'folder',
      size: 0,
      path: '/',
      children: [],
      modifiedAt: new Date()
    };

    for (const file of acceptedFiles) {
      const fileNode: FileNode = {
        id: file.name,
        name: file.name,
        type: 'file',
        size: file.size,
        path: file.name,
        modifiedAt: new Date(file.lastModified)
      };
      rootNode.children!.push(fileNode);
      rootNode.size += file.size;
    }

    setFiles(rootNode);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true
  });

  const handleSelectFolder = async () => {
    try {
      const selectedFiles = await selectFiles();
      if (selectedFiles.length > 0) {
        // Build tree structure from selected files
        const rootPath = selectedFiles[0].path.split('/').slice(0, -1).join('/');
        const rootNode = await indexFolder(rootPath);
        setFiles(rootNode);
      }
    } catch (error) {
      console.error('Failed to select folder:', error);
      toast.error('Failed to select folder');
    }
  };

  const handleCreateShare = async () => {
    if (!files || selectedFiles.length === 0) {
      toast.error('Please select files to share');
      return;
    }

    if (shareType === 'protected' && !password) {
      toast.error('Please enter a password for protected share');
      return;
    }

    setIsUploading(true);

    try {
      const filePaths = selectedFiles.map(f => f.path);
      const share = await createShare(
        filePaths,
        shareType,
        shareType === 'protected' ? password : undefined
      );

      // Create transfer object for tracking
      const transfer: Transfer = {
        id: `upload-${Date.now()}`,
        type: 'upload',
        name: share.name,
        totalSize: selectedFiles.reduce((sum, f) => sum + f.size, 0),
        transferredSize: 0,
        speed: 0,
        eta: 0,
        status: 'active',
        segments: [],
        startedAt: new Date()
      };

      addUpload(transfer);
      
      toast.success(`Share created: ${share.shareId}`);
      
      // Reset form
      setFiles(null);
      clearSelection();
      setPassword('');
      
    } catch (error: any) {
      console.error('Failed to create share:', error);
      toast.error(error.toString());
    } finally {
      setIsUploading(false);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const totalSize = selectedFiles.reduce((sum, f) => sum + f.size, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Upload Files</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Select files or folders to create a secure share
        </p>
      </div>

      {/* File Selection */}
      {!files ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Drag & Drop Area */}
          <div
            {...getRootProps()}
            className={clsx(
              'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all',
              isDragActive
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-300 dark:border-dark-border hover:border-primary-400'
            )}
          >
            <input {...getInputProps()} />
            <UploadIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {isDragActive ? 'Drop files here' : 'Drag & drop files'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              or click to select files
            </p>
          </div>

          {/* Folder Selection */}
          <div
            onClick={handleSelectFolder}
            className="border-2 border-dashed border-gray-300 dark:border-dark-border rounded-lg p-12 text-center cursor-pointer hover:border-primary-400 transition-all"
          >
            <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Select Folder
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Choose an entire folder to upload
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* File Tree */}
          <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border">
            <div className="p-4 border-b border-gray-200 dark:border-dark-border">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Selected Files
                </h2>
                <button
                  onClick={() => {
                    setFiles(null);
                    clearSelection();
                  }}
                  className="p-1.5 hover:bg-gray-100 dark:hover:bg-dark-border rounded"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
                <span>{selectedFiles.length} selected</span>
                <span>•</span>
                <span>{formatBytes(totalSize)}</span>
              </div>
            </div>
            
            <FileTree 
              data={files} 
              selectable={true}
              className="h-96"
            />
          </div>

          {/* Share Options */}
          <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Share Options
            </h2>
            
            <div className="space-y-4">
              {/* Share Type Selection */}
              <div className="grid grid-cols-3 gap-3">
                <button
                  onClick={() => setShareType('public')}
                  className={clsx(
                    'p-3 rounded-lg border-2 transition-all',
                    shareType === 'public'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-dark-border hover:border-gray-300'
                  )}
                >
                  <Globe className="w-5 h-5 text-gray-600 dark:text-gray-400 mx-auto mb-1" />
                  <p className="text-sm font-medium text-gray-900 dark:text-white">Public</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Anyone with link
                  </p>
                </button>

                <button
                  onClick={() => setShareType('private')}
                  className={clsx(
                    'p-3 rounded-lg border-2 transition-all',
                    shareType === 'private'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-dark-border hover:border-gray-300'
                  )}
                >
                  <Shield className="w-5 h-5 text-gray-600 dark:text-gray-400 mx-auto mb-1" />
                  <p className="text-sm font-medium text-gray-900 dark:text-white">Private</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Verified users only
                  </p>
                </button>

                <button
                  onClick={() => setShareType('protected')}
                  className={clsx(
                    'p-3 rounded-lg border-2 transition-all',
                    shareType === 'protected'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-dark-border hover:border-gray-300'
                  )}
                >
                  <Lock className="w-5 h-5 text-gray-600 dark:text-gray-400 mx-auto mb-1" />
                  <p className="text-sm font-medium text-gray-900 dark:text-white">Protected</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Password required
                  </p>
                </button>
              </div>

              {/* Password Input */}
              {shareType === 'protected' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password for share"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
                  />
                </div>
              )}

              {/* Info Box */}
              <div className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-700 dark:text-blue-400">
                  <p className="font-medium mb-1">End-to-end encryption</p>
                  <p>All files are encrypted before uploading. Only people with the share ID can decrypt them.</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleCreateShare}
                  disabled={isUploading || selectedFiles.length === 0}
                  className="flex-1 flex items-center justify-center gap-2 bg-primary-500 text-white px-4 py-2 rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Share2 className="w-4 h-4" />
                  {isUploading ? 'Creating Share...' : 'Create Share'}
                </button>
                
                <button
                  onClick={() => {
                    setFiles(null);
                    clearSelection();
                    setPassword('');
                  }}
                  disabled={isUploading}
                  className="px-4 py-2 border border-gray-300 dark:border-dark-border text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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