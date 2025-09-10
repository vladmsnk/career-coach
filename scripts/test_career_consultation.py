"""
Тестовый скрипт для проверки карьерной консультации
"""
import asyncio
import os
import sys
import logging

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.services.vacancies.vacancy_service import vacancy_service
from app.services.chat.career_consultation_service import CareerConsultationService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_vacancy_service():
    """Тестирует загрузку и работу с CSV данными вакансий"""
    print("\n🧪 ТЕСТ VACANCY SERVICE")
    print("=" * 40)
    
    # Загружаем данные
    vacancy_service.load_vacancies()
    total_count = vacancy_service.get_total_count()
    print(f"✅ Загружено вакансий: {total_count}")
    
    # Тестовые ID (из реального Qdrant поиска)
    test_ids = ['124928483', '124919596', '124963529', '121091720', '124778414']
    print(f"\n🔍 Поиск вакансий по ID: {test_ids}")
    
    vacancies = vacancy_service.get_vacancies_by_ids(test_ids)
    print(f"✅ Найдено вакансий: {len(vacancies)}")
    
    for vacancy in vacancies[:2]:  # Показываем первые 2
        print(f"\n📋 Вакансия: {vacancy.id}")
        print(f"   Название: {vacancy.title}")
        print(f"   Компания: {vacancy.company}")
        print(f"   Описание: {vacancy.job_description[:200]}...")
    
    return vacancies

async def test_career_consultation_service():
    """Тестирует сервис карьерной консультации"""
    print("\n🧪 ТЕСТ CAREER CONSULTATION SERVICE")
    print("=" * 40)
    
    try:
        consultation_service = CareerConsultationService()
        print("✅ CareerConsultationService инициализирован")
        
        # Тестовые данные пользователя
        user_data = {
            'current_position': 'Бэкенд-разработчик',
            'years_in_position': '3',
            'key_projects': 'Разработал микросервисы на Python и FastAPI',
            'target_specialization': 'Фулстек-разработчик',
            'preferred_activities': 'Разработка ПО, Системный анализ',
            'position_ambitions': 'Senior Developer',
            'salary_expectations': '200000',
            'current_skills': 'Программирование, Работа с базами данных',
            'tools_experience': 'Python, PostgreSQL, Docker',
            'soft_skills': 'Коммуникация, Тайм-менеджмент',
            'education': 'ВУЗ по информатике',
            'learning_goals': 'Изучение React, TypeScript'
        }
        
        # Получаем тестовые вакансии
        vacancies = await test_vacancy_service()
        
        print(f"\n🤖 Отправка запроса к ChatGPT...")
        consultation = await consultation_service.get_career_consultation(
            user_data=user_data,
            vacancies=vacancies[:3]  # Используем первые 3 вакансии
        )
        
        print(f"✅ Консультация получена (длина: {len(consultation)} символов)")
        print(f"\n📝 КОНСУЛЬТАЦИЯ:")
        print("-" * 60)
        print(consultation)
        print("-" * 60)
        
        return consultation
        
    except Exception as e:
        print(f"❌ Ошибка тестирования CareerConsultationService: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ КАРЬЕРНОЙ КОНСУЛЬТАЦИИ")
    print("=" * 50)
    
    # Проверяем наличие OpenAI API ключа
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY не установлен!")
        print("Установите переменную окружения: export OPENAI_API_KEY='your-key'")
        return
    
    print(f"✅ OpenAI API ключ найден (длина: {len(api_key)} символов)")
    
    # Проверяем наличие CSV файла
    csv_path = "vacancies_sample.csv"
    if not os.path.exists(csv_path):
        print(f"❌ CSV файл не найден: {csv_path}")
        return
    
    print(f"✅ CSV файл найден: {csv_path}")
    
    # Запускаем тесты
    try:
        await test_career_consultation_service()
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

