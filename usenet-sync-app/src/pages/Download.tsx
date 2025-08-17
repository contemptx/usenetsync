import React, { useState } from 'react';
import { getShareDetails, downloadShare } from '../lib/tauri';
import { FileTree } from '../components/FileTree';
import { useAppStore } from '../stores/useAppStore';
import { Download as DownloadIcon, Search, Lock, Folder } from 'lucide-react';
import toast from 'react-hot-toast';
import { FileNode, Transfer } from '../types';

export const Download: React.FC = () => {
  const [shareId, setShareId] = useState('');
  const [password, setPassword] = useState('');
  const [shareDetails, setShareDetails] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [fileTree, setFileTree] = useState<FileNode | null>(null);
  
  const { addDownload, selectedFiles } = useAppStore();

  const handleLookupShare = async () => {
    if (!shareId.trim()) {
      toast.error('Please enter a share ID');
      return;
    }

    setIsLoading(true);
    try {
      const details = await getShareDetails(shareId);
      setShareDetails(details);
      
      // Build file tree from share details
      const tree: FileNode = {
        id: 'root',
        name: details.name,
        type: 'folder',
        size: details.size,
        path: '/',
        children: [], // Would be populated from actual share data
        modifiedAt: new Date(details.createdAt)
      };
      setFileTree(tree);
      
      toast.success('Share found!');
    } catch (error: any) {
      toast.error('Share not found or invalid');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!shareDetails) return;

    const selectedPaths = selectedFiles.map(f => f.path);
    
    try {
      await downloadShare(
        shareId,
        '/downloads', // Default download location
        selectedPaths.length > 0 ? selectedPaths : undefined
      );

      // Create transfer for tracking
      const transfer: Transfer = {
        id: `download-${Date.now()}`,
        type: 'download',
        name: shareDetails.name,
        totalSize: shareDetails.size,
        transferredSize: 0,
        speed: 0,
        eta: 0,
        status: 'active',
        segments: [],
        startedAt: new Date()
      };

      addDownload(transfer);
      toast.success('Download started');
      
      // Reset
      setShareId('');
      setPassword('');
      setShareDetails(null);
      setFileTree(null);
      
    } catch (error: any) {
      toast.error(error.toString());
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Download Share</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Enter a share ID to download files
        </p>
      </div>

      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Share ID
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={shareId}
                onChange={(e) => setShareId(e.target.value.toUpperCase())}
                placeholder="Enter share ID (e.g., MRFE3BX25XTF5CH6FPP2PXDL)"
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
                disabled={isLoading}
              />
              <button
                onClick={handleLookupShare}
                disabled={isLoading || !shareId.trim()}
                className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                <Search className="w-4 h-4" />
                {isLoading ? 'Looking up...' : 'Look up'}
              </button>
            </div>
          </div>

          {shareDetails?.type === 'protected' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Lock className="w-4 h-4 inline mr-1" />
                Password Required
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
              />
            </div>
          )}
        </div>
      </div>

      {shareDetails && fileTree && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border">
            <div className="p-4 border-b border-gray-200 dark:border-dark-border">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Share Contents
              </h2>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
                <span>{shareDetails.fileCount} files</span>
                <span>•</span>
                <span>{shareDetails.folderCount} folders</span>
                <span>•</span>
                <span>{formatBytes(shareDetails.size)}</span>
              </div>
            </div>
            
            <FileTree 
              data={fileTree}
              selectable={true}
              className="h-96"
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleDownload}
              className="flex-1 flex items-center justify-center gap-2 bg-primary-500 text-white px-4 py-3 rounded-lg hover:bg-primary-600 transition-colors"
            >
              <DownloadIcon className="w-5 h-5" />
              Download {selectedFiles.length > 0 ? `${selectedFiles.length} Selected` : 'All'}
            </button>
            
            <button
              onClick={() => {
                setShareDetails(null);
                setFileTree(null);
                setShareId('');
                setPassword('');
              }}
              className="px-4 py-3 border border-gray-300 dark:border-dark-border text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-bg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};