import React, { useState } from 'react';
import { activateLicense, startTrial, checkLicense } from '../lib/tauri.ts';
import { useAppStore } from '../stores/useAppStore';
import { AlertCircle, Key, Clock, CheckCircle } from 'lucide-react';

interface LicenseActivationProps {
  onActivated: () => void;
}

export const LicenseActivation: React.FC<LicenseActivationProps> = ({ onActivated }) => {
  const [licenseKey, setLicenseKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const setLicenseStatus = useAppStore((state) => state.setLicenseStatus);

  const handleActivate = async () => {
    if (!licenseKey.trim()) {
      setError('Please enter a license key');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const success = await activateLicense(licenseKey);
      if (success) {
        const status = await checkLicense();
        setLicenseStatus(status);
        setShowSuccess(true);
        setTimeout(() => {
          onActivated();
        }, 2000);
      }
    } catch (err: any) {
      setError(err.toString());
    } finally {
      setLoading(false);
    }
  };

  const handleTrial = async () => {
    setLoading(true);
    setError('');
    
    try {
      
      const status = await checkLicense();
      setLicenseStatus(status);
      setShowSuccess(true);
      setTimeout(() => {
        onActivated();
      }, 2000);
    } catch (err: any) {
      setError(err.toString());
    } finally {
      setLoading(false);
    }
  };

  const formatLicenseKey = (value: string) => {
    // Format as XXXX-XXXX-XXXX-XXXX
    const cleaned = value.replace(/[^A-Z0-9]/gi, '').toUpperCase();
    const chunks = cleaned.match(/.{1,4}/g) || [];
    return chunks.slice(0, 4).join('-');
  };

  if (showSuccess) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-dark-surface rounded-lg p-8 max-w-md w-full mx-4 animate-fade-in">
          <div className="flex flex-col items-center">
            <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
            <h2 className="text-2xl font-bold mb-2 dark:text-white">Activation Successful!</h2>
            <p className="text-gray-600 dark:text-gray-400 text-center">
              UsenetSync has been activated successfully. Launching application...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-dark-surface rounded-lg p-8 max-w-md w-full mx-4 animate-slide-in">
        <div className="flex items-center mb-6">
          <Key className="w-8 h-8 text-primary-500 mr-3" />
          <h2 className="text-2xl font-bold dark:text-white">Activate UsenetSync</h2>
        </div>
        
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Enter your license key to unlock all features, or start a 14-day free trial.
        </p>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 dark:text-gray-300">
              License Key
            </label>
            <input
              type="text"
              placeholder="XXXX-XXXX-XXXX-XXXX"
              value={licenseKey}
              onChange={(e) => setLicenseKey(formatLicenseKey(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-dark-bg dark:text-white"
              disabled={loading}
              maxLength={19}
            />
          </div>
          
          {error && (
            <div className="flex items-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0" />
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}
          
          <div className="flex gap-3">
            <button
              onClick={handleActivate}
              disabled={loading || !licenseKey}
              className="flex-1 bg-primary-500 text-white px-4 py-2 rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Activating...' : 'Activate'}
            </button>
            
            <button
              onClick={handleTrial}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 border border-gray-300 dark:border-dark-border text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Clock className="w-4 h-4" />
              Start Trial
            </button>
          </div>
          
          <div className="pt-4 border-t border-gray-200 dark:border-dark-border">
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
              Need a license? Visit{' '}
              <a
                href="https://usenetsync.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-500 hover:text-primary-600 underline"
              >
                usenetsync.com
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};