import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTools } from '../hooks/useTools';
import { useJobs } from '../hooks/useJobs';
import { getCategoryDisplayName, getToolIcon } from '../utils/api';
import ToolCard from '../components/ToolCard';
import './Home.css';

const Home = () => {
  const { user, logout } = useAuth();
  const { tools, loading: toolsLoading } = useTools();
  const { jobs } = useJobs(true, 5000);
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Extract categories from tools
  const categories = useMemo(() => {
    const cats = new Set(tools.map((t) => t.category || 'other'));
    return Array.from(cats).sort();
  }, [tools]);

  // Filter tools
  const filteredTools = useMemo(() => {
    return tools.filter((tool) => {
      // Category filter
      if (selectedCategory !== 'all' && tool.category !== selectedCategory) {
        return false;
      }

      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const name = (tool.display_name || tool.name).toLowerCase();
        const description = (tool.description || '').toLowerCase();
        const category = (tool.category || '').toLowerCase();

        return (
          name.includes(query) ||
          description.includes(query) ||
          category.includes(query)
        );
      }

      return true;
    });
  }, [tools, searchQuery, selectedCategory]);

  // Calculate stats
  const completedJobs = jobs.filter((j) => j.status === 'completed').length;

  if (toolsLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Загрузка инструментов...</p>
      </div>
    );
  }

  return (
    <div className="home-container">
      {/* Header */}
      <div className="header card fade-in">
        <div className="user-info">
          <div className="user-avatar">
            {user.username.charAt(0).toUpperCase()}
          </div>
          <div className="user-details">
            <h2>
              {user.full_name || user.username}{' '}
              <span className={`user-role ${user.role}`}>
                {user.role === 'admin' ? '👑 Администратор' : '👤 Пользователь'}
              </span>
            </h2>
            <p>{user.email}</p>
          </div>
        </div>
        <div className="header-actions">
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/jobs')}
          >
            📋 История задач
          </button>
          {user.role === 'admin' && (
            <button
              className="btn btn-secondary"
              onClick={() => navigate('/admin')}
            >
              👑 Админ-панель
            </button>
          )}
          <button className="btn btn-secondary" onClick={logout}>
            🚪 Выход
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="stats fade-in">
        <div className="stat-card card">
          <h4>Всего инструментов</h4>
          <div className="stat-value">{tools.length}</div>
        </div>
        <div className="stat-card card">
          <h4>Категорий</h4>
          <div className="stat-value">{categories.length}</div>
        </div>
        <div className="stat-card card">
          <h4>Выполнено задач</h4>
          <div className="stat-value">{completedJobs}</div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="search-section card fade-in">
        <div className="search-box">
          <input
            type="text"
            placeholder="🔍 Поиск инструментов..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="category-filters">
          <button
            className={`category-btn ${selectedCategory === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('all')}
          >
            Все инструменты
          </button>
          {categories.map((category) => (
            <button
              key={category}
              className={`category-btn ${selectedCategory === category ? 'active' : ''}`}
              onClick={() => setSelectedCategory(category)}
            >
              {getCategoryDisplayName(category)}
            </button>
          ))}
        </div>
      </div>

      {/* Tools Grid */}
      {filteredTools.length === 0 ? (
        <div className="no-results card fade-in">
          <h3>😕 Ничего не найдено</h3>
          <p>Попробуйте изменить запрос или выбрать другую категорию</p>
        </div>
      ) : (
        <div className="tools-grid fade-in">
          {filteredTools.map((tool) => (
            <ToolCard
              key={tool.name}
              tool={tool}
              onClick={() => navigate(`/run/${tool.name}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Home;
