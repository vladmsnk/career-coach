const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

function toFriendlyMessage(status, payload) {
  const detail = typeof payload?.detail === 'string' ? payload.detail : null;
  if (detail === 'User already exists') return 'Пользователь уже существует';
  if (detail === 'Invalid credentials') return 'Неверный логин или пароль';

  if (status === 400) return 'Некорректные данные. Проверьте введённые поля.';
  if (status === 401) return 'Неверный логин или пароль';
  if (status === 422) return 'Проверьте корректность введённых данных.';
  if (status >= 500) return 'Ошибка сервера. Повторите попытку позже.';
  return detail || 'Не удалось выполнить запрос';
}

export async function post(path, data) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      let json = null;
      try {
        json = await res.json();
      } catch (_) {
        // ignore
      }
      const message = toFriendlyMessage(res.status, json);
      throw new Error(message);
    }

    return res.json();
  } catch (e) {
    if (e instanceof TypeError) {
      // network error / CORS / connection refused
      throw new Error('Нет соединения с сервером. Проверьте подключение.');
    }
    throw e;
  }
}
