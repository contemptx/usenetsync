import { useState, useCallback, useRef, DragEvent } from 'react';

export type DropZoneState = 'idle' | 'active' | 'reject';

interface DragItem {
  id: string;
  type: string;
  data: any;
}

interface UseDragDropOptions {
  accept?: string[];
  multiple?: boolean;
  maxSize?: number;
  maxFiles?: number;
  onDragEnter?: (items: DragItem[]) => void;
  onDragLeave?: () => void;
  onDrop?: (items: DragItem[], event: DragEvent) => void;
  onDropReject?: (reason: string) => void;
}

export const useDragDrop = (options: UseDragDropOptions = {}) => {
  const {
    accept = [],
    multiple = true,
    maxSize = Infinity,
    maxFiles = Infinity,
    onDragEnter,
    onDragLeave,
    onDrop,
    onDropReject
  } = options;

  const [isDragging, setIsDragging] = useState(false);
  const [dropZoneState, setDropZoneState] = useState<DropZoneState>('idle');
  const [draggedItems, setDraggedItems] = useState<DragItem[]>([]);
  const dragCounter = useRef(0);

  const validateFiles = (files: FileList): { valid: File[]; rejected: string[] } => {
    const valid: File[] = [];
    const rejected: string[] = [];

    Array.from(files).forEach(file => {
      // Check file count
      if (!multiple && valid.length >= 1) {
        rejected.push(`Only single file allowed`);
        return;
      }
      
      if (valid.length >= maxFiles) {
        rejected.push(`Maximum ${maxFiles} files allowed`);
        return;
      }

      // Check file type
      if (accept.length > 0) {
        const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
        const mimeType = file.type;
        
        const isAccepted = accept.some(pattern => {
          if (pattern.startsWith('.')) {
            return fileExt === pattern.toLowerCase();
          }
          if (pattern.includes('*')) {
            const regex = new RegExp(pattern.replace('*', '.*'));
            return regex.test(mimeType);
          }
          return mimeType === pattern;
        });

        if (!isAccepted) {
          rejected.push(`File type not accepted: ${file.name}`);
          return;
        }
      }

      // Check file size
      if (file.size > maxSize) {
        rejected.push(`File too large: ${file.name} (max ${formatBytes(maxSize)})`);
        return;
      }

      valid.push(file);
    });

    return { valid, rejected };
  };

  const handleDragEnter = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    dragCounter.current++;
    
    if (dragCounter.current === 1) {
      setIsDragging(true);
      
      // Check if we can accept the dragged items
      const items = Array.from(event.dataTransfer.items);
      let canAccept = true;
      
      if (!multiple && items.length > 1) {
        canAccept = false;
      }
      
      setDropZoneState(canAccept ? 'active' : 'reject');
      
      // Extract drag items
      const dragItems: DragItem[] = items.map((item, index) => ({
        id: `drag-${index}`,
        type: item.type || 'file',
        data: null // Can't access file data until drop
      }));
      
      setDraggedItems(dragItems);
      onDragEnter?.(dragItems);
    }
  }, [multiple, onDragEnter]);

  const handleDragLeave = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    dragCounter.current--;
    
    if (dragCounter.current === 0) {
      setIsDragging(false);
      setDropZoneState('idle');
      setDraggedItems([]);
      onDragLeave?.();
    }
  }, [onDragLeave]);

  const handleDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    // Set drop effect
    if (dropZoneState === 'active') {
      event.dataTransfer.dropEffect = 'copy';
    } else {
      event.dataTransfer.dropEffect = 'none';
    }
  }, [dropZoneState]);

  const handleDrop = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    dragCounter.current = 0;
    setIsDragging(false);
    setDropZoneState('idle');
    
    const files = event.dataTransfer.files;
    const { valid, rejected } = validateFiles(files);
    
    if (rejected.length > 0) {
      onDropReject?.(rejected.join(', '));
    }
    
    if (valid.length > 0) {
      const items: DragItem[] = valid.map((file, index) => ({
        id: `file-${Date.now()}-${index}`,
        type: 'file',
        data: file
      }));
      
      onDrop?.(items, event);
    }
    
    setDraggedItems([]);
  }, [validateFiles, onDrop, onDropReject]);

  const getRootProps = () => ({
    onDragEnter: handleDragEnter,
    onDragLeave: handleDragLeave,
    onDragOver: handleDragOver,
    onDrop: handleDrop
  });

  const getInputProps = () => ({
    type: 'file',
    multiple,
    accept: accept.join(','),
    style: { display: 'none' }
  });

  return {
    getRootProps,
    getInputProps,
    isDragging,
    dropZoneState,
    draggedItems
  };
};

// Draggable item hook
interface UseDraggableOptions {
  item: any;
  type: string;
  effectAllowed?: DataTransfer['effectAllowed'];
  onDragStart?: () => void;
  onDragEnd?: (dropped: boolean) => void;
}

export const useDraggable = (options: UseDraggableOptions) => {
  const {
    item,
    type,
    effectAllowed = 'copy',
    onDragStart,
    onDragEnd
  } = options;

  const [isDragging, setIsDragging] = useState(false);
  const dropped = useRef(false);

  const handleDragStart = useCallback((event: DragEvent) => {
    dropped.current = false;
    setIsDragging(true);
    
    // Set drag data
    event.dataTransfer.effectAllowed = effectAllowed;
    event.dataTransfer.setData('application/json', JSON.stringify({
      type,
      item
    }));
    
    // Set drag image (optional)
    if (event.target instanceof HTMLElement) {
      const dragImage = event.target.cloneNode(true) as HTMLElement;
      dragImage.style.opacity = '0.5';
      document.body.appendChild(dragImage);
      event.dataTransfer.setDragImage(dragImage, 0, 0);
      setTimeout(() => document.body.removeChild(dragImage), 0);
    }
    
    onDragStart?.();
  }, [item, type, effectAllowed, onDragStart]);

  const handleDragEnd = useCallback((event: DragEvent) => {
    setIsDragging(false);
    
    // Check if drop was successful
    const wasDropped = event.dataTransfer.dropEffect !== 'none';
    onDragEnd?.(wasDropped);
  }, [onDragEnd]);

  const getDraggableProps = () => ({
    draggable: true,
    onDragStart: handleDragStart,
    onDragEnd: handleDragEnd,
    style: {
      cursor: isDragging ? 'grabbing' : 'grab',
      opacity: isDragging ? 0.5 : 1
    }
  });

  return {
    getDraggableProps,
    isDragging
  };
};

// Sortable list hook
interface UseSortableOptions<T> {
  items: T[];
  onReorder: (items: T[]) => void;
  itemKey: (item: T) => string;
}

export const useSortable = <T>({ items, onReorder, itemKey }: UseSortableOptions<T>) => {
  const [draggedItem, setDraggedItem] = useState<T | null>(null);
  const [draggedOverItem, setDraggedOverItem] = useState<T | null>(null);

  const handleDragStart = useCallback((item: T) => {
    setDraggedItem(item);
  }, []);

  const handleDragOver = useCallback((item: T) => {
    if (!draggedItem || itemKey(item) === itemKey(draggedItem)) return;
    setDraggedOverItem(item);
  }, [draggedItem, itemKey]);

  const handleDragEnd = useCallback(() => {
    if (!draggedItem || !draggedOverItem) {
      setDraggedItem(null);
      setDraggedOverItem(null);
      return;
    }

    const draggedIndex = items.findIndex(item => itemKey(item) === itemKey(draggedItem));
    const targetIndex = items.findIndex(item => itemKey(item) === itemKey(draggedOverItem));

    if (draggedIndex === -1 || targetIndex === -1) {
      setDraggedItem(null);
      setDraggedOverItem(null);
      return;
    }

    const newItems = [...items];
    const [removed] = newItems.splice(draggedIndex, 1);
    newItems.splice(targetIndex, 0, removed);

    onReorder(newItems);
    setDraggedItem(null);
    setDraggedOverItem(null);
  }, [items, draggedItem, draggedOverItem, itemKey, onReorder]);

  const getSortableItemProps = (item: T) => ({
    draggable: true,
    onDragStart: () => handleDragStart(item),
    onDragOver: () => handleDragOver(item),
    onDragEnd: handleDragEnd,
    style: {
      opacity: draggedItem && itemKey(draggedItem) === itemKey(item) ? 0.5 : 1,
      transform: draggedOverItem && itemKey(draggedOverItem) === itemKey(item) ? 'scale(1.05)' : 'scale(1)',
      transition: 'transform 0.2s'
    }
  });

  return {
    getSortableItemProps,
    isDragging: !!draggedItem
  };
};

// Utility functions
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}