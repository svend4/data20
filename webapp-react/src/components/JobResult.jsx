import { Link } from 'react-router-dom';
import { getStatusDisplayName, formatDateTime, formatDuration } from '../utils/api';
import './JobResult.css';

const JobResult = ({ job, loading }) => {
  if (!job) return null;

  const duration =
    job.started_at && job.completed_at
      ? (new Date(job.completed_at) - new Date(job.started_at)) / 1000
      : job.started_at
      ? (new Date() - new Date(job.started_at)) / 1000
      : null;

  const progress = job.status === 'running' ? 50 : job.status === 'completed' ? 100 : 0;

  return (
    <div className="result-section card fade-in">
      <h2>
        📊 Результат
        <span className={`status-badge ${job.status}`}>
          {getStatusDisplayName(job.status)}
        </span>
      </h2>

      {(job.status === 'pending' || job.status === 'running') && (
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
        </div>
      )}

      <div className="result-info">
        <div className="result-info-item">
          <label>ID задачи</label>
          <div className="value">{job.job_id}</div>
        </div>
        <div className="result-info-item">
          <label>Статус</label>
          <div className="value">{getStatusDisplayName(job.status)}</div>
        </div>
        {duration && (
          <div className="result-info-item">
            <label>Время выполнения</label>
            <div className="value">
              {formatDuration(duration)}
              {job.status === 'running' && ' (выполняется)'}
            </div>
          </div>
        )}
        <div className="result-info-item">
          <label>Создана</label>
          <div className="value">{formatDateTime(job.created_at)}</div>
        </div>
      </div>

      {job.status === 'completed' && job.result && (
        <div className="result-output">
          <strong>Результат:</strong>
          <pre>{JSON.stringify(job.result, null, 2)}</pre>
        </div>
      )}

      {job.status === 'failed' && job.error && (
        <div className="error-message">
          <strong>❌ Ошибка:</strong>
          <pre>{job.error}</pre>
        </div>
      )}

      <div className="result-actions">
        <Link to="/" className="btn btn-secondary">
          ← Назад к инструментам
        </Link>
        <Link to="/jobs" className="btn btn-primary">
          📋 Все задачи
        </Link>
      </div>
    </div>
  );
};

export default JobResult;
