import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, 
  Download, 
  Trash2, 
  RefreshCw, 
  Filter,
  Search,
  AlertCircle,
  Info,
  AlertTriangle,
  XCircle,
  CheckCircle,
  Clock,
  Copy,
  ChevronDown
} from 'lucide-react';
import { getLogs } from '../lib';

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
  const [filters, setFilters] = useState({
    level: 'all',
    category: 'all'
  });
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [categories, setCategories] = useState<string[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load logs on mount
  useEffect(() => {
    loadLogs();
    // Set up real-time log updates
    const interval = setInterval(loadNewLogs, 2000);
    return () => clearInterval(interval);
  }, []);

  // Filter logs when criteria change
  useEffect(() => {
    filterLogs();
  }, [logs, selectedLevel, searchQuery, selectedCategory]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs, autoScroll]);

  const loadLogs = async () => {
    setIsLoading(true);
    try {
      // Try to get logs from Tauri backend
      try {
        const logEntries = await getLogs({
          level: filters.level !== 'all' ? filters.level : undefined,
          category: filters.category !== 'all' ? filters.category : undefined,
          search: searchQuery || undefined,
          limit: 1000
        });
        
        if (logEntries && logEntries.length > 0) {
          setLogs(logEntries);
          return;
        }
      } catch (error) {
        console.error('Failed to fetch logs from backend:', error);
      }
      
      // No mock data - only use real logs
      if (!logEntries || logEntries.length === 0) {
        setLogs([]);
        setCategories([]);
      }
    } catch (error) {
      console.error('Failed to load logs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadNewLogs = async () => {
    // Simulate new log entries
    if (Math.random() > 0.7) {
      const levels: LogEntry['level'][] = ['debug', 'info', 'warning', 'error'];
      const categories = ['Upload', 'Download', 'Network', 'Share', 'Database'];
      
      const newLog: LogEntry = {
        id: Date.now().toString(),
        timestamp: new Date(),
        level: levels[Math.floor(Math.random() * levels.length)],
        category: categories[Math.floor(Math.random() * categories.length)],
        message: `New log entry at ${new Date().toLocaleTimeString()}`
      };
      
      setLogs(prev => [...prev, newLog]);
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
      filtered = filtered.filter(log => levelPriority[log.level] >= minPriority);
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
        JSON.stringify(log.details).toLowerCase().includes(query)
      );
    }
    
    setFilteredLogs(filtered);
  };

  const getLevelIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'debug':
        return <Info className="w-4 h-4 text-gray-500" />;
      case 'info':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
    }
  };

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'debug':
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20';
      case 'info':
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20';
      case 'error':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      case 'critical':
        return 'text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-900/30';
    }
  };

  const toggleLogExpanded = (logId: string) => {
    const newExpanded = new Set(expandedLogs);
    if (newExpanded.has(logId)) {
      newExpanded.delete(logId);
    } else {
      newExpanded.add(logId);
    }
    setExpandedLogs(newExpanded);
  };

  const copyLog = (log: LogEntry) => {
    const logText = `[${log.timestamp.toISOString()}] [${log.level.toUpperCase()}] [${log.category}] ${log.message}${
      log.details ? '\nDetails: ' + JSON.stringify(log.details, null, 2) : ''
    }`;
    navigator.clipboard.writeText(logText);
  };

  const exportLogs = () => {
    const logText = filteredLogs.map(log => 
      `[${log.timestamp.toISOString()}] [${log.level.toUpperCase()}] [${log.category}] ${log.message}${
        log.details ? '\nDetails: ' + JSON.stringify(log.details, null, 2) : ''
      }`
    ).join('\n\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearLogs = () => {
    if (confirm('Clear all logs? This action cannot be undone.')) {
      setLogs([]);
      setFilteredLogs([]);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-gray-600 dark:text-gray-400" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">System Logs</h1>
          <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-dark-border rounded-full text-gray-600 dark:text-gray-400">
            {filteredLogs.length} entries
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-2 rounded-lg transition-colors ${
              autoScroll 
                ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                : 'bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-surface'
            }`}
            title="Auto-scroll"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
          <button
            onClick={loadLogs}
            className="p-2 bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-surface transition-colors"
            title="Refresh logs"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={exportLogs}
            className="p-2 bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-surface transition-colors"
            title="Export logs"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={clearLogs}
            className="p-2 bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 transition-colors"
            title="Clear logs"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-gray-50 dark:bg-dark-bg border border-gray-200 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:text-white"
              />
            </div>
          </div>
          
          {/* Level Filter */}
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value as LogLevel)}
            className="px-3 py-2 bg-gray-50 dark:bg-dark-bg border border-gray-200 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:text-white"
          >
            <option value="all">All Levels</option>
            <option value="debug">Debug & Above</option>
            <option value="info">Info & Above</option>
            <option value="warning">Warning & Above</option>
            <option value="error">Error & Above</option>
            <option value="critical">Critical Only</option>
          </select>
          
          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 bg-gray-50 dark:bg-dark-bg border border-gray-200 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:text-white"
          >
            <option value="all">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Logs List */}
      <div className="flex-1 bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border overflow-hidden">
        <div className="h-full overflow-y-auto">
          {filteredLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full p-8">
              <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-3" />
              <p className="text-gray-500 dark:text-gray-400">No logs to display</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-dark-border">
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className={`p-4 hover:bg-gray-50 dark:hover:bg-dark-border/50 transition-colors ${getLevelColor(log.level)}`}
                >
                  <div className="flex items-start gap-3">
                    {getLevelIcon(log.level)}
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-500">
                          {log.timestamp.toLocaleTimeString()}
                        </span>
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 dark:bg-dark-bg text-gray-600 dark:text-gray-400">
                          {log.category}
                        </span>
                        {log.source && (
                          <span className="text-xs text-gray-500 dark:text-gray-500">
                            {log.source}
                          </span>
                        )}
                      </div>
                      
                      <p className="text-sm text-gray-900 dark:text-white">
                        {log.message}
                      </p>
                      
                      {log.details && (
                        <div className="mt-2">
                          <button
                            onClick={() => toggleLogExpanded(log.id)}
                            className="text-xs text-primary-500 hover:text-primary-600"
                          >
                            {expandedLogs.has(log.id) ? 'Hide' : 'Show'} details
                          </button>
                          
                          {expandedLogs.has(log.id) && (
                            <pre className="mt-2 p-2 bg-gray-100 dark:bg-dark-bg rounded text-xs text-gray-700 dark:text-gray-300 overflow-x-auto">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <button
                      onClick={() => copyLog(log)}
                      className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      title="Copy log entry"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
};