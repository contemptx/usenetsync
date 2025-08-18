import React, { useState, useEffect } from 'react';
import { 
  History, 
  Clock, 
  User, 
  Download, 
  RotateCcw,
  ChevronDown,
  ChevronRight,
  HardDrive,
  Diff
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface FileVersion {
  version_id: string;
  file_name: string;
  file_path: string;
  share_id: string;
  file_hash: string;
  file_size: number;
  version_number: number;
  created_at: string;
  created_by: string;
  parent_version_id?: string;
  changes_description?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

interface VersionHistoryProps {
  filePath: string;
  currentVersion?: string;
  onVersionSelect?: (version: FileVersion) => void;
  onRollback?: (versionId: string) => void;
  onDownload?: (versionId: string) => void;
  onCompare?: (version1: string, version2: string) => void;
}

export const VersionHistory: React.FC<VersionHistoryProps> = ({
  filePath,
  currentVersion,
  onVersionSelect,
  onRollback,
  onDownload,
  onCompare
}) => {
  const [versions, setVersions] = useState<FileVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedVersions, setExpandedVersions] = useState<Set<string>>(new Set());
  const [selectedVersions, setSelectedVersions] = useState<Set<string>>(new Set());
  const [compareMode, setCompareMode] = useState(false);

  useEffect(() => {
    loadVersionHistory();
  }, [filePath]);

  const loadVersionHistory = async () => {
    setLoading(true);
    try {
      // This would call the Tauri backend
      // const history = await getFileVersions(filePath);
      
      // TODO: Implement real version history API
      setVersions([]);
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
      // TODO: Implement real version history API
    } catch (error) {
      console.error('Failed to load version history:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleVersionExpanded = (versionId: string) => {
    const newExpanded = new Set(expandedVersions);
    if (newExpanded.has(versionId)) {
      newExpanded.delete(versionId);
    } else {
      newExpanded.add(versionId);
    }
    setExpandedVersions(newExpanded);
  };

  const toggleVersionSelection = (versionId: string) => {
    const newSelected = new Set(selectedVersions);
    if (newSelected.has(versionId)) {
      newSelected.delete(versionId);
    } else {
      newSelected.add(versionId);
      if (newSelected.size > 2) {
        // Only allow 2 versions for comparison
        const first = newSelected.values().next().value;
        newSelected.delete(first);
      }
    }
    setSelectedVersions(newSelected);
  };

  const handleCompare = () => {
    if (selectedVersions.size === 2) {
      const [v1, v2] = Array.from(selectedVersions);
      onCompare?.(v1, v2);
    }
  };

  const formatFileSize = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(2)} ${units[unitIndex]}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Version History
          </h3>
          <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-dark-border rounded-full text-gray-600 dark:text-gray-400">
            {versions.length} versions
          </span>
        </div>
        
        {/* Compare Mode Toggle */}
        <div className="flex items-center gap-2">
          {compareMode && selectedVersions.size === 2 && (
            <button
              onClick={handleCompare}
              className="px-3 py-1 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors text-sm"
            >
              Compare Selected
            </button>
          )}
          <button
            onClick={() => {
              setCompareMode(!compareMode);
              setSelectedVersions(new Set());
            }}
            className={`px-3 py-1 rounded-lg transition-colors text-sm ${
              compareMode 
                ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                : 'bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-surface'
            }`}
          >
            <Diff className="w-4 h-4 inline mr-1" />
            Compare
          </button>
        </div>
      </div>

      {/* Version Timeline */}
      <div className="relative">
        {/* Timeline Line */}
        <div className="absolute left-6 top-8 bottom-0 w-0.5 bg-gray-200 dark:bg-dark-border"></div>
        
        {/* Version Items */}
        <div className="space-y-4">
          {versions.map((version, index) => (
            <div key={version.version_id} className="relative">
              {/* Timeline Dot */}
              <div className={`absolute left-5 w-3 h-3 rounded-full border-2 ${
                version.version_id === currentVersion
                  ? 'bg-primary-500 border-primary-500'
                  : 'bg-white dark:bg-dark-bg border-gray-300 dark:border-dark-border'
              }`}></div>
              
              {/* Version Card */}
              <div className={`ml-12 bg-white dark:bg-dark-surface rounded-lg border ${
                version.version_id === currentVersion
                  ? 'border-primary-500'
                  : 'border-gray-200 dark:border-dark-border'
              } transition-all hover:shadow-md`}>
                {/* Version Header */}
                <div 
                  className="p-4 cursor-pointer"
                  onClick={() => !compareMode && toggleVersionExpanded(version.version_id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {/* Expand/Checkbox */}
                      {compareMode ? (
                        <input
                          type="checkbox"
                          checked={selectedVersions.has(version.version_id)}
                          onChange={(e) => {
                            e.stopPropagation();
                            toggleVersionSelection(version.version_id);
                          }}
                          className="mt-1 w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <button className="mt-1">
                          {expandedVersions.has(version.version_id) 
                            ? <ChevronDown className="w-4 h-4 text-gray-500" />
                            : <ChevronRight className="w-4 h-4 text-gray-500" />
                          }
                        </button>
                      )}
                      
                      {/* Version Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-gray-900 dark:text-white">
                            Version {version.version_number}
                          </span>
                          {version.tags?.map(tag => (
                            <span 
                              key={tag}
                              className="px-2 py-0.5 text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                          {version.version_id === currentVersion && (
                            <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-full">
                              Current
                            </span>
                          )}
                        </div>
                        
                        {version.changes_description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            {version.changes_description}
                          </p>
                        )}
                        
                        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {version.created_by}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDistanceToNow(new Date(version.created_at), { addSuffix: true })}
                          </span>
                          <span className="flex items-center gap-1">
                            <HardDrive className="w-3 h-3" />
                            {formatFileSize(version.file_size)}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Actions */}
                    {!compareMode && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDownload?.(version.version_id);
                          }}
                          className="p-2 text-gray-500 hover:text-primary-500 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
                          title="Download this version"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        {index > 0 && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onRollback?.(version.version_id);
                            }}
                            className="p-2 text-gray-500 hover:text-primary-500 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
                            title="Rollback to this version"
                          >
                            <RotateCcw className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Expanded Details */}
                {expandedVersions.has(version.version_id) && !compareMode && (
                  <div className="px-4 pb-4 border-t border-gray-200 dark:border-dark-border pt-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500 dark:text-gray-500">Share ID:</span>
                        <p className="font-mono text-gray-900 dark:text-white">{version.share_id}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-500">File:</span>
                        <p className="font-mono text-gray-900 dark:text-white truncate" title={version.file_hash}>
                          {version.file_hash}
                        </p>
                      </div>
                      {version.parent_version_id && (
                        <div>
                          <span className="text-gray-500 dark:text-gray-500">Parent Version:</span>
                          <p className="text-gray-900 dark:text-white">{version.parent_version_id}</p>
                        </div>
                      )}
                      <div>
                        <span className="text-gray-500 dark:text-gray-500">Version ID:</span>
                        <p className="font-mono text-gray-900 dark:text-white">{version.version_id}</p>
                      </div>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="mt-4 flex gap-2">
                      <button
                        onClick={() => onVersionSelect?.(version)}
                        className="px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors text-sm"
                      >
                        Use This Version
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};