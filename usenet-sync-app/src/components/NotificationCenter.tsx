import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Info, 
  AlertTriangle,
  Download,
  Upload,
  Share2,
  Trash2,
  Settings,
  Clock
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

export type NotificationType = 'info' | 'success' | 'warning' | 'error';
export type NotificationCategory = 'upload' | 'download' | 'share' | 'system' | 'general';

export interface Notification {
  id: string;
  type: NotificationType;
  category: NotificationCategory;
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  persistent: boolean;
  actions?: NotificationAction[];
  metadata?: Record<string, any>;
}

interface NotificationAction {
  label: string;
  action: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
}

interface NotificationCenterProps {
  notifications: Notification[];
  onMarkAsRead?: (id: string) => void;
  onMarkAllAsRead?: () => void;
  onDismiss?: (id: string) => void;
  onClearAll?: () => void;
  maxHeight?: string;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  notifications,
  onMarkAsRead,
  onMarkAllAsRead,
  onDismiss,
  onClearAll,
  maxHeight = '500px'
}) => {
  const [filter, setFilter] = useState<NotificationCategory | 'all'>('all');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  
  const filteredNotifications = notifications.filter(n => {
    if (filter !== 'all' && n.category !== filter) return false;
    if (showUnreadOnly && n.read) return false;
    return true;
  });
  
  const unreadCount = notifications.filter(n => !n.read).length;
  
  const getIcon = (notification: Notification) => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };
  
  const getCategoryIcon = (category: NotificationCategory) => {
    switch (category) {
      case 'upload':
        return <Upload className="w-4 h-4" />;
      case 'download':
        return <Download className="w-4 h-4" />;
      case 'share':
        return <Share2 className="w-4 h-4" />;
      case 'system':
        return <Settings className="w-4 h-4" />;
      default:
        return <Bell className="w-4 h-4" />;
    }
  };
  
  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      onMarkAsRead?.(notification.id);
    }
  };
  
  return (
    <div className="flex flex-col h-full bg-white dark:bg-dark-surface rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-dark-border">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Notifications
            </h2>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-full">
                {unreadCount} new
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <button
                onClick={onMarkAllAsRead}
                className="text-sm text-primary-500 hover:text-primary-600"
              >
                Mark all as read
              </button>
            )}
            {filteredNotifications.length > 0 && (
              <button
                onClick={onClearAll}
                className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              >
                Clear all
              </button>
            )}
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-gray-100 dark:bg-dark-border rounded-lg p-1">
            <button
              onClick={() => setFilter('all')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filter === 'all'
                  ? 'bg-white dark:bg-dark-surface text-primary-500'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('upload')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filter === 'upload'
                  ? 'bg-white dark:bg-dark-surface text-primary-500'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Uploads
            </button>
            <button
              onClick={() => setFilter('download')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filter === 'download'
                  ? 'bg-white dark:bg-dark-surface text-primary-500'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Downloads
            </button>
            <button
              onClick={() => setFilter('share')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filter === 'share'
                  ? 'bg-white dark:bg-dark-surface text-primary-500'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Shares
            </button>
            <button
              onClick={() => setFilter('system')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filter === 'system'
                  ? 'bg-white dark:bg-dark-surface text-primary-500'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              System
            </button>
          </div>
          
          <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={(e) => setShowUnreadOnly(e.target.checked)}
              className="rounded border-gray-300 dark:border-gray-600 text-primary-500 focus:ring-primary-500"
            />
            Unread only
          </label>
        </div>
      </div>
      
      {/* Notifications List */}
      <div className="flex-1 overflow-y-auto" style={{ maxHeight }}>
        {filteredNotifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full p-8">
            <Bell className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-3" />
            <p className="text-gray-500 dark:text-gray-400">No notifications</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-dark-border">
            {filteredNotifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 hover:bg-gray-50 dark:hover:bg-dark-border/50 transition-colors cursor-pointer ${
                  !notification.read ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''
                }`}
                onClick={() => handleNotificationClick(notification)}
              >
                <div className="flex items-start gap-3">
                  {getIcon(notification)}
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                        {notification.title}
                      </h3>
                      {getCategoryIcon(notification.category)}
                      {!notification.read && (
                        <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {notification.message}
                    </p>
                    
                    {notification.actions && notification.actions.length > 0 && (
                      <div className="flex items-center gap-2 mt-2">
                        {notification.actions.map((action, index) => (
                          <button
                            key={index}
                            onClick={(e) => {
                              e.stopPropagation();
                              action.action();
                            }}
                            className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                              action.variant === 'primary'
                                ? 'bg-primary-500 text-white hover:bg-primary-600'
                                : action.variant === 'danger'
                                ? 'bg-red-500 text-white hover:bg-red-600'
                                : 'bg-gray-100 dark:bg-dark-border text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-surface'
                            }`}
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    )}
                    
                    <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-500">
                      <Clock className="w-3 h-3" />
                      {formatDistanceToNow(notification.timestamp, { addSuffix: true })}
                    </div>
                  </div>
                  
                  {!notification.persistent && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDismiss?.(notification.id);
                      }}
                      className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Notification Manager Hook
export const useNotifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  
  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false
    };
    
    setNotifications(prev => [newNotification, ...prev]);
    
    // Show toast for important notifications
    if (notification.type === 'error') {
      toast.error(notification.title);
    } else if (notification.type === 'success') {
      toast.success(notification.title);
    }
    
    return newNotification.id;
  };
  
  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };
  
  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(n => ({ ...n, read: true }))
    );
  };
  
  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };
  
  const clearAll = () => {
    setNotifications([]);
  };
  
  return {
    notifications,
    addNotification,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    clearAll
  };
};