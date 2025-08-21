import React, { useState, useCallback } from 'react';
import { 
  CheckSquare, 
  Square, 
  MinusSquare,
  Download,
  Trash2,
  Share2,
  Archive,
  Move,
  Copy,
  X
} from 'lucide-react';
import toast from 'react-hot-toast';

export interface BatchItem {
  id: string;
  name: string;
  type: 'file' | 'folder';
  size?: number;
  path: string;
  modifiedAt?: Date;
}

interface BatchOperationsProps {
  items: BatchItem[];
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
  onBatchAction?: (action: string, items: BatchItem[]) => Promise<void>;
}

export const BatchOperations: React.FC<BatchOperationsProps> = ({
  items,
  selectedIds,
  onSelectionChange,
  onBatchAction
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState<string | null>(null);

  const selectedItems = items.filter(item => selectedIds.has(item.id));
  const allSelected = items.length > 0 && selectedIds.size === items.length;
  const someSelected = selectedIds.size > 0 && selectedIds.size < items.length;

  const toggleSelectAll = () => {
    if (allSelected) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(items.map(item => item.id)));
    }
    };

  const handleBatchAction = async (action: string) => {
    if (selectedItems.length === 0) {
      toast.error('No items selected');
      return;
    }

    // Show confirmation for destructive actions
    if (['delete', 'move'].includes(action)) {
      setShowConfirmDialog(action);
      return;
    }

    await executeBatchAction(action);
  };

  const executeBatchAction = async (action: string) => {
    setIsProcessing(true);
    setShowConfirmDialog(null);

    try {
      if (onBatchAction) {
        await onBatchAction(action, selectedItems);
      } else {
        // Default handlers
        switch (action) {
          case 'download':
            toast.success(`Downloading ${selectedItems.length} items...`);
            break;
          case 'share':
            toast.success(`Creating share for ${selectedItems.length} items...`);
            break;
          case 'archive':
            toast.success(`Archiving ${selectedItems.length} items...`);
            break;
          case 'delete':
            toast.success(`Deleted ${selectedItems.length} items`);
            onSelectionChange(new Set());
            break;
          case 'copy':
            toast.success(`Copied ${selectedItems.length} items to clipboard`);
            break;
          case 'move':
            toast.success(`Moving ${selectedItems.length} items...`);
            onSelectionChange(new Set());
            break;
          default:
            toast.error(`Unknown action: ${action}`);
        }
      }
    } catch (error) {
      toast.error(`Failed to ${action} items`);
      console.error(`Batch ${action} failed:`, error);
    } finally {
      setIsProcessing(false);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const getTotalSize = () => {
    return selectedItems.reduce((sum, item) => sum + (item.size || 0), 0);
  };

  if (items.length === 0) {
    return null;
  }

  return (
    <>
      {/* Batch Actions Bar */}
      {selectedIds.size > 0 && (
        <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
                {selectedIds.size} item{selectedIds.size !== 1 ? 's' : ''} selected
              </span>
              {getTotalSize() > 0 && (
                <span className="text-sm text-primary-600 dark:text-primary-400">
                  ({formatFileSize(getTotalSize())})
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleBatchAction('download')}
                disabled={isProcessing}
                className="px-3 py-1.5 bg-white dark:bg-dark-surface text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-border transition-colors flex items-center gap-2 text-sm"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
              
              <button
                onClick={() => handleBatchAction('share')}
                disabled={isProcessing}
                className="px-3 py-1.5 bg-white dark:bg-dark-surface text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-border transition-colors flex items-center gap-2 text-sm"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>
              
              <button
                onClick={() => handleBatchAction('archive')}
                disabled={isProcessing}
                className="px-3 py-1.5 bg-white dark:bg-dark-surface text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-border transition-colors flex items-center gap-2 text-sm"
              >
                <Archive className="w-4 h-4" />
                Archive
              </button>
              
              <button
                onClick={() => handleBatchAction('copy')}
                disabled={isProcessing}
                className="px-3 py-1.5 bg-white dark:bg-dark-surface text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-border transition-colors flex items-center gap-2 text-sm"
              >
                <Copy className="w-4 h-4" />
                Copy
              </button>
              
              <button
                onClick={() => handleBatchAction('move')}
                disabled={isProcessing}
                className="px-3 py-1.5 bg-white dark:bg-dark-surface text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-border transition-colors flex items-center gap-2 text-sm"
              >
                <Move className="w-4 h-4" />
                Move
              </button>
              
              <div className="w-px h-6 bg-primary-200 dark:bg-primary-800 mx-1" />
              
              <button
                onClick={() => handleBatchAction('delete')}
                disabled={isProcessing}
                className="px-3 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2 text-sm"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
              
              <button
                onClick={() => onSelectionChange(new Set())}
                className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Select All Checkbox */}
      <div className="flex items-center gap-2 p-2">
        <button
          onClick={toggleSelectAll}
          className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
        >
          {allSelected ? (
            <CheckSquare className="w-4 h-4 text-primary-500" />
          ) : someSelected ? (
            <MinusSquare className="w-4 h-4 text-primary-500" />
          ) : (
            <Square className="w-4 h-4" />
          )}
          Select All
        </button>
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Confirm {showConfirmDialog === 'delete' ? 'Deletion' : 'Move'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Are you sure you want to {showConfirmDialog} {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''}?
              {showConfirmDialog === 'delete' && ' This action cannot be undone.'}
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowConfirmDialog(null)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => executeBatchAction(showConfirmDialog)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  showConfirmDialog === 'delete'
                    ? 'bg-red-500 text-white hover:bg-red-600'
                    : 'bg-primary-500 text-white hover:bg-primary-600'
                }`}
              >
                {showConfirmDialog === 'delete' ? 'Delete' : 'Move'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Hook for managing batch selection
export const useBatchSelection = <T extends { id: string }>(items: T[]) => {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const toggleSelection = useCallback((itemId: string) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedIds(new Set(items.map(item => item.id)));
  }, [items]);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const selectRange = useCallback((startId: string, endId: string) => {
    const startIndex = items.findIndex(item => item.id === startId);
    const endIndex = items.findIndex(item => item.id === endId);
    
    if (startIndex === -1 || endIndex === -1) return;
    
    const [from, to] = startIndex < endIndex ? [startIndex, endIndex] : [endIndex, startIndex];
    const rangeIds = items.slice(from, to + 1).map(item => item.id);
    
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      rangeIds.forEach(id => newSet.add(id));
      return newSet;
    });
  }, [items]);

  const isSelected = useCallback((itemId: string) => {
    return selectedIds.has(itemId);
  }, [selectedIds]);

  const selectedItems = items.filter(item => selectedIds.has(item.id));

  return {
    selectedIds,
    selectedItems,
    setSelectedIds,
    toggleSelection,
    selectAll,
    clearSelection,
    selectRange,
    isSelected,
    hasSelection: selectedIds.size > 0,
    selectionCount: selectedIds.size
  };
};