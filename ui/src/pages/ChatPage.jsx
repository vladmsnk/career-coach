import React, { useState, useEffect, useRef } from 'react';

function ChatPage({ token, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [error, setError] = useState(null);
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
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received:', data);
          
          if (data.event === 'finished') {
            setMessages(prev => [...prev, {
              type: 'system',
              content: 'Спасибо за ответы! Диалог завершен. Вы можете начать новый диалог.',
              timestamp: new Date()
            }]);
            setIsWaitingForResponse(false);
          } else if (data.error === 'duplicate') {
            setMessages(prev => [...prev, {
              type: 'error',
              content: 'Пожалуйста, дайте другой ответ (не повторяйте предыдущий).',
              timestamp: new Date()
            }]);
            setIsWaitingForResponse(false);
          } else if (data.id && data.prompt) {
            // Новый вопрос от бота
            setMessages(prev => [...prev, {
              type: 'bot',
              content: data.prompt,
              questionId: data.id,
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
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        if (event.code !== 1000) {
          setError('Соединение с сервером потеряно');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Ошибка соединения с сервером');
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('Failed to connect WebSocket:', e);
      setError('Не удалось подключиться к серверу');
    }
  };

  const sendMessage = () => {
    if (!currentInput.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    const message = currentInput.trim();
    
    // Добавляем сообщение пользователя в чат
    setMessages(prev => [...prev, {
      type: 'user',
      content: message,
      timestamp: new Date()
    }]);

    // Отправляем сообщение на сервер
    wsRef.current.send(message);
    setCurrentInput('');
    setIsWaitingForResponse(true);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setError(null);
    if (wsRef.current) {
      wsRef.current.close();
    }
    setTimeout(connectWebSocket, 100);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Карьерный консультант</h2>
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

      {error && (
        <div className="error-message">
          {error}
          <button onClick={connectWebSocket} className="retry-btn">
            Переподключиться
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

      <div className="input-container">
        <input
          type="text"
          value={currentInput}
          onChange={(e) => setCurrentInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Введите ваш ответ..."
          disabled={!isConnected || isWaitingForResponse}
          className="message-input"
        />
        <button
          onClick={sendMessage}
          disabled={!isConnected || !currentInput.trim() || isWaitingForResponse}
          className="send-btn"
        >
          Отправить
        </button>
      </div>
    </div>
  );
}

export default ChatPage;
