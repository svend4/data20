import { useState, useEffect } from 'react';
import { apiRequest, API } from '../utils/api';

export const useTools = () => {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiRequest(API.tools);
      setTools(data);
    } catch (err) {
      console.error('Failed to load tools:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { tools, loading, error, reload: loadTools };
};

export const useTool = (toolName) => {
  const [tool, setTool] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (toolName) {
      loadTool();
    }
  }, [toolName]);

  const loadTool = async () => {
    try {
      setLoading(true);
      setError(null);
      // Load all tools and find the specific one
      const tools = await apiRequest(API.tools);
      const foundTool = tools.find(t => t.name === toolName);

      if (!foundTool) {
        throw new Error('Инструмент не найден');
      }

      setTool(foundTool);
    } catch (err) {
      console.error('Failed to load tool:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { tool, loading, error, reload: loadTool };
};
