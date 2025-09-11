# Career Coach Project Makefile
# ==================================

# Включение переменных из .env файла (если существует)
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Переменные проекта
PROJECT_ROOT := $(shell pwd)
VENV_DIR := $(PROJECT_ROOT)/venv
VENV_BIN := $(VENV_DIR)/bin
PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
UVICORN := $(VENV_BIN)/uvicorn
ALEMBIC := $(VENV_BIN)/alembic
PYTEST := $(VENV_BIN)/pytest

# Переменные окружения по умолчанию (если не заданы в .env)
DATABASE_URL ?= postgresql+asyncpg://user:password@localhost:5432/chat_service
SECRET_KEY ?= changeme
ENABLE_VACANCY_RECOMMENDATIONS ?= false
YANDEX_GPT_API_KEY ?= 
YANDEX_GPT_FOLDER_ID ?= 
QDRANT_URL ?= http://localhost:6333
QDRANT_COLLECTION ?= vacancies_tasks

# Цвета для вывода
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

.PHONY: help install setup backend frontend db-up db-down db-migrate db-reset test test-recommendations clean status logs

# Помощь (по умолчанию)
help:
	@echo "$(BLUE)Career Coach - Команды запуска проекта$(RESET)"
	@echo ""
	@echo "$(GREEN)🚀 ОСНОВНЫЕ КОМАНДЫ:$(RESET)"
	@echo "  make backend          - Запустить бэкенд API (FastAPI)"
	@echo "  make frontend         - Запустить фронтенд UI (React + Vite)"
	@echo "  make dev              - Запустить бэкенд и фронтенд параллельно"
	@echo ""
	@echo "$(GREEN)🛠️  НАСТРОЙКА И УСТАНОВКА:$(RESET)"
	@echo "  make install          - Установить все зависимости"
	@echo "  make setup            - Полная настройка проекта (первый запуск)"
	@echo ""
	@echo "$(GREEN)🗃️  БАЗА ДАННЫХ:$(RESET)"
	@echo "  make db-up            - Запустить PostgreSQL + Qdrant"
	@echo "  make db-down          - Остановить базы данных"
	@echo "  make db-migrate       - Применить миграции"
	@echo "  make db-reset         - Сбросить базу данных"
	@echo ""
	@echo "$(GREEN)🧪 ТЕСТИРОВАНИЕ:$(RESET)"
	@echo "  make test             - Запустить все тесты"
	@echo "  make test-recommendations - Тестировать систему рекомендаций"
	@echo ""
	@echo "$(GREEN)📊 МОНИТОРИНГ:$(RESET)"
	@echo "  make status           - Проверить статус всех сервисов"
	@echo "  make logs             - Показать логи Docker"
	@echo "  make clean            - Очистить временные файлы"
	@echo ""

# Установка зависимостей
install:
	@echo "$(YELLOW)📦 Установка зависимостей...$(RESET)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(BLUE)Создание виртуального окружения...$(RESET)"; \
		python3 -m venv $(VENV_DIR); \
	fi
	@echo "$(BLUE)Установка Python зависимостей...$(RESET)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "$(BLUE)Установка Node.js зависимостей...$(RESET)"
	@cd ui && npm install
	@echo "$(GREEN)✅ Зависимости установлены$(RESET)"

# Полная настройка проекта
setup: install db-up db-migrate load-vacancies
	@echo "$(GREEN)✅ Проект настроен и готов к работе!$(RESET)"
	@echo "$(BLUE)Запустите:$(RESET)"
	@echo "  make dev              - для разработки"
	@echo "  make backend          - только бэкенд"
	@echo "  make frontend         - только фронтенд"

# Запуск бэкенда
backend:
	@echo "$(BLUE)🚀 Запуск Backend API на http://localhost:8000$(RESET)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(RESET)"
	@export PYTHONPATH="$(PROJECT_ROOT):$$PYTHONPATH" && \
	export DATABASE_URL="$(DATABASE_URL)" && \
	export SECRET_KEY="$(SECRET_KEY)" && \
	export ENABLE_VACANCY_RECOMMENDATIONS="$(ENABLE_VACANCY_RECOMMENDATIONS)" && \
	export QDRANT_URL="$(QDRANT_URL)" && \
	export QDRANT_COLLECTION="$(QDRANT_COLLECTION)" && \
	$(UVICORN) app.main:app --host 127.0.0.1 --port 8000 --reload

# Запуск фронтенда  
frontend:
	@echo "$(BLUE)🎨 Запуск Frontend UI на http://localhost:5173$(RESET)"
	@cd ui && npm run dev

# Параллельный запуск бэкенда и фронтенда (для разработки)
dev:
	@echo "$(GREEN)🔥 Запуск в режиме разработки...$(RESET)"
	@echo "$(BLUE)Backend: http://localhost:8000$(RESET)"
	@echo "$(BLUE)Frontend: http://localhost:5173$(RESET)"
	@make -j2 backend frontend

# Запуск баз данных
db-up:
	@echo "$(BLUE)🗃️  Запуск PostgreSQL + Qdrant...$(RESET)"
	@docker-compose up -d
	@echo "$(YELLOW)Ждем инициализации баз данных...$(RESET)"
	@sleep 10
	@echo "$(GREEN)✅ Базы данных запущены$(RESET)"

# Остановка баз данных
db-down:
	@echo "$(YELLOW)⏹️  Остановка баз данных...$(RESET)"
	@docker-compose down
	@echo "$(GREEN)✅ Базы данных остановлены$(RESET)"

# Применение миграций
db-migrate:
	@echo "$(BLUE)📊 Применение миграций базы данных...$(RESET)"
	@export PYTHONPATH="$(PROJECT_ROOT):$$PYTHONPATH" && \
	export DATABASE_URL="$(DATABASE_URL)" && \
	$(ALEMBIC) upgrade head
	@echo "$(GREEN)✅ Миграции применены$(RESET)"

# Сброс базы данных
db-reset:
	@echo "$(RED)⚠️  ВНИМАНИЕ: Это удалит ВСЕ данные!$(RESET)"
	@read -p "Продолжить? (y/N): " confirm && [ "$$confirm" = "y" ]
	@docker-compose down -v
	@docker-compose up -d
	@sleep 10
	@make db-migrate
	@echo "$(GREEN)✅ База данных сброшена$(RESET)"

# Запуск всех тестов
test:
	@echo "$(BLUE)🧪 Запуск тестов...$(RESET)"
	@export PYTHONPATH="$(PROJECT_ROOT):$$PYTHONPATH" && \
	export DATABASE_URL="$(DATABASE_URL)" && \
	$(PYTEST) tests/ -v
	@echo "$(GREEN)✅ Тесты завершены$(RESET)"

# Тесты системы рекомендаций
test-recommendations:
	@echo "$(BLUE)🎯 Тестирование системы рекомендаций...$(RESET)"
	@export PYTHONPATH="$(PROJECT_ROOT):$$PYTHONPATH" && \
	export ENABLE_VACANCY_RECOMMENDATIONS="true" && \
	$(PYTHON) scripts/test_recommendations_integration.py
	@echo "$(GREEN)✅ Тесты рекомендаций завершены$(RESET)"

# Проверка статуса сервисов
status:
	@echo "$(BLUE)📊 Статус сервисов:$(RESET)"
	@echo ""
	@echo "$(YELLOW)🐳 Docker контейнеры:$(RESET)"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "Docker не запущен"
	@echo ""
	@echo "$(YELLOW)🌐 Проверка портов:$(RESET)"
	@if nc -z localhost 8000 2>/dev/null; then \
		echo "$(GREEN)✅ Backend API (8000): Работает$(RESET)"; \
	else \
		echo "$(RED)❌ Backend API (8000): Не доступен$(RESET)"; \
	fi
	@if nc -z localhost 5173 2>/dev/null; then \
		echo "$(GREEN)✅ Frontend UI (5173): Работает$(RESET)"; \
	else \
		echo "$(RED)❌ Frontend UI (5173): Не доступен$(RESET)"; \
	fi
	@if nc -z localhost 5432 2>/dev/null; then \
		echo "$(GREEN)✅ PostgreSQL (5432): Работает$(RESET)"; \
	else \
		echo "$(RED)❌ PostgreSQL (5432): Не доступен$(RESET)"; \
	fi
	@if curl -s http://localhost:6333/health >/dev/null 2>&1; then \
		echo "$(GREEN)✅ Qdrant (6333): Работает$(RESET)"; \
	else \
		echo "$(RED)❌ Qdrant (6333): Не доступен$(RESET)"; \
	fi
	@echo ""
	@echo "$(YELLOW)⚙️  Переменные окружения:$(RESET)"
	@echo "DATABASE_URL: $(DATABASE_URL)"
	@echo "ENABLE_VACANCY_RECOMMENDATIONS: $(ENABLE_VACANCY_RECOMMENDATIONS)"
	@echo "QDRANT_URL: $(QDRANT_URL)"

# Просмотр логов
logs:
	@echo "$(BLUE)📜 Логи Docker сервисов:$(RESET)"
	@docker-compose logs --tail=50 -f

# Очистка временных файлов
clean:
	@echo "$(YELLOW)🧹 Очистка временных файлов...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf ui/dist/ 2>/dev/null || true
	@rm -rf ui/.vite/ 2>/dev/null || true
	@echo "$(GREEN)✅ Очистка завершена$(RESET)"

# Создание .env файла с примером
env-example:
	@echo "$(BLUE)📝 Создание примера .env файла...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "# Career Coach Environment Variables" > .env; \
		echo "DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chat_service" >> .env; \
		echo "SECRET_KEY=changeme" >> .env; \
		echo "ENABLE_VACANCY_RECOMMENDATIONS=false" >> .env; \
 \
		echo "QDRANT_URL=http://localhost:6333" >> .env; \
		echo "QDRANT_COLLECTION=vacancies_tasks" >> .env; \
		echo "$(GREEN)✅ Файл .env создан$(RESET)"; \
		echo "$(YELLOW)⚠️  Не забудьте заполнить YANDEX_GPT_API_KEY и YANDEX_GPT_FOLDER_ID для работы рекомендаций$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Файл .env уже существует$(RESET)"; \
	fi

# Генерация эмбеддингов из вакансий (шаг 1 - долгий, дорогой)
generate-embeddings:
	@echo "$(BLUE)🤖 Генерация эмбеддингов из вакансий...$(RESET)"
	@if [ -z "$(YANDEX_GPT_API_KEY)" ]; then \
		echo "$(RED)❌ YANDEX_GPT_API_KEY не установлен!$(RESET)"; \
		exit 1; \
	fi
	@if [ ! -f scored_vacs.pickle ]; then \
		echo "$(RED)❌ Файл scored_vacs.pickle не найден!$(RESET)"; \
		exit 1; \
	fi
	@export PYTHONPATH="$(PROJECT_ROOT):$$PYTHONPATH" && \
	$(PYTHON) scripts/generate_embeddings.py
	@echo "$(GREEN)✅ Эмбеддинги сгенерированы и сохранены$(RESET)"

# Загрузка готовых эмбеддингов в Qdrant (шаг 2 - быстрый)
load-vacancies:
	@echo "$(BLUE)📊 Загрузка готовых эмбеддингов в Qdrant...$(RESET)"
	@if [ ! -f vacancies_with_embeddings.pickle ]; then \
		echo "$(RED)❌ Файл vacancies_with_embeddings.pickle не найден!$(RESET)"; \
		echo "$(YELLOW)💡 Сначала выполните: make generate-embeddings$(RESET)"; \
		exit 1; \
	fi
	@export PYTHONPATH="$(PROJECT_ROOT):$$PYTHONPATH" && \
	$(PYTHON) scripts/load_to_qdrant.py
	@echo "$(GREEN)✅ Вакансии загружены в Qdrant$(RESET)"

# Полный pipeline: генерация + загрузка (для первого запуска)
setup-vacancies: generate-embeddings load-vacancies
	@echo "$(GREEN)✅ Полная настройка вакансий завершена$(RESET)"

