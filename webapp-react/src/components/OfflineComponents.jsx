/**
 * Offline UI Components for Data20 PWA
 * Phase 8.1.3: Offline UI Components
 *
 * React components for offline functionality:
 * - OfflineStatusBanner: Network status indicator
 * - OfflineQueuePanel: Manage offline operations queue
 * - SyncButton: Manual sync trigger
 * - StorageStats: Database storage statistics
 * - QueueItem: Single queue item display
 * - QueueStats: Queue statistics widget
 *
 * Version: 1.0.0
 * Created: 2026-01-05
 */

import React from 'react';
import {
  useOfflineStatus,
  useOfflineQueue,
  useOfflineSync,
  useOfflineStorage,
  useNetworkSpeed,
} from '../hooks/useOffline.js';

/**
 * OfflineStatusBanner
 * Shows current network status with visual indicator
 *
 * @param {object} props
 * @param {boolean} props.showWhenOnline - Show banner when online (default: false)
 * @param {string} props.className - Additional CSS classes
 */
export function OfflineStatusBanner({ showWhenOnline = false, className = '' }) {
  const { isOnline, isOffline } = useOfflineStatus();
  const { effectiveType, downlink } = useNetworkSpeed();

  // Don't show when online unless explicitly requested
  if (isOnline && !showWhenOnline) {
    return null;
  }

  const statusClass = isOnline ? 'bg-green-100 text-green-800 border-green-300' : 'bg-yellow-100 text-yellow-800 border-yellow-300';

  const icon = isOnline ? '✓' : '⚠️';

  const message = isOnline
    ? `Online${effectiveType !== 'unknown' ? ` (${effectiveType})` : ''}`
    : 'Offline - Some features are limited';

  const details = isOnline && downlink
    ? `${downlink} Mbps`
    : isOffline
    ? 'Changes will sync when connection is restored'
    : '';

  return (
    <div className={`px-4 py-3 border-b ${statusClass} ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{icon}</span>
          <div>
            <p className="font-medium">{message}</p>
            {details && <p className="text-sm opacity-80">{details}</p>}
          </div>
        </div>

        {isOffline && (
          <button
            onClick={() => window.location.reload()}
            className="px-3 py-1 text-sm bg-yellow-200 hover:bg-yellow-300 rounded transition-colors"
          >
            Retry Connection
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * SyncButton
 * Manual sync trigger with progress indication
 *
 * @param {object} props
 * @param {string} props.variant - Button variant: 'primary', 'secondary', 'text'
 * @param {string} props.size - Button size: 'sm', 'md', 'lg'
 * @param {boolean} props.showLastSync - Show last sync time
 * @param {string} props.className - Additional CSS classes
 */
export function SyncButton({
  variant = 'primary',
  size = 'md',
  showLastSync = true,
  className = '',
}) {
  const { sync, syncing, lastSync } = useOfflineSync();
  const { isOffline } = useOfflineStatus();

  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    text: 'text-blue-600 hover:text-blue-700 hover:bg-blue-50',
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };

  const formatLastSync = () => {
    if (!lastSync) return null;

    const diffMs = Date.now() - lastSync.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <div className={className}>
      <button
        onClick={sync}
        disabled={syncing || isOffline}
        className={`
          ${variantClasses[variant]}
          ${sizeClasses[size]}
          rounded font-medium transition-colors
          disabled:opacity-50 disabled:cursor-not-allowed
          flex items-center space-x-2
        `}
      >
        <span className={syncing ? 'animate-spin' : ''}>
          {syncing ? '🔄' : '↻'}
        </span>
        <span>{syncing ? 'Syncing...' : 'Sync'}</span>
      </button>

      {showLastSync && lastSync && (
        <p className="text-xs text-gray-500 mt-1">
          Last synced: {formatLastSync()}
        </p>
      )}
    </div>
  );
}

/**
 * QueueStats
 * Display queue statistics
 *
 * @param {object} props
 * @param {boolean} props.compact - Compact display mode
 * @param {string} props.className - Additional CSS classes
 */
export function QueueStats({ compact = false, className = '' }) {
  const { stats, loading } = useOfflineQueue();

  if (loading || !stats) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-4 bg-gray-200 rounded w-24"></div>
      </div>
    );
  }

  if (compact) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        {stats.pending > 0 && (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
            {stats.pending} pending
          </span>
        )}
        {stats.failed > 0 && (
          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
            {stats.failed} failed
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-4 gap-4 ${className}`}>
      <div className="text-center p-4 bg-gray-100 rounded">
        <div className="text-2xl font-bold text-gray-800">{stats.total}</div>
        <div className="text-xs text-gray-600">Total</div>
      </div>

      <div className="text-center p-4 bg-yellow-100 rounded">
        <div className="text-2xl font-bold text-yellow-800">{stats.pending}</div>
        <div className="text-xs text-yellow-700">Pending</div>
      </div>

      <div className="text-center p-4 bg-green-100 rounded">
        <div className="text-2xl font-bold text-green-800">{stats.completed}</div>
        <div className="text-xs text-green-700">Completed</div>
      </div>

      <div className="text-center p-4 bg-red-100 rounded">
        <div className="text-2xl font-bold text-red-800">{stats.failed}</div>
        <div className="text-xs text-red-700">Failed</div>
      </div>
    </div>
  );
}

/**
 * QueueItem
 * Display single queue item
 *
 * @param {object} props
 * @param {object} props.item - Queue item
 * @param {function} props.onRemove - Remove callback
 * @param {function} props.onRetry - Retry callback
 */
export function QueueItem({ item, onRemove, onRetry }) {
  const statusColors = {
    pending: 'bg-yellow-50 border-yellow-200',
    processing: 'bg-blue-50 border-blue-200',
    completed: 'bg-green-50 border-green-200',
    failed: 'bg-red-50 border-red-200',
  };

  const statusIcons = {
    pending: '⏳',
    processing: '⚙️',
    completed: '✅',
    failed: '❌',
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`border rounded-lg p-4 ${statusColors[item.status]}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-lg">{statusIcons[item.status]}</span>
            <span className="font-medium text-gray-900">
              {item.type.replace(/_/g, ' ').toUpperCase()}
            </span>
            <span className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">
              Priority: {item.priority}
            </span>
          </div>

          <div className="text-sm text-gray-600 space-y-1">
            <div>
              <strong>Created:</strong> {formatDate(item.createdAt)}
            </div>

            {item.data && item.data.toolName && (
              <div>
                <strong>Tool:</strong> {item.data.toolName}
              </div>
            )}

            {item.error && (
              <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-800">
                <strong>Error:</strong> {item.error}
              </div>
            )}

            {item.retries > 0 && (
              <div>
                <strong>Retries:</strong> {item.retries} / {item.maxRetries}
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col space-y-2 ml-4">
          {item.status === 'failed' && onRetry && (
            <button
              onClick={() => onRetry(item)}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          )}

          {(item.status === 'completed' || item.status === 'failed') && onRemove && (
            <button
              onClick={() => onRemove(item.id)}
              className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition-colors"
            >
              Remove
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * OfflineQueuePanel
 * Full queue management panel
 *
 * @param {object} props
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.collapsible - Allow collapsing panel
 */
export function OfflineQueuePanel({ className = '', collapsible = true }) {
  const [collapsed, setCollapsed] = React.useState(false);
  const { queueItems, pending, stats, syncing, sync, clearCompleted, removeItem } =
    useOfflineQueue();
  const { isOffline } = useOfflineStatus();

  if (queueItems.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <p className="text-lg">📭</p>
          <p>No items in queue</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Offline Queue</h2>
            <p className="text-sm text-gray-500">
              {pending.length} pending operation{pending.length !== 1 ? 's' : ''}
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {stats && stats.completed > 0 && (
              <button
                onClick={clearCompleted}
                className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded transition-colors"
              >
                Clear Completed
              </button>
            )}

            <button
              onClick={sync}
              disabled={syncing || isOffline}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50 transition-colors"
            >
              {syncing ? 'Syncing...' : 'Sync Now'}
            </button>

            {collapsible && (
              <button
                onClick={() => setCollapsed(!collapsed)}
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
              >
                {collapsed ? '▼' : '▲'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      {!collapsed && stats && (
        <div className="px-6 py-4 border-b border-gray-200">
          <QueueStats />
        </div>
      )}

      {/* Queue Items */}
      {!collapsed && (
        <div className="px-6 py-4 max-h-96 overflow-y-auto space-y-3">
          {queueItems.map((item) => (
            <QueueItem
              key={item.id}
              item={item}
              onRemove={removeItem}
              onRetry={(retryItem) => {
                // Retry logic would go here
                console.log('Retry:', retryItem);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * StorageStats
 * Display database storage statistics
 *
 * @param {object} props
 * @param {boolean} props.detailed - Show detailed stats
 * @param {string} props.className - Additional CSS classes
 */
export function StorageStats({ detailed = false, className = '' }) {
  const { stats, refreshStats } = useOfflineStorage();

  if (!stats) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    );
  }

  const { stores, storage } = stats;

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Storage Statistics</h3>
        <button
          onClick={refreshStats}
          className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
        >
          ↻
        </button>
      </div>

      {/* Storage Usage */}
      {storage && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600">Storage Used</span>
            <span className="font-medium text-gray-900">
              {storage.usageMB} MB / {storage.quotaMB} MB
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${Math.min(storage.usagePercent, 100)}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {storage.usagePercent}% used
          </p>
        </div>
      )}

      {/* Store Counts */}
      {detailed && (
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-blue-50 rounded">
            <div className="text-xs text-blue-600 uppercase">Tools</div>
            <div className="text-2xl font-bold text-blue-900">{stores.tools}</div>
          </div>

          <div className="p-3 bg-green-50 rounded">
            <div className="text-xs text-green-600 uppercase">Jobs</div>
            <div className="text-2xl font-bold text-green-900">{stores.jobs}</div>
          </div>

          <div className="p-3 bg-yellow-50 rounded">
            <div className="text-xs text-yellow-600 uppercase">Queue</div>
            <div className="text-2xl font-bold text-yellow-900">
              {stores.offlineQueue}
            </div>
          </div>

          <div className="p-3 bg-purple-50 rounded">
            <div className="text-xs text-purple-600 uppercase">Cache</div>
            <div className="text-2xl font-bold text-purple-900">{stores.cache}</div>
          </div>
        </div>
      )}

      {!detailed && (
        <div className="text-sm text-gray-600">
          <div className="flex justify-between py-1">
            <span>Tools:</span>
            <span className="font-medium">{stores.tools}</span>
          </div>
          <div className="flex justify-between py-1">
            <span>Jobs:</span>
            <span className="font-medium">{stores.jobs}</span>
          </div>
          <div className="flex justify-between py-1">
            <span>Queue:</span>
            <span className="font-medium">{stores.offlineQueue}</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * OfflineBadge
 * Small badge showing offline status
 *
 * @param {object} props
 * @param {string} props.className - Additional CSS classes
 */
export function OfflineBadge({ className = '' }) {
  const { isOffline } = useOfflineStatus();

  if (!isOffline) return null;

  return (
    <span
      className={`px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded ${className}`}
    >
      Offline Mode
    </span>
  );
}

/**
 * NetworkIndicator
 * Visual network connection indicator
 *
 * @param {object} props
 * @param {string} props.size - Size: 'sm', 'md', 'lg'
 * @param {boolean} props.showLabel - Show status label
 * @param {string} props.className - Additional CSS classes
 */
export function NetworkIndicator({ size = 'md', showLabel = false, className = '' }) {
  const { isOnline } = useOfflineStatus();
  const { effectiveType } = useNetworkSpeed();

  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  };

  const pulseClass = isOnline ? 'animate-pulse' : '';

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div
        className={`${sizeClasses[size]} rounded-full ${
          isOnline ? 'bg-green-500' : 'bg-red-500'
        } ${pulseClass}`}
      ></div>
      {showLabel && (
        <span className="text-sm text-gray-600">
          {isOnline ? (effectiveType !== 'unknown' ? effectiveType : 'Online') : 'Offline'}
        </span>
      )}
    </div>
  );
}

console.log('[OfflineComponents] Components loaded');
