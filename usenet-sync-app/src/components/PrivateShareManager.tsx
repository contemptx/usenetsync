import React, { useState } from 'react';
import { UserPlus, X, Copy, Check, Info } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface PrivateShareManagerProps {
  authorizedUsers: string[];
  onUsersChange: (users: string[]) => void;
  disabled?: boolean;
}

export const PrivateShareManager: React.FC<PrivateShareManagerProps> = ({
  authorizedUsers = [],
  onUsersChange,
  disabled = false
}) => {
  const [newUserId, setNewUserId] = useState('');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleAddUser = () => {
    const trimmedId = newUserId.trim();
    
    // Validate User ID format (64 hex characters)
    if (!/^[a-f0-9]{64}$/i.test(trimmedId)) {
      toast.error('Invalid User ID format. Must be 64 hexadecimal characters.');
      return;
    }

    if (authorizedUsers.includes(trimmedId)) {
      toast.error('This User ID is already authorized');
      return;
    }

    onUsersChange([...authorizedUsers, trimmedId]);
    setNewUserId('');
    toast.success('User ID added successfully');
  };

  const handleRemoveUser = (userId: string) => {
    onUsersChange(authorizedUsers.filter(id => id !== userId));
    toast.success('User ID removed');
  };

  const handleCopyUserId = (userId: string, index: number) => {
    navigator.clipboard.writeText(userId);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
    toast.success('User ID copied to clipboard');
  };

  const formatUserId = (userId: string) => {
    // Show first 8 and last 8 characters
    return `${userId.slice(0, 8)}...${userId.slice(-8)}`;
  };

  return (
    <div className="space-y-4">
      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div className="text-sm text-blue-700 dark:text-blue-300">
            <p className="font-medium mb-1">Private Share Access</p>
            <p>Add User IDs of people who should have access to this private share.</p>
          </div>
        </div>
      </div>

      {/* Add User Section */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Add Authorized User
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={newUserId}
            onChange={(e) => setNewUserId(e.target.value)}
            disabled={disabled}
            placeholder="Enter 64-character User ID"
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-bg font-mono text-sm disabled:opacity-50"
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !disabled) {
                handleAddUser();
              }
            }}
          />
          <button
            onClick={handleAddUser}
            disabled={disabled || !newUserId.trim()}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <UserPlus className="w-4 h-4" />
            Add
          </button>
        </div>
      </div>

      {/* Authorized Users List */}
      {authorizedUsers.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Authorized Users ({authorizedUsers.length})
          </label>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {authorizedUsers.map((userId, index) => (
              <div
                key={userId}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-center gap-3 flex-1">
                  <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-primary">
                      {index + 1}
                    </span>
                  </div>
                  <span className="font-mono text-sm text-gray-700 dark:text-gray-300">
                    {formatUserId(userId)}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleCopyUserId(userId, index)}
                    disabled={disabled}
                    className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
                    title="Copy User ID"
                  >
                    {copiedIndex === index ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <Copy className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                  <button
                    onClick={() => handleRemoveUser(userId)}
                    disabled={disabled}
                    className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/20 rounded transition-colors disabled:opacity-50"
                    title="Remove User"
                  >
                    <X className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {authorizedUsers.length === 0 && (
        <div className="text-center py-6 text-gray-500 dark:text-gray-400">
          <p className="text-sm">No authorized users yet</p>
          <p className="text-xs mt-1">Add User IDs to grant access to this private share</p>
        </div>
      )}
    </div>
  );
};
