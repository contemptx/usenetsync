import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Search, 
  X, 
  Filter,
  Calendar,
  FileText,
  Folder,
  Hash,
  User,
  Clock,
  ChevronDown
} from 'lucide-react';
import { debounce } from 'lodash';

interface SearchResult {
  id: string;
  type: 'file' | 'folder' | 'share';
  name: string;
  path?: string;
  shareId?: string;
  size?: number;
  modifiedAt?: string;
  createdBy?: string;
  matches?: {
    field: string;
    snippet: string;
  }[];
}

interface SearchFilters {
  type?: ('file' | 'folder' | 'share')[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  sizeRange?: {
    min: number;
    max: number;
  };
  creator?: string;
}

interface SearchBarProps {
  placeholder?: string;
  onSearch?: (query: string, filters?: SearchFilters) => void;
  onResultSelect?: (result: SearchResult) => void;
  showFilters?: boolean;
  autoFocus?: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = "Search files, folders, or shares...",
  onSearch,
  onResultSelect,
  showFilters = true,
  autoFocus = false
}) => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [filters, setFilters] = useState<SearchFilters>({});
  
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
        setShowFilterMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  const debouncedSearch = useCallback(
    debounce(async (searchQuery: string, searchFilters: SearchFilters) => {
      if (!searchQuery.trim() && Object.keys(searchFilters).length === 0) {
        setResults([]);
        setIsSearching(false);
        return;
      }

      setIsSearching(true);
      
      try {
        // Call search API
        onSearch?.(searchQuery, searchFilters);
        
        // Mock results for demo
        const mockResults: SearchResult[] = [
          {
            id: '1',
            type: 'file',
            name: 'document.pdf',
            path: '/documents/document.pdf',
            size: 2048576,
            modifiedAt: new Date().toISOString(),
            createdBy: 'user@example.com',
            matches: [
              { field: 'name', snippet: '<mark>document</mark>.pdf' }
            ]
          },
          {
            id: '2',
            type: 'folder',
            name: 'Documents',
            path: '/documents',
            modifiedAt: new Date().toISOString(),
            matches: [
              { field: 'name', snippet: '<mark>Document</mark>s' }
            ]
          },
          {
            id: '3',
            type: 'share',
            name: 'Shared Document',
            shareId: 'SHARE123',
            size: 1048576,
            createdBy: 'user@example.com',
            matches: [
              { field: 'name', snippet: 'Shared <mark>Document</mark>' }
            ]
          }
        ].filter(r => 
          r.name.toLowerCase().includes(searchQuery.toLowerCase())
        );
        
        setResults(mockResults);
        setShowResults(true);
      } catch (error) {
        console.error('Search failed:', error);
      } finally {
        setIsSearching(false);
      }
    }, 300),
    [onSearch]
  );

  useEffect(() => {
    debouncedSearch(query, filters);
  }, [query, filters, debouncedSearch]);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showResults || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < results.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : results.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleResultClick(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowResults(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const handleResultClick = (result: SearchResult) => {
    onResultSelect?.(result);
    setShowResults(false);
    setQuery('');
    setSelectedIndex(-1);
  };

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'file':
        return <FileText className="w-4 h-4" />;
      case 'folder':
        return <Folder className="w-4 h-4" />;
      case 'share':
        return <Hash className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
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

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setShowResults(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  const toggleFilter = (filterType: string, value: any) => {
    setFilters(prev => {
      const newFilters = { ...prev };
      
      if (filterType === 'type') {
        const types = newFilters.type || [];
        const index = types.indexOf(value);
        if (index > -1) {
          types.splice(index, 1);
        } else {
          types.push(value);
        }
        newFilters.type = types.length > 0 ? types : undefined;
      }
      
      return newFilters;
    });
  };

  const hasActiveFilters = Object.keys(filters).length > 0;

  return (
    <div ref={searchRef} className="relative w-full max-w-2xl">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className={`w-5 h-5 ${isSearching ? 'text-primary-500' : 'text-gray-400'}`} />
        </div>
        
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query && setShowResults(true)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="w-full pl-10 pr-20 py-2 bg-white dark:bg-dark-surface border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:text-white placeholder-gray-400"
        />
        
        {/* Right side actions */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 gap-1">
          {query && (
            <button
              onClick={clearSearch}
              className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-dark-border"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          
          {showFilters && (
            <button
              onClick={() => setShowFilterMenu(!showFilterMenu)}
              className={`p-1.5 rounded hover:bg-gray-100 dark:hover:bg-dark-border ${
                hasActiveFilters 
                  ? 'text-primary-500' 
                  : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
            >
              <Filter className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Filter Menu */}
      {showFilterMenu && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg shadow-lg p-4 z-50">
          <div className="space-y-4">
            {/* Type Filters */}
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Type
              </label>
              <div className="flex gap-2">
                {(['file', 'folder', 'share'] as const).map(type => (
                  <button
                    key={type}
                    onClick={() => toggleFilter('type', type)}
                    className={`px-3 py-1 rounded-lg text-sm capitalize transition-colors ${
                      filters.type?.includes(type)
                        ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                        : 'bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-surface'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Date Range */}
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Modified Date
              </label>
              <div className="flex gap-2">
                <button className="px-3 py-1 bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-dark-surface">
                  Today
                </button>
                <button className="px-3 py-1 bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-dark-surface">
                  Last 7 days
                </button>
                <button className="px-3 py-1 bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-dark-surface">
                  Last 30 days
                </button>
              </div>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <button
                onClick={() => setFilters({})}
                className="text-sm text-primary-500 hover:text-primary-600"
              >
                Clear all filters
              </button>
            )}
          </div>
        </div>
      )}

      {/* Search Results */}
      {showResults && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg shadow-lg max-h-96 overflow-y-auto z-50">
          {results.map((result, index) => (
            <button
              key={result.id}
              onClick={() => handleResultClick(result)}
              onMouseEnter={() => setSelectedIndex(index)}
              className={`w-full px-4 py-3 flex items-start gap-3 hover:bg-gray-50 dark:hover:bg-dark-border transition-colors text-left ${
                index === selectedIndex ? 'bg-gray-50 dark:bg-dark-border' : ''
              }`}
            >
              <div className={`mt-0.5 ${
                result.type === 'share' ? 'text-primary-500' : 'text-gray-400'
              }`}>
                {getResultIcon(result.type)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span 
                    className="font-medium text-gray-900 dark:text-white truncate"
                    dangerouslySetInnerHTML={{ 
                      __html: result.matches?.[0]?.snippet || result.name 
                    }}
                  />
                  {result.type === 'share' && result.shareId && (
                    <span className="text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 px-2 py-0.5 rounded-full">
                      {result.shareId}
                    </span>
                  )}
                </div>
                
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-500">
                  {result.path && (
                    <span className="truncate">{result.path}</span>
                  )}
                  {result.size && (
                    <span>{formatFileSize(result.size)}</span>
                  )}
                  {result.createdBy && (
                    <span className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {result.createdBy}
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No Results */}
      {showResults && query && results.length === 0 && !isSearching && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg shadow-lg p-8 text-center z-50">
          <Search className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400">
            No results found for "{query}"
          </p>
          {hasActiveFilters && (
            <button
              onClick={() => setFilters({})}
              className="mt-2 text-sm text-primary-500 hover:text-primary-600"
            >
              Try clearing filters
            </button>
          )}
        </div>
      )}

      {/* Loading */}
      {isSearching && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg shadow-lg p-4 z-50">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500"></div>
            <span className="ml-3 text-gray-500 dark:text-gray-400">Searching...</span>
          </div>
        </div>
      )}
    </div>
  );
};