# 🚀 Настройка векторной базы данных Qdrant

Инструкция по загрузке вакансий в векторную базу данных Qdrant для системы рекомендаций.

## 📋 Предварительные требования

1. **OpenAI API ключ** - для создания эмбеддингов
2. **Файл данных** - `scored_vacs.pickle` в корне проекта
3. **Docker** - для запуска Qdrant
4. **Python 3.9+** - с установленными зависимостями

## 🛠️ Пошаговая инструкция

### Шаг 1: Установка зависимостей

```bash
cd /Users/vymoiseenkov/Desktop/career-coach-be
source venv/bin/activate
pip install -r requirements.txt
```

### Шаг 2: Запуск сервисов

```bash
# Запуск PostgreSQL и Qdrant
docker-compose up -d

# Проверка что Qdrant работает
curl http://localhost:6333/health
```

### Шаг 3: Настройка переменных окружения

```bash
# Установите OpenAI API ключ
export OPENAI_API_KEY="your-openai-key-here"

# Или создайте файл .env
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### Шаг 4: Подготовка файла данных

Убедитесь что файл `scored_vacs.pickle` находится в корне проекта:

```bash
ls -la scored_vacs.pickle
# Если файла нет, скопируйте его:
# cp /path/to/scored_vacs.pickle ./
```

### Шаг 5: Запуск загрузки данных

```bash
# Запуск полного pipeline
python scripts/load_vacancies_to_qdrant.py
```

## 📊 Что происходит в процессе

1. **Парсинг данных** (~1 мин) - извлечение вакансий из pickle файла
2. **Создание эмбеддингов** (~15-25 мин) - генерация векторов через OpenAI API
3. **Загрузка в Qdrant** (~2-3 мин) - сохранение векторов и метаданных
4. **Тестирование поиска** (~30 сек) - проверка функциональности

## 💰 Стоимость и ресурсы

- **Данные**: ~13,500 вакансий
- **Токены**: ~5.4M токенов
- **OpenAI стоимость**: ~$1-2 USD
- **Время**: ~25-30 минут
- **Место на диске**: ~500MB

## 🎯 Результат

После успешной загрузки у вас будет:

- ✅ Векторная коллекция `vacancies_tasks` в Qdrant
- ✅ ~13,500 вакансий с эмбеддингами
- ✅ Метаданные для фильтрации
- ✅ REST API для поиска (порт 6333)

## 🔍 Проверка результата

### Веб интерфейс Qdrant
```
http://localhost:6333/dashboard
```

### API запросы
```bash
# Список коллекций
curl http://localhost:6333/collections

# Информация о коллекции
curl http://localhost:6333/collections/vacancies_tasks

# Количество записей
curl http://localhost:6333/collections/vacancies_tasks/points/count
```

## 🛠️ Настройки скрипта

В файле `scripts/load_vacancies_to_qdrant.py` можно изменить:

```python
# Настройки эмбеддингов
MODEL = "text-embedding-3-small"  # или text-embedding-3-large
DIM = 768                         # или 1536 для большей точности

# Настройки производительности  
CONCURRENCY = 8                   # параллельные запросы к OpenAI
BATCH_SIZE = 128                  # размер батча

# Настройки Qdrant
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "vacancies_tasks"
```

## ⚠️ Возможные проблемы

### Qdrant не запускается
```bash
# Проверьте Docker
docker ps | grep qdrant

# Перезапустите
docker-compose restart qdrant
```

### Ошибки OpenAI API
```bash
# Проверьте ключ
echo $OPENAI_API_KEY

# Проверьте квоты в OpenAI аккаунте
```

### Нет файла данных
```bash
# Убедитесь что файл в корне проекта
ls -la scored_vacs.pickle
```

## 🔄 Обновление данных

Для обновления векторной базы новыми вакансиями:

1. Замените файл `scored_vacs.pickle`
2. Запустите скрипт повторно
3. Старая коллекция будет пересоздана автоматически

## 📞 Использование в приложении

После загрузки данных можно использовать Qdrant для поиска:

```python
from qdrant_client import QdrantClient

client = QdrantClient("http://localhost:6333")

# Поиск по векторному запросу
results = client.search(
    collection_name="vacancies_tasks",
    query_vector=("tasks", your_query_embedding),
    limit=5
)
```

## 🎉 Готово!

Векторная база данных настроена и готова для интеграции с системой рекомендаций вакансий!
