import React, { useEffect, useState } from 'react';
import { Activity, Server, TrendingUp, AlertCircle, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

interface PoolConnection {
  id: string;
  status: 'active' | 'idle' | 'connecting' | 'error';
  server: string;
  duration: number;
  bytesTransferred: number;
  lastActivity: Date;
}

interface PoolStats {
  totalConnections: number;
  activeConnections: number;
  idleConnections: number;
  failedConnections: number;
  totalBytesTransferred: number;
  avgResponseTime: number;
  connectionLimit: number;
  uptime: number;
}

interface ConnectionPoolVisualizationProps {
  onRefresh?: () => Promise<void>;
}

export const ConnectionPoolVisualization: React.FC<ConnectionPoolVisualizationProps> = ({ onRefresh }) => {
  const [connections, setConnections] = useState<PoolConnection[]>([]);
  const [stats, setStats] = useState<PoolStats>({
    totalConnections: 0,
    activeConnections: 0,
    idleConnections: 0,
    failedConnections: 0,
    totalBytesTransferred: 0,
    avgResponseTime: 0,
    connectionLimit: 10,
    uptime: 0
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Simulate connection pool data
  useEffect(() => {
    const generateConnections = () => {
      const mockConnections: PoolConnection[] = [];
      const numConnections = Math.floor(Math.random() * 8) + 2;
      
      for (let i = 0; i < numConnections; i++) {
        const statuses: Array<'active' | 'idle' | 'connecting' | 'error'> = ['active', 'idle', 'connecting', 'error'];
        const status = statuses[Math.floor(Math.random() * statuses.length)];
        
        mockConnections.push({
          id: `conn-${i}`,
          status,
          server: `news${Math.floor(Math.random() * 3) + 1}.provider.com`,
          duration: Math.floor(Math.random() * 3600),
          bytesTransferred: Math.floor(Math.random() * 1000000000),
          lastActivity: new Date(Date.now() - Math.random() * 3600000)
        });
      }
      
      setConnections(mockConnections);
      
      // Update stats
      const active = mockConnections.filter(c => c.status === 'active').length;
      const idle = mockConnections.filter(c => c.status === 'idle').length;
      const failed = mockConnections.filter(c => c.status === 'error').length;
      
      setStats({
        totalConnections: mockConnections.length,
        activeConnections: active,
        idleConnections: idle,
        failedConnections: failed,
        totalBytesTransferred: mockConnections.reduce((sum, c) => sum + c.bytesTransferred, 0),
        avgResponseTime: Math.random() * 500 + 50,
        connectionLimit: 10,
        uptime: Date.now() - (Date.now() - 86400000)
      });
    };
    
    generateConnections();
    const interval = setInterval(generateConnections, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    if (onRefresh) {
      await onRefresh();
    }
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  const formatUptime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Activity className="w-4 h-4 text-green-500" />;
      case 'idle':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case 'connecting':
        return <RefreshCw className="w-4 h-4 text-yellow-500 animate-spin" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'idle':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'connecting':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  const utilizationPercentage = (stats.activeConnections / stats.connectionLimit) * 100;

  return (
    <div className="space-y-6">
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Server className="w-6 h-6 text-gray-600 dark:text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Connection Pool Status
          </h2>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-border transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-dark-surface rounded-lg p-4 border border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Active</span>
            <Activity className="w-4 h-4 text-green-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {stats.activeConnections}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-500">
            of {stats.connectionLimit} max
          </div>
        </div>

        <div className="bg-white dark:bg-dark-surface rounded-lg p-4 border border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Idle</span>
            <CheckCircle className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {stats.idleConnections}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-500">
            ready to use
          </div>
        </div>

        <div className="bg-white dark:bg-dark-surface rounded-lg p-4 border border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Failed</span>
            <XCircle className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {stats.failedConnections}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-500">
            errors today
          </div>
        </div>

        <div className="bg-white dark:bg-dark-surface rounded-lg p-4 border border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Avg Response</span>
            <TrendingUp className="w-4 h-4 text-purple-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {stats.avgResponseTime.toFixed(0)}ms
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-500">
            last 5 min
          </div>
        </div>
      </div>

      {/* Utilization Bar */}
      <div className="bg-white dark:bg-dark-surface rounded-lg p-4 border border-gray-200 dark:border-dark-border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Pool Utilization
          </span>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {utilizationPercentage.toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-dark-bg rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${
              utilizationPercentage > 80 ? 'bg-red-500' :
              utilizationPercentage > 60 ? 'bg-yellow-500' :
              'bg-green-500'
            }`}
            style={{ width: `${utilizationPercentage}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-gray-500">
            {stats.activeConnections} active connections
          </span>
          <span className="text-xs text-gray-500">
            {stats.connectionLimit - stats.activeConnections} available
          </span>
        </div>
      </div>

      {/* Connection List */}
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-dark-border">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            Active Connections
          </h3>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-dark-border max-h-96 overflow-y-auto">
          {connections.map((connection) => (
            <div key={connection.id} className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-dark-border/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getStatusIcon(connection.status)}
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {connection.server}
                      </span>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${getStatusColor(connection.status)}`}>
                        {connection.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-1">
                      <span className="text-xs text-gray-500 dark:text-gray-500">
                        Duration: {formatDuration(connection.duration)}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-500">
                        Transferred: {formatBytes(connection.bytesTransferred)}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-500">
                        Last activity: {new Date(connection.lastActivity).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <Activity className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <p className="font-medium text-blue-900 dark:text-blue-400 mb-1">
              Connection Pool Summary
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-blue-700 dark:text-blue-300">
              <span>Total transferred: {formatBytes(stats.totalBytesTransferred)}</span>
              <span>Uptime: {formatUptime(stats.uptime)}</span>
              <span>Pool size: {stats.connectionLimit}</span>
              <span>Health: {stats.failedConnections === 0 ? 'Excellent' : 'Degraded'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};