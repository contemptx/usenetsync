import React from 'react';

interface ProgressBarProps {
  percentage: number;
  message?: string;
  status?: 'starting' | 'processing' | 'completed' | 'error';
  operation?: string;
  showPercentage?: boolean;
  height?: string;
  color?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  percentage,
  message,
  status = 'processing',
  operation,
  showPercentage = true,
  height = 'h-6',
  color
}) => {
  const getColor = () => {
    if (color) return color;
    switch (status) {
      case 'starting':
        return 'bg-blue-500';
      case 'processing':
        return 'bg-blue-600';
      case 'completed':
        return 'bg-green-600';
      case 'error':
        return 'bg-red-600';
      default:
        return 'bg-blue-600';
    }
  };

  const getAnimationClass = () => {
    if (status === 'processing' && percentage < 100) {
      return 'animate-pulse';
    }
    return '';
  };

  return (
    <div className="w-full space-y-2">
      {operation && (
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium capitalize">{operation}</span>
          {showPercentage && (
            <span className="text-gray-600 dark:text-gray-400">
              {percentage}%
            </span>
          )}
        </div>
      )}
      
      <div className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full ${height} overflow-hidden`}>
        <div
          className={`${getColor()} ${height} rounded-full transition-all duration-300 ease-out ${getAnimationClass()} relative`}
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
        >
          {showPercentage && percentage > 5 && (
            <span className="absolute inset-0 flex items-center justify-center text-white text-xs font-medium">
              {percentage}%
            </span>
          )}
        </div>
      </div>
      
      {message && (
        <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
          {message}
        </p>
      )}
    </div>
  );
};