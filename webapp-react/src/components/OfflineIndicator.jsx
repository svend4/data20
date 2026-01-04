/**
 * Offline Indicator Component
 * Phase 7.2: Progressive Web App
 *
 * Shows connection status to the user
 */

import { useState, useEffect } from 'react';
import { getConnectionStatus, onConnectionChange } from '../serviceWorkerRegistration';

export default function OfflineIndicator() {
  const [status, setStatus] = useState(getConnectionStatus());
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const cleanup = onConnectionChange((newStatus) => {
      setStatus(newStatus);

      // Show banner when going offline
      if (!newStatus.online) {
        setShowBanner(true);
      } else {
        // Auto-hide banner after 3 seconds when back online
        setTimeout(() => setShowBanner(false), 3000);
      }
    });

    return cleanup;
  }, []);

  if (!showBanner) {
    return null;
  }

  return (
    <div style={{
      ...styles.banner,
      background: status.online ? '#4ade80' : '#ff6b6b',
    }}>
      <div style={styles.content}>
        <span style={styles.icon}>
          {status.online ? '✓' : '📡'}
        </span>
        <span style={styles.text}>
          {status.online
            ? 'You are back online!'
            : 'You are offline. Some features may be limited.'
          }
        </span>
        {status.online && (
          <button
            style={styles.closeButton}
            onClick={() => setShowBanner(false)}
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}

const styles = {
  banner: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10000,
    color: 'white',
    padding: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    animation: 'slideDown 0.3s ease-out',
  },
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  icon: {
    fontSize: '20px',
  },
  text: {
    flex: 1,
    fontSize: '14px',
    fontWeight: '500',
  },
  closeButton: {
    background: 'transparent',
    border: 'none',
    color: 'white',
    fontSize: '24px',
    cursor: 'pointer',
    padding: '0 8px',
    lineHeight: 1,
  },
};
