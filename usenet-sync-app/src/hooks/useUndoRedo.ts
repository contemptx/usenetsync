import { useState, useCallback, useEffect } from 'react';

export interface Action {
  id: string;
  type: string;
  description: string;
  timestamp: Date;
  data: any;
  undo: () => Promise<void> | void;
  redo: () => Promise<void> | void;
}

interface UndoRedoOptions {
  maxHistorySize?: number;
  persistHistory?: boolean;
  storageKey?: string;
}

export const useUndoRedo = (options: UndoRedoOptions = {}) => {
  const {
    maxHistorySize = 50,
    persistHistory = false,
    storageKey = 'undo-redo-history'
  } = options;

  const [history, setHistory] = useState<Action[]>([]);
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [isUndoing, setIsUndoing] = useState(false);
  const [isRedoing, setIsRedoing] = useState(false);

  // Load history from storage if persistence is enabled
  useEffect(() => {
    if (persistHistory && typeof window !== 'undefined') {
      const savedHistory = localStorage.getItem(storageKey);
      if (savedHistory) {
        try {
          const parsed = JSON.parse(savedHistory);
          // Note: We can't restore functions from JSON, so this is limited
          // In a real app, you'd need to reconstruct actions based on type
          setHistory(parsed.history || []);
          setCurrentIndex(parsed.currentIndex || -1);
        } catch (error) {
          console.error('Failed to load undo/redo history:', error);
        }
      }
    }
  }, [persistHistory, storageKey]);

  // Save history to storage
  useEffect(() => {
    if (persistHistory && typeof window !== 'undefined') {
      const dataToSave = {
        history: history.map(action => ({
          ...action,
          undo: undefined,
          redo: undefined
        })),
        currentIndex
      };
      localStorage.setItem(storageKey, JSON.stringify(dataToSave));
    }
  }, [history, currentIndex, persistHistory, storageKey]);

  const canUndo = currentIndex >= 0;
  const canRedo = currentIndex < history.length - 1;

  const addAction = useCallback((action: Omit<Action, 'id' | 'timestamp'>) => {
    const newAction: Action = {
      ...action,
      id: Date.now().toString(),
      timestamp: new Date()
    };

    setHistory(prev => {
      // Remove any actions after current index (they're being replaced)
      const newHistory = prev.slice(0, currentIndex + 1);
      
      // Add new action
      newHistory.push(newAction);
      
      // Trim history if it exceeds max size
      if (newHistory.length > maxHistorySize) {
        return newHistory.slice(-maxHistorySize);
      }
      
      return newHistory;
    });
    
    setCurrentIndex(prev => Math.min(prev + 1, maxHistorySize - 1));
  }, [currentIndex, maxHistorySize]);

  const undo = useCallback(async () => {
    if (!canUndo || isUndoing) return;
    
    setIsUndoing(true);
    try {
      const action = history[currentIndex];
      await action.undo();
      setCurrentIndex(prev => prev - 1);
    } catch (error) {
      console.error('Undo failed:', error);
      throw error;
    } finally {
      setIsUndoing(false);
    }
  }, [canUndo, currentIndex, history, isUndoing]);

  const redo = useCallback(async () => {
    if (!canRedo || isRedoing) return;
    
    setIsRedoing(true);
    try {
      const action = history[currentIndex + 1];
      await action.redo();
      setCurrentIndex(prev => prev + 1);
    } catch (error) {
      console.error('Redo failed:', error);
      throw error;
    } finally {
      setIsRedoing(false);
    }
  }, [canRedo, currentIndex, history, isRedoing]);

  const clear = useCallback(() => {
    setHistory([]);
    setCurrentIndex(-1);
  }, []);

  const getHistory = useCallback(() => {
    return history.slice(0, currentIndex + 1);
  }, [history, currentIndex]);

  const getFuture = useCallback(() => {
    return history.slice(currentIndex + 1);
  }, [history, currentIndex]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Cmd/Ctrl + Z for undo
      if ((event.metaKey || event.ctrlKey) && event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        undo();
      }
      // Cmd/Ctrl + Shift + Z or Cmd/Ctrl + Y for redo
      else if (
        ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === 'z') ||
        ((event.metaKey || event.ctrlKey) && event.key === 'y')
      ) {
        event.preventDefault();
        redo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [undo, redo]);

  return {
    // Actions
    addAction,
    undo,
    redo,
    clear,
    
    // State
    canUndo,
    canRedo,
    isUndoing,
    isRedoing,
    history: getHistory(),
    future: getFuture(),
    currentAction: currentIndex >= 0 ? history[currentIndex] : null,
    
    // Info
    historySize: history.length,
    currentIndex
  };
};

// Helper function to create common actions
export const createAction = {
  fileOperation: (
    type: 'create' | 'delete' | 'rename' | 'move',
    data: any,
    undoFn: () => void,
    redoFn: () => void
  ): Omit<Action, 'id' | 'timestamp'> => ({
    type: `file.${type}`,
    description: `${type} ${data.name || 'file'}`,
    data,
    undo: undoFn,
    redo: redoFn
  }),

  textEdit: (
    data: { file: string; oldContent: string; newContent: string },
    undoFn: () => void,
    redoFn: () => void
  ): Omit<Action, 'id' | 'timestamp'> => ({
    type: 'text.edit',
    description: `Edit ${data.file}`,
    data,
    undo: undoFn,
    redo: redoFn
  }),

  settingsChange: (
    data: { setting: string; oldValue: any; newValue: any },
    undoFn: () => void,
    redoFn: () => void
  ): Omit<Action, 'id' | 'timestamp'> => ({
    type: 'settings.change',
    description: `Change ${data.setting}`,
    data,
    undo: undoFn,
    redo: redoFn
  })
};