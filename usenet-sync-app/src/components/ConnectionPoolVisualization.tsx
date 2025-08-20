import React, { useState, useEffect } from 'react';
import { Activity, Server, Zap, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { getConnectionPoolStats } from '../lib/backend-api';

interface Connection {
  id: string;
  server: string;
  status: 'active' | 'idle' | 'connecting' | 'error';
  duration: number;
  bytesTransferred: number;
}

interface PoolStats {
  active: number;
  idle: number;
  total: number;
  max: number;
  connections?: Connection[];
}

export const ConnectionPoolVisualization: React.FC = () => {
  const [poolStats, setPoolStats] = useState<PoolStats>({
    active: 0,
    idle: 0,
    total: 0,
    max: 10,
    connections: []
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPoolStats();
    // Refresh every 2 seconds
    const interval = setInterval(loadPoolStats, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadPoolStats = async () => {
    try {
      setError(null);
      const stats = await getConnectionPoolStats();
      
      // Generate mock connections if not provided by backend
      if (!stats.connections || stats.connections.length === 0) {
        const mockConnections: Connection[] = [];
        for (let i = 0; i < stats.active; i++) {
          mockConnections.push({
            id: `active-${i}`,
            server: 'news.newshosting.com',
            status: 'active',
            duration: Math.floor(Math.random() * 300),
            bytesTransferred: Math.floor(Math.random() * 1000000)
          });
        }
        for (let i = 0; i < stats.idle; i++) {
          mockConnections.push({
            id: `idle-${i}`,
            server: 'news.newshosting.com',
            status: 'idle',
            duration: 0,
            bytesTransferred: 0
          });
        }
        stats.connections = mockConnections;
      }
      
      setPoolStats(stats);
      setIsLoading(false);
    } catch (err) {
      console.error('Failed to load connection pool stats:', err);
      setError('Failed to load connection pool statistics');
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'idle': return 'bg-yellow-500';
      case 'connecting': return 'bg-blue-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <Zap className="w-4 h-4" />;
      case 'idle': return <Clock className="w-4 h-4" />;
      case 'connecting': return <Activity className="w-4 h-4 animate-pulse" />;
      case 'error': return <AlertCircle className="w-4 h-4" />;
      default: return <Server className="w-4 h-4" />;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (isLoading) {
    return (
      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="flex items-center gap-2 text-red-500">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  const usagePercentage = poolStats.max > 0 
    ? (poolStats.total / poolStats.max) * 100 
    : 0;

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Connection Pool</h3>
        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
          <span>Active: {poolStats.active}</span>
          <span>Idle: {poolStats.idle}</span>
          <span>Total: {poolStats.total}/{poolStats.max}</span>
        </div>
      </div>

      {/* Usage bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-1">
          <span>Pool Usage</span>
          <span>{usagePercentage.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
          <div className="h-full flex">
            <div 
              className="bg-green-500 transition-all duration-300"
              style={{ width: `${(poolStats.active / poolStats.max) * 100}%` }}
            />
            <div 
              className="bg-yellow-500 transition-all duration-300"
              style={{ width: `${(poolStats.idle / poolStats.max) * 100}%` }}
            />
          </div>
        </div>
        <div className="flex items-center gap-4 mt-2 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>Active</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <span>Idle</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <span>Available</span>
          </div>
        </div>
      </div>

      {/* Connection grid */}
      <div className="grid grid-cols-5 gap-2 mb-6">
        {Array.from({ length: poolStats.max }).map((_, index) => {
          const connection = poolStats.connections?.[index];
          const isActive = index < poolStats.active;
          const isIdle = index >= poolStats.active && index < poolStats.total;
          
          return (
            <div
              key={index}
              className={`aspect-square rounded-lg flex items-center justify-center transition-all ${
                isActive ? 'bg-green-100 dark:bg-green-900' :
                isIdle ? 'bg-yellow-100 dark:bg-yellow-900' :
                'bg-gray-100 dark:bg-gray-700'
              }`}
              title={connection ? `${connection.server} - ${connection.status}` : 'Available'}
            >
              {isActive ? (
                <Zap className="w-4 h-4 text-green-600 dark:text-green-400" />
              ) : isIdle ? (
                <Clock className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
              ) : (
                <div className="w-2 h-2 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
              )}
            </div>
          );
        })}
      </div>

      {/* Connection details */}
      {poolStats.connections && poolStats.connections.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold mb-2">Active Connections</h4>
          <div className="space-y-2">
            {poolStats.connections
              .filter(conn => conn.status === 'active')
              .slice(0, 5)
              .map(conn => (
                <div
                  key={conn.id}
                  className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded"
                >
                  <div className="flex items-center gap-2">
                    {getStatusIcon(conn.status)}
                    <span className="text-sm font-medium">{conn.server}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>{formatDuration(conn.duration)}</span>
                    <span>{formatBytes(conn.bytesTransferred)}</span>
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(conn.status)}`}></div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Stats summary */}
      <div className="mt-4 pt-4 border-t dark:border-gray-700">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-green-500">{poolStats.active}</div>
            <div className="text-xs text-gray-500">Active</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-yellow-500">{poolStats.idle}</div>
            <div className="text-xs text-gray-500">Idle</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-500">
              {poolStats.max - poolStats.total}
            </div>
            <div className="text-xs text-gray-500">Available</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConnectionPoolVisualization;
