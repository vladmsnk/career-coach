# 🚀 Генерация и загрузка эмбеддингов

Простые команды для запуска генерации эмбеддингов и их загрузки в Qdrant.

## 📋 **Предварительные требования**

1. Файл `.env.prod` с настройками:
   ```bash
   YANDEX_GPT_API_KEY=your_yandex_gpt_api_key_here
   YANDEX_GPT_FOLDER_ID=your_yandex_folder_id_here
   QDRANT_COLLECTION=vacancies_tasks
   ```

2. Файл `scored_vacs.pickle` в корне проекта

## 🎯 **Простые команды для запуска**

### **Вариант 1: Полный пайплайн (все в одной команде) ⭐ РЕКОМЕНДУЕМЫЙ**
```bash
# Загрузить переменные окружения
source .env.prod

# Запустить Qdrant + полную генерацию + загрузку
docker-compose -f docker-compose.prod.yml up -d qdrant
docker-compose -f docker-compose.prod.yml --profile embeddings up embeddings-pipeline
```

### **Вариант 2: Пошагово**
```bash
# 1. Загрузить переменные
source .env.prod

# 2. Запустить Qdrant
docker-compose -f docker-compose.prod.yml up -d qdrant

# 3. Сгенерировать эмбеддинги
docker-compose -f docker-compose.prod.yml --profile embeddings up generate-embeddings

# 4. Загрузить в Qdrant
docker-compose -f docker-compose.prod.yml --profile embeddings up load-to-qdrant
```

### **Вариант 3: Через exec (если backend уже запущен)**
```bash
# 1. Загрузить переменные
source .env.prod

# 2. Убедиться, что сервисы запущены
docker-compose -f docker-compose.prod.yml up -d qdrant backend

# 3. Сгенерировать эмбеддинги (с автоподтверждением)
docker-compose -f docker-compose.prod.yml exec -e AUTO_CONFIRM=true backend python scripts/generate_embeddings.py

# 4. Загрузить в Qdrant
docker-compose -f docker-compose.prod.yml exec backend python scripts/load_to_qdrant.py
```

## 🔍 **Проверка результатов**

```bash
# Проверить созданные файлы
ls -la *.pickle

# Проверить Qdrant dashboard
open http://localhost:6333/dashboard

# Проверить логи
docker-compose -f docker-compose.prod.yml logs generate-embeddings
docker-compose -f docker-compose.prod.yml logs load-to-qdrant
```

## 🛠️ **Дополнительные команды**

```bash
# Очистить все и перезапустить
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d qdrant

# Только генерация (без загрузки)
docker-compose -f docker-compose.prod.yml --profile embeddings up generate-embeddings

# Только загрузка (если файл уже есть)  
docker-compose -f docker-compose.prod.yml --profile embeddings up load-to-qdrant

# Полный пайплайн
docker-compose -f docker-compose.prod.yml --profile embeddings up embeddings-pipeline

# Принудительная пересборка образов
docker-compose -f docker-compose.prod.yml build --no-cache
```

## 📊 **Ожидаемые результаты**

После успешного выполнения у вас будет:

- ✅ `vacancies_with_embeddings.pickle` (или `vacancies_with_embeddings_test.pickle`)
- ✅ Данные загружены в Qdrant коллекцию `vacancies_tasks`
- ✅ Доступен Qdrant dashboard на http://localhost:6333/dashboard
- ✅ Рекомендательная система готова к работе

## ⚠️ **Устранение проблем**

**Ошибка доступа к файлам:**
```bash
# Убедитесь, что файлы доступны
ls -la scored_vacs.pickle
docker-compose -f docker-compose.prod.yml --profile embeddings run --rm generate-embeddings ls -la /app/
```

**Ошибка подключения к Qdrant:**
```bash
# Проверьте статус Qdrant
docker-compose -f docker-compose.prod.yml ps qdrant
docker-compose -f docker-compose.prod.yml logs qdrant
```

**Проблемы с переменными окружения:**
```bash
# Проверьте переменные
echo $YANDEX_GPT_API_KEY
echo $YANDEX_GPT_FOLDER_ID
```
