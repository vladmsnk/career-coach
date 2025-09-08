import React, { useState, useEffect } from 'react';

function QuestionInput({ question, onSubmit, disabled }) {
  const [value, setValue] = useState('');
  const [multiSelectValues, setMultiSelectValues] = useState([]);

  useEffect(() => {
    setValue('');
    setMultiSelectValues([]);
  }, [question]);

  const handleSubmit = () => {
    let submitValue = value;
    
    if (question?.type === 'multiselect') {
      submitValue = multiSelectValues.join(', ');
    }
    
    if (submitValue.trim()) {
      onSubmit(submitValue.trim());
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleMultiSelectChange = (option, checked) => {
    if (checked) {
      setMultiSelectValues(prev => [...prev, option]);
    } else {
      setMultiSelectValues(prev => prev.filter(v => v !== option));
    }
  };

  if (!question) {
    return (
      <div className="input-container">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Введите ваш ответ..."
          disabled={disabled}
          className="message-input"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="send-btn"
        >
          Отправить
        </button>
      </div>
    );
  }

  const { type, options, constraints } = question;

  // Select dropdown
  if (type === 'select' && options) {
    return (
      <div className="input-container">
        <select
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={disabled}
          className="question-select"
        >
          <option value="">Выберите вариант...</option>
          {options.map(option => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
        <button
          onClick={handleSubmit}
          disabled={disabled || !value}
          className="send-btn"
        >
          Отправить
        </button>
      </div>
    );
  }

  // Multi-select checkboxes
  if (type === 'multiselect' && options) {
    return (
      <div className="input-container multiselect-container">
        <div className="multiselect-options">
          {options.map(option => (
            <label key={option} className="multiselect-option">
              <input
                type="checkbox"
                checked={multiSelectValues.includes(option)}
                onChange={(e) => handleMultiSelectChange(option, e.target.checked)}
                disabled={disabled}
              />
              <span>{option}</span>
            </label>
          ))}
        </div>
        <button
          onClick={handleSubmit}
          disabled={disabled || multiSelectValues.length === 0}
          className="send-btn"
        >
          Отправить ({multiSelectValues.length})
        </button>
      </div>
    );
  }

  // Number input
  if (type === 'number' && constraints) {
    const { min, max } = constraints;
    return (
      <div className="input-container">
        <input
          type="number"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyPress={handleKeyPress}
          min={min}
          max={max}
          placeholder={`Введите число от ${min} до ${max}`}
          disabled={disabled}
          className="message-input"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="send-btn"
        >
          Отправить
        </button>
      </div>
    );
  }

  // Range input
  if (type === 'range' && constraints) {
    const { min, max, step } = constraints;
    return (
      <div className="input-container range-container">
        <div className="range-input-group">
          <input
            type="range"
            value={value || min}
            onChange={(e) => setValue(e.target.value)}
            min={min}
            max={max}
            step={step || 1}
            disabled={disabled}
            className="range-slider"
          />
          <input
            type="number"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            min={min}
            max={max}
            step={step || 1}
            disabled={disabled}
            className="range-number-input"
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={disabled || !value}
          className="send-btn"
        >
          Отправить
        </button>
      </div>
    );
  }

  // Text area for long text
  if (type === 'text') {
    const maxLength = constraints?.max_length || 1000;
    return (
      <div className="input-container text-container">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Введите ваш ответ..."
          maxLength={maxLength}
          disabled={disabled}
          className="message-textarea"
          rows={3}
        />
        <div className="text-info">
          <span className="char-count">{value.length}/{maxLength}</span>
          <button
            onClick={handleSubmit}
            disabled={disabled || !value.trim()}
            className="send-btn"
          >
            Отправить
          </button>
        </div>
      </div>
    );
  }

  // Default text input
  const maxLength = constraints?.max_length || 1000;
  return (
    <div className="input-container">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Введите ваш ответ..."
        maxLength={maxLength}
        disabled={disabled}
        className="message-input"
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
        className="send-btn"
      >
        Отправить
      </button>
    </div>
  );
}

export default QuestionInput;
