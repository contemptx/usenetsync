import React from 'react';
import { SegmentProgress as SegmentType } from '../../types';
import clsx from 'clsx';

interface SegmentProgressProps {
  segments: SegmentType[];
  className?: string;
}

export const SegmentProgress: React.FC<SegmentProgressProps> = ({ segments, className }) => {
  const totalSegments = segments.length;
  const completedSegments = segments.filter(s => s.completed).length;
  const percentage = totalSegments > 0 ? (completedSegments / totalSegments) * 100 : 0;

  // Group segments into chunks for better visualization
  const chunkSize = Math.ceil(totalSegments / 100); // Max 100 visual blocks
  const visualSegments: boolean[] = [];
  
  for (let i = 0; i < totalSegments; i += chunkSize) {
    const chunk = segments.slice(i, i + chunkSize);
    const isCompleted = chunk.every(s => s.completed);
    visualSegments.push(isCompleted);
  }

  return (
    <div className={clsx('space-y-2', className)}>
      <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
        <span>{completedSegments} / {totalSegments} segments</span>
        <span>{percentage.toFixed(1)}%</span>
      </div>
      
      <div className="relative">
        {/* Background progress bar */}
        <div className="h-2 bg-gray-200 dark:bg-dark-border rounded-full overflow-hidden">
          <div 
            className="h-full bg-primary-500 transition-all duration-300 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
        
        {/* Segment grid visualization */}
        {totalSegments <= 50 && (
          <div className="mt-2 grid grid-cols-25 gap-px">
            {segments.map((segment, idx) => (
              <div
                key={idx}
                className={clsx(
                  'w-2 h-2 rounded-sm transition-all duration-200',
                  segment.completed 
                    ? 'bg-green-500 scale-100' 
                    : segment.retries > 0
                    ? 'bg-yellow-500 scale-90'
                    : 'bg-gray-300 dark:bg-gray-600 scale-75'
                )}
                title={`Segment ${idx + 1}: ${segment.completed ? 'Complete' : segment.retries > 0 ? `Retrying (${segment.retries})` : 'Pending'}`}
              />
            ))}
          </div>
        )}
        
        {/* Compressed visualization for many segments */}
        {totalSegments > 50 && (
          <div className="mt-2 flex gap-px">
            {visualSegments.map((completed, idx) => (
              <div
                key={idx}
                className={clsx(
                  'flex-1 h-1 transition-all duration-200',
                  completed ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                )}
                style={{ minWidth: '2px' }}
              />
            ))}
          </div>
        )}
      </div>
      
      {/* Failed segments indicator */}
      {segments.some(s => s.retries >= 3) && (
        <div className="flex items-center text-xs text-yellow-600 dark:text-yellow-400">
          <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          Some segments need retry
        </div>
      )}
    </div>
  );
};