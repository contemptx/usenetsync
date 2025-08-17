import { useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import toast from 'react-hot-toast';

export interface ShortcutDefinition {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  meta?: boolean;
  description: string;
  category: string;
  action: () => void;
  enabled?: boolean;
}

// Default keyboard shortcuts
const defaultShortcuts: ShortcutDefinition[] = [
  // Navigation
  {
    key: 'h',
    ctrl: true,
    description: 'Go to Dashboard',
    category: 'Navigation',
    action: () => window.location.href = '/'
  },
  {
    key: 'u',
    ctrl: true,
    description: 'Go to Upload',
    category: 'Navigation',
    action: () => window.location.href = '/upload'
  },
  {
    key: 'd',
    ctrl: true,
    shift: true,
    description: 'Go to Download',
    category: 'Navigation',
    action: () => window.location.href = '/download'
  },
  {
    key: 's',
    ctrl: true,
    shift: true,
    description: 'Go to Shares',
    category: 'Navigation',
    action: () => window.location.href = '/shares'
  },
  {
    key: ',',
    ctrl: true,
    description: 'Open Settings',
    category: 'Navigation',
    action: () => window.location.href = '/settings'
  },
  
  // File Operations
  {
    key: 'n',
    ctrl: true,
    description: 'New Upload',
    category: 'File Operations',
    action: () => {
      const uploadInput = document.querySelector<HTMLInputElement>('input[type="file"]');
      uploadInput?.click();
    }
  },
  {
    key: 'o',
    ctrl: true,
    description: 'Open File',
    category: 'File Operations',
    action: () => {
      toast('Opening file...');
    }
  },
  {
    key: 's',
    ctrl: true,
    description: 'Create Share',
    category: 'File Operations',
    action: () => {
      toast('Creating share...');
    }
  },
  {
    key: 'Delete',
    description: 'Delete Selected',
    category: 'File Operations',
    action: () => {
      if (confirm('Delete selected items?')) {
        toast('Items deleted');
      }
    }
  },
  
  // Edit Operations
  {
    key: 'c',
    ctrl: true,
    description: 'Copy',
    category: 'Edit',
    action: () => {
      document.execCommand('copy');
      toast.success('Copied to clipboard');
    }
  },
  {
    key: 'v',
    ctrl: true,
    description: 'Paste',
    category: 'Edit',
    action: () => {
      document.execCommand('paste');
    }
  },
  {
    key: 'x',
    ctrl: true,
    description: 'Cut',
    category: 'Edit',
    action: () => {
      document.execCommand('cut');
      toast.success('Cut to clipboard');
    }
  },
  {
    key: 'a',
    ctrl: true,
    description: 'Select All',
    category: 'Edit',
    action: () => {
      document.execCommand('selectAll');
    }
  },
  {
    key: 'z',
    ctrl: true,
    description: 'Undo',
    category: 'Edit',
    action: () => {
      document.execCommand('undo');
    }
  },
  {
    key: 'y',
    ctrl: true,
    description: 'Redo',
    category: 'Edit',
    action: () => {
      document.execCommand('redo');
    }
  },
  
  // View Operations
  {
    key: 'f',
    ctrl: true,
    description: 'Search',
    category: 'View',
    action: () => {
      const searchInput = document.querySelector<HTMLInputElement>('input[type="search"], input[placeholder*="Search"]');
      searchInput?.focus();
    }
  },
  {
    key: 'r',
    ctrl: true,
    description: 'Refresh',
    category: 'View',
    action: () => {
      window.location.reload();
    }
  },
  {
    key: '+',
    ctrl: true,
    description: 'Zoom In',
    category: 'View',
    action: () => {
      document.body.style.zoom = `${(parseFloat(document.body.style.zoom || '1') * 1.1)}`;
    }
  },
  {
    key: '-',
    ctrl: true,
    description: 'Zoom Out',
    category: 'View',
    action: () => {
      document.body.style.zoom = `${(parseFloat(document.body.style.zoom || '1') * 0.9)}`;
    }
  },
  {
    key: '0',
    ctrl: true,
    description: 'Reset Zoom',
    category: 'View',
    action: () => {
      document.body.style.zoom = '1';
    }
  },
  
  // Application
  {
    key: 'F1',
    description: 'Help',
    category: 'Application',
    action: () => {
      toast('Opening help...');
    }
  },
  {
    key: 'F11',
    description: 'Toggle Fullscreen',
    category: 'Application',
    action: () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
      } else {
        document.exitFullscreen();
      }
    }
  },
  {
    key: 'Escape',
    description: 'Cancel/Close',
    category: 'Application',
    action: () => {
      // Close any open modals or dialogs
      const modal = document.querySelector('[role="dialog"]');
      if (modal) {
        const closeButton = modal.querySelector<HTMLButtonElement>('[aria-label="Close"]');
        closeButton?.click();
      }
    }
  },
  {
    key: '?',
    shift: true,
    description: 'Show Shortcuts',
    category: 'Application',
    action: () => {
      // Would show shortcuts modal
      toast('Keyboard Shortcuts:\nCtrl+H - Dashboard\nCtrl+U - Upload\nCtrl+F - Search\nF1 - Help');
    }
  }
];

export const useKeyboardShortcuts = (customShortcuts?: ShortcutDefinition[]) => {
  const shortcuts = useRef<ShortcutDefinition[]>([...defaultShortcuts, ...(customShortcuts || [])]);
  const isInputFocused = useRef(false);

  // Check if user is typing in an input field
  const checkInputFocus = useCallback(() => {
    const activeElement = document.activeElement;
    const isInput = activeElement instanceof HTMLInputElement ||
                   activeElement instanceof HTMLTextAreaElement ||
                   activeElement?.getAttribute('contenteditable') === 'true';
    isInputFocused.current = isInput;
  }, []);

  // Match shortcut based on key event
  const matchShortcut = useCallback((event: KeyboardEvent): ShortcutDefinition | undefined => {
    return shortcuts.current.find(shortcut => {
      const keyMatch = shortcut.key.toLowerCase() === event.key.toLowerCase() ||
                      shortcut.key === event.code;
      const ctrlMatch = shortcut.ctrl ? (event.ctrlKey || event.metaKey) : !event.ctrlKey && !event.metaKey;
      const altMatch = shortcut.alt ? event.altKey : !event.altKey;
      const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
      const metaMatch = shortcut.meta ? event.metaKey : !shortcut.ctrl && !event.metaKey;
      
      return keyMatch && ctrlMatch && altMatch && shiftMatch && metaMatch && shortcut.enabled !== false;
    });
  }, []);

  // Handle keyboard events
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    checkInputFocus();
    
    // Don't trigger shortcuts when typing in inputs (unless it's a global shortcut like F1)
    if (isInputFocused.current && !['F1', 'F11', 'Escape'].includes(event.key)) {
      return;
    }

    const matchedShortcut = matchShortcut(event);
    
    if (matchedShortcut) {
      event.preventDefault();
      event.stopPropagation();
      
      try {
        matchedShortcut.action();
      } catch (error) {
        console.error('Error executing shortcut:', error);
        toast.error('Failed to execute shortcut');
      }
    }
  }, [checkInputFocus, matchShortcut]);

  // Set up event listeners
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('focusin', checkInputFocus);
    document.addEventListener('focusout', checkInputFocus);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('focusin', checkInputFocus);
      document.removeEventListener('focusout', checkInputFocus);
    };
  }, [handleKeyDown, checkInputFocus]);

  // Add or update a shortcut
  const addShortcut = useCallback((shortcut: ShortcutDefinition) => {
    const existingIndex = shortcuts.current.findIndex(s => 
      s.key === shortcut.key &&
      s.ctrl === shortcut.ctrl &&
      s.alt === shortcut.alt &&
      s.shift === shortcut.shift
    );
    
    if (existingIndex >= 0) {
      shortcuts.current[existingIndex] = shortcut;
    } else {
      shortcuts.current.push(shortcut);
    }
  }, []);

  // Remove a shortcut
  const removeShortcut = useCallback((key: string, modifiers?: { ctrl?: boolean; alt?: boolean; shift?: boolean }) => {
    shortcuts.current = shortcuts.current.filter(s => 
      !(s.key === key &&
        s.ctrl === modifiers?.ctrl &&
        s.alt === modifiers?.alt &&
        s.shift === modifiers?.shift)
    );
  }, []);

  // Enable/disable a shortcut
  const toggleShortcut = useCallback((key: string, enabled: boolean, modifiers?: { ctrl?: boolean; alt?: boolean; shift?: boolean }) => {
    const shortcut = shortcuts.current.find(s => 
      s.key === key &&
      s.ctrl === modifiers?.ctrl &&
      s.alt === modifiers?.alt &&
      s.shift === modifiers?.shift
    );
    
    if (shortcut) {
      shortcut.enabled = enabled;
    }
  }, []);

  // Get all shortcuts grouped by category
  const getShortcutsByCategory = useCallback(() => {
    const grouped: Record<string, ShortcutDefinition[]> = {};
    
    shortcuts.current.forEach(shortcut => {
      if (!grouped[shortcut.category]) {
        grouped[shortcut.category] = [];
      }
      grouped[shortcut.category].push(shortcut);
    });
    
    return grouped;
  }, []);

  // Format shortcut for display
  const formatShortcut = useCallback((shortcut: ShortcutDefinition): string => {
    const parts: string[] = [];
    
    if (shortcut.ctrl) parts.push('Ctrl');
    if (shortcut.alt) parts.push('Alt');
    if (shortcut.shift) parts.push('Shift');
    if (shortcut.meta) parts.push('Cmd');
    
    parts.push(shortcut.key.length === 1 ? shortcut.key.toUpperCase() : shortcut.key);
    
    return parts.join('+');
  }, []);

  return {
    addShortcut,
    removeShortcut,
    toggleShortcut,
    getShortcutsByCategory,
    formatShortcut,
    shortcuts: shortcuts.current
  };
};