# 🎯 Система рекомендаций вакансий

Система персонализированных рекомендаций вакансий для карьерного консультанта, интегрированная в WebSocket чат.

## 📋 Обзор функциональности

После завершения интервью система автоматически:
1. **Создает эмбеддинг** для поля `preferred_activities` из ответов пользователя
2. **Выполняет гибридный поиск** в Qdrant по специализации и семантическому сходству
3. **Возвращает 5 наиболее подходящих вакансий** с HH ID
4. **Отправляет рекомендации в чат** перед завершением сессии

## 🛡️ Безопасная архитектура

Система спроектирована с принципом **graceful degradation**:
- ✅ **Feature flag** - можно включать/выключать в любой момент
- ✅ **Изолированные сервисы** - не влияют на основной чат
- ✅ **Обработка ошибок** - сессия завершается даже при сбоях рекомендаций
- ✅ **Таймауты и retry** - защита от зависших запросов

## ⚙️ Настройка

### 1. Настройки в `app/core/settings.py`

```python
class Settings(BaseSettings):
    # ... существующие настройки ...
    
    # Recommendations system
    enable_vacancy_recommendations: bool = False  # Feature flag
    openai_api_key: str = ""
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "vacancies_tasks"
```

### 2. Переменные окружения

```bash
# В .env файле или export
ENABLE_VACANCY_RECOMMENDATIONS=true
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Зависимости

```bash
# Уже установлены в requirements.txt:
pip install qdrant-client openai tiktoken tenacity numpy
```

## 🚀 Быстрый старт

### 1. Запуск Qdrant

```bash
docker-compose up -d
```

### 2. Загрузка данных вакансий

```bash
python scripts/load_vacancies_to_qdrant.py
```

### 3. Включение рекомендаций

```bash
export ENABLE_VACANCY_RECOMMENDATIONS=true
export OPENAI_API_KEY=your_key_here
```

### 4. Тестирование

```bash
# Проверка архитектуры
python scripts/test_recommendations_mock.py

# Интеграционный тест
python scripts/test_recommendations_integration.py

# Демонстрация функциональности
python scripts/test_full_chat_with_recommendations.py

# Обычные тесты (должны проходить)
python -m pytest tests/ -v
```

## 🔧 Компоненты системы

### Сервисы

- **`EmbeddingsService`** - создание эмбеддингов через OpenAI API
- **`QdrantService`** - поиск вакансий в векторной базе  
- **`RecommendationService`** - основная бизнес-логика

### Файлы

```
app/services/recommendations/
├── __init__.py
├── embeddings_service.py      # OpenAI эмбеддинги
├── qdrant_service.py          # Поиск в Qdrant
└── recommendation_service.py  # Основной сервис

scripts/
├── test_recommendations.py           # Тест с реальными API
├── test_recommendations_mock.py      # Тест с mock данными
├── test_recommendations_integration.py # Интеграционный тест
└── test_full_chat_with_recommendations.py # Демонстрация
```

## 💬 Формат сообщений в чате

При завершении сессии с включенными рекомендациями отправляется:

```json
{
    "event": "recommendations",
    "message": "🎯 Нашли 5 подходящих вакансий для вас:",
    "data": {
        "recommendations": [
            {
                "hh_id": "124423602",
                "title": "Senior Python Developer", 
                "company": "Яндекс",
                "score": 84.7,
                "url": "https://hh.ru/vacancy/124423602",
                "category": "Бэкенд-разработчик"
            }
            // ... до 5 вакансий
        ],
        "hh_ids": ["124423602", "124281649", "124095408", "123987654", "123876543"]
    }
}
```

## 🔍 Алгоритм поиска

### 1. Извлечение данных
```python
target_specialization = collected_data["target_specialization"]  
preferred_activities = collected_data["preferred_activities"]
```

### 2. Создание эмбеддинга
```python
embedding = await embeddings_service.create_embedding(preferred_activities)
```

### 3. Гибридный поиск в Qdrant
```python
# Фильтр по специализации
filter_categories = get_mapping(target_specialization)

# Векторный поиск + фильтр
results = qdrant_client.search(
    collection_name="vacancies_tasks",
    query_vector=("tasks", embedding),
    query_filter=Filter(categories=filter_categories),
    limit=5
)
```

### 4. Маппинг специализаций

```python
SPECIALIZATION_MAPPING = {
    "Фулстек-разработчик": ["Бэкенд-разработчик", "Фронтенд-разработчик", "Фулстек-разработчик"],
    "ML-разработчик": ["ML-разработчик", "Machine Learning Engineer"],
    "DevOps-инженер": ["DevOps-инженер"],
    # ... полный список в qdrant_service.py
}
```

## 📊 Мониторинг и логирование

Система выводит подробные логи:

```bash
🔍 Получение рекомендаций для сессии 123e4567-e89b-12d3-a456-426614174000
📊 Данные для рекомендаций:
   Специализация: Фулстек-разработчик
   Активности: Разработка ПО, Системный анализ
✅ Эмбеддинг создан: размерность (768,)
🔍 Поиск для специализации: Фулстек-разработчик
📋 Фильтр категорий: ['Бэкенд-разработчик', 'Фронтенд-разработчик', 'Фулстек-разработчик']
✅ Найдено 5 рекомендаций
✅ Отправлены рекомендации: ['124423602', '124281649', '124095408', '123987654', '123876543']
```

## ⚠️ Обработка ошибок

### Graceful degradation
- **OpenAI недоступен** → сессия завершается без рекомендаций
- **Qdrant недоступен** → сессия завершается без рекомендаций  
- **Нет подходящих вакансий** → отправляется сообщение "рекомендации не найдены"
- **Некорректные данные сессии** → логируется, сессия завершается

### Пример обработки
```python
try:
    await self._send_vacancy_recommendations(session_id)
except Exception as e:
    print(f"❌ Ошибка получения рекомендаций (не критично): {e}")
    # Сессия продолжает завершаться корректно
finally:
    await self.repo.update_session(session_id, status="finished")
```

## 🧪 Тестирование

### Автоматические тесты
```bash
# Все существующие тесты должны проходить
python -m pytest tests/ -v

# Конкретно тест WebSocket чата
python -m pytest tests/test_e2e.py -v
```

### Ручное тестирование
1. **Выключенный флаг** - чат работает как обычно
2. **Включенный флаг без Qdrant** - чат завершается с сообщением об ошибке
3. **Включенный флаг с Qdrant** - чат завершается с рекомендациями
4. **Различные специализации** - проверить правильность фильтрации

## 📈 Производительность

### Типичные времена выполнения
- **Создание эмбеддинга**: ~1-3 секунды
- **Поиск в Qdrant**: ~100-500 мс
- **Общее время**: ~2-5 секунд

### Оптимизации
- Retry с exponential backoff для OpenAI
- Таймауты на все внешние вызовы
- Нормализация векторов для ускорения поиска

## 🔄 Версионность и миграции

### Текущая версия: v1.0
- Поддержка 12 вопросов интервью
- 33 специализации в маппинге
- 13,511 вакансий в базе данных

### Будущие улучшения
- Кэширование эмбеддингов
- Персонализация весов факторов
- Интеграция с другими источниками вакансий
- Обратная связь пользователей для улучшения рекомендаций

## 🆘 Troubleshooting

### Частые проблемы

**1. "OpenAI API key not found"**
```bash
export OPENAI_API_KEY=your_key_here
# или добавить в .env файл
```

**2. "Qdrant connection failed"**
```bash
docker-compose up -d
curl http://localhost:6333/health  # должен вернуть {"status":"ok"}
```

**3. "Collection vacancies_tasks not found"**
```bash
python scripts/load_vacancies_to_qdrant.py
```

**4. "No recommendations found"**
- Проверить данные в collected_data
- Убедиться что target_specialization есть в маппинге
- Проверить что preferred_activities не пустое

### Полезные команды

```bash
# Проверить статус Qdrant
curl http://localhost:6333/collections/vacancies_tasks

# Проверить количество векторов
curl http://localhost:6333/collections/vacancies_tasks/points/count

# Открыть Qdrant Dashboard
open http://localhost:6333/dashboard

# Посмотреть логи Docker
docker-compose logs qdrant
```

## 🤝 Поддержка

Система разработана с принципом **fail-safe** - основной чат никогда не сломается из-за ошибок в рекомендациях.

При возникновении проблем:
1. Проверить логи приложения
2. Убедиться что все внешние сервисы доступны  
3. Временно выключить feature flag: `ENABLE_VACANCY_RECOMMENDATIONS=false`
4. Использовать тестовые скрипты для диагностики компонентов

---

✅ **Система готова к продакшну и безопасна для использования!**
