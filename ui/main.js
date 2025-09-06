document.addEventListener('DOMContentLoaded', () => {
  const authContainer = document.getElementById('auth-container');
  const welcome = document.getElementById('welcome');
  const token = localStorage.getItem('token');

  if (token) {
    authContainer.classList.add('hidden');
    welcome.classList.remove('hidden');
  }

  const registerForm = document.getElementById('register-form');
  const loginForm = document.getElementById('login-form');
  const logoutBtn = document.getElementById('logout');

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const login = document.getElementById('register-login').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    try {
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login, email, password })
      });
      if (!res.ok) {
        throw new Error('Registration failed');
      }
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      authContainer.classList.add('hidden');
      welcome.classList.remove('hidden');
    } catch (err) {
      alert(err.message);
    }
  });

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const login = document.getElementById('login-login').value;
    const password = document.getElementById('login-password').value;
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login, password })
      });
      if (!res.ok) {
        throw new Error('Login failed');
      }
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      authContainer.classList.add('hidden');
      welcome.classList.remove('hidden');
    } catch (err) {
      alert(err.message);
    }
  });

  logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('token');
    welcome.classList.add('hidden');
    authContainer.classList.remove('hidden');
  });
});
