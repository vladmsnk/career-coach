import React, { useState, useEffect, useRef } from 'react';
import QuestionInput from '../components/QuestionInput.jsx';

function ChatPage({ token, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [error, setError] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [progress, setProgress] = useState({ current: 0, total: 12 });
  const [validationError, setValidationError] = useState(null);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [token]);

  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://127.0.0.1:8000/api/v1/chat/ws?token=${token}`;
      console.log('🔌 Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Received message:', data);
          
          if (data.event === 'finished') {
            setMessages(prev => [...prev, {
              type: 'system',
              content: 'Спасибо за ответы! Диалог завершен. Вы можете начать новый диалог.',
              timestamp: new Date()
            }]);
            setCurrentQuestion(null);
            setIsWaitingForResponse(false);
          } else if (data.error) {
            // Обработка ошибок валидации
            if (data.error.code === 'validation_failed') {
              setValidationError(data.error.message);
              setIsWaitingForResponse(false);
            } else if (data.error === 'duplicate') {
              setMessages(prev => [...prev, {
                type: 'error',
                content: 'Пожалуйста, дайте другой ответ (не повторяйте предыдущий).',
                timestamp: new Date()
              }]);
              setIsWaitingForResponse(false);
            }
          } else if (data.id && data.prompt) {
            // Новый вопрос от бота с расширенными метаданными
            setCurrentQuestion(data);
            setProgress(data.progress || { current: 0, total: 12 });
            setValidationError(null);
            
            setMessages(prev => [...prev, {
              type: 'bot',
              content: data.prompt,
              questionId: data.id,
              questionType: data.type,
              module: data.module,
              moduleTitle: data.module_title,
              timestamp: new Date()
            }]);
            setIsWaitingForResponse(false);
          } else if (data.role === 'bot' && data.content) {
            // Предыдущий вопрос (при восстановлении сессии)
            setMessages(prev => [...prev, {
              type: 'bot',
              content: data.content,
              timestamp: new Date()
            }]);
          } else if (data.role === 'user' && data.content) {
            // Предыдущий ответ пользователя (при восстановлении сессии)
            setMessages(prev => [...prev, {
              type: 'user',
              content: data.content,
              timestamp: new Date()
            }]);
          }
        } catch (e) {
          console.error('Error parsing message:', e);
          setError('Ошибка обработки сообщения от сервера');
        }
      };

      ws.onclose = (event) => {
        console.log('❌ WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        if (event.code !== 1000) {
          console.error('Unexpected WebSocket close code:', event.code);
          setError('Соединение с сервером потеряно');
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setError('Ошибка соединения с сервером. Проверьте что backend запущен на порту 8000');
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('Failed to connect WebSocket:', e);
      setError('Не удалось подключиться к серверу');
    }
  };

  const sendMessage = (message) => {
    if (!message || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ Cannot send message:', !message ? 'empty message' : !wsRef.current ? 'no websocket' : 'websocket not open');
      return;
    }

    console.log('📤 Sending message:', message);

    // Добавляем сообщение пользователя в чат
    setMessages(prev => [...prev, {
      type: 'user',
      content: message,
      timestamp: new Date()
    }]);

    // Отправляем сообщение на сервер
    wsRef.current.send(message);
    setCurrentInput('');
    setValidationError(null);
    setIsWaitingForResponse(true);
  };


  const startNewChat = () => {
    console.log('🔄 Starting new chat...');
    setMessages([]);
    setError(null);
    setCurrentQuestion(null);
    setProgress({ current: 0, total: 12 });
    setValidationError(null);
    setCurrentInput('');
    setIsWaitingForResponse(false);
    if (wsRef.current) {
      console.log('🔌 Closing existing WebSocket connection');
      wsRef.current.close();
    }
    setTimeout(() => {
      console.log('🔌 Reconnecting WebSocket in 100ms...');
      connectWebSocket();
    }, 100);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="header-main">
          <h2>Карьерный консультант</h2>
          {currentQuestion && (
            <div className="module-info">
              <span className="module-title">{currentQuestion.module_title}</span>
            </div>
          )}
        </div>
        <div className="header-controls">
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Подключено' : '🔴 Не подключено'}
          </div>
          <button onClick={startNewChat} className="new-chat-btn">
            Новый диалог
          </button>
          <button onClick={onLogout} className="logout-btn">
            Выйти
          </button>
        </div>
      </div>

      {progress.current > 0 && (
        <div className="progress-container">
          <div className="progress-info">
            <span>Вопрос {progress.current} из {progress.total}</span>
            {currentQuestion && (
              <span className={`module-badge module-${currentQuestion.module}`}>
                {currentQuestion.module === 'context' && '📋 Контекст'}
                {currentQuestion.module === 'goals' && '🎯 Цели'}
                {currentQuestion.module === 'skills' && '🛠️ Навыки'}
              </span>
            )}
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
          <button onClick={connectWebSocket} className="retry-btn">
            Переподключиться
          </button>
        </div>
      )}

      {validationError && (
        <div className="validation-error">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{validationError}</span>
          <button 
            onClick={() => setValidationError(null)} 
            className="error-close"
          >
            ✕
          </button>
        </div>
      )}

      <div className="messages-container">
        {messages.length === 0 && isConnected && (
          <div className="welcome-message">
            Добро пожаловать! Ожидайте первый вопрос от консультанта...
          </div>
        )}
        
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            <div className="message-content">
              {msg.content}
            </div>
            <div className="message-time">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        
        {isWaitingForResponse && (
          <div className="message bot typing">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <QuestionInput
        question={currentQuestion}
        onSubmit={sendMessage}
        disabled={!isConnected || isWaitingForResponse}
      />
    </div>
  );
}

export default ChatPage;
