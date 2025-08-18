import React from 'react';
import { Transfer } from '../../types';
import { SegmentProgress } from './SegmentProgress';
import { 
  Pause, 
  Play, 
  X, 
  Upload, 
  Download, 
  Clock, 
  Zap,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import clsx from 'clsx';
import { pauseTransfer, resumeTransfer, cancelTransfer } from '../../lib/tauri.ts';
import { useAppStore } from '../../stores/useAppStore';

interface TransferCardProps {
  transfer: Transfer;
}

export const TransferCard: React.FC<TransferCardProps> = ({ transfer }) => {
  const removeTransfer = useAppStore((state) => state.removeTransfer);
  const updateTransfer = useAppStore((state) => state.updateTransfer);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatSpeed = (bytesPerSecond: number): string => {
    return `${formatBytes(bytesPerSecond)}/s`;
  };

  const formatETA = (seconds: number): string => {
    if (!seconds || seconds === Infinity) return '--';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.round((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const handlePause = async () => {
    try {
      await pauseTransfer(transfer.id);
      updateTransfer(transfer.id, { status: 'paused' });
    } catch (error) {
      console.error('Failed to pause transfer:', error);
    }
  };

  const handleResume = async () => {
    try {
      await resumeTransfer(transfer.id);
      updateTransfer(transfer.id, { status: 'active' });
    } catch (error) {
      console.error('Failed to resume transfer:', error);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelTransfer(transfer.id);
      removeTransfer(transfer.id, transfer.type);
    } catch (error) {
      console.error('Failed to cancel transfer:', error);
    }
  };

  const percentage = transfer.totalSize > 0 
    ? (transfer.transferredSize / transfer.totalSize) * 100 
    : 0;

  const statusIcon = {
    pending: <Clock className="w-4 h-4 text-gray-500" />,
    active: <Zap className="w-4 h-4 text-blue-500 animate-pulse" />,
    paused: <Pause className="w-4 h-4 text-yellow-500" />,
    completed: <CheckCircle className="w-4 h-4 text-green-500" />,
    error: <AlertCircle className="w-4 h-4 text-red-500" />
  }[transfer.status];

  const statusColor = {
    pending: 'bg-gray-100 dark:bg-gray-800',
    active: 'bg-blue-50 dark:bg-blue-900/20',
    paused: 'bg-yellow-50 dark:bg-yellow-900/20',
    completed: 'bg-green-50 dark:bg-green-900/20',
    error: 'bg-red-50 dark:bg-red-900/20'
  }[transfer.status];

  return (
    <div className={clsx(
      'rounded-lg border transition-all duration-200',
      statusColor,
      'border-gray-200 dark:border-dark-border'
    )}>
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start gap-3">
            <div className={clsx(
              'p-2 rounded-lg',
              transfer.type === 'upload' 
                ? 'bg-blue-100 dark:bg-blue-900/30' 
                : 'bg-green-100 dark:bg-green-900/30'
            )}>
              {transfer.type === 'upload' ? (
                <Upload className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              ) : (
                <Download className="w-5 h-5 text-green-600 dark:text-green-400" />
              )}
            </div>
            
            <div className="flex-1">
              <h3 className="font-medium text-gray-900 dark:text-white truncate">
                {transfer.name}
              </h3>
              <div className="flex items-center gap-4 mt-1 text-sm text-gray-600 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  {statusIcon}
                  <span className="capitalize">{transfer.status}</span>
                </span>
                {transfer.status === 'active' && (
                  <>
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      {formatSpeed(transfer.speed)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatETA(transfer.eta)}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            {transfer.status === 'active' && (
              <button
                onClick={handlePause}
                className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-dark-surface transition-colors"
                title="Pause"
              >
                <Pause className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              </button>
            )}
            
            {transfer.status === 'paused' && (
              <button
                onClick={handleResume}
                className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-dark-surface transition-colors"
                title="Resume"
              >
                <Play className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              </button>
            )}
            
            <button
              onClick={handleCancel}
              className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-dark-surface transition-colors"
              title="Cancel"
            >
              <X className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>
        
        {/* Main progress bar */}
        <div className="mb-3">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600 dark:text-gray-400">
              {formatBytes(transfer.transferredSize)} / {formatBytes(transfer.totalSize)}
            </span>
            <span className="font-medium text-gray-900 dark:text-white">
              {percentage.toFixed(1)}%
            </span>
          </div>
          <div className="h-3 bg-gray-200 dark:bg-dark-border rounded-full overflow-hidden">
            <div 
              className={clsx(
                'h-full transition-all duration-300 ease-out',
                transfer.status === 'error' 
                  ? 'bg-red-500' 
                  : transfer.status === 'completed'
                  ? 'bg-green-500'
                  : 'bg-primary-500'
              )}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
        
        {/* Segment progress visualization */}
        {transfer.segments.length > 0 && (
          <SegmentProgress segments={transfer.segments} />
        )}
        
        {/* Error message */}
        {transfer.error && (
          <div className="mt-3 p-2 bg-red-100 dark:bg-red-900/30 rounded text-sm text-red-700 dark:text-red-400">
            {transfer.error}
          </div>
        )}
      </div>
    </div>
  );
};