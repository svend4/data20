/**
 * PWA Install Prompt Component
 * Phase 7.2: Progressive Web App
 *
 * Displays a prompt to install the PWA on supported devices
 */

import { useState, useEffect } from 'react';
import { showInstallPrompt, canInstall, isStandalone } from '../serviceWorkerRegistration';

export default function PWAInstallPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    // Don't show if already installed
    if (isStandalone()) {
      return;
    }

    // Check if install prompt is available
    const checkPrompt = () => {
      if (canInstall()) {
        setShowPrompt(true);
      }
    };

    // Check immediately
    checkPrompt();

    // Check again after a delay (prompt might not be available immediately)
    const timeout = setTimeout(checkPrompt, 1000);

    return () => clearTimeout(timeout);
  }, []);

  const handleInstall = async () => {
    const result = await showInstallPrompt();

    if (result.outcome === 'accepted') {
      setShowPrompt(false);
    }
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    // Remember dismissal for 7 days
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
  };

  // Check if user dismissed recently
  useEffect(() => {
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed);
      const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);

      if (daysSinceDismissed < 7) {
        setShowPrompt(false);
      }
    }
  }, []);

  if (!showPrompt) {
    return null;
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <button style={styles.closeButton} onClick={handleDismiss}>
          ×
        </button>

        <div style={styles.icon}>📱</div>

        <h3 style={styles.title}>Install Data20 App</h3>

        <p style={styles.description}>
          Install our app for a better experience with offline support and faster loading!
        </p>

        <div style={styles.features}>
          <div style={styles.feature}>
            <span style={styles.featureIcon}>⚡</span>
            <span>Faster loading</span>
          </div>
          <div style={styles.feature}>
            <span style={styles.featureIcon}>📴</span>
            <span>Works offline</span>
          </div>
          <div style={styles.feature}>
            <span style={styles.featureIcon}>🏠</span>
            <span>Home screen access</span>
          </div>
        </div>

        <button style={styles.installButton} onClick={handleInstall}>
          Install App
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    zIndex: 9999,
    animation: 'slideUp 0.3s ease-out',
  },
  card: {
    background: 'white',
    borderRadius: '12px',
    padding: '24px',
    maxWidth: '320px',
    boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
    position: 'relative',
  },
  closeButton: {
    position: 'absolute',
    top: '12px',
    right: '12px',
    background: 'transparent',
    border: 'none',
    fontSize: '24px',
    cursor: 'pointer',
    color: '#999',
    padding: '4px 8px',
    lineHeight: 1,
  },
  icon: {
    fontSize: '48px',
    textAlign: 'center',
    marginBottom: '16px',
  },
  title: {
    fontSize: '20px',
    fontWeight: '600',
    color: '#333',
    marginBottom: '8px',
    textAlign: 'center',
  },
  description: {
    fontSize: '14px',
    color: '#666',
    lineHeight: '1.5',
    marginBottom: '16px',
    textAlign: 'center',
  },
  features: {
    display: 'flex',
    gap: '12px',
    marginBottom: '20px',
    justifyContent: 'space-around',
  },
  feature: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
    fontSize: '12px',
    color: '#666',
  },
  featureIcon: {
    fontSize: '20px',
  },
  installButton: {
    width: '100%',
    padding: '12px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'transform 0.2s',
  },
};
