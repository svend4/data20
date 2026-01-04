/**
 * PWA Update Notification Component
 * Phase 7.2: Progressive Web App
 *
 * Notifies users when a new version is available
 */

import { useState, useEffect } from 'react';
import { skipWaiting } from '../serviceWorkerRegistration';

export default function PWAUpdateNotification() {
  const [showUpdate, setShowUpdate] = useState(false);
  const [registration, setRegistration] = useState(null);

  useEffect(() => {
    // This would be set by the SW registration callback
    const handleUpdate = (reg) => {
      setRegistration(reg);
      setShowUpdate(true);
    };

    // Listen for custom event from serviceWorkerRegistration
    window.addEventListener('sw-update-available', (e) => {
      handleUpdate(e.detail);
    });

    return () => {
      window.removeEventListener('sw-update-available', handleUpdate);
    };
  }, []);

  const handleUpdate = () => {
    skipWaiting();
    setShowUpdate(false);

    // Reload after a short delay
    setTimeout(() => {
      window.location.reload();
    }, 500);
  };

  const handleDismiss = () => {
    setShowUpdate(false);
  };

  if (!showUpdate) {
    return null;
  }

  return (
    <div style={styles.container}>
      <div style={styles.notification}>
        <div style={styles.icon}>🎉</div>

        <div style={styles.content}>
          <div style={styles.title}>New version available!</div>
          <div style={styles.message}>
            A new version of the app is ready. Update now to get the latest features.
          </div>
        </div>

        <div style={styles.actions}>
          <button style={styles.updateButton} onClick={handleUpdate}>
            Update Now
          </button>
          <button style={styles.dismissButton} onClick={handleDismiss}>
            Later
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    position: 'fixed',
    top: '20px',
    right: '20px',
    zIndex: 9999,
    animation: 'slideDown 0.3s ease-out',
  },
  notification: {
    background: 'white',
    borderRadius: '12px',
    padding: '20px',
    maxWidth: '400px',
    boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '16px',
  },
  icon: {
    fontSize: '32px',
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
    marginBottom: '4px',
  },
  message: {
    fontSize: '14px',
    color: '#666',
    lineHeight: '1.4',
    marginBottom: '12px',
  },
  actions: {
    display: 'flex',
    gap: '8px',
    flexDirection: 'column',
  },
  updateButton: {
    padding: '8px 16px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  dismissButton: {
    padding: '8px 16px',
    background: 'transparent',
    color: '#666',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '14px',
    cursor: 'pointer',
  },
};
