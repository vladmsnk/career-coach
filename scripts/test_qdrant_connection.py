#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к Qdrant
Использование: python scripts/test_qdrant_connection.py
"""
import asyncio
import sys
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import VectorParams, Distance, PointStruct
    import numpy as np
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установите зависимости: pip install qdrant-client numpy")
    sys.exit(1)

QDRANT_URL = "http://localhost:6333"
TEST_COLLECTION = "test_connection"

def test_qdrant_connection():
    """Тестирует подключение к Qdrant и основные операции."""
    print("🧪 Тестирование подключения к Qdrant")
    print("=" * 50)
    
    # 1. Подключение
    print(f"🔌 Подключение к {QDRANT_URL}...")
    try:
        client = QdrantClient(url=QDRANT_URL)
        print("✅ Подключение успешно")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("   Убедитесь что Qdrant запущен: docker-compose up -d qdrant")
        return False
    
    # 2. Получение информации
    try:
        collections = client.get_collections()
        print(f"✅ Найдено коллекций: {len(collections.collections)}")
        
        if collections.collections:
            print("   Существующие коллекции:")
            for coll in collections.collections:
                try:
                    count = client.count(coll.name).count
                    print(f"     • {coll.name}: {count:,} точек")
                except:
                    print(f"     • {coll.name}: (не удалось получить количество)")
    except Exception as e:
        print(f"❌ Ошибка получения списка коллекций: {e}")
        return False
    
    # 3. Создание тестовой коллекции
    print(f"\n🧪 Создание тестовой коллекции '{TEST_COLLECTION}'...")
    try:
        # Удаляем если существует
        try:
            client.delete_collection(TEST_COLLECTION)
            print("   Старая тестовая коллекция удалена")
        except:
            pass
        
        # Создаем новую
        client.create_collection(
            collection_name=TEST_COLLECTION,
            vectors_config={
                "default": VectorParams(size=128, distance=Distance.COSINE)
            }
        )
        print("✅ Тестовая коллекция создана")
    except Exception as e:
        print(f"❌ Ошибка создания коллекции: {e}")
        return False
    
    # 4. Добавление тестовых данных
    print("\n📤 Добавление тестовых точек...")
    try:
        test_points = [
            PointStruct(
                id=i,
                vector={"default": np.random.random(128).tolist()},
                payload={
                    "title": f"Test Vacancy {i}",
                    "company": f"Company {i}",
                    "category": "Тестировщик" if i % 2 == 0 else "Разработчик"
                }
            )
            for i in range(1, 11)  # 10 тестовых точек
        ]
        
        result = client.upsert(
            collection_name=TEST_COLLECTION,
            points=test_points
        )
        print(f"✅ Добавлено {len(test_points)} тестовых точек")
        
        # Проверяем количество
        count = client.count(TEST_COLLECTION).count
        print(f"✅ Подтвержено в коллекции: {count} точек")
    except Exception as e:
        print(f"❌ Ошибка добавления данных: {e}")
        return False
    
    # 5. Тестирование поиска
    print("\n🔍 Тестирование векторного поиска...")
    try:
        query_vector = np.random.random(128).tolist()
        results = client.search(
            collection_name=TEST_COLLECTION,
            query_vector=("default", query_vector),
            limit=3,
            with_payload=True
        )
        
        print(f"✅ Найдено {len(results)} результатов:")
        for i, result in enumerate(results, 1):
            payload = result.payload or {}
            print(f"   {i}. {payload.get('title')} | Score: {result.score:.3f}")
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return False
    
    # 6. Тестирование фильтрации
    print("\n🔎 Тестирование поиска с фильтрами...")
    try:
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        filtered_results = client.search(
            collection_name=TEST_COLLECTION,
            query_vector=("default", query_vector),
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="category", 
                        match=MatchValue(value="Разработчик")
                    )
                ]
            ),
            limit=5,
            with_payload=True
        )
        
        print(f"✅ С фильтром 'category=Разработчик' найдено: {len(filtered_results)} результатов")
        for i, result in enumerate(filtered_results, 1):
            payload = result.payload or {}
            print(f"   {i}. {payload.get('title')} | {payload.get('category')} | Score: {result.score:.3f}")
    except Exception as e:
        print(f"❌ Ошибка фильтрованного поиска: {e}")
        return False
    
    # 7. Очистка
    print(f"\n🧹 Удаление тестовой коллекции...")
    try:
        client.delete_collection(TEST_COLLECTION)
        print("✅ Тестовая коллекция удалена")
    except Exception as e:
        print(f"⚠️ Не удалось удалить тестовую коллекцию: {e}")
    
    # 8. Финальная проверка основной коллекции
    if "vacancies_tasks" in [coll.name for coll in collections.collections]:
        try:
            main_count = client.count("vacancies_tasks").count
            print(f"\n📊 Основная коллекция 'vacancies_tasks': {main_count:,} вакансий")
        except:
            print(f"\n⚠️ Основная коллекция 'vacancies_tasks' существует, но не удалось получить количество")
    
    print(f"\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print(f"🌐 Qdrant Dashboard: http://localhost:6333/dashboard")
    return True

if __name__ == "__main__":
    success = test_qdrant_connection()
    sys.exit(0 if success else 1)
