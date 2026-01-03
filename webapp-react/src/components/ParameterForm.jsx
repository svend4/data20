import { useState } from 'react';
import './ParameterForm.css';

const ParameterForm = ({ parameters, onSubmit, submitting }) => {
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});

  const handleInputChange = (paramName, value) => {
    setFormData({ ...formData, [paramName]: value });
    // Clear error for this field
    if (errors[paramName]) {
      setErrors({ ...errors, [paramName]: null });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const processedParams = {};
    const newErrors = {};

    Object.entries(parameters).forEach(([key, spec]) => {
      const value = formData[key];

      // Skip empty optional values
      if (!value && !spec.required) {
        return;
      }

      // Check required
      if (spec.required && !value) {
        newErrors[key] = 'Обязательное поле';
        return;
      }

      // Parse value based on type
      try {
        if (spec.type === 'boolean') {
          processedParams[key] = value === 'true';
        } else if (spec.type === 'integer') {
          processedParams[key] = parseInt(value);
        } else if (spec.type === 'number') {
          processedParams[key] = parseFloat(value);
        } else if (spec.type === 'array' || spec.type === 'object') {
          processedParams[key] = JSON.parse(value);
        } else {
          processedParams[key] = value;
        }
      } catch (err) {
        newErrors[key] = `Ошибка парсинга JSON`;
      }
    });

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSubmit(processedParams);
  };

  const renderInput = (paramName, paramSpec) => {
    const value = formData[paramName] || paramSpec.default || '';

    if (paramSpec.type === 'boolean') {
      return (
        <select
          value={value}
          onChange={(e) => handleInputChange(paramName, e.target.value)}
          disabled={submitting}
        >
          <option value="">-- Выберите --</option>
          <option value="true">Да</option>
          <option value="false">Нет</option>
        </select>
      );
    } else if (paramSpec.enum && paramSpec.enum.length > 0) {
      return (
        <select
          value={value}
          onChange={(e) => handleInputChange(paramName, e.target.value)}
          disabled={submitting}
        >
          <option value="">-- Выберите --</option>
          {paramSpec.enum.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      );
    } else if (paramSpec.type === 'integer' || paramSpec.type === 'number') {
      return (
        <input
          type="number"
          step={paramSpec.type === 'integer' ? '1' : 'any'}
          value={value}
          onChange={(e) => handleInputChange(paramName, e.target.value)}
          disabled={submitting}
        />
      );
    } else if (paramSpec.type === 'array' || paramSpec.type === 'object') {
      return (
        <textarea
          value={value}
          onChange={(e) => handleInputChange(paramName, e.target.value)}
          placeholder={
            paramSpec.type === 'array' ? '["item1", "item2"]' : '{"key": "value"}'
          }
          disabled={submitting}
        />
      );
    } else {
      return (
        <input
          type="text"
          value={value}
          onChange={(e) => handleInputChange(paramName, e.target.value)}
          disabled={submitting}
        />
      );
    }
  };

  if (Object.keys(parameters).length === 0) {
    return (
      <>
        <p style={{ color: '#999' }}>Этот инструмент не требует параметров</p>
        <button
          type="button"
          className="btn btn-primary btn-full"
          onClick={() => onSubmit({})}
          disabled={submitting}
        >
          {submitting ? 'Загрузка...' : '🚀 Запустить инструмент'}
        </button>
      </>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      {Object.entries(parameters).map(([paramName, paramSpec]) => (
        <div key={paramName} className="form-group">
          <label>
            {paramSpec.display_name || paramName}{' '}
            {paramSpec.required && <span className="required">*</span>}
          </label>
          {renderInput(paramName, paramSpec)}
          {paramSpec.description && (
            <div className="help-text">{paramSpec.description}</div>
          )}
          {errors[paramName] && (
            <div className="error-text">{errors[paramName]}</div>
          )}
        </div>
      ))}
      <button
        type="submit"
        className="btn btn-primary btn-full"
        disabled={submitting}
      >
        {submitting ? 'Загрузка...' : '🚀 Запустить инструмент'}
      </button>
    </form>
  );
};

export default ParameterForm;
