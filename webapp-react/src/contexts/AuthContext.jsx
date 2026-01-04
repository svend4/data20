import { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  apiRequest,
  API,
  getToken,
  setToken,
  clearAuth,
  getUser,
  setUser as saveUser,
  isAuthenticated as checkAuth,
} from '../utils/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(getUser());
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Check authentication on mount
  useEffect(() => {
    const checkAuthentication = async () => {
      if (checkAuth()) {
        try {
          const userData = await apiRequest(API.me);
          setUser(userData);
          saveUser(userData);
        } catch (error) {
          console.error('Auth check failed:', error);
          clearAuth();
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkAuthentication();
  }, []);

  const login = async (username, password) => {
    const response = await apiRequest(API.login, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
      noAuth: true,
    });

    setToken(response.access_token, response.refresh_token);

    const userData = await apiRequest(API.me);
    setUser(userData);
    saveUser(userData);

    return userData;
  };

  const register = async (username, email, password, full_name) => {
    const userData = await apiRequest(API.register, {
      method: 'POST',
      body: JSON.stringify({ username, email, password, full_name }),
      noAuth: true,
    });

    return userData;
  };

  const logout = () => {
    clearAuth();
    setUser(null);
    navigate('/login');
  };

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
