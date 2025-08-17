import React, { useState } from 'react';
import { useAppStore } from '../stores/useAppStore';
import { Share2, Copy, Trash2, Eye, Calendar, Users, History, X } from 'lucide-react';
import { QRCodeSVG as QRCode } from 'qrcode.react';
import { VersionHistory } from '../components/VersionHistory';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import toast from 'react-hot-toast';
import clsx from 'clsx';

export const Shares: React.FC = () => {
  const { shares, removeShare } = useAppStore();
  const [selectedShare, setSelectedShare] = useState<string | null>(null);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  
  // Use keyboard shortcuts
  useKeyboardShortcuts();

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDate = (date: Date): string => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(date));
  };

  const getShareTypeIcon = (type: string) => {
    const icons = {
      public: '🌍',
      private: '🔒',
      protected: '🛡️'
    };
    return icons[type as keyof typeof icons] || '📁';
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">My Shares</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Manage and monitor your shared files
        </p>
      </div>

      {shares.length === 0 ? (
        <div className="bg-white dark:bg-dark-surface rounded-lg p-12 border border-gray-200 dark:border-dark-border text-center">
          <Share2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No shares yet
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Upload files to create your first share
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {shares.map((share) => (
            <div
              key={share.id}
              className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border overflow-hidden hover:shadow-lg transition-shadow"
            >
              <div className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getShareTypeIcon(share.type)}</span>
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        {share.name}
                      </h3>
                      <span className={clsx(
                        'text-xs px-2 py-0.5 rounded-full',
                        share.type === 'public' && 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
                        share.type === 'private' && 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
                        share.type === 'protected' && 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                      )}>
                        {share.type}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex gap-1">
                    <button
                      onClick={() => {
                        setSelectedShare(share.shareId);
                        setShowVersionHistory(true);
                      }}
                      className="p-1 hover:bg-gray-100 dark:hover:bg-dark-border rounded"
                      title="Version History"
                    >
                      <History className="w-4 h-4 text-gray-500" />
                    </button>
                    <button
                      onClick={() => {
                        removeShare(share.id);
                        toast.success('Share removed');
                      }}
                      className="p-1 hover:bg-gray-100 dark:hover:bg-dark-border rounded"
                    >
                      <Trash2 className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                </div>

                <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>{formatDate(share.createdAt)}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    <span>{share.accessCount} accesses</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    <span>{share.fileCount} files • {formatBytes(share.size)}</span>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-gray-50 dark:bg-dark-bg rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Share ID
                    </span>
                    <button
                      onClick={() => copyToClipboard(share.shareId)}
                      className="p-1 hover:bg-gray-200 dark:hover:bg-dark-surface rounded"
                    >
                      <Copy className="w-3 h-3 text-gray-500" />
                    </button>
                  </div>
                  <code className="text-xs font-mono text-gray-900 dark:text-white break-all">
                    {share.shareId}
                  </code>
                </div>

                <details className="mt-4">
                  <summary className="cursor-pointer text-sm text-primary-500 hover:text-primary-600">
                    Show QR Code
                  </summary>
                  <div className="mt-3 flex justify-center p-4 bg-white rounded">
                    <QRCode 
                      value={share.shareId}
                      size={150}
                      level="M"
                    />
                  </div>
                </details>

                {share.expiresAt && (
                  <div className="mt-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-xs text-yellow-700 dark:text-yellow-400">
                    Expires: {formatDate(share.expiresAt)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Version History Modal */}
      {showVersionHistory && selectedShare && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-black bg-opacity-50" 
            onClick={() => setShowVersionHistory(false)}
          />
          <div className="relative bg-white dark:bg-dark-surface rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-dark-border flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Version History
              </h2>
              <button
                onClick={() => setShowVersionHistory(false)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-dark-border rounded"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="p-4 overflow-auto max-h-[calc(80vh-80px)]">
              <VersionHistory 
                fileId={selectedShare}
                onRollback={(versionId) => {
                  console.log('Rollback to version:', versionId);
                  toast.success('Rolled back to selected version');
                }}
                onCompare={(v1, v2) => {
                  console.log('Compare versions:', v1, v2);
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};