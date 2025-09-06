const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function post(path, data) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || 'Request failed');
  }

  return res.json();
}
