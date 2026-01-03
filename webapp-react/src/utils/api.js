/**
 * API Configuration and Utilities
 */

// API Base URL (proxied by Vite in development)
const API_URL = import.meta.env.VITE_API_URL || '';

// API Endpoints
export const API = {
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
export const STORAGE = {
  accessToken: 'data20_access_token',
  refreshToken: 'data20_refresh_token',
  user: 'data20_user',
};

// Token Management
export const getToken = () => {
  return localStorage.getItem(STORAGE.accessToken);
};

export const setToken = (accessToken, refreshToken = null) => {
  localStorage.setItem(STORAGE.accessToken, accessToken);
  if (refreshToken) {
    localStorage.setItem(STORAGE.refreshToken, refreshToken);
  }
};

export const clearAuth = () => {
  localStorage.removeItem(STORAGE.accessToken);
  localStorage.removeItem(STORAGE.refreshToken);
  localStorage.removeItem(STORAGE.user);
};

export const getUser = () => {
  const userStr = localStorage.getItem(STORAGE.user);
  return userStr ? JSON.parse(userStr) : null;
};

export const setUser = (user) => {
  localStorage.setItem(STORAGE.user, JSON.stringify(user));
};

export const isAuthenticated = () => {
  return !!getToken();
};

// API Request Helper
export const apiRequest = async (url, options = {}) => {
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
      // Redirect will be handled by AuthContext
    }
    throw error;
  }
};

// Format Utilities
export const formatDateTime = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatDuration = (seconds) => {
  if (!seconds) return '-';
  if (seconds < 60) return `${seconds.toFixed(1)}с`;
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes}м ${secs}с`;
};

// Category Helpers
export const getCategoryDisplayName = (category) => {
  const categoryMap = {
    'statistics': '📊 Статистика',
    'visualization': '📈 Визуализация',
    'cleaning': '🧹 Очистка данных',
    'transformation': '🔄 Преобразование',
    'analysis': '🔍 Анализ',
    'ml': '🤖 Машинное обучение',
    'nlp': '💬 NLP',
    'timeseries': '⏰ Временные ряды',
    'text': '📝 Текст',
    'network': '🌐 Сети',
    'other': '🔧 Другое',
  };
  return categoryMap[category] || category;
};

export const getToolIcon = (category) => {
  const iconMap = {
    'statistics': '📊',
    'visualization': '📈',
    'cleaning': '🧹',
    'transformation': '🔄',
    'analysis': '🔍',
    'ml': '🤖',
    'nlp': '💬',
    'timeseries': '⏰',
    'text': '📝',
    'network': '🌐',
    'other': '🔧',
  };
  return iconMap[category] || '🔧';
};

// Status Helpers
export const getStatusDisplayName = (status) => {
  const statusMap = {
    'pending': '⏳ Ожидание',
    'running': '▶️ Выполняется',
    'completed': '✅ Завершено',
    'failed': '❌ Ошибка',
  };
  return statusMap[status] || status;
};

export const getRoleDisplayName = (role) => {
  const roleMap = {
    'admin': '👑 Администратор',
    'user': '👤 Пользователь',
    'guest': '👥 Гость',
  };
  return roleMap[role] || role;
};
