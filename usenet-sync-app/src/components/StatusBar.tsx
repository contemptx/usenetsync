import React, { useState, useEffect } from 'react';
import { 
  Wifi, 
  WifiOff, 
  HardDrive, 
  Upload, 
  Download, 
  Activity,
  AlertCircle,
  Clock
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface StatusBarProps {
  className?: string;
}

interface ConnectionStatus {
  isConnected: boolean;
  serverName?: string;
  latency?: number;
}

interface TransferStatus {
  uploadSpeed: number;
  downloadSpeed: number;
  activeUploads: number;
  activeDownloads: number;
}

interface StorageStatus {
  used: number;
  total: number;
  percentage: number;
}

export const StatusBar: React.FC<StatusBarProps> = ({ className = '' }) => {
  const [connectionStatus] = useState<ConnectionStatus>({
    isConnected: true,
    serverName: 'news.provider.com',
    latency: 45
  });
  
  const [transferStatus, setTransferStatus] = useState<TransferStatus>({
    uploadSpeed: 0,
    downloadSpeed: 0,
    activeUploads: 0,
    activeDownloads: 0
  });
  
  const [storageStatus] = useState<StorageStatus>({
    used: 45 * 1024 * 1024 * 1024, // 45 GB
    total: 100 * 1024 * 1024 * 1024, // 100 GB
    percentage: 45
  });
  
  const [lastSync, setLastSync] = useState<Date>(new Date());
  const [notifications] = useState<number>(0);

  // Update status periodically
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate status updates
      setTransferStatus({
        uploadSpeed: Math.random() * 500,
        downloadSpeed: Math.random() * 2000,
        activeUploads: Math.floor(Math.random() * 3),
        activeDownloads: Math.floor(Math.random() * 5)
      });
      
      // Update last sync time
      if (Math.random() > 0.8) {
        setLastSync(new Date());
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, []);

  const formatBytes = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatSpeed = (bytesPerSecond: number): string => {
    return `${formatBytes(bytesPerSecond)}/s`;
  };

  const getConnectionColor = () => {
    if (!connectionStatus.isConnected) return 'text-red-500';
    if (connectionStatus.latency && connectionStatus.latency > 100) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getConnectionIcon = () => {
    return connectionStatus.isConnected ? (
      <Wifi className="w-4 h-4" />
    ) : (
      <WifiOff className="w-4 h-4" />
    );
  };

  return (
    <div className={`flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-dark-surface border-t border-gray-200 dark:border-dark-border text-xs ${className}`}>
      {/* Left Section - Connection Status */}
      <div className="flex items-center gap-4">
        {/* Connection Indicator */}
        <div className={`flex items-center gap-2 ${getConnectionColor()}`}>
          {getConnectionIcon()}
          <span className="text-gray-600 dark:text-gray-400">
            {connectionStatus.isConnected ? (
              <>
                Connected to {connectionStatus.serverName}
                {connectionStatus.latency && (
                  <span className="ml-1 text-gray-500">
                    ({connectionStatus.latency}ms)
                  </span>
                )}
              </>
            ) : (
              'Disconnected'
            )}
          </span>
        </div>

        {/* Transfer Status */}
        {(transferStatus.activeUploads > 0 || transferStatus.activeDownloads > 0) && (
          <>
            <div className="w-px h-4 bg-gray-300 dark:bg-dark-border" />
            <div className="flex items-center gap-3">
              {transferStatus.activeUploads > 0 && (
                <div className="flex items-center gap-1 text-blue-500">
                  <Upload className="w-3 h-3" />
                  <span className="text-gray-600 dark:text-gray-400">
                    {transferStatus.activeUploads} ({formatSpeed(transferStatus.uploadSpeed)})
                  </span>
                </div>
              )}
              
              {transferStatus.activeDownloads > 0 && (
                <div className="flex items-center gap-1 text-green-500">
                  <Download className="w-3 h-3" />
                  <span className="text-gray-600 dark:text-gray-400">
                    {transferStatus.activeDownloads} ({formatSpeed(transferStatus.downloadSpeed)})
                  </span>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Center Section - Activity Indicator */}
      <div className="flex items-center gap-3">
        {(transferStatus.activeUploads > 0 || transferStatus.activeDownloads > 0) && (
          <div className="flex items-center gap-2">
            <Activity className="w-3 h-3 text-primary-500 animate-pulse" />
            <span className="text-gray-500 dark:text-gray-500">
              Active transfers
            </span>
          </div>
        )}
      </div>

      {/* Right Section - System Status */}
      <div className="flex items-center gap-4">
        {/* Last Sync */}
        <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
          <Clock className="w-3 h-3" />
          <span>
            Last sync: {formatDistanceToNow(lastSync, { addSuffix: true })}
          </span>
        </div>

        <div className="w-px h-4 bg-gray-300 dark:bg-dark-border" />

        {/* Storage Status */}
        <div className="flex items-center gap-2">
          <HardDrive className="w-3 h-3 text-gray-500" />
          <div className="flex items-center gap-2">
            <div className="w-24 h-1.5 bg-gray-200 dark:bg-dark-border rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all ${
                  storageStatus.percentage > 80 
                    ? 'bg-red-500' 
                    : storageStatus.percentage > 60 
                    ? 'bg-yellow-500' 
                    : 'bg-green-500'
                }`}
                style={{ width: `${storageStatus.percentage}%` }}
              />
            </div>
            <span className="text-gray-600 dark:text-gray-400">
              {formatBytes(storageStatus.used)} / {formatBytes(storageStatus.total)}
            </span>
          </div>
        </div>

        {/* Notifications */}
        {notifications > 0 && (
          <>
            <div className="w-px h-4 bg-gray-300 dark:bg-dark-border" />
            <div className="flex items-center gap-1">
              <AlertCircle className="w-3 h-3 text-yellow-500" />
              <span className="text-gray-600 dark:text-gray-400">
                {notifications} notification{notifications !== 1 ? 's' : ''}
              </span>
            </div>
          </>
        )}

        {/* System Status Indicator */}
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-gray-500 dark:text-gray-500">
            All systems operational
          </span>
        </div>
      </div>
    </div>
  );
};