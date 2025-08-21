import React, { useState, useEffect, useRef } from 'react';
import { Search, X, File, Folder, Clock, Filter } from 'lucide-react';
import { searchContent } from '../lib/backend-api';

interface SearchResult {
  id: string;
  name: string;
  type: 'file' | 'folder';
  path: string;
  size?: number;
  modified?: Date;
}

interface SearchBarProps {
  onSelect?: (result: SearchResult) => void;
  placeholder?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({ 
  onSelect, 
  placeholder = "Search files and folders..." 
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [searchType, setSearchType] = useState<'all' | 'files' | 'folders'>('all');
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchTimeout = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Handle click outside to close results
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    // Debounced search
    if (query.length > 0) {
      setIsSearching(true);
      clearTimeout(searchTimeout.current);
      
      searchTimeout.current = setTimeout(async () => {
        await performSearch();
      }, 300);
    } else {
      setResults([]);
      setShowResults(false);
    }

    return () => clearTimeout(searchTimeout.current);
  }, [query, searchType]);

  const performSearch = async () => {
    try {
      const searchResults = await searchContent(
        query, 
        searchType === 'all' ? undefined : searchType
      );
      
      // Transform results to unified format
      const formattedResults: SearchResult[] = [];
      
      if (searchResults.files && Array.isArray(searchResults.files)) {
        searchResults.files.forEach((file: any) => {
          formattedResults.push({
            id: file.file_id || file.id,
            name: file.name || file.file_name,
            type: 'file',
            path: file.file_path || file.path || '',
            size: file.size,
            modified: file.modified_at ? new Date(file.modified_at) : undefined
          });
        });
      }
      
      if (searchResults.folders && Array.isArray(searchResults.folders)) {
        searchResults.folders.forEach((folder: any) => {
          formattedResults.push({
            id: folder.folder_id || folder.id,
            name: folder.name,
            type: 'folder',
            path: folder.path || '',
            modified: folder.created_at ? new Date(folder.created_at) : undefined
          });
        });
      }
      
      setResults(formattedResults);
      setShowResults(formattedResults.length > 0);
      setSelectedIndex(-1);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

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
        if (selectedIndex >= 0 && results[selectedIndex]) {
          handleSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowResults(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const handleSelect = (result: SearchResult) => {
    setQuery('');
    setShowResults(false);
    setSelectedIndex(-1);
    if (onSelect) {
      onSelect(result);
    }
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setShowResults(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
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

  return (
    <div ref={searchRef} className="relative w-full max-w-2xl">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query && setShowResults(true)}
          placeholder={placeholder}
          className="block w-full pl-10 pr-20 py-2 border border-gray-300 rounded-lg 
                     bg-white dark:bg-gray-800 dark:border-gray-700 
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 gap-1">
          {/* Type filter */}
          <select
            value={searchType}
            onChange={(e) => setSearchType(e.target.value as any)}
            className="text-sm px-2 py-1 border rounded bg-gray-50 dark:bg-gray-700 dark:border-gray-600"
          >
            <option value="all">All</option>
            <option value="files">Files</option>
            <option value="folders">Folders</option>
          </select>
          
          {query && (
            <button
              onClick={clearSearch}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              <X className="h-4 w-4 text-gray-400" />
            </button>
          )}
        </div>
      </div>

      {/* Search results dropdown */}
      {showResults && (
        <div className="absolute z-50 w-full mt-2 py-2 bg-white dark:bg-gray-800 
                        border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg 
                        max-h-96 overflow-auto">
          {isSearching ? (
            <div className="px-4 py-3 text-gray-500 text-center">
              <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 dark:border-gray-100"></div>
              <span className="ml-2">Searching...</span>
            </div>
          ) : results.length === 0 ? (
            <div className="px-4 py-3 text-gray-500 text-center">
              No results found for "{query}"
            </div>
          ) : (
            <div>
              {results.map((result, index) => (
                <button
                  key={result.id}
                  onClick={() => handleSelect(result)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`w-full px-4 py-2 flex items-center gap-3 hover:bg-gray-100 
                             dark:hover:bg-gray-700 transition-colors text-left
                             ${selectedIndex === index ? 'bg-gray-100 dark:bg-gray-700' : ''}`}
                >
                  {result.type === 'folder' ? (
                    <Folder className="h-5 w-5 text-blue-500 flex-shrink-0" />
                  ) : (
                    <File className="h-5 w-5 text-gray-400 flex-shrink-0" />
                  )}
                  
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                      {result.name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                      {result.path}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    {result.size && (
                      <span>{formatFileSize(result.size)}</span>
                    )}
                    {result.modified && (
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>{result.modified.toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
