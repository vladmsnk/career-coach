import React, { useState } from 'react';
import AuthForm from '../components/AuthForm.jsx';
import { login, register } from '../services/auth.js';

function AuthPage({ onAuth }) {
  const [mode, setMode] = useState('login');
  const [error, setError] = useState('');

  const handleSubmit = async (email, password) => {
    setError('');
    try {
      const token =
        mode === 'login' ? await login(email, password) : await register(email, password);
      onAuth(token);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <AuthForm
        title={mode === 'login' ? 'Login' : 'Register'}
        error={error}
        onSubmit={handleSubmit}
        switchText={mode === 'login' ? 'Need an account? Register' : 'Have an account? Login'}
        onSwitch={() => setMode(mode === 'login' ? 'register' : 'login')}
      />
    </div>
  );
}

export default AuthPage;
