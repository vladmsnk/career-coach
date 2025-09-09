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
    
    // Validate input based on question type
    if (!validateInput(submitValue)) {
      return;
    }
    
    if (submitValue.trim()) {
      onSubmit(submitValue.trim());
    }
  };
  
  const validateInput = (input) => {
    if (!question) return true;
    
    switch (question.type) {
      case 'number':
        const num = parseFloat(input);
        if (isNaN(num)) return false;
        if (min !== undefined && num < min) return false;
        if (max !== undefined && num > max) return false;
        return true;
      
      case 'range':
        const rangeNum = parseFloat(input);
        if (isNaN(rangeNum)) return false;
        if (min !== undefined && rangeNum < min) return false;
        if (max !== undefined && rangeNum > max) return false;
        return true;
        
      case 'text':
        if (max_length && input.length > max_length) return false;
        return input.trim().length > 0;
        
      case 'select':
        return options && options.includes(input);
        
      case 'multiselect':
        return multiSelectValues.length > 0;
        
      default:
        return input.trim().length > 0;
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
          aria-label="Поле ввода ответа"
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

  const { type, options, min, max, step, max_length } = question;
  const constraints = { min, max, step, max_length };

  // Select dropdown
  if (type === 'select' && options) {
    return (
      <div className="input-container">
        <select
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={disabled}
          className="question-select"
          aria-label="Выбор варианта ответа"
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
                aria-describedby={`option-${option.replace(/\s+/g, '-')}`}
              />
              <span id={`option-${option.replace(/\s+/g, '-')}`}>{option}</span>
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
  if (type === 'number' && (min !== undefined || max !== undefined)) {
    return (
      <div className="input-container">
        <input
          type="number"
          value={value}
          onChange={(e) => {
            const newValue = e.target.value;
            if (min !== undefined && max !== undefined) {
              const num = parseFloat(newValue);
              if (!isNaN(num) && num >= min && num <= max) {
                setValue(newValue);
              } else if (newValue === '') {
                setValue('');
              }
            } else {
              setValue(newValue);
            }
          }}
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
  if (type === 'range' && (min !== undefined || max !== undefined)) {
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
    const maxLength = max_length || 1000;
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
          aria-label="Поле ввода развернутого ответа"
          aria-describedby="char-count"
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
  const maxLength = max_length || 1000;
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
