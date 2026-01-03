/**
 * Configuration
 * Simple Web UI for Data20 Knowledge Base
 */

// API Configuration
const API_URL = window.location.origin;  // Same origin (http://localhost:8001)

// API Endpoints
const API = {
    // Authentication
    register: `${API_URL}/auth/register`,
    login: `${API_URL}/auth/login`,
    refresh: `${API_URL}/auth/refresh`,
    me: `${API_URL}/auth/me`,
    logout: `${API_URL}/auth/logout`,

    // Tools
    tools: `${API_URL}/api/tools`,
    toolDetail: (name) => `${API_URL}/api/tools/${name}`,
    categories: `${API_URL}/api/categories`,

    // Jobs
    runTool: `${API_URL}/api/run`,
    jobs: `${API_URL}/api/jobs`,
    jobDetail: (id) => `${API_URL}/api/jobs/${id}`,
    jobLogs: (id) => `${API_URL}/api/jobs/${id}/logs`,

    // Admin
    adminUsers: `${API_URL}/admin/users`,
};

// Storage Keys
const STORAGE = {
    accessToken: 'data20_access_token',
    refreshToken: 'data20_refresh_token',
    user: 'data20_user',
};

// Utility Functions
function getToken() {
    return localStorage.getItem(STORAGE.accessToken);
}

function setToken(accessToken, refreshToken = null) {
    localStorage.setItem(STORAGE.accessToken, accessToken);
    if (refreshToken) {
        localStorage.setItem(STORAGE.refreshToken, refreshToken);
    }
}

function clearAuth() {
    localStorage.removeItem(STORAGE.accessToken);
    localStorage.removeItem(STORAGE.refreshToken);
    localStorage.removeItem(STORAGE.user);
}

function getUser() {
    const userStr = localStorage.getItem(STORAGE.user);
    return userStr ? JSON.parse(userStr) : null;
}

function setUser(user) {
    localStorage.setItem(STORAGE.user, JSON.stringify(user));
}

// API Request Helper
async function apiRequest(url, options = {}) {
    const token = getToken();

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    // Add authorization header if token exists
    if (token && !options.noAuth) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers,
    };

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw {
                status: response.status,
                message: data.detail || data.message || 'Ошибка запроса',
                data,
            };
        }

        return data;
    } catch (error) {
        if (error.status === 401) {
            // Unauthorized - token expired
            clearAuth();
            if (window.location.pathname !== '/index.html' && window.location.pathname !== '/') {
                window.location.href = 'index.html';
            }
        }
        throw error;
    }
}

// Check if user is authenticated
function isAuthenticated() {
    return !!getToken();
}

// Redirect if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return false;
    }
    return true;
}

// Show/hide loading state
function setLoading(element, loading) {
    if (loading) {
        element.disabled = true;
        const originalText = element.textContent;
        element.dataset.originalText = originalText;
        element.innerHTML = '<span class="loading"></span> Загрузка...';
    } else {
        element.disabled = false;
        element.textContent = element.dataset.originalText || 'Готово';
    }
}

// Show error message
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}

// Show success message
function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}

// Format date/time
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

// Format duration
function formatDuration(seconds) {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds.toFixed(1)}с`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}м ${secs}с`;
}
