import React, { useState } from 'react';
import { 
  Search, 
  Bell, 
  Settings, 
  User, 
  HelpCircle,
  Moon,
  Sun,
  LogOut,
  ChevronDown,
  Command
} from 'lucide-react';
import { SearchBar } from './SearchBar';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

interface HeaderBarProps {
  title?: string;
  showSearch?: boolean;
  onThemeToggle?: () => void;
  isDarkMode?: boolean;
  userName?: string;
  notifications?: number;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({
  title = 'UsenetSync',
  showSearch = true,
  onThemeToggle,
  isDarkMode = false,
  userName = 'User',
  notifications = 0
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  
  const { shortcuts } = useKeyboardShortcuts();

  const handleLogout = () => {
    if (confirm('Are you sure you want to logout?')) {
      // Handle logout
      console.log('Logging out...');
    }
  };

  const handleSettings = () => {
    // Navigate to settings
    window.location.href = '#/settings';
  };

  const handleHelp = () => {
    // Open help documentation
    window.open('https://docs.usenetsync.com', '_blank');
  };

  return (
    <header className="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Left Section - Logo/Title */}
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              {title}
            </h1>
            
            {/* Command Palette Trigger */}
            <button
              onClick={() => setShowCommandPalette(true)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-dark-border rounded-lg hover:bg-gray-200 dark:hover:bg-dark-bg transition-colors"
            >
              <Command className="w-3 h-3" />
              <span>Quick Actions</span>
              <kbd className="ml-2 px-1.5 py-0.5 text-xs bg-white dark:bg-dark-surface rounded border border-gray-300 dark:border-dark-border">
                ⌘K
              </kbd>
            </button>
          </div>

          {/* Center Section - Search */}
          {showSearch && (
            <div className="flex-1 max-w-xl mx-4">
              <SearchBar />
            </div>
          )}

          {/* Right Section - Actions */}
          <div className="flex items-center gap-3">
            {/* Theme Toggle */}
            {onThemeToggle && (
              <button
                onClick={onThemeToggle}
                className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
                title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {isDarkMode ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </button>
            )}

            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
                title="Notifications"
              >
                <Bell className="w-5 h-5" />
                {notifications > 0 && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                )}
              </button>
              
              {/* Notifications Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-dark-surface rounded-lg shadow-lg border border-gray-200 dark:border-dark-border z-50">
                  <div className="p-4 border-b border-gray-200 dark:border-dark-border">
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      Notifications
                    </h3>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {notifications > 0 ? (
                      <div className="p-4 space-y-3">
                        <div className="flex gap-3">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                          <div className="flex-1">
                            <p className="text-sm text-gray-900 dark:text-white">
                              Upload completed successfully
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              2 minutes ago
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-3">
                          <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                          <div className="flex-1">
                            <p className="text-sm text-gray-900 dark:text-white">
                              New share created
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              15 minutes ago
                            </p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-8 text-center">
                        <Bell className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          No new notifications
                        </p>
                      </div>
                    )}
                  </div>
                  <div className="p-3 border-t border-gray-200 dark:border-dark-border">
                    <button className="w-full text-sm text-primary-500 hover:text-primary-600">
                      View all notifications
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Help */}
            <button
              onClick={handleHelp}
              className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
              title="Help"
            >
              <HelpCircle className="w-5 h-5" />
            </button>

            {/* Settings */}
            <button
              onClick={handleSettings}
              className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
              title="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>

            <div className="w-px h-6 bg-gray-200 dark:bg-dark-border" />

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
              >
                <div className="w-7 h-7 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                </div>
                <span>{userName}</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              
              {/* User Dropdown */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-dark-surface rounded-lg shadow-lg border border-gray-200 dark:border-dark-border z-50">
                  <div className="p-4 border-b border-gray-200 dark:border-dark-border">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {userName}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      user@example.com
                    </p>
                  </div>
                  <div className="p-2">
                    <button
                      onClick={() => window.location.href = '#/profile'}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors text-left"
                    >
                      <User className="w-4 h-4" />
                      Profile
                    </button>
                    <button
                      onClick={handleSettings}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors text-left"
                    >
                      <Settings className="w-4 h-4" />
                      Settings
                    </button>
                    <div className="my-2 border-t border-gray-200 dark:border-dark-border" />
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors text-left"
                    >
                      <LogOut className="w-4 h-4" />
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Command Palette Modal */}
      {showCommandPalette && (
        <div className="fixed inset-0 bg-black/50 flex items-start justify-center pt-20 z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow-xl w-full max-w-2xl mx-4">
            <div className="p-4 border-b border-gray-200 dark:border-dark-border">
              <input
                type="text"
                placeholder="Type a command or search..."
                className="w-full px-3 py-2 bg-gray-50 dark:bg-dark-bg border border-gray-200 dark:border-dark-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:text-white"
                autoFocus
              />
            </div>
            <div className="max-h-96 overflow-y-auto p-2">
              <div className="space-y-1">
                {shortcuts.slice(0, 10).map((shortcut, index) => (
                  <button
                    key={index}
                    className="w-full flex items-center justify-between px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors text-left"
                  >
                    <span>{shortcut.description}</span>
                    <kbd className="px-2 py-1 text-xs bg-gray-100 dark:bg-dark-border rounded">
                      {shortcut.keys.join(' + ')}
                    </kbd>
                  </button>
                ))}
              </div>
            </div>
            <div className="p-3 border-t border-gray-200 dark:border-dark-border flex justify-end">
              <button
                onClick={() => setShowCommandPalette(false)}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};