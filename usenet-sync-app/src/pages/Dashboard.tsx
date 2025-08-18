import React, { useEffect, useState } from 'react';
import { useAppStore } from '../stores/useAppStore';
import { TransferCard } from '../components/progress/TransferCard';
import { ConnectionPoolVisualization } from '../components/ConnectionPoolVisualization';
import { ContextMenu, useContextMenu } from '../components/ContextMenu';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { getSystemStats } from '../lib';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { 
  Activity, 
  HardDrive, 
  Cpu, 
  Wifi,
  Upload,
  Download,
  Share2,
  Clock
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export const Dashboard: React.FC = () => {
  const { uploads, downloads, shares, licenseStatus } = useAppStore();
  const [stats, setStats] = useState<any>(null);
  const [speedHistory, setSpeedHistory] = useState<number[]>([]);
  const navigate = useNavigate();
  
  // Use keyboard shortcuts
  useKeyboardShortcuts();
  
  // Context menu setup
  const { menuState: contextMenu, openContextMenu: handleContextMenu, closeContextMenu } = useContextMenu();
  
  const dashboardContextMenuItems: ContextMenuItem[] = [
    {

      id: 'New Upload'.toLowerCase().replace(/ /g, '-'),

      label: 'New Upload',
      icon: Upload,
      onClick: () => navigate('/upload'),
      shortcut: 'Ctrl+U'
    },
    {

      id: 'New Download'.toLowerCase().replace(/ /g, '-'),

      label: 'New Download',
      icon: Download,
      onClick: () => navigate('/download'),
      shortcut: 'Ctrl+D'
    },
    { type: 'separator' as const },
    {

      id: 'View Shares'.toLowerCase().replace(/ /g, '-'),

      label: 'View Shares',
      icon: Share2,
      onClick: () => navigate('/shares')
    },
    {

      id: 'Settings'.toLowerCase().replace(/ /g, '-'),

      label: 'Settings',
      onClick: () => navigate('/settings'),
      shortcut: 'Ctrl+,'
    },
    { type: 'separator' as const },
    {

      id: 'Refresh'.toLowerCase().replace(/ /g, '-'),

      label: 'Refresh',
      onClick: () => {
        toast.success('Dashboard refreshed');
        window.location.reload();
      },
      shortcut: 'F5'
    }
  ];

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const systemStats = await getSystemStats();
        setStats(systemStats);
        
        // Update speed history
        setSpeedHistory(prev => {
          const newHistory = [...prev, systemStats.networkSpeed.download + systemStats.networkSpeed.upload];
          return newHistory.slice(-30); // Keep last 30 data points
        });
      } catch (error) {
        console.error('Failed to fetch system stats:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const activeTransfers = [...uploads, ...downloads].filter(
    t => t.status === 'active'
  );

  const completedTransfers = [...uploads, ...downloads].filter(
    t => t.status === 'completed'
  );

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const chartData = {
    labels: speedHistory.map((_, i) => `${30 - i}s`),
    datasets: [
      {

        id: 'Network Speed'.toLowerCase().replace(/ /g, '-'),

        label: 'Network Speed',
        data: speedHistory,
        fill: true,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `Speed: ${formatBytes(context.parsed.y)}/s`;
          },
        },
      },
    },
    scales: {
      x: {
        display: false,
      },
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: any) => formatBytes(value) + '/s',
        },
      },
    },
  };

  return (
    <div 
      className="p-6 space-y-6"
      onContextMenu={handleContextMenu}
    >
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor your transfers and system performance
          </p>
        </div>
        
        {licenseStatus && (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-green-700 dark:text-green-400">
              {licenseStatus.tier} License Active
            </span>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-dark-surface rounded-lg p-4 border border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">CPU Usage</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.cpuUsage.toFixed(1) || '0'}%
              </p>
            </div>
            <Cpu className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-dark-surface rounded-lg p-4 border border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Memory</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.memoryUsage.toFixed(1) || '0'}%
              </p>
            </div>
            <Activity className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-dark-surface rounded-lg p-4 border border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Storage</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.diskUsage.toFixed(1) || '0'}%
              </p>
            </div>
            <HardDrive className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-dark-surface rounded-lg p-4 border border-gray-200 dark:border-dark-border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Active Shares</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {shares.length}
              </p>
            </div>
            <Share2 className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Network Speed Chart */}
      <div className="bg-white dark:bg-dark-surface rounded-lg p-6 border border-gray-200 dark:border-dark-border">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Network Activity
        </h2>
        <div className="h-48">
          <Line data={chartData} options={chartOptions} />
        </div>
        <div className="flex justify-around mt-4 pt-4 border-t border-gray-200 dark:border-dark-border">
          <div className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-blue-500" />
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Upload</p>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {formatBytes(stats?.networkSpeed.upload || 0)}/s
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Download className="w-4 h-4 text-green-500" />
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400">Download</p>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {formatBytes(stats?.networkSpeed.download || 0)}/s
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Active Transfers */}
      {activeTransfers.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Active Transfers ({activeTransfers.length})
          </h2>
          <div className="space-y-3">
            {activeTransfers.map(transfer => (
              <TransferCard key={transfer.id} transfer={transfer} />
            ))}
          </div>
        </div>
      )}

      {/* Recent Transfers */}
      {completedTransfers.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Transfers
          </h2>
          <div className="space-y-3">
            {completedTransfers.slice(0, 5).map(transfer => (
              <TransferCard key={transfer.id} transfer={transfer} />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {activeTransfers.length === 0 && completedTransfers.length === 0 && (
        <div className="bg-white dark:bg-dark-surface rounded-lg p-12 border border-gray-200 dark:border-dark-border text-center">
          <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No transfers yet
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Start by uploading files or downloading a share
          </p>
        </div>
      )}

      {/* Connection Pool Visualization */}
      <div className="mt-6">
        <ConnectionPoolVisualization />
      </div>
      
      {/* Context Menu */}
      {contextMenu && (
        <ContextMenu
          position={{ x: contextMenu.x, y: contextMenu.y }}
          items={dashboardContextMenuItems}
          onClose={closeContextMenu}
        />
      )}
    </div>
  );
};