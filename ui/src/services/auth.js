import { post } from './apiClient.js';

export async function login(email, password) {
  const data = await post('/api/v1/auth/login', { email, password });
  return data.access_token;
}

export async function register(email, password) {
  const data = await post('/api/v1/auth/register', { email, password });
  return data.access_token;
}
