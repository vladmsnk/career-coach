# 🚀 Career Coach - Руководство по запуску

Полное руководство по запуску системы карьерного консультанта с чат-ботом и рекомендациями вакансий.

## 📋 Обзор системы

**Career Coach** - это веб-приложение для карьерного консультирования, состоящее из:

- 🤖 **Чат-бот** - интерактивные интервью для определения карьерных предпочтений
- 🎯 **Система рекомендаций** - подбор вакансий на основе ответов пользователя
- 🔐 **Аутентификация** - регистрация и авторизация пользователей
- 📊 **Векторный поиск** - семантический поиск по вакансиям через Qdrant + OpenAI

## 🛠️ Стек технологий

### Backend
- **FastAPI** - API сервер
- **PostgreSQL** - основная база данных
- **Qdrant** - векторная база для поиска вакансий
- **OpenAI API** - создание эмбеддингов для семантического поиска
- **SQLAlchemy** - ORM для работы с БД
- **WebSockets** - реалтайм чат

### Frontend  
- **React** - пользовательский интерфейс
- **Vite** - сборщик и dev-сервер
- **CSS** - стилизация компонентов

### Инфраструктура
- **Docker Compose** - контейнеризация сервисов
- **Alembic** - миграции базы данных
- **JWT** - токены авторизации

---

## 🚀 Быстрый старт

### 1. Предварительные требования

Убедитесь что у вас установлены:
- **Python 3.9+**
- **Node.js 18+** и **npm**
- **Docker** и **Docker Compose**
- **Git**

### 2. Клонирование и переход в проект

```bash
git clone <repository-url>
cd career-coach-be
```

### 3. Полная автоматическая установка ⚡

```bash
# Одна команда для полной настройки проекта
make setup
```

Эта команда автоматически:
- ✅ Создаст виртуальное окружение Python
- ✅ Установит все зависимости Python и Node.js
- ✅ Запустит PostgreSQL и Qdrant в Docker
- ✅ Применит миграции базы данных

### 4. Запуск в режиме разработки

```bash
# Запуск бэкенда и фронтенда параллельно
make dev
```

🎉 **Готово!** Система будет доступна по адресам:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📖 Пошаговая настройка (альтернатива)

<details>
<summary>Если хотите настроить вручную, разверните этот раздел</summary>

### Шаг 1: Виртуальное окружение Python

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или 
# venv\Scripts\activate  # Windows
```

### Шаг 2: Установка зависимостей

```bash
# Python зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Node.js зависимости  
cd ui
npm install
cd ..
```

### Шаг 3: Запуск сервисов

```bash
# PostgreSQL + Qdrant
docker-compose up -d

# Ждем запуска (10-15 секунд)
sleep 15
```

### Шаг 4: Настройка базы данных

```bash
# Применение миграций
PYTHONPATH=. alembic upgrade head
```

### Шаг 5: Настройка переменных окружения (опционально)

```bash
# Создание .env файла
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chat_service
SECRET_KEY=your-secret-key-here
ENABLE_VACANCY_RECOMMENDATIONS=false
OPENAI_API_KEY=
YANDEX_GPT_API_KEY=
YANDEX_GPT_FOLDER_ID=
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=vacancies_tasks
EOF
```

### Шаг 6: Запуск приложения

```bash
# Backend (в первом терминале)
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (во втором терминале)
cd ui
npm run dev
```

</details>

---

## 🎯 Настройка системы рекомендаций (опционально)

Система рекомендаций вакансий работает на основе векторного поиска и требует дополнительной настройки.

### 1. Получение API ключей

#### OpenAI API
1. Зарегистрируйтесь на https://platform.openai.com/
2. Создайте API ключ
3. Добавьте ключ в переменные окружения:

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
# или добавьте в .env файл
echo "OPENAI_API_KEY=your-key-here" >> .env
```

#### Yandex GPT API
1. Создайте аккаунт в Yandex Cloud
2. Получите API ключ и folder_id
3. Добавьте credentials в переменные окружения:

```bash
export YANDEX_GPT_API_KEY="your-yandex-gpt-api-key"
export YANDEX_GPT_FOLDER_ID="your-folder-id"
# или добавьте в .env файл
echo "YANDEX_GPT_API_KEY=your-key-here" >> .env
echo "YANDEX_GPT_FOLDER_ID=your-folder-id" >> .env
```

### 2. Подготовка данных вакансий

Поместите файл с вакансиями в корень проекта:

```bash
# Файл должен называться scored_vacs.pickle
ls -la scored_vacs.pickle
```

### 3. Загрузка данных в Qdrant

```bash
# Загрузка ~13,500 вакансий (займет 20-30 минут, ~$1-2 USD)
make load-vacancies
```

### 4. Включение рекомендаций

```bash
# Включить систему рекомендаций
export ENABLE_VACANCY_RECOMMENDATIONS=true
```

### 5. Тестирование рекомендаций

```bash
# Тест интеграции с реальными API
make test-recommendations
```

---

## 🔧 Полезные команды

### Управление проектом

```bash
make help              # Показать все доступные команды
make status             # Проверить статус всех сервисов  
make logs               # Показать логи Docker контейнеров
make clean              # Очистить временные файлы
```

### Запуск компонентов по отдельности

```bash
make backend            # Только Backend API (порт 8000)
make frontend           # Только Frontend UI (порт 5173)
make db-up              # Только базы данных (PostgreSQL + Qdrant)
make db-down            # Остановить базы данных
```

### База данных

```bash
make db-migrate         # Применить новые миграции
make db-reset           # Сбросить БД (ВНИМАНИЕ: удалит все данные!)
```

### Тестирование

```bash
make test               # Запустить все тесты
make test-recommendations # Тестировать систему рекомендаций
```

---

## 🌐 Доступные сервисы

После запуска будут доступны:

| Сервис | URL | Описание |
|--------|-----|----------|
| **Frontend** | http://localhost:5173 | Веб-интерфейс приложения |
| **Backend API** | http://localhost:8000 | REST API сервер |
| **API Documentation** | http://localhost:8000/docs | Swagger UI с документацией API |
| **PostgreSQL** | localhost:5432 | Основная база данных |
| **Qdrant REST** | http://localhost:6333 | Векторная база данных |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Web UI для Qdrant |

---

## 🧪 Тестирование системы

### Автоматические тесты

```bash
# Запуск всех тестов
make test

# Конкретные тесты
python -m pytest tests/test_auth.py -v          # Тесты аутентификации  
python -m pytest tests/test_chat.py -v          # Тесты чата
python -m pytest tests/test_e2e.py -v           # End-to-end тесты
```

### Ручное тестирование через API

```bash
# Проверка здоровья API
curl http://localhost:8000/health

# Регистрация пользователя
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "password123"}'

# Авторизация  
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "password123"}'
```

### Тестирование чата через WebSocket

Откройте браузер на http://localhost:5173 и:

1. **Зарегистрируйтесь** или войдите в систему
2. **Начните чат** - система задаст вопросы о карьерных предпочтениях  
3. **Ответьте на вопросы** - бот проведет интерактивное интервью
4. **Получите рекомендации** (если настроена система рекомендаций)

---

## ⚠️ Решение проблем

### Backend не запускается

```bash
# Проверьте что БД запущена
make status

# Проверьте переменные окружения
echo $DATABASE_URL

# Примените миграции заново  
make db-migrate
```

### Frontend показывает ошибки

```bash
# Переустановите зависимости
cd ui
rm -rf node_modules package-lock.json  
npm install

# Проверьте что backend доступен
curl http://localhost:8000/health
```

### Qdrant недоступен

```bash
# Перезапустите контейнеры
docker-compose restart qdrant

# Проверьте логи
docker-compose logs qdrant

# Проверьте что порт свободен
netstat -tulpn | grep 6333
```

### Система рекомендаций не работает

```bash
# Проверьте OpenAI ключ
echo $OPENAI_API_KEY

# Проверьте что данные загружены
curl http://localhost:6333/collections/vacancies_tasks

# Запустите диагностику
python scripts/test_qdrant_connection.py
```

### Ошибки миграций

```bash
# Сбросить и создать БД заново (ВНИМАНИЕ: удалит данные!)
make db-reset

# Или применить миграции вручную
PYTHONPATH=. alembic upgrade head
```

---

## 📊 Архитектура системы

### Backend (Clean Architecture)

```
app/
├── api/v1/routes/          # REST API endpoints
├── application/            # Use cases (бизнес-логика)  
├── domain/                 # Entities и repository интерфейсы
├── infrastructure/         # Реализации репозиториев, БД модели
├── services/               # Внешние сервисы (OpenAI, Qdrant)
├── schemas/                # Pydantic модели
└── core/                   # Настройки, подключение к БД
```

### Основные компоненты

- **Authentication** - JWT токены, регистрация/авторизация
- **Chat System** - WebSocket чат с bot, сессии разговоров
- **Recommendation Engine** - векторный поиск вакансий на основе предпочтений
- **Database Layer** - PostgreSQL для данных, Qdrant для векторов

---

## 🔒 Безопасность

- **JWT токены** для аутентификации
- **Bcrypt** для хеширования паролей
- **CORS** настроен для разработки
- **Environment variables** для чувствительных данных
- **Graceful error handling** - система не падает при ошибках рекомендаций

---

## 📈 Производительность

### Ожидаемые времена отклика

- **REST API**: 50-200ms
- **WebSocket чат**: <100ms  
- **Создание эмбеддинга**: 1-3 секунды
- **Поиск в Qdrant**: 100-500ms
- **Полный цикл рекомендаций**: 2-5 секунд

### Мониторинг

```bash
# Проверка статуса всех сервисов
make status

# Мониторинг логов в реальном времени  
make logs

# Проверка ресурсов Docker
docker stats
```

---

## 🚀 Готово к использованию!

После выполнения команды `make setup` и `make dev` у вас будет полностью рабочая система карьерного консультанта с чат-ботом.

**Для включения рекомендаций вакансий дополнительно потребуется:**
1. OpenAI API ключ
2. Файл с данными вакансий (`scored_vacs.pickle`)  
3. Загрузка данных: `make load-vacancies`
4. Включение флага: `ENABLE_VACANCY_RECOMMENDATIONS=true`

**Быстрые ссылки:**
- 🌐 Приложение: http://localhost:5173
- 📚 API Docs: http://localhost:8000/docs  
- 🔍 Qdrant Dashboard: http://localhost:6333/dashboard

---

*Система спроектирована с принципом fail-safe - основной чат будет работать корректно даже без настроенных рекомендаций или при ошибках внешних сервисов.*
