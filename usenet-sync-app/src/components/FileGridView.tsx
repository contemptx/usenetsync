import React, { useState, useMemo } from 'react';
import { 
  Grid, 
  List, 
  Folder, 
  File, 
  Image, 
  Video, 
  Music, 
  Archive,
  FileText,
  Code,
  Download,
  Share2,
  Trash2,
  MoreVertical,
  Check
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useContextMenu } from './ContextMenu';
import { useBatchSelection } from './BatchOperations';

interface FileItem {
  id: string;
  name: string;
  type: 'file' | 'folder';
  size?: number;
  modifiedAt: Date;
  extension?: string;
  thumbnail?: string;
  selected?: boolean;
}

interface FileGridViewProps {
  files: FileItem[];
  viewMode?: 'grid' | 'list';
  onViewModeChange?: (mode: 'grid' | 'list') => void;
  onFileSelect?: (file: FileItem) => void;
  onFileOpen?: (file: FileItem) => void;
  onBatchAction?: (action: string, files: FileItem[]) => void;
  gridSize?: 'small' | 'medium' | 'large';
}

export const FileGridView: React.FC<FileGridViewProps> = ({
  files,
  viewMode = 'grid',
  onViewModeChange,
  onFileSelect,
  onFileOpen,
  onBatchAction,
  gridSize = 'medium'
}) => {
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'date'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const { showContextMenu } = useContextMenu();
  const {
    selectedIds,
    toggleSelection,
    selectRange,
    isSelected,
    clearSelection,
    selectedItems
  } = useBatchSelection(files);
  
  const [lastSelectedId, setLastSelectedId] = useState<string | null>(null);

  // Sort files
  const sortedFiles = useMemo(() => {
    const sorted = [...files].sort((a, b) => {
      let comparison = 0;
      
      // Folders first
      if (a.type !== b.type) {
        return a.type === 'folder' ? -1 : 1;
      }
      
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'size':
          comparison = (a.size || 0) - (b.size || 0);
          break;
        case 'date':
          comparison = a.modifiedAt.getTime() - b.modifiedAt.getTime();
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });
    
    return sorted;
  }, [files, sortBy, sortOrder]);

  const getFileIcon = (file: FileItem) => {
    if (file.type === 'folder') return Folder;
    
    const ext = file.extension?.toLowerCase();
    if (!ext) return File;
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) return Image;
    if (['mp4', 'avi', 'mkv', 'mov', 'webm'].includes(ext)) return Video;
    if (['mp3', 'wav', 'flac', 'ogg', 'm4a'].includes(ext)) return Music;
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return Archive;
    if (['txt', 'md', 'doc', 'docx', 'pdf'].includes(ext)) return FileText;
    if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp'].includes(ext)) return Code;
    
    return File;
  };

  const getGridSizeClasses = () => {
    switch (gridSize) {
      case 'small':
        return 'w-24 h-24';
      case 'large':
        return 'w-40 h-40';
      default:
        return 'w-32 h-32';
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

  const handleFileClick = (file: FileItem, event: React.MouseEvent) => {
    if (event.shiftKey && lastSelectedId) {
      // Range selection
      selectRange(lastSelectedId, file.id);
    } else if (event.ctrlKey || event.metaKey) {
      // Toggle selection
      toggleSelection(file.id);
      setLastSelectedId(file.id);
    } else {
      // Single selection
      clearSelection();
      toggleSelection(file.id);
      setLastSelectedId(file.id);
      onFileSelect?.(file);
    }
  };

  const handleFileDoubleClick = (file: FileItem) => {
    onFileOpen?.(file);
  };

  const handleContextMenu = (event: React.MouseEvent, file: FileItem) => {
    event.preventDefault();
    
    // If file not selected, select only this file
    if (!isSelected(file.id)) {
      clearSelection();
      toggleSelection(file.id);
    }
    
    showContextMenu(event, {
      type: file.type,
      items: selectedItems.length > 1 ? selectedItems : [file],
      onAction: (action) => {
        if (onBatchAction) {
          onBatchAction(action, selectedItems.length > 1 ? selectedItems : [file]);
        }
      }
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-dark-border">
        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-gray-100 dark:bg-dark-border rounded-lg p-1">
            <button
              onClick={() => onViewModeChange?.('grid')}
              className={`p-1.5 rounded transition-colors ${
                viewMode === 'grid'
                  ? 'bg-white dark:bg-dark-surface text-primary-500'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
              title="Grid view"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => onViewModeChange?.('list')}
              className={`p-1.5 rounded transition-colors ${
                viewMode === 'list'
                  ? 'bg-white dark:bg-dark-surface text-primary-500'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Sort Options */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-1.5 text-sm bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:text-white"
          >
            <option value="name">Name</option>
            <option value="size">Size</option>
            <option value="date">Date</option>
          </select>

          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
          >
            {sortOrder === 'asc' ? '↑' : '↓'}
          </button>

          {viewMode === 'grid' && (
            <select
              value={gridSize}
              onChange={(e) => {}}
              className="px-3 py-1.5 text-sm bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:text-white"
            >
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </select>
          )}
        </div>

        <div className="text-sm text-gray-500 dark:text-gray-400">
          {sortedFiles.length} items
          {selectedIds.size > 0 && ` • ${selectedIds.size} selected`}
        </div>
      </div>

      {/* File Display */}
      <div className="flex-1 overflow-auto p-4">
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-fill-32 gap-4">
            {sortedFiles.map((file) => {
              const Icon = getFileIcon(file);
              const selected = isSelected(file.id);
              
              return (
                <div
                  key={file.id}
                  className={`relative group cursor-pointer rounded-lg transition-all ${
                    selected
                      ? 'bg-primary-50 dark:bg-primary-900/20 ring-2 ring-primary-500'
                      : 'hover:bg-gray-50 dark:hover:bg-dark-border'
                  }`}
                  onClick={(e) => handleFileClick(file, e)}
                  onDoubleClick={() => handleFileDoubleClick(file)}
                  onContextMenu={(e) => handleContextMenu(e, file)}
                >
                  {/* Selection Checkbox */}
                  <div className={`absolute top-2 left-2 z-10 ${
                    selected || selectedIds.size > 0 ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                  } transition-opacity`}>
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                      selected
                        ? 'bg-primary-500 border-primary-500'
                        : 'bg-white dark:bg-dark-surface border-gray-300 dark:border-gray-600'
                    }`}>
                      {selected && <Check className="w-3 h-3 text-white" />}
                    </div>
                  </div>

                  {/* File Preview */}
                  <div className={`${getGridSizeClasses()} mx-auto p-4 flex items-center justify-center`}>
                    {file.thumbnail ? (
                      <img
                        src={file.thumbnail}
                        alt={file.name}
                        className="max-w-full max-h-full object-contain rounded"
                      />
                    ) : (
                      <Icon className={`${
                        gridSize === 'small' ? 'w-12 h-12' :
                        gridSize === 'large' ? 'w-20 h-20' :
                        'w-16 h-16'
                      } text-gray-400 dark:text-gray-500`} />
                    )}
                  </div>

                  {/* File Info */}
                  <div className="px-2 pb-2">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate" title={file.name}>
                      {file.name}
                    </p>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {file.type === 'folder' ? 'Folder' : formatFileSize(file.size)}
                      </span>
                      <button
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-200 dark:hover:bg-dark-surface rounded"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleContextMenu(e, file);
                        }}
                      >
                        <MoreVertical className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-dark-border">
                <th className="text-left p-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                  <div className="w-5 h-5" />
                </th>
                <th className="text-left p-2 text-xs font-medium text-gray-500 dark:text-gray-400">Name</th>
                <th className="text-left p-2 text-xs font-medium text-gray-500 dark:text-gray-400">Size</th>
                <th className="text-left p-2 text-xs font-medium text-gray-500 dark:text-gray-400">Modified</th>
                <th className="text-left p-2 text-xs font-medium text-gray-500 dark:text-gray-400"></th>
              </tr>
            </thead>
            <tbody>
              {sortedFiles.map((file) => {
                const Icon = getFileIcon(file);
                const selected = isSelected(file.id);
                
                return (
                  <tr
                    key={file.id}
                    className={`border-b border-gray-100 dark:border-dark-border cursor-pointer transition-colors ${
                      selected
                        ? 'bg-primary-50 dark:bg-primary-900/20'
                        : 'hover:bg-gray-50 dark:hover:bg-dark-border'
                    }`}
                    onClick={(e) => handleFileClick(file, e)}
                    onDoubleClick={() => handleFileDoubleClick(file)}
                    onContextMenu={(e) => handleContextMenu(e, file)}
                  >
                    <td className="p-2">
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                        selected
                          ? 'bg-primary-500 border-primary-500'
                          : 'bg-white dark:bg-dark-surface border-gray-300 dark:border-gray-600'
                      }`}>
                        {selected && <Check className="w-3 h-3 text-white" />}
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                        <span className="text-sm text-gray-900 dark:text-white">{file.name}</span>
                      </div>
                    </td>
                    <td className="p-2 text-sm text-gray-600 dark:text-gray-400">
                      {file.type === 'folder' ? '-' : formatFileSize(file.size)}
                    </td>
                    <td className="p-2 text-sm text-gray-600 dark:text-gray-400">
                      {formatDistanceToNow(file.modifiedAt, { addSuffix: true })}
                    </td>
                    <td className="p-2">
                      <button
                        className="p-1 hover:bg-gray-200 dark:hover:bg-dark-surface rounded"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleContextMenu(e, file);
                        }}
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};