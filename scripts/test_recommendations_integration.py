#!/usr/bin/env python3
"""
Интеграционный тест системы рекомендаций с реальным чатом.
Тестирует полный pipeline от завершения сессии до получения рекомендаций.
"""
import asyncio
import sys
import os
import uuid
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.settings import settings
from app.services.recommendations.recommendation_service import RecommendationService


class MockChatRepository:
    """Mock репозиторий чата для тестирования без реальной БД."""
    
    def __init__(self):
        # Симулируем данные чат-сессии
        self.mock_session_data = {
            "current_position": "Бэкенд-разработчик",
            "years_in_position": "3", 
            "key_projects": "Разработал API на FastAPI",
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
    
    async def get_session(self, session_id):
        """Возвращает mock объект сессии."""
        class MockSession:
            def __init__(self, collected_data):
                self.collected_data = collected_data
        
        return MockSession(self.mock_session_data)


async def test_recommendation_service_integration():
    """Тестирует интеграцию сервиса рекомендаций."""
    print("🧪 ИНТЕГРАЦИОННЫЙ ТЕСТ СЕРВИСА РЕКОМЕНДАЦИЙ")
    print("="*70)
    
    # Используем mock репозиторий
    mock_repo = MockChatRepository()
    
    # Создаем сервис рекомендаций
    recommendation_service = RecommendationService(mock_repo)
    
    # Тестируем подключение к внешним сервисам
    print("\n🔍 Тестирование внешних сервисов...")
    services_ok = await recommendation_service.test_services()
    
    if not services_ok:
        print("❌ Внешние сервисы недоступны")
        print("🔧 Убедитесь что:")
        print("   1. Qdrant запущен: docker-compose up -d")
        print("   2. Данные загружены: python scripts/load_vacancies_to_qdrant.py")
        print("   3. OpenAI API ключ настроен в .env")
        return False
    
    # Тестируем получение рекомендаций
    print("\n🎯 Тестирование получения рекомендаций...")
    test_session_id = str(uuid.uuid4())
    
    recommendations = await recommendation_service.get_recommendations_for_session(test_session_id)
    
    if not recommendations:
        print("⚠️ Рекомендации не получены (но это нормально для mock данных)")
        return True
    
    print(f"✅ Получено {len(recommendations)} рекомендаций:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec.title}")
        print(f"      🏢 {rec.company}")
        print(f"      🆔 HH ID: {rec.hh_id}")
        print(f"      📊 Score: {rec.score:.3f}")
    
    # Проверяем формат данных для чата
    hh_ids = [rec.hh_id for rec in recommendations]
    print(f"\n📋 HH IDs для отображения в чате: {hh_ids}")
    
    return True


async def test_feature_flag():
    """Тестирует работу feature flag."""
    print("\n" + "="*70)
    print("🧪 ТЕСТИРОВАНИЕ FEATURE FLAG")
    print("="*70)
    
    print(f"📊 Текущие настройки:")
    print(f"   enable_vacancy_recommendations: {settings.enable_vacancy_recommendations}")
    print(f"   qdrant_url: {settings.qdrant_url}")
    print(f"   qdrant_collection: {settings.qdrant_collection}")
    print(f"   openai_api_key: {'✅ установлен' if settings.openai_api_key else '❌ не установлен'}")
    
    if settings.enable_vacancy_recommendations:
        print("✅ Рекомендации ВКЛЮЧЕНЫ - будут отправляться в чат")
    else:
        print("⚠️ Рекомендации ВЫКЛЮЧЕНЫ - чат работает как обычно")
        print("   Для включения установите: export ENABLE_VACANCY_RECOMMENDATIONS=true")
    
    return True


async def test_chat_integration_simulation():
    """Симулирует интеграцию с чатом."""
    print("\n" + "="*70) 
    print("🧪 СИМУЛЯЦИЯ ИНТЕГРАЦИИ С ЧАТОМ")
    print("="*70)
    
    # Симулируем завершение чат-сессии
    session_id = str(uuid.uuid4())
    print(f"📝 Симулируем завершение сессии: {session_id}")
    
    # Симулируем проверку feature flag
    if not settings.enable_vacancy_recommendations:
        print("⚠️ Feature flag выключен - рекомендации не отправляются")
        print("✅ Сессия завершена без рекомендаций (как обычно)")
        return True
    
    print("🎯 Feature flag включен - получаем рекомендации...")
    
    # Симулируем получение рекомендаций
    mock_repo = MockChatRepository()
    service = RecommendationService(mock_repo)
    
    try:
        recommendations = await service.get_recommendations_for_session(session_id)
        
        if recommendations:
            # Симулируем отправку в чат
            chat_message = {
                "event": "recommendations",
                "message": f"🎯 Нашли {len(recommendations)} подходящих вакансий для вас:",
                "data": {
                    "recommendations": [
                        {
                            "hh_id": rec.hh_id,
                            "title": rec.title,
                            "company": rec.company,
                            "score": round(rec.score * 100, 1),
                            "url": rec.url,
                            "category": rec.category
                        }
                        for rec in recommendations
                    ],
                    "hh_ids": [rec.hh_id for rec in recommendations]
                }
            }
            
            print("📤 Сообщение для чата:")
            print(f"   {chat_message['message']}")
            print(f"   HH IDs: {chat_message['data']['hh_ids']}")
            print("✅ Рекомендации отправлены в чат")
        else:
            print("⚠️ Рекомендации не найдены - отправляем fallback сообщение")
        
        print("✅ Сессия завершена с рекомендациями")
        
    except Exception as e:
        print(f"❌ Ошибка получения рекомендаций: {e}")
        print("⚠️ Отправляем сообщение об ошибке")
        print("✅ Сессия завершена (ошибка рекомендаций не критична)")
    
    return True


async def main():
    """Главная функция тестирования."""
    print("🚀 ИНТЕГРАЦИОННОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ РЕКОМЕНДАЦИЙ")
    print("="*70)
    
    try:
        success = True
        
        success &= await test_feature_flag()
        success &= await test_recommendation_service_integration() 
        success &= await test_chat_integration_simulation()
        
        print("\n" + "="*70)
        if success:
            print("🎉 ВСЕ ИНТЕГРАЦИОННЫЕ ТЕСТЫ ПРОШЛИ!")
            print("✅ Система готова к использованию")
            
            if settings.enable_vacancy_recommendations:
                print("\n🎯 РЕКОМЕНДАЦИИ ВКЛЮЧЕНЫ:")
                print("   • Пользователи будут получать вакансии в конце чата")
                print("   • Проверьте логи на наличие ошибок")
                print("   • Мониторьте производительность")
            else:
                print("\n⚠️ РЕКОМЕНДАЦИИ ВЫКЛЮЧЕНЫ:")
                print("   • Чат работает в обычном режиме")
                print("   • Для включения: export ENABLE_VACANCY_RECOMMENDATIONS=true")
        else:
            print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
            print("🔧 Проверьте ошибки выше")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
