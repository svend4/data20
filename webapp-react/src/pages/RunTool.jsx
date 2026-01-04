import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTool } from '../hooks/useTools';
import { useJob } from '../hooks/useJobs';
import { apiRequest, API, getCategoryDisplayName, getStatusDisplayName, formatDateTime, formatDuration } from '../utils/api';
import ParameterForm from '../components/ParameterForm';
import JobResult from '../components/JobResult';
import './RunTool.css';

const RunTool = () => {
  const { toolName } = useParams();
  const navigate = useNavigate();
  const { tool, loading: toolLoading } = useTool(toolName);
  const [jobId, setJobId] = useState(null);
  const { job, loading: jobLoading } = useJob(jobId, true, 2000);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (parameters) => {
    setError('');
    setSubmitting(true);

    try {
      const result = await apiRequest(API.runTool, {
        method: 'POST',
        body: JSON.stringify({
          tool_name: tool.name,
          parameters: parameters || {},
        }),
      });

      setJobId(result.job_id);
    } catch (err) {
      console.error('Failed to submit job:', err);
      setError(err.message || 'Ошибка запуска инструмента');
    } finally {
      setSubmitting(false);
    }
  };

  if (toolLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Загрузка инструмента...</p>
      </div>
    );
  }

  if (!tool) {
    return (
      <div className="container">
        <div className="alert alert-error">
          Инструмент не найден
        </div>
        <Link to="/" className="btn btn-secondary">
          ← Назад к инструментам
        </Link>
      </div>
    );
  }

  return (
    <div className="run-container">
      <Link to="/" className="back-button">
        ← Назад к инструментам
      </Link>

      {/* Tool Header */}
      <div className="tool-header card fade-in">
        <h1>{tool.display_name || tool.name}</h1>
        <p>{tool.description || 'Описание недоступно'}</p>
        <span className="tool-category-badge">
          {getCategoryDisplayName(tool.category || 'other')}
        </span>
      </div>

      {error && (
        <div className="alert alert-error fade-in">{error}</div>
      )}

      {/* Parameters Form */}
      {!jobId && (
        <div className="parameters-form card fade-in">
          <h2>📝 Параметры</h2>
          <ParameterForm
            parameters={tool.parameters || {}}
            onSubmit={handleSubmit}
            submitting={submitting}
          />
        </div>
      )}

      {/* Job Result */}
      {jobId && job && (
        <JobResult job={job} loading={jobLoading} />
      )}
    </div>
  );
};

export default RunTool;
