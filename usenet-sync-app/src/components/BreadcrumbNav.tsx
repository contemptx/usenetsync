import React from 'react';
import { ChevronRight, Home, Folder } from 'lucide-react';

interface BreadcrumbItem {
  id: string;
  label: string;
  path: string;
  icon?: React.ComponentType<any>;
}

interface BreadcrumbNavProps {
  items: BreadcrumbItem[];
  onNavigate?: (item: BreadcrumbItem) => void;
  separator?: React.ReactNode;
  maxItems?: number;
  className?: string;
}

export const BreadcrumbNav: React.FC<BreadcrumbNavProps> = ({
  items,
  onNavigate,
  separator = <ChevronRight className="w-4 h-4" />,
  maxItems = 5,
  className = ''
}) => {
  // Collapse middle items if too many
  const getDisplayItems = () => {
    if (items.length <= maxItems) {
      return items;
    }
    
    const firstItems = items.slice(0, 2);
    const lastItems = items.slice(-2);
    
    return [
      ...firstItems,
      { id: `ellipsis-${items.length}`, label: '...', path: '', isEllipsis: true },
      ...lastItems
    ];
  };
  
  const displayItems = getDisplayItems();
  
  return (
    <nav className={`flex items-center space-x-1 ${className}`}>
      {/* Home icon */}
      <button
        onClick={() => onNavigate?.({ id: 'home', label: 'Home', path: '/' })}
        className="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-dark-border rounded transition-colors"
        title="Go to home"
      >
        <Home className="w-4 h-4" />
      </button>
      
      {displayItems.length > 0 && (
        <React.Fragment key="home-separator">
          <span className="text-gray-400 dark:text-gray-600">{separator}</span>
        </React.Fragment>
      )}
      
      {displayItems.map((item, index) => {
        const isLast = index === displayItems.length - 1;
        const Icon = item.icon || Folder;
        const isEllipsis = 'isEllipsis' in item && item.isEllipsis;
        
        return (
          <React.Fragment key={item.id}>
            {isEllipsis ? (
              <div className="relative group">
                <button
                  className="px-2 py-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                >
                  {item.label}
                </button>
                
                {/* Dropdown for collapsed items */}
                <div className="absolute top-full left-0 mt-1 hidden group-hover:block z-50">
                  <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg border border-gray-200 dark:border-dark-border py-1 min-w-[150px]">
                    {items.slice(2, -2).map((collapsedItem) => (
                      <button
                        key={collapsedItem.id}
                        onClick={() => onNavigate?.(collapsedItem)}
                        className="w-full px-3 py-2 text-sm text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-border transition-colors flex items-center gap-2"
                      >
                        <Folder className="w-3 h-3" />
                        {collapsedItem.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <button
                onClick={() => !isLast && onNavigate?.(item)}
                className={`
                  flex items-center gap-1 px-2 py-1 text-sm rounded transition-colors
                  ${isLast 
                    ? 'text-gray-900 dark:text-white font-medium cursor-default' 
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-dark-border'
                  }
                `}
                disabled={isLast}
              >
                {!isLast && <Icon className="w-3 h-3" />}
                {item.label}
              </button>
            )}
            
            {!isLast && index < displayItems.length - 1 && (
              <span key={`separator-${item.id}`} className="text-gray-400 dark:text-gray-600">{separator}</span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

// Helper function to generate breadcrumb items from path
export const pathToBreadcrumbs = (path: string): BreadcrumbItem[] => {
  const segments = path.split('/').filter(Boolean);
  const breadcrumbs: BreadcrumbItem[] = [];
  
  segments.forEach((segment, index) => {
    const currentPath = '/' + segments.slice(0, index + 1).join('/');
    breadcrumbs.push({
      id: `segment-${index}`,
      label: segment,
      path: currentPath
    });
  });
  
  return breadcrumbs;
};