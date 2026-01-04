import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useJobs } from '../hooks/useJobs';
import { getStatusDisplayName, formatDateTime, formatDuration } from '../utils/api';
import './Jobs.css';

const Jobs = () => {
  const { jobs, loading, reload } = useJobs(true, 5000);
  const [statusFilter, setStatusFilter] = useState('all');
  const [toolFilter, setToolFilter] = useState('all');

  // Extract unique tool names
  const toolNames = useMemo(() => {
    return [...new Set(jobs.map((j) => j.tool_name))].sort();
  }, [jobs]);

  // Filter jobs
  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      if (statusFilter !== 'all' && job.status !== statusFilter) {
        return false;
      }
      if (toolFilter !== 'all' && job.tool_name !== toolFilter) {
        return false;
      }
      return true;
    });
  }, [jobs, statusFilter, toolFilter]);

  const calculateDuration = (job) => {
    if (job.started_at && job.completed_at) {
      const duration = (new Date(job.completed_at) - new Date(job.started_at)) / 1000;
      return formatDuration(duration);
    } else if (job.started_at && job.status === 'running') {
      const duration = (new Date() - new Date(job.started_at)) / 1000;
      return formatDuration(duration) + ' (выполняется)';
    }
    return null;
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Загрузка задач...</p>
      </div>
    );
  }

  return (
    <div className="jobs-container">
      <Link to="/" className="back-button">
        ← Назад к инструментам
      </Link>

      {/* Page Header */}
      <div className="page-header card fade-in">
        <h1>📋 История задач</h1>
        <p>Просмотр и управление выполненными и текущими задачами</p>
      </div>

      {/* Filters */}
      <div className="filters card fade-in">
        <div className="filter-group">
          <label>Статус:</label>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">Все</option>
            <option value="pending">⏳ Ожидание</option>
            <option value="running">▶️ Выполняется</option>
            <option value="completed">✅ Завершено</option>
            <option value="failed">❌ Ошибка</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Инструмент:</label>
          <select value={toolFilter} onChange={(e) => setToolFilter(e.target.value)}>
            <option value="all">Все инструменты</option>
            {toolNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <button className="refresh-btn" onClick={() => reload()}>
          🔄 Обновить
        </button>
      </div>

      {/* Jobs List */}
      {filteredJobs.length === 0 ? (
        <div className="no-jobs card fade-in">
          <h3>📭 Задач пока нет</h3>
          <p>Запустите инструмент, чтобы создать задачу</p>
          <Link to="/" className="btn btn-primary">
            🚀 Выбрать инструмент
          </Link>
        </div>
      ) : (
        <div className="jobs-list fade-in">
          {filteredJobs.map((job) => {
            const duration = calculateDuration(job);

            return (
              <div key={job.job_id} className="job-card card">
                <div className="job-card-header">
                  <div className="job-title">
                    <h3>{job.tool_name}</h3>
                    <div className="job-id">ID: {job.job_id}</div>
                  </div>
                  <span className={`status-badge ${job.status}`}>
                    {getStatusDisplayName(job.status)}
                  </span>
                </div>

                <div className="job-info">
                  <div className="job-info-item">
                    <label>Создана</label>
                    <div className="value">{formatDateTime(job.created_at)}</div>
                  </div>
                  {job.started_at && (
                    <div className="job-info-item">
                      <label>Запущена</label>
                      <div className="value">{formatDateTime(job.started_at)}</div>
                    </div>
                  )}
                  {job.completed_at && (
                    <div className="job-info-item">
                      <label>Завершена</label>
                      <div className="value">{formatDateTime(job.completed_at)}</div>
                    </div>
                  )}
                  {duration && (
                    <div className="job-info-item">
                      <label>Длительность</label>
                      <div className="value">{duration}</div>
                    </div>
                  )}
                </div>

                {job.parameters && Object.keys(job.parameters).length > 0 && (
                  <details className="job-parameters">
                    <summary>Параметры</summary>
                    <pre>{JSON.stringify(job.parameters, null, 2)}</pre>
                  </details>
                )}

                {job.result && (
                  <details className="job-result">
                    <summary>Результат</summary>
                    <pre>{JSON.stringify(job.result, null, 2)}</pre>
                  </details>
                )}

                {job.error && (
                  <div className="job-error">
                    <strong>Ошибка:</strong>
                    <pre>{job.error}</pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Jobs;
