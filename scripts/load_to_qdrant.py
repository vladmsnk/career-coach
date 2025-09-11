#!/usr/bin/env python3
"""
Скрипт для загрузки готовых эмбеддингов в Qdrant.
Использование: python scripts/load_to_qdrant.py
"""
import asyncio
import os
import pickle
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid5, NAMESPACE_URL
from datetime import datetime

import numpy as np
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, PointStruct, 
    CollectionStatus, OptimizersConfigDiff
)

# ==================== НАСТРОЙКИ ====================
QDRANT_URL = os.getenv('QDRANT_URL', "http://localhost:6333")
COLLECTION_NAME = os.getenv('QDRANT_COLLECTION', "vacancies_tasks")
INPUT_FILE = "vacancies_with_embeddings.pickle"
UPLOAD_BATCH_SIZE = 256

# ==================== QDRANT ФУНКЦИИ ====================

async def setup_qdrant_collection(client: QdrantClient, collection_name: str, vector_dim: int):
    """Создает или пересоздает коллекцию Qdrant."""
    print(f"🔧 Настройка коллекции '{collection_name}'...")
    
    try:
        # Проверяем существование коллекции
        collections = client.get_collections()
        existing_collection = next(
            (c for c in collections.collections if c.name == collection_name), 
            None
        )
        
        if existing_collection:
            print(f"⚠️  Коллекция '{collection_name}' уже существует. Удаляем...")
            client.delete_collection(collection_name)
        
        # Создаем новую коллекцию
        print(f"🆕 Создаем коллекцию '{collection_name}' с размерностью {vector_dim}...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "tasks": VectorParams(
                    size=vector_dim,
                    distance=Distance.COSINE
                )
            },
            optimizers_config=OptimizersConfigDiff(
                indexing_threshold=10000
            )
        )
        
        print(f"✅ Коллекция '{collection_name}' создана успешно")
        
    except Exception as e:
        print(f"❌ Ошибка настройки коллекции: {e}")
        raise

def parse_vacancy_data(row) -> Dict[str, Any]:
    """Парсит и очищает данные вакансии."""
    def safe_get(field, default=""):
        value = row.get(field, default)
        if pd.isna(value):
            return default
        return str(value).strip()
    
    def parse_json_field(field, default=None):
        try:
            value = row.get(field)
            if pd.isna(value):
                return default
            if isinstance(value, str):
                return json.loads(value)
            return value
        except:
            return default
    
    # Парсим основные поля (они уже должны быть распарсены из answers_list)
    hh_id = safe_get('hh_id')
    if not hh_id:
        # Fallback: извлекаем из URL если есть
        url = safe_get('url')
        if url and 'vacancy/' in url:
            hh_id = url.split('/')[-1]
        else:
            hh_id = safe_get('id')
    
    # URL должен быть уже готовым или создаем его
    url = safe_get('url')
    if not url and hh_id:
        url = f"https://hh.ru/vacancy/{hh_id}"
    
    # Парсим задачи - они могут быть уже как список или строка
    tasks = row.get('tasks', [])
    if isinstance(tasks, list):
        tasks_list = tasks
        tasks_text = " ".join(str(task).strip() for task in tasks if str(task).strip())
    elif isinstance(tasks, str):
        try:
            tasks_list = json.loads(tasks)
            tasks_text = " ".join(str(task).strip() for task in tasks_list if str(task).strip())
        except:
            tasks_list = [tasks]
            tasks_text = tasks.strip()
    else:
        tasks_list = []
        tasks_text = ""
    
    # Используем готовый tasks_text если есть
    if 'tasks_text' in row and row['tasks_text']:
        tasks_text = safe_get('tasks_text')
    
    # Парсим навыки
    skills = row.get('skills', [])
    if isinstance(skills, str):
        try:
            skills = json.loads(skills)
        except:
            skills = [skills] if skills.strip() else []
    if not isinstance(skills, list):
        skills = []
    
    return {
        "hh_id": hh_id,
        "url": url,
        "title": safe_get("title"),
        "company": safe_get("company"),
        "location": safe_get("location"),
        "experience": safe_get("experience"),
        "employment_type": safe_get("employment_type"),
        "remote": safe_get("remote"),
        "posted_at": safe_get("posted_at"),
        "tasks_list": tasks_list,
        "tasks_text": tasks_text,
        "skills": skills,
        "raw_category": safe_get("category"),
        "confidence": float(row.get("confidence", 0.0)) if not pd.isna(row.get("confidence")) else 0.0,
    }

async def upload_to_qdrant(
    client: QdrantClient, 
    collection_name: str, 
    df: pd.DataFrame, 
    embeddings: np.ndarray,
    batch_size: int = UPLOAD_BATCH_SIZE
):
    """Загружает данные и эмбеддинги в Qdrant."""
    print(f"📤 Загружаем {len(df)} записей в Qdrant...")
    
    if len(df) != len(embeddings):
        raise ValueError(f"Размерности не совпадают: df={len(df)}, embeddings={len(embeddings)}")
    
    total_batches = (len(df) + batch_size - 1) // batch_size
    successful_uploads = 0
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(df))
        
        print(f"   📦 Батч {batch_num + 1}/{total_batches}: записи {start_idx}-{end_idx}")
        
        points = []
        for idx in range(start_idx, end_idx):
            row = df.iloc[idx]
            
            # Парсим данные вакансии
            parsed = parse_vacancy_data(row)
            
            # Генерируем ID точки
            hh_id = parsed["hh_id"]
            if not hh_id:
                print(f"⚠️  Пропускаем запись без hh_id на индексе {idx}")
                continue
            
            # Создаем уникальный ID на основе hh_id
            point_id = str(uuid5(NAMESPACE_URL, hh_id))
            
            # Получаем эмбеддинг
            vector = embeddings[idx].tolist()
            
            # Создаем точку
            point = PointStruct(
                id=point_id,
                vector={"tasks": vector},
                payload=parsed
            )
            points.append(point)
        
        if not points:
            print(f"⚠️  Батч {batch_num + 1} пуст, пропускаем")
            continue
        
        try:
            # Загружаем батч
            operation_info = client.upsert(
                collection_name=collection_name,
                points=points
            )
            successful_uploads += len(points)
            print(f"   ✅ Загружено {len(points)} точек (статус: {operation_info.status})")
            
        except Exception as e:
            print(f"   ❌ Ошибка загрузки батча {batch_num + 1}: {e}")
            continue
    
    print(f"✅ Загрузка завершена: {successful_uploads}/{len(df)} записей")
    
    # Проверяем итоговое количество
    try:
        collection_info = client.get_collection(collection_name)
        points_count = collection_info.points_count
        print(f"📊 Записей в коллекции: {points_count}")
    except Exception as e:
        print(f"⚠️  Не удалось получить информацию о коллекции: {e}")

async def test_search(client: QdrantClient, collection_name: str, test_embedding: np.ndarray):
    """Тестирует поиск в созданной коллекции."""
    print(f"🔍 Тестируем поиск в коллекции '{collection_name}'...")
    
    try:
        # Используем первый эмбеддинг для тестового поиска
        query_vector = test_embedding[0].tolist()
        
        # Выполняем поиск
        search_result = client.search(
            collection_name=collection_name,
            query_vector=("tasks", query_vector),
            limit=3,
            with_payload=True
        )
        
        print(f"✅ Найдено {len(search_result)} результатов:")
        for i, hit in enumerate(search_result, 1):
            payload = hit.payload
            print(f"   {i}. {payload.get('title', 'Без названия')} ({payload.get('company', 'Неизвестная компания')})")
            print(f"      Скор: {hit.score:.3f}, HH ID: {payload.get('hh_id', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования поиска: {e}")
        return False

async def main():
    """Основная функция для загрузки в Qdrant."""
    print("🚀 ЗАГРУЗКА ЭМБЕДДИНГОВ В QDRANT")
    print("=" * 50)
    
    # Проверяем наличие входного файла
    if not Path(INPUT_FILE).exists():
        print(f"❌ Файл {INPUT_FILE} не найден!")
        print("💡 Сначала запустите: python scripts/generate_embeddings.py")
        return
    
    # Загружаем подготовленные данные
    print(f"📂 Загружаем данные из {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "rb") as f:
            data = pickle.load(f)
        
        df = data['dataframe']
        embeddings = data['embeddings']
        metadata = data['metadata']
        
        print(f"✅ Загружено:")
        print(f"   📊 Записей: {len(df)}")
        print(f"   🤖 Эмбеддингов: {embeddings.shape}")
        print(f"   📅 Создано: {metadata['created_at']}")
        print(f"   🔧 Модель: {metadata['model']}")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        return
    
    # Проверяем соответствие размерностей
    if len(df) != len(embeddings):
        print(f"❌ Размерности не совпадают: df={len(df)}, embeddings={len(embeddings)}")
        return
    
    # Подключаемся к Qdrant
    print(f"🔗 Подключаемся к Qdrant: {QDRANT_URL}")
    try:
        qdrant_client = QdrantClient(url=QDRANT_URL)
        
        # Проверяем подключение
        collections = qdrant_client.get_collections()
        print(f"✅ Подключение к Qdrant установлено")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Qdrant: {e}")
        print("💡 Убедитесь, что Qdrant запущен: docker-compose up -d")
        return
    
    # Настраиваем коллекцию
    try:
        vector_dim = embeddings.shape[1]
        await setup_qdrant_collection(qdrant_client, COLLECTION_NAME, vector_dim)
    except Exception as e:
        print(f"❌ Ошибка настройки коллекции: {e}")
        return
    
    # Загружаем данные
    try:
        await upload_to_qdrant(qdrant_client, COLLECTION_NAME, df, embeddings)
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        return
    
    # Тестируем поиск
    test_success = await test_search(qdrant_client, COLLECTION_NAME, embeddings)
    
    # Итоговая статистика
    print(f"\n🎉 ЗАГРУЗКА ЗАВЕРШЕНА!")
    print(f"   📊 Обработано записей: {len(df):,}")
    print(f"   🤖 Загружено эмбеддингов: {len(embeddings):,}")
    print(f"   🗄️ Коллекция Qdrant: {COLLECTION_NAME}")
    print(f"   🔍 Тест поиска: {'✅ Прошел' if test_success else '❌ Не прошел'}")
    print(f"   🌐 Qdrant Dashboard: {QDRANT_URL}/dashboard")

if __name__ == "__main__":
    asyncio.run(main())