import React, { useState, useEffect } from 'react';
import { User, Shield, Copy, Check, AlertCircle, Info } from 'lucide-react';
import { getUserInfo, initializeUser } from '../lib/tauri';
import { toast } from 'react-hot-toast';

export default function UserProfile() {
  const [userInfo, setUserInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadUserInfo();
  }, []);

  const loadUserInfo = async () => {
    try {
      setLoading(true);
      const info = await getUserInfo();
      setUserInfo(info);
    } catch (error) {
      console.error('Error loading user info:', error);
      // User might not be initialized yet
      setUserInfo(null);
    } finally {
      setLoading(false);
    }
  };

  const handleInitialize = async () => {
    try {
      const userId = await initializeUser();
      toast.success('User profile initialized successfully');
      await loadUserInfo();
    } catch (error) {
      toast.error(`Failed to initialize user: ${error}`);
    }
  };

  const copyUserId = () => {
    if (userInfo?.user_id) {
      navigator.clipboard.writeText(userInfo.user_id);
      setCopied(true);
      toast.success('User ID copied to clipboard');
      setTimeout(() => setCopied(false), 3000);
    }
  };

  const formatUserId = (userId: string) => {
    if (!userId) return '';
    // Always show full ID
    return userId;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!userInfo || !userInfo.initialized) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-6 border border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-yellow-600 dark:text-yellow-400 mt-1" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                User Profile Not Initialized
              </h3>
              <p className="text-yellow-700 dark:text-yellow-300 mb-4">
                Your user profile needs to be initialized before you can use private shares. 
                This will generate a unique, permanent User ID that cannot be recovered if lost.
              </p>
              <button
                onClick={handleInitialize}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-md hover:shadow-lg"
              >
                Initialize User Profile
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <User className="w-8 h-8 text-primary" />
        <h1 className="text-2xl font-bold">User Profile</h1>
      </div>

      {/* User Info Card */}
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-lg p-6">
        <div className="space-y-6">
          {/* User ID */}
          <div>
            <label className="block text-base font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Your Unique User ID
            </label>
            <div className="flex items-center gap-3">
              <div className="flex-1 font-mono bg-gray-50 dark:bg-gray-800 rounded-lg px-4 py-4 flex items-center justify-between border border-gray-300 dark:border-gray-600">
                <span 
                  className="text-base text-gray-900 dark:text-gray-100 select-all break-all font-medium"
                  title="Your unique User ID"
                >
                  {formatUserId(userInfo.user_id)}
                </span>
                <button
                  onClick={copyUserId}
                  className="ml-3 p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                  title="Copy User ID to clipboard"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4 text-green-500" />
                      <span className="text-xs text-green-600 dark:text-green-400 font-medium">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <span className="text-xs text-gray-600 dark:text-gray-400 font-medium">Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Share this ID with folder owners to get access to their private shares. This ID is permanent and cannot be regenerated.
            </p>
          </div>

          {/* Created Date */}
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Profile Created
            </label>
            <div className="text-sm">
              {new Date(userInfo.created_at).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Security Information */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400 mt-1" />
          <div>
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
              Security Information
            </h3>
            <ul className="space-y-2 text-sm text-blue-700 dark:text-blue-300">
              <li className="flex items-start gap-2">
                <span className="text-blue-500">•</span>
                <span>Your User ID is permanent and cannot be changed or regenerated</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500">•</span>
                <span>If you lose your User ID, you will need to request access again from folder owners</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500">•</span>
                <span>Your User ID is used for zero-knowledge proof authentication on private shares</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500">•</span>
                <span>Never share your User ID publicly - only with trusted folder owners</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <Info className="w-6 h-6 text-gray-600 dark:text-gray-400 mt-1" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              How Private Shares Work
            </h3>
            <ol className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
              <li>
                <span className="font-medium">1. Share Your ID:</span> Send your User ID to the folder owner
              </li>
              <li>
                <span className="font-medium">2. Owner Grants Access:</span> The folder owner adds your User ID to their private share
              </li>
              <li>
                <span className="font-medium">3. Access Granted:</span> You can now download the private share using zero-knowledge proof authentication
              </li>
              <li>
                <span className="font-medium">4. Secure Access:</span> Your User ID is never transmitted or stored on servers
              </li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}