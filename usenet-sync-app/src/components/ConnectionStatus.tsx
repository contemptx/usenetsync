import React, { useEffect, useState } from 'react';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { getSystemInfo } from '../lib/tauri';

interface ConnectionInfo {
  isConnected: boolean;
  serverCount: number;
  activeConnections: number;
  status: 'connected' | 'disconnected' | 'error';
  lastChecked: Date;
}

export function ConnectionStatus() {
  const [connectionInfo, setConnectionInfo] = useState<ConnectionInfo>({
    isConnected: false,
    serverCount: 0,
    activeConnections: 0,
    status: 'disconnected',
    lastChecked: new Date()
  });

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const info = await getSystemInfo();
        setConnectionInfo({
          isConnected: true,
          serverCount: info.serverCount || 1,
          activeConnections: info.activeConnections || 0,
          status: 'connected',
          lastChecked: new Date()
        });
      } catch (error) {
        setConnectionInfo(prev => ({
          ...prev,
          isConnected: false,
          status: 'error',
          lastChecked: new Date()
        }));
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = () => {
    switch (connectionInfo.status) {
      case 'connected':
        return <Wifi className="h-5 w-5 text-green-500" />;
      case 'disconnected':
        return <WifiOff className="h-5 w-5 text-gray-400" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const getStatusText = () => {
    if (connectionInfo.status === 'connected') {
      return `Connected (${connectionInfo.activeConnections} active)`;
    } else if (connectionInfo.status === 'error') {
      return 'Connection Error';
    }
    return 'Disconnected';
  };

  return (
    <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-gray-100 dark:bg-gray-800">
      {getStatusIcon()}
      <div className="flex flex-col">
        <span className="text-sm font-medium">{getStatusText()}</span>
        {connectionInfo.serverCount > 0 && (
          <span className="text-xs text-gray-500">
            {connectionInfo.serverCount} server{connectionInfo.serverCount !== 1 ? 's' : ''} available
          </span>
        )}
      </div>
    </div>
  );
}

export default ConnectionStatus;