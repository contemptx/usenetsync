import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, Download, Trash2, RefreshCw, Filter, Search,
  AlertCircle, Info, AlertTriangle, XCircle, CheckCircle,
  Clock, Copy, ChevronDown
} from 'lucide-react';
import { getLogs } from '../lib';
import { fetchLogs } from '../lib/backend-api';

interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  category: string;
  message: string;
  details?: Record<string, any>;
  source?: string;
}

type LogLevel = 'all' | 'debug' | 'info' | 'warning' | 'error' | 'critical';

export const Logs: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [selectedLevel, setSelectedLevel] = useState<LogLevel>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [categories, setCategories] = useState<string[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load logs on mount
  useEffect(() => {
    loadLogs();
    // Set up polling for new logs
    const interval = setInterval(loadNewLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll effect
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs, autoScroll]);

  // Filter logs when filters change
  useEffect(() => {
    filterLogs();
  }, [logs, selectedLevel, selectedCategory, searchQuery]);

  const loadLogs = async () => {
    try {
      setIsLoading(true);
      
      // Try to fetch from backend API first
      let logEntries = await fetchLogs(500, selectedLevel === 'all' ? undefined : selectedLevel);
      
      // If backend fails, try Tauri command
      if (!logEntries || logEntries.length === 0) {
        try {
          const tauriLogs = await getLogs();
          if (tauriLogs && Array.isArray(tauriLogs)) {
            logEntries = tauriLogs.map((log: any) => ({
              id: log.id || `${Date.now()}-${Math.random()}`,
              timestamp: new Date(log.timestamp),
              level: log.level || 'info',
              category: log.category || 'system',
              message: log.message || '',
              details: log.details,
              source: log.source || 'tauri'
            }));
          }
        } catch (error) {
          console.error('Failed to fetch logs from Tauri:', error);
        }
      }
      
      if (logEntries && logEntries.length > 0) {
        setLogs(logEntries);
        
        // Extract unique categories
        const uniqueCategories = [...new Set(logEntries.map(log => log.category))];
        setCategories(uniqueCategories);
      } else {
        setLogs([]);
        setCategories([]);
      }
    } catch (error) {
      console.error('Failed to load logs:', error);
      setLogs([]);
      setCategories([]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadNewLogs = async () => {
    // Fetch only recent logs
    const newLogs = await fetchLogs(50);
    if (newLogs && newLogs.length > 0) {
      setLogs(prev => {
        // Merge new logs, avoiding duplicates
        const existingIds = new Set(prev.map(log => log.id));
        const uniqueNewLogs = newLogs.filter(log => !existingIds.has(log.id));
        return [...prev, ...uniqueNewLogs].slice(-1000); // Keep last 1000 logs
      });
    }
  };

  const filterLogs = () => {
    let filtered = [...logs];
    
    // Filter by level
    if (selectedLevel !== 'all') {
      const levelPriority = {
        debug: 0,
        info: 1,
        warning: 2,
        error: 3,
        critical: 4
      };
      
      const minPriority = levelPriority[selectedLevel];
      filtered = filtered.filter(log => 
        levelPriority[log.level] >= minPriority
      );
    }
    
    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(log => log.category === selectedCategory);
    }
    
    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(query) ||
        log.category.toLowerCase().includes(query) ||
        (log.source && log.source.toLowerCase().includes(query))
      );
    }
    
    setFilteredLogs(filtered);
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'debug': return <Clock className="w-4 h-4" />;
      case 'info': return <Info className="w-4 h-4" />;
      case 'warning': return <AlertTriangle className="w-4 h-4" />;
      case 'error': return <XCircle className="w-4 h-4" />;
      case 'critical': return <AlertCircle className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'debug': return 'text-gray-500';
      case 'info': return 'text-blue-500';
      case 'warning': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      case 'critical': return 'text-red-700';
      default: return 'text-gray-500';
    }
  };

  const exportLogs = () => {
    const logData = filteredLogs.map(log => ({
      timestamp: log.timestamp.toISOString(),
      level: log.level,
      category: log.category,
      message: log.message,
      details: log.details,
      source: log.source
    }));
    
    const blob = new Blob([JSON.stringify(logData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearLogs = () => {
    setLogs([]);
    setFilteredLogs([]);
  };

  const copyLog = (log: LogEntry) => {
    const logText = `[${log.timestamp.toISOString()}] [${log.level.toUpperCase()}] [${log.category}] ${log.message}`;
    navigator.clipboard.writeText(logText);
  };

  const toggleLogExpansion = (logId: string) => {
    const newExpanded = new Set(expandedLogs);
    if (newExpanded.has(logId)) {
      newExpanded.delete(logId);
    } else {
      newExpanded.add(logId);
    }
    setExpandedLogs(newExpanded);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">System Logs</h1>
        <p className="text-gray-600 dark:text-gray-400">
          View and analyze system logs from backend and frontend
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value as LogLevel)}
            className="px-3 py-1 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
          >
            <option value="all">All Levels</option>
            <option value="debug">Debug</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
          >
            <option value="all">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 flex-1">
          <Search className="w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-1 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
          />
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadLogs}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
            title="Refresh logs"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={exportLogs}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
            title="Export logs"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={clearLogs}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
            title="Clear logs"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            <span className="text-sm">Auto-scroll</span>
          </label>
        </div>
      </div>

      {/* Log entries */}
      <div className="flex-1 overflow-auto border rounded-lg p-4 bg-gray-50 dark:bg-gray-900 dark:border-gray-700">
        {filteredLogs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No logs to display</p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map(log => (
              <div
                key={log.id}
                className="flex items-start gap-2 p-2 hover:bg-white dark:hover:bg-gray-800 rounded group"
              >
                <span className={getLevelColor(log.level)}>
                  {getLevelIcon(log.level)}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">
                      {log.timestamp.toLocaleTimeString()}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                      {log.category}
                    </span>
                    {log.source && (
                      <span className="text-xs text-gray-400">
                        [{log.source}]
                      </span>
                    )}
                  </div>
                  <div className="text-sm mt-1">
                    {log.message}
                  </div>
                  {log.details && (
                    <div className="mt-1">
                      <button
                        onClick={() => toggleLogExpansion(log.id)}
                        className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1"
                      >
                        <ChevronDown className={`w-3 h-3 transition-transform ${
                          expandedLogs.has(log.id) ? 'rotate-180' : ''
                        }`} />
                        Details
                      </button>
                      {expandedLogs.has(log.id) && (
                        <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => copyLog(log)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                  title="Copy log"
                >
                  <Copy className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
        <div ref={logsEndRef} />
      </div>

      {/* Status bar */}
      <div className="mt-4 text-sm text-gray-500">
        Showing {filteredLogs.length} of {logs.length} logs
      </div>
    </div>
  );
};
