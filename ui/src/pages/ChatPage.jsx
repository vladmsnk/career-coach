import React, { useEffect, useRef, useState } from 'react';

function ChatPage({ token, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/^http/, 'ws');
    const ws = new WebSocket(`${base}/api/v1/chat/ws?token=${token}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.role && data.content) {
        setMessages((m) => [...m, { role: data.role, content: data.content }]);
      } else if (data.prompt) {
        setMessages((m) => [...m, { role: 'bot', content: data.prompt }]);
      } else if (data.error) {
        setError('Сообщение повторяет предыдущий ответ');
      } else if (data.event === 'finished') {
        ws.close();
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    return () => {
      ws.close();
    };
  }, [token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || !wsRef.current) return;
    wsRef.current.send(input.trim());
    setMessages((m) => [...m, { role: 'user', content: input.trim() }]);
    setInput('');
    setError('');
  };

  return (
    <div className="chat-container">
      <div className="chat-box">
        <div className="chat-header">
          <button onClick={onLogout}>Logout</button>
        </div>
        <div className="messages">
          {messages.map((m, idx) => (
            <div key={idx} className={`message ${m.role}`}>
              {m.content}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        {error && <div className="error">{error}</div>}
        <form className="input-area" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your answer..."
          />
          <button type="submit">Send</button>
        </form>
      </div>
    </div>
  );
}

export default ChatPage;
