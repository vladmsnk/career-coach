import React, { useState } from 'react';

function AuthForm({ title, error, onSubmit, switchText, onSwitch }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(email, password);
  };

  return (
    <div className="card">
      <h2>{title}</h2>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">{title}</button>
      </form>
      <button className="link" type="button" onClick={onSwitch}>
        {switchText}
      </button>
    </div>
  );
}

export default AuthForm;
