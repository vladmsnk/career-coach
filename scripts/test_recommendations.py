#!/usr/bin/env python3
"""
Изолированный тест системы рекомендаций вакансий.
Проверяет все компоненты без интеграции с основным чатом.
"""
import asyncio
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.recommendations.embeddings_service import EmbeddingsService
from app.services.recommendations.qdrant_service import QdrantService, VacancyRecommendation


async def test_embeddings_service():
    """Тестирует сервис создания эмбеддингов."""
    print("\n" + "="*70)
    print("🧪 ТЕСТИРОВАНИЕ СЕРВИСА ЭМБЕДДИНГОВ")
    print("="*70)
    
    service = EmbeddingsService()
    
    # Тестовые данные - как в реальном чате
    test_activities = [
        "Разработка ПО",
        "Разработка ПО, Системный анализ", 
        "Машинное обучение / AI, Работа с данными / Data Science",
        "Инфраструктура и DevOps, Администрирование систем"
    ]
    
    for i, activity in enumerate(test_activities, 1):
        print(f"\n📝 Тест {i}: {activity}")
        
        # Подсчет токенов
        token_count = service.count_tokens(activity)
        print(f"   Токенов: {token_count}")
        
        # Создание эмбеддинга
        embedding = await service.create_embedding(activity)
        
        if embedding is not None:
            print(f"   ✅ Эмбеддинг создан: {embedding.shape}")
            print(f"   📊 Min: {embedding.min():.4f}, Max: {embedding.max():.4f}")
        else:
            print(f"   ❌ Ошибка создания эмбеддинга")
    
    return True


async def test_qdrant_service():
    """Тестирует сервис Qdrant."""
    print("\n" + "="*70)
    print("🧪 ТЕСТИРОВАНИЕ СЕРВИСА QDRANT")
    print("="*70)
    
    service = QdrantService()
    
    # Проверка подключения
    if not service.test_connection():
        print("❌ Не удалось подключиться к Qdrant")
        return False
    
    if not service.check_collection():
        print("❌ Коллекция vacancies_tasks не найдена")
        return False
    
    # Тестовые поиски
    embeddings_service = EmbeddingsService()
    
    test_cases = [
        {
            "specialization": "Бэкенд-разработчик",
            "activities": "Разработка ПО, Системный анализ"
        },
        {
            "specialization": "Фронтенд-разработчик", 
            "activities": "Разработка ПО, UX/UI дизайн"
        },
        {
            "specialization": "ML-разработчик",
            "activities": "Машинное обучение / AI, Работа с данными / Data Science"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔍 Тест поиска {i}:")
        print(f"   Специализация: {case['specialization']}")
        print(f"   Активности: {case['activities']}")
        
        # Создаем эмбеддинг
        embedding = await embeddings_service.create_embedding(case['activities'])
        if embedding is None:
            print("   ❌ Не удалось создать эмбеддинг")
            continue
        
        # Выполняем поиск
        recommendations = await service.search_similar_vacancies(
            embedding=embedding,
            target_specialization=case['specialization'],
            limit=5
        )
        
        print(f"   📋 Найдено рекомендаций: {len(recommendations)}")
        
        # Показываем результаты
        for j, rec in enumerate(recommendations[:3], 1):  # Показываем топ-3
            print(f"      {j}. {rec.title}")
            print(f"         🏢 {rec.company}")
            print(f"         🆔 HH ID: {rec.hh_id}")
            print(f"         📊 Score: {rec.score:.3f}")
            print(f"         🏷️ Категория: {rec.category}")
    
    return True


async def test_full_pipeline():
    """Тестирует полный pipeline рекомендаций."""
    print("\n" + "="*70)
    print("🧪 ТЕСТИРОВАНИЕ ПОЛНОГО PIPELINE")
    print("="*70)
    
    # Симулируем данные из реальной чат-сессии
    mock_session_data = {
        "current_position": "Бэкенд-разработчик",
        "years_in_position": "3",
        "key_projects": "Разработал REST API на FastAPI",
        "target_specialization": "Фулстек-разработчик",
        "preferred_activities": "Разработка ПО, Системный анализ",
        "position_ambitions": "Senior Developer",
        "salary_expectations": "180000",
        "current_skills": "Программирование",
        "tools_experience": "Python",
        "soft_skills": "Коммуникация",
        "education": "ВУЗ",
        "learning_goals": "React, TypeScript"
    }
    
    print(f"📊 Тестовые данные сессии:")
    for key, value in mock_session_data.items():
        print(f"   {key}: {value}")
    
    # Извлекаем данные для рекомендаций
    target_specialization = mock_session_data['target_specialization']
    preferred_activities = mock_session_data['preferred_activities']
    
    print(f"\n🎯 Параметры для поиска:")
    print(f"   Целевая специализация: {target_specialization}")
    print(f"   Предпочитаемые активности: {preferred_activities}")
    
    # Создаем сервисы
    embeddings_service = EmbeddingsService()
    qdrant_service = QdrantService()
    
    # Создаем эмбеддинг
    print(f"\n🤖 Создание эмбеддинга...")
    embedding = await embeddings_service.create_embedding(preferred_activities)
    if embedding is None:
        print("❌ Не удалось создать эмбеддинг")
        return False
    
    print(f"✅ Эмбеддинг создан: {embedding.shape}")
    
    # Выполняем поиск
    print(f"\n🔍 Поиск рекомендаций...")
    recommendations = await qdrant_service.search_similar_vacancies(
        embedding=embedding,
        target_specialization=target_specialization,
        limit=5
    )
    
    if not recommendations:
        print("❌ Рекомендации не найдены")
        return False
    
    # Форматируем результаты как для чата
    print(f"\n🎯 РЕКОМЕНДАЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЯ:")
    print(f"Найдено {len(recommendations)} подходящих вакансий:")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec.title}")
        print(f"   🏢 Компания: {rec.company}")
        print(f"   🆔 HH ID: {rec.hh_id}")
        print(f"   📊 Соответствие: {rec.score:.1%}")
        print(f"   🏷️ Категория: {rec.category}")
        if rec.url:
            print(f"   🔗 Ссылка: {rec.url}")
    
    # Извлекаем только hh_id для отправки в чат
    hh_ids = [rec.hh_id for rec in recommendations]
    print(f"\n📋 HH IDs для чата: {hh_ids}")
    
    return True


async def main():
    """Основная функция тестирования."""
    print("🚀 ЗАПУСК ТЕСТОВ СИСТЕМЫ РЕКОМЕНДАЦИЙ")
    print("="*70)
    
    # Проверка окружения
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Не установлен OPENAI_API_KEY")
        print("   Установите: export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Последовательное тестирование компонентов
        success = True
        
        success &= await test_embeddings_service()
        success &= await test_qdrant_service() 
        success &= await test_full_pipeline()
        
        if success:
            print("\n" + "="*70)
            print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            print("✅ Система рекомендаций готова к интеграции")
            print("="*70)
        else:
            print("\n" + "="*70)
            print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
            print("🔧 Исправьте ошибки перед интеграцией")
            print("="*70)
            
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
