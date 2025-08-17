import React, { useEffect, useRef, useState } from 'react';
import { 
  Copy, 
  Download, 
  Trash2, 
  Edit, 
  Share2, 
  Info, 
  FolderOpen,
  FileText,
  RotateCcw,
  History,
  Lock,
  Unlock,
  Archive,
  Eye,
  Link,
  Settings,
  ChevronRight
} from 'lucide-react';

export interface ContextMenuItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  shortcut?: string;
  disabled?: boolean;
  danger?: boolean;
  type?: 'separator';
  submenu?: ContextMenuItem[];
  onClick?: () => void;
}

interface ContextMenuProps {
  items: ContextMenuItem[];
  position: { x: number; y: number };
  onClose: () => void;
}

export const ContextMenu: React.FC<ContextMenuProps> = ({ items, position, onClose }) => {
  const menuRef = useRef<HTMLDivElement>(null);
  const [activeSubmenu, setActiveSubmenu] = useState<string | null>(null);
  const [submenuPosition, setSubmenuPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  // Adjust position to keep menu in viewport
  useEffect(() => {
    if (menuRef.current) {
      const rect = menuRef.current.getBoundingClientRect();
      const { innerWidth, innerHeight } = window;
      
      let adjustedX = position.x;
      let adjustedY = position.y;
      
      if (rect.right > innerWidth) {
        adjustedX = innerWidth - rect.width - 10;
      }
      
      if (rect.bottom > innerHeight) {
        adjustedY = innerHeight - rect.height - 10;
      }
      
      menuRef.current.style.left = `${adjustedX}px`;
      menuRef.current.style.top = `${adjustedY}px`;
    }
  }, [position]);

  const handleItemClick = (item: ContextMenuItem) => {
    if (item.disabled || item.type === 'separator') return;
    
    if (item.submenu) {
      setActiveSubmenu(activeSubmenu === item.id ? null : item.id);
    } else {
      item.onClick?.();
      onClose();
    }
  };

  const handleSubmenuHover = (item: ContextMenuItem, index: number) => {
    if (item.submenu && menuRef.current) {
      const itemElement = menuRef.current.children[index] as HTMLElement;
      if (itemElement) {
        const rect = itemElement.getBoundingClientRect();
        setSubmenuPosition({ x: rect.right, y: rect.top });
        setActiveSubmenu(item.id);
      }
    }
  };

  const renderMenuItem = (item: ContextMenuItem, index: number) => {
    if (item.type === 'separator') {
      return <div key={`sep-${index}`} className="h-px bg-gray-200 dark:bg-dark-border my-1" />;
    }

    const isActive = activeSubmenu === item.id;

    return (
      <button
        key={item.id}
        onClick={() => handleItemClick(item)}
        onMouseEnter={() => item.submenu && handleSubmenuHover(item, index)}
        onMouseLeave={() => !item.submenu && setActiveSubmenu(null)}
        disabled={item.disabled}
        className={`
          w-full px-3 py-2 flex items-center justify-between text-sm
          transition-colors rounded-md
          ${item.disabled 
            ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed' 
            : item.danger
              ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-border'
          }
          ${isActive ? 'bg-gray-100 dark:bg-dark-border' : ''}
        `}
      >
        <div className="flex items-center gap-3">
          {item.icon && (
            <span className={`w-4 h-4 ${item.danger ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'}`}>
              {item.icon}
            </span>
          )}
          <span>{item.label}</span>
        </div>
        
        <div className="flex items-center gap-2">
          {item.shortcut && (
            <span className="text-xs text-gray-400 dark:text-gray-600">
              {item.shortcut}
            </span>
          )}
          {item.submenu && (
            <ChevronRight className="w-3 h-3 text-gray-400" />
          )}
        </div>
      </button>
    );
  };

  return (
    <>
      <div
        ref={menuRef}
        className="fixed z-50 min-w-[200px] bg-white dark:bg-dark-surface rounded-lg shadow-lg border border-gray-200 dark:border-dark-border py-1"
        style={{ left: position.x, top: position.y }}
      >
        {items.map((item, index) => renderMenuItem(item, index))}
      </div>
      
      {/* Submenu */}
      {activeSubmenu && (
        <div
          className="fixed z-50 min-w-[180px] bg-white dark:bg-dark-surface rounded-lg shadow-lg border border-gray-200 dark:border-dark-border py-1"
          style={{ left: submenuPosition.x, top: submenuPosition.y }}
        >
          {items
            .find(item => item.id === activeSubmenu)
            ?.submenu?.map((subitem, index) => renderMenuItem(subitem, index))}
        </div>
      )}
    </>
  );
};

// Context menu hook for easy usage
export const useContextMenu = () => {
  const [menuState, setMenuState] = useState<{
    isOpen: boolean;
    position: { x: number; y: number };
    items: ContextMenuItem[];
  }>({
    isOpen: false,
    position: { x: 0, y: 0 },
    items: []
  });

  const openContextMenu = (
    event: React.MouseEvent,
    items: ContextMenuItem[]
  ) => {
    event.preventDefault();
    setMenuState({
      isOpen: true,
      position: { x: event.clientX, y: event.clientY },
      items
    });
  };

  const closeContextMenu = () => {
    setMenuState(prev => ({ ...prev, isOpen: false }));
  };

  return {
    menuState,
    openContextMenu,
    closeContextMenu
  };
};

// Pre-defined context menu templates
export const contextMenuTemplates = {
  file: (handlers: Record<string, () => void>): ContextMenuItem[] => [
    {
      id: 'open',
      label: 'Open',
      icon: <FolderOpen className="w-4 h-4" />,
      shortcut: 'Enter',
      onClick: handlers.open
    },
    {
      id: 'preview',
      label: 'Preview',
      icon: <Eye className="w-4 h-4" />,
      shortcut: 'Space',
      onClick: handlers.preview
    },
    { id: 'separator-1', label: '', type: 'separator' as const },
    {
      id: 'version',
      label: 'Version History',
      icon: <History className="w-4 h-4" />,
      shortcut: 'Ctrl+H',
      onClick: handlers.versions
    },
    {
      id: 'download',
      label: 'Download',
      icon: <Download className="w-4 h-4" />,
      shortcut: 'Ctrl+D',
      onClick: handlers.download
    },
    { id: 'separator-2', label: '', type: 'separator' as const },
    {
      id: 'share',
      label: 'Share',
      icon: <Share2 className="w-4 h-4" />,
      shortcut: 'Ctrl+S',
      submenu: [
        {
          id: 'share-public',
          label: 'Create Public Share',
          icon: <Unlock className="w-4 h-4" />,
          onClick: handlers.sharePublic
        },
        {
          id: 'share-private',
          label: 'Create Private Share',
          icon: <Lock className="w-4 h-4" />,
          onClick: handlers.sharePrivate
        },
        { id: 'separator-3', label: '', type: 'separator' as const },
        {
          id: 'copy-link',
          label: 'Copy Share Link',
          icon: <Link className="w-4 h-4" />,
          onClick: handlers.copyLink,
          disabled: !handlers.copyLink
        }
      ]
    },
    { id: 'separator-4', label: '', type: 'separator' as const },
    {
      id: 'rename',
      label: 'Rename',
      icon: <Edit className="w-4 h-4" />,
      shortcut: 'F2',
      onClick: handlers.rename
    },
    {
      id: 'copy',
      label: 'Copy',
      icon: <Copy className="w-4 h-4" />,
      shortcut: 'Ctrl+C',
      onClick: handlers.copy
    },
    {
      id: 'archive',
      label: 'Archive',
      icon: <Archive className="w-4 h-4" />,
      onClick: handlers.archive
    },
    { id: 'separator-5', label: '', type: 'separator' as const },
    {
      id: 'info',
      label: 'Properties',
      icon: <Info className="w-4 h-4" />,
      shortcut: 'Alt+Enter',
      onClick: handlers.info
    },
    { id: 'separator-6', label: '', type: 'separator' as const },
    {
      id: 'delete',
      label: 'Delete',
      icon: <Trash2 className="w-4 h-4" />,
      shortcut: 'Delete',
      danger: true,
      onClick: handlers.delete
    }
  ],
  
  folder: (handlers: Record<string, () => void>): ContextMenuItem[] => [
    {
      id: 'open',
      label: 'Open',
      icon: <FolderOpen className="w-4 h-4" />,
      shortcut: 'Enter',
      onClick: handlers.open
    },
    {
      id: 'open-new-tab',
      label: 'Open in New Tab',
      icon: <FileText className="w-4 h-4" />,
      onClick: handlers.openNewTab
    },
    { id: 'separator-7', label: '', type: 'separator' as const },
    {
      id: 'upload',
      label: 'Upload to Folder',
      icon: <Share2 className="w-4 h-4" />,
      onClick: handlers.upload
    },
    { id: 'separator-8', label: '', type: 'separator' as const },
    {
      id: 'rename',
      label: 'Rename',
      icon: <Edit className="w-4 h-4" />,
      shortcut: 'F2',
      onClick: handlers.rename
    },
    {
      id: 'copy',
      label: 'Copy',
      icon: <Copy className="w-4 h-4" />,
      shortcut: 'Ctrl+C',
      onClick: handlers.copy
    },
    { id: 'separator-9', label: '', type: 'separator' as const },
    {
      id: 'info',
      label: 'Properties',
      icon: <Info className="w-4 h-4" />,
      shortcut: 'Alt+Enter',
      onClick: handlers.info
    },
    { id: 'separator-10', label: '', type: 'separator' as const },
    {
      id: 'delete',
      label: 'Delete',
      icon: <Trash2 className="w-4 h-4" />,
      shortcut: 'Delete',
      danger: true,
      onClick: handlers.delete
    }
  ],
  
  share: (handlers: Record<string, () => void>): ContextMenuItem[] => [
    {
      id: 'download',
      label: 'Download',
      icon: <Download className="w-4 h-4" />,
      shortcut: 'Ctrl+D',
      onClick: handlers.download
    },
    {
      id: 'copy-id',
      label: 'Copy Share ID',
      icon: <Copy className="w-4 h-4" />,
      onClick: handlers.copyId
    },
    {
      id: 'copy-link',
      label: 'Copy Share Link',
      icon: <Link className="w-4 h-4" />,
      onClick: handlers.copyLink
    },
    { id: 'separator-11', label: '', type: 'separator' as const },
    {
      id: 'regenerate',
      label: 'Regenerate Share',
      icon: <RotateCcw className="w-4 h-4" />,
      onClick: handlers.regenerate
    },
    {
      id: 'settings',
      label: 'Share Settings',
      icon: <Settings className="w-4 h-4" />,
      onClick: handlers.settings
    },
    { id: 'separator-12', label: '', type: 'separator' as const },
    {
      id: 'info',
      label: 'Share Details',
      icon: <Info className="w-4 h-4" />,
      onClick: handlers.info
    },
    { id: 'separator-13', label: '', type: 'separator' as const },
    {
      id: 'revoke',
      label: 'Revoke Share',
      icon: <Trash2 className="w-4 h-4" />,
      danger: true,
      onClick: handlers.revoke
    }
  ]
};