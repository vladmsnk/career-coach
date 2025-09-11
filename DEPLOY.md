# 🚀 Инструкция по деплою Career Coach

Пошаговое руководство по разворачиванию приложения на виртуальной машине с помощью Docker Compose.

## 📋 Предварительные требования

### На виртуальной машине должны быть установлены:

1. **Docker и Docker Compose**
```bash
# Обновление системы (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перелогиниться для применения группы docker
newgrp docker
```

2. **Git**
```bash
sudo apt install git -y
```

3. **Проверка установки**
```bash
docker --version
docker-compose --version
git --version
```

## 🔧 Процесс деплоя

### 1. Клонирование проекта

```bash
# На виртуальной машине
git clone <your-repository-url>
cd career-coach-be
```

### 2. Настройка переменных окружения

```bash
# Создать файл переменных окружения из шаблона
cp env.production.template .env.prod

# Отредактировать файл с актуальными значениями
nano .env.prod
```

**Важно заполнить:**
- `POSTGRES_PASSWORD` - надежный пароль для БД
- `SECRET_KEY` - секретный ключ для JWT (минимум 32 символа)
- `OPENAI_API_KEY` - ключ OpenAI API (если нужны рекомендации)

### 3. Подготовка данных вакансий (опционально)

Если требуются рекомендации вакансий:

```bash
# Поместить файл с эмбеддингами в корень проекта
# Файл должен называться: vacancies_with_embeddings.pickle
ls -la vacancies_with_embeddings.pickle
```

**Если файла нет:**
- Скопируйте `scored_vacs.pickle` в корень проекта
- Локально выполните `make generate-embeddings`  
- Скопируйте полученный `vacancies_with_embeddings.pickle` на сервер

### 4. Запуск приложения

```bash
# Сборка и запуск всех сервисов
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Проверка статуса контейнеров
docker-compose -f docker-compose.prod.yml ps
```

**Если возникли ошибки сборки:**
```bash
# Остановить контейнеры
docker-compose -f docker-compose.prod.yml --env-file .env.prod down

# Пересобрать с очисткой кеша
docker-compose -f docker-compose.prod.yml --env-file .env.prod build --no-cache

# Запустить заново
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### 5. Ожидание инициализации

```bash
# Дождаться готовности всех сервисов (обычно 1-2 минуты)
# Проверить логи
docker-compose -f docker-compose.prod.yml logs -f
```

### 6. Применение миграций

```bash
# Применить миграции базы данных
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 7. Загрузка данных вакансий (если есть файл)

```bash
# Если файл vacancies_with_embeddings.pickle присутствует
docker-compose -f docker-compose.prod.yml exec backend python scripts/load_to_qdrant.py
```

## 🌐 Проверка работоспособности

### Проверить доступность сервисов:

```bash
# Фронтенд
curl http://localhost/health

# Backend
curl http://localhost/api/health  

# Qdrant
curl http://localhost:6333/health

# PostgreSQL (изнутри контейнера)
docker-compose -f docker-compose.prod.yml exec backend pg_isready -h db -U career_coach_user
```

### Доступные URL:
- **Приложение**: http://your-server-ip
- **API Docs**: http://your-server-ip/api/docs  
- **Qdrant Dashboard**: http://your-server-ip:6333/dashboard

## 🔄 Управление приложением

### Остановка всех сервисов
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod down
```

### Перезапуск сервисов
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod restart
```

### Просмотр логов
```bash
# Все сервисы
docker-compose -f docker-compose.prod.yml logs -f

# Конкретный сервис
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Обновление приложения
```bash
# Получить обновления из Git
git pull origin main

# Пересобрать и перезапустить
docker-compose -f docker-compose.prod.yml --env-file .env.prod down
docker-compose -f docker-compose.prod.yml --env-file .env.prod build --no-cache
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## 📊 Мониторинг

### Статус контейнеров
```bash
docker ps
docker stats
```

### Дисковое пространство
```bash
# Размер volumes
docker system df

# Очистка неиспользуемых данных
docker system prune -a
```

### Backup данных
```bash
# Backup PostgreSQL
docker run --rm -v career-coach-be_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Backup Qdrant
docker run --rm -v career-coach-be_qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_backup.tar.gz -C /data .
```

## ⚠️ Решение проблем

### Контейнер backend не запускается
```bash
# Проверить логи
docker-compose -f docker-compose.prod.yml logs backend

# Проверить подключение к БД
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.core.db import engine; print('DB OK')"
```

### Ошибки миграций
```bash
# Проверить текущую версию БД
docker-compose -f docker-compose.prod.yml exec backend alembic current

# Сбросить и применить миграции заново
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade base
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Qdrant недоступен
```bash
# Перезапуск Qdrant
docker-compose -f docker-compose.prod.yml restart qdrant

# Проверка storage
docker-compose -f docker-compose.prod.yml exec qdrant ls -la /qdrant/storage
```

### Frontend показывает ошибку 502
```bash
# Проверить что backend доступен
docker-compose -f docker-compose.prod.yml exec frontend curl http://backend:8000/health

# Проверить nginx конфигурацию
docker-compose -f docker-compose.prod.yml exec frontend nginx -t
```

## 🔐 Безопасность

### Рекомендации для production:

1. **Смените пароли по умолчанию**
   - DATABASE_URL пароль
   - SECRET_KEY

2. **Настройте SSL** (опционально)
   ```bash
   # Добавить Let's Encrypt или собственные сертификаты
   # Обновить nginx конфигурацию для HTTPS
   ```

3. **Ограничьте доступ к портам**
   ```bash
   # Закрыть прямой доступ к БД и Qdrant извне
   # Оставить открытыми только 80 (и 443 для SSL)
   ```

4. **Регулярные обновления**
   ```bash
   # Обновляйте Docker образы
   docker-compose -f docker-compose.prod.yml pull
   ```

## ✅ Готово!

После выполнения всех шагов приложение будет доступно по IP адресу вашей виртуальной машины. 

**Основные компоненты:**
- ✅ Frontend (React) с nginx - порт 80
- ✅ Backend API (FastAPI) - внутренний порт 8000  
- ✅ PostgreSQL база данных - внутренний порт 5432
- ✅ Qdrant векторная БД - внутренний порт 6333

**Система готова к работе!** 🎉
