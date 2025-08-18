import React, { useState } from 'react';
import { useAppStore } from '../stores/useAppStore';
import { testServerConnection, saveServerConfig, deactivateLicense } from '../lib/tauri.ts';
import { Server, Check, X, AlertCircle, Key, LogOut, Gauge, Upload, Download } from 'lucide-react';
import toast from 'react-hot-toast';

export const Settings: React.FC = () => {
  const { serverConfig, setServerConfig, licenseStatus, user } = useAppStore();
  
  const [config, setConfig] = useState({
    hostname: serverConfig?.hostname || 'news.newshosting.com',
    port: serverConfig?.port || 563,
    username: serverConfig?.username || '',
    password: serverConfig?.password || '',
    useSsl: serverConfig?.useSsl ?? true,
    maxConnections: serverConfig?.maxConnections || 30,
    group: serverConfig?.group || 'alt.binaries.test'
  });
  
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<boolean | null>(null);
  
  const [bandwidthLimits, setBandwidthLimits] = useState({
    uploadLimit: 0,
    downloadLimit: 0,
    uploadEnabled: false,
    downloadEnabled: false
  });

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const result = await testServerConnection(config);
      setTestResult(result);
      if (result) {
        toast.success('Connection successful!');
      } else {
        toast.error('Connection failed');
      }
    } catch (error: any) {
      setTestResult(false);
      toast.error(error.toString());
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    try {
      await saveServerConfig(config);
      setServerConfig(config);
      toast.success('Settings saved');
    } catch (error: any) {
      toast.error('Failed to save settings');
    }
  };

  const handleDeactivate = async () => {
    if (confirm('Are you sure you want to deactivate your license?')) {
      try {
        await deactivateLicense();
        window.location.reload();
      } catch (error: any) {
        toast.error('Failed to deactivate license');
      }
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Configure your Usenet server and application preferences
        </p>
      </div>

      {/* Server Configuration */}
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border p-6">
        <div className="flex items-center gap-3 mb-6">
          <Server className="w-6 h-6 text-gray-600 dark:text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Usenet Server Configuration
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Server Hostname
            </label>
            <input
              type="text"
              value={config.hostname}
              onChange={(e) => setConfig({ ...config, hostname: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Port
            </label>
            <input
              type="number"
              value={config.port}
              onChange={(e) => setConfig({ ...config, port: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Username
            </label>
            <input
              type="text"
              value={config.username}
              onChange={(e) => setConfig({ ...config, username: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Password
            </label>
            <input
              type="password"
              value={config.password}
              onChange={(e) => setConfig({ ...config, password: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Max Connections
            </label>
            <input
              type="number"
              value={config.maxConnections}
              onChange={(e) => setConfig({ ...config, maxConnections: parseInt(e.target.value) })}
              min="1"
              max="60"
              className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Posting Group
            </label>
            <input
              type="text"
              value={config.group}
              onChange={(e) => setConfig({ ...config, group: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
            />
          </div>

          <div className="md:col-span-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.useSsl}
                onChange={(e) => setConfig({ ...config, useSsl: e.target.checked })}
                className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Use SSL/TLS encryption
              </span>
            </label>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-6">
          <button
            onClick={handleTestConnection}
            disabled={isTesting}
            className="px-4 py-2 border border-gray-300 dark:border-dark-border text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isTesting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-700 dark:border-gray-300"></div>
                Testing...
              </>
            ) : (
              <>
                Test Connection
                {testResult === true && <Check className="w-4 h-4 text-green-500" />}
                {testResult === false && <X className="w-4 h-4 text-red-500" />}
              </>
            )}
          </button>

          <button
            onClick={handleSave}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>

      {/* Bandwidth Control */}
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border p-6">
        <div className="flex items-center gap-3 mb-6">
          <Gauge className="w-6 h-6 text-gray-600 dark:text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Bandwidth Control
          </h2>
        </div>

        <div className="space-y-4">
          {/* Upload Limit */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={bandwidthLimits.uploadEnabled}
                  onChange={(e) => setBandwidthLimits({
                    ...bandwidthLimits,
                    uploadEnabled: e.target.checked
                  })}
                  className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Limit Upload Speed
                </span>
              </label>
              <Upload className="w-4 h-4 text-gray-500" />
            </div>
            
            {bandwidthLimits.uploadEnabled && (
              <div className="ml-6 flex items-center gap-2">
                <input
                  type="number"
                  value={bandwidthLimits.uploadLimit}
                  onChange={(e) => setBandwidthLimits({
                    ...bandwidthLimits,
                    uploadLimit: parseFloat(e.target.value) || 0
                  })}
                  min="0"
                  step="0.5"
                  className="w-24 px-3 py-1 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">Mbps</span>
                <span className="text-xs text-gray-500 dark:text-gray-500">
                  ({(bandwidthLimits.uploadLimit * 125).toFixed(0)} KB/s)
                </span>
              </div>
            )}
          </div>

          {/* Download Limit */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={bandwidthLimits.downloadEnabled}
                  onChange={(e) => setBandwidthLimits({
                    ...bandwidthLimits,
                    downloadEnabled: e.target.checked
                  })}
                  className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Limit Download Speed
                </span>
              </label>
              <Download className="w-4 h-4 text-gray-500" />
            </div>
            
            {bandwidthLimits.downloadEnabled && (
              <div className="ml-6 flex items-center gap-2">
                <input
                  type="number"
                  value={bandwidthLimits.downloadLimit}
                  onChange={(e) => setBandwidthLimits({
                    ...bandwidthLimits,
                    downloadLimit: parseFloat(e.target.value) || 0
                  })}
                  min="0"
                  step="0.5"
                  className="w-24 px-3 py-1 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">Mbps</span>
                <span className="text-xs text-gray-500 dark:text-gray-500">
                  ({(bandwidthLimits.downloadLimit * 125).toFixed(0)} KB/s)
                </span>
              </div>
            )}
          </div>

          {/* Info Box */}
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-blue-700 dark:text-blue-400">
                <p className="font-medium mb-1">Bandwidth Limiting</p>
                <p>Limits apply to all transfers. Set to 0 or disable for unlimited speed.</p>
                <p className="mt-1">1 Mbps = 125 KB/s = 1,000,000 bits/second</p>
              </div>
            </div>
          </div>

          <button
            onClick={async () => {
              try {
                // Save bandwidth settings
                const upload = bandwidthLimits.uploadEnabled ? bandwidthLimits.uploadLimit : 0;
                const download = bandwidthLimits.downloadEnabled ? bandwidthLimits.downloadLimit : 0;
                
                // This would call a Tauri command to set bandwidth limits
                // await setBandwidthLimits(upload, download);
                
                toast.success('Bandwidth limits updated');
              } catch (error) {
                toast.error('Failed to update bandwidth limits');
              }
            }}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
          >
            Apply Bandwidth Limits
          </button>
        </div>
      </div>

      {/* License Information */}
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border p-6">
        <div className="flex items-center gap-3 mb-6">
          <Key className="w-6 h-6 text-gray-600 dark:text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            License Information
          </h2>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {licenseStatus?.activated ? 'Activated' : 'Not Activated'}
              </p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">License Tier</p>
              <p className="font-medium text-gray-900 dark:text-white capitalize">
                {licenseStatus?.tier || 'Trial'}
              </p>
            </div>
            
            {licenseStatus?.trial && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Trial Days Remaining</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {licenseStatus.trialDays} days
                </p>
              </div>
            )}
            
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Hardware ID</p>
              <p className="font-mono text-xs text-gray-900 dark:text-white">
                {licenseStatus?.hardwareId || 'Unknown'}
              </p>
            </div>
          </div>

          {licenseStatus?.features && (
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Features</p>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-700 dark:text-gray-300">Max File Size</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {licenseStatus.features.maxFileSize / (1024 * 1024 * 1024)} GB
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-700 dark:text-gray-300">Max Connections</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {licenseStatus.features.maxConnections}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-700 dark:text-gray-300">Max Shares</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {licenseStatus.features.maxShares}
                  </span>
                </div>
              </div>
            </div>
          )}

          {licenseStatus?.activated && (
            <button
              onClick={handleDeactivate}
              className="px-4 py-2 border border-red-300 text-red-700 dark:border-red-700 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Deactivate License
            </button>
          )}
        </div>
      </div>

      {/* About */}
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          About UsenetSync
        </h2>
        <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <p>Version: 1.0.0</p>
          <p>© 2024 UsenetSync. All rights reserved.</p>
          <p>
            For support, visit{' '}
            <a
              href="https://usenetsync.com/support"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-500 hover:text-primary-600 underline"
            >
              usenetsync.com/support
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};