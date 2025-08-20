import React, { useState, useCallback, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import { FileNode } from '../types';
import { 
  Folder, 
  FolderOpen, 
  File, 
  ChevronRight, 
  ChevronDown,
  CheckSquare,
  Square
} from 'lucide-react';
import clsx from 'clsx';
import { useAppStore } from '../stores/useAppStore';

interface FileTreeProps {
  data: FileNode;
  onSelect?: (node: FileNode) => void;
  selectable?: boolean;
  className?: string;
}

interface TreeNode {
  data: FileNode;
  isLeaf: boolean;
  isOpenByDefault: boolean;
  nestingLevel: number;
}

const getNodeData = (
  node: FileNode,
  nestingLevel: number
): TreeNode => ({
  data: node,
  isLeaf: node.type === 'file' || !node.children?.length,
  isOpenByDefault: false,
  nestingLevel,
});

function* treeWalker(root: FileNode): any {
  const stack: TreeNode[] = [getNodeData(root, 0)];

  while (stack.length !== 0) {
    const node = stack.pop()!;
    yield node;

    if (node.data.children && node.isOpenByDefault) {
      for (let i = node.data.children.length - 1; i >= 0; i--) {
        stack.push(getNodeData(
          node.data.children[i],
          node.nestingLevel + 1
        ));
      }
    }
  }
}

export const FileTree: React.FC<FileTreeProps> = ({ 
  data, 
  onSelect, 
  selectable = false,
  className 
}) => {
  const [openNodes, setOpenNodes] = useState<Set<string>>(new Set());
  const selectedFiles = useAppStore((state) => state.selectedFiles);
  const toggleFileSelection = useAppStore((state) => state.toggleFileSelection);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const toggleNode = useCallback((nodeId: string) => {
    setOpenNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  const isSelected = useCallback((node: FileNode): boolean => {
    return selectedFiles.some(f => f.id === node.id);
  }, [selectedFiles]);

  const Node = ({ data: treeNode, isOpen, style, toggle }: any) => {
    const node = treeNode.data as FileNode;
    const isNodeOpen = openNodes.has(node.id);
    const isNodeSelected = isSelected(node);
    const hasChildren = node.children && node.children.length > 0;

    const handleToggle = (e: React.MouseEvent) => {
      e.stopPropagation();
      if (hasChildren) {
        toggleNode(node.id);
        toggle();
      }
    };

    const handleSelect = (e: React.MouseEvent) => {
      e.stopPropagation();
      if (selectable) {
        toggleFileSelection(node);
      }
      onSelect?.(node);
    };

    return (
      <div 
        style={style} 
        className={clsx(
          'flex items-center py-1 px-2 hover:bg-gray-100 dark:hover:bg-dark-surface cursor-pointer transition-colors',
          isNodeSelected && 'bg-primary-50 dark:bg-primary-900/20'
        )}
        onClick={handleSelect}
      >
        <div 
          className="flex items-center"
          style={{ paddingLeft: `${treeNode.nestingLevel * 20}px` }}
        >
          {/* Expand/Collapse Icon */}
          {hasChildren && (
            <button
              onClick={handleToggle}
              className="p-0.5 mr-1 hover:bg-gray-200 dark:hover:bg-dark-border rounded"
            >
              {isNodeOpen ? (
                <ChevronDown className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              )}
            </button>
          )}
          
          {!hasChildren && (
            <div className="w-5 mr-1" />
          )}

          {/* Selection Checkbox */}
          {selectable && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleFileSelection(node);
              }}
              className="mr-2"
            >
              {isNodeSelected ? (
                <CheckSquare className="w-4 h-4 text-primary-500" />
              ) : (
                <Square className="w-4 h-4 text-gray-400" />
              )}
            </button>
          )}

          {/* File/Folder Icon */}
          {node.type === 'folder' ? (
            isNodeOpen ? (
              <FolderOpen className="w-5 h-5 text-yellow-600 mr-2" />
            ) : (
              <Folder className="w-5 h-5 text-yellow-600 mr-2" />
            )
          ) : (
            <File className="w-5 h-5 text-gray-500 mr-2" />
          )}

          {/* Name */}
          <span className="text-sm font-medium text-gray-900 dark:text-white mr-3">
            {node.name}
          </span>

          {/* Size */}
          {node.type === 'file' && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatBytes(node.size)}
            </span>
          )}

          {/* Folder Info */}
          {node.type === 'folder' && node.children && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {node.children.length} items
            </span>
          )}

          {/* Progress Indicator */}
          {node.progress !== undefined && node.progress > 0 && node.progress < 100 && (
            <div className="ml-3 w-20 h-1.5 bg-gray-200 dark:bg-dark-border rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary-500 transition-all duration-300"
                style={{ width: `${node.progress}%` }}
              />
            </div>
          )}
        </div>
      </div>
    );
  };

  const flattenTree = useCallback((node: FileNode, level = 0): TreeNode[] => {
    const result: TreeNode[] = [];
    result.push(getNodeData(node, level));
    
    if (node.children && openNodes.has(node.id)) {
      node.children.forEach(child => {
        result.push(...flattenTree(child, level + 1));
      });
    }
    
    return result;
  }, [openNodes]);

  const treeData = useMemo(() => flattenTree(data), [data, flattenTree]);

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const treeNode = treeData[index];
    if (!treeNode) return null;
    
    return (
      <Node 
        data={treeNode} 
        isOpen={openNodes.has(treeNode.data.id)}
        style={style}
        toggle={() => toggleNode(treeNode.data.id)}
      />
    );
  };

  return (
    <div className={clsx('h-full w-full overflow-hidden', className)}>
      <List
        height={600}
        itemCount={treeData.length}
        itemSize={32}
        width="100%"
      >
        {Row}
      </List>
    </div>
  );
};