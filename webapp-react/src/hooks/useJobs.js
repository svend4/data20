import { useState, useEffect, useCallback } from 'react';
import { apiRequest, API } from '../utils/api';

export const useJobs = (autoRefresh = true, refreshInterval = 5000) => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadJobs = useCallback(async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true);
        setError(null);
      }

      const data = await apiRequest(API.jobs);
      setJobs(data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
    } catch (err) {
      console.error('Failed to load jobs:', err);
      if (!silent) {
        setError(err.message);
      }
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadJobs();

    if (autoRefresh) {
      const interval = setInterval(() => {
        loadJobs(true); // Silent refresh
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [loadJobs, autoRefresh, refreshInterval]);

  const runTool = async (toolName, parameters) => {
    const job = await apiRequest(API.runTool, {
      method: 'POST',
      body: JSON.stringify({
        tool_name: toolName,
        parameters: parameters || {},
      }),
    });

    // Reload jobs to include the new one
    await loadJobs(true);

    return job;
  };

  return { jobs, loading, error, reload: loadJobs, runTool };
};

export const useJob = (jobId, autoPoll = true, pollInterval = 2000) => {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadJob = useCallback(async () => {
    if (!jobId) return;

    try {
      setLoading(true);
      setError(null);
      const data = await apiRequest(API.jobDetail(jobId));
      setJob(data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load job:', err);
      setError(err.message);
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    loadJob();

    if (autoPoll && jobId) {
      const interval = setInterval(async () => {
        try {
          const data = await apiRequest(API.jobDetail(jobId));
          setJob(data);

          // Stop polling if job is completed or failed
          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Failed to poll job:', err);
          clearInterval(interval);
        }
      }, pollInterval);

      return () => clearInterval(interval);
    }
  }, [jobId, autoPoll, pollInterval, loadJob]);

  return { job, loading, error, reload: loadJob };
};
