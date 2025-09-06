import React, { useState, useEffect } from 'react';
import AuthPage from '../pages/AuthPage.jsx';
import HomePage from '../pages/HomePage.jsx';

function App() {
  const [token, setToken] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('token');
    if (stored) {
      setToken(stored);
    }
  }, []);

  const handleAuth = (t) => {
    localStorage.setItem('token', t);
    setToken(t);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) {
    return <AuthPage onAuth={handleAuth} />;
  }

  return <HomePage onLogout={handleLogout} />;
}

export default App;
