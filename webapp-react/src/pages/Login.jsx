import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Login.css';

const Login = () => {
  const [activeTab, setActiveTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { login, register } = useAuth();
  const navigate = useNavigate();

  // Login form state
  const [loginData, setLoginData] = useState({
    username: '',
    password: '',
  });

  // Register form state
  const [registerData, setRegisterData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
  });

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(loginData.username, loginData.password);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    // Validation
    if (registerData.username.length < 3) {
      setError('Логин должен быть минимум 3 символа');
      setLoading(false);
      return;
    }

    if (registerData.password.length < 8) {
      setError('Пароль должен быть минимум 8 символов');
      setLoading(false);
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(registerData.email)) {
      setError('Введите корректный email');
      setLoading(false);
      return;
    }

    try {
      const user = await register(
        registerData.username,
        registerData.email,
        registerData.password,
        registerData.full_name
      );

      setSuccess(
        `Регистрация успешна! ${user.role === 'admin' ? '👑 Вы - администратор!' : ''}`
      );

      // Auto-switch to login tab after 2 seconds
      setTimeout(() => {
        setActiveTab('login');
        setSuccess('');
      }, 2000);
    } catch (err) {
      setError(err.message || 'Ошибка регистрации');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box fade-in">
        <h1>Data20 Knowledge Base</h1>
        <p className="subtitle">Система управления инструментами данных</p>

        <div className="tabs">
          <button
            className={`tab ${activeTab === 'login' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('login');
              setError('');
              setSuccess('');
            }}
          >
            Вход
          </button>
          <button
            className={`tab ${activeTab === 'register' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('register');
              setError('');
              setSuccess('');
            }}
          >
            Регистрация
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {activeTab === 'login' ? (
          <form onSubmit={handleLoginSubmit}>
            <div className="form-group">
              <label htmlFor="login-username">Логин</label>
              <input
                type="text"
                id="login-username"
                value={loginData.username}
                onChange={(e) =>
                  setLoginData({ ...loginData, username: e.target.value })
                }
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="login-password">Пароль</label>
              <input
                type="password"
                id="login-password"
                value={loginData.password}
                onChange={(e) =>
                  setLoginData({ ...loginData, password: e.target.value })
                }
                required
                disabled={loading}
              />
            </div>

            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? 'Загрузка...' : 'Войти'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegisterSubmit}>
            <div className="form-group">
              <label htmlFor="register-username">
                Логин <span className="required">*</span>
              </label>
              <input
                type="text"
                id="register-username"
                value={registerData.username}
                onChange={(e) =>
                  setRegisterData({ ...registerData, username: e.target.value })
                }
                minLength={3}
                required
                disabled={loading}
              />
              <div className="help-text">Минимум 3 символа</div>
            </div>

            <div className="form-group">
              <label htmlFor="register-email">
                Email <span className="required">*</span>
              </label>
              <input
                type="email"
                id="register-email"
                value={registerData.email}
                onChange={(e) =>
                  setRegisterData({ ...registerData, email: e.target.value })
                }
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="register-password">
                Пароль <span className="required">*</span>
              </label>
              <input
                type="password"
                id="register-password"
                value={registerData.password}
                onChange={(e) =>
                  setRegisterData({ ...registerData, password: e.target.value })
                }
                minLength={8}
                required
                disabled={loading}
              />
              <div className="help-text">Минимум 8 символов</div>
            </div>

            <div className="form-group">
              <label htmlFor="register-fullname">Полное имя</label>
              <input
                type="text"
                id="register-fullname"
                value={registerData.full_name}
                onChange={(e) =>
                  setRegisterData({ ...registerData, full_name: e.target.value })
                }
                disabled={loading}
              />
            </div>

            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? 'Загрузка...' : 'Зарегистрироваться'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default Login;
