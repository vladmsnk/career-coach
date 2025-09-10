"""
Основной сервис для получения рекомендаций вакансий.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from dataclasses import dataclass

from app.services.recommendations.embeddings_service import EmbeddingsService
from app.services.recommendations.qdrant_service import QdrantService, VacancyRecommendation
from app.services.vacancies.vacancy_service import vacancy_service
from app.services.chat.career_consultation_service import CareerConsultationService
from app.domain.chat.repositories import ChatRepository


@dataclass
class CareerRecommendationResult:
    """Результат карьерной рекомендации, включающий консультацию и вакансии"""
    career_consultation: str
    vacancy_recommendations: List[VacancyRecommendation]


class RecommendationService:
    """Сервис для получения персонализированных рекомендаций вакансий."""
    
    def __init__(self, chat_repo: ChatRepository):
        self.chat_repo = chat_repo
        self.embeddings_service = EmbeddingsService()
        self.qdrant_service = QdrantService()
        self.career_consultation_service = CareerConsultationService()
        
        # Инициализируем vacancy_service при первом использовании
        if not vacancy_service.is_loaded():
            vacancy_service.load_vacancies()
    
    async def get_recommendations_for_session(self, session_id: UUID) -> List[VacancyRecommendation]:
        """
        Получает рекомендации вакансий для завершенной чат-сессии.
        
        Args:
            session_id: ID чат-сессии
            
        Returns:
            Список рекомендаций или пустой список при ошибке
        """
        try:
            # 1. Получаем данные сессии
            session_data = await self._get_session_data(session_id)
            if not session_data:
                print(f"⚠️ Данные сессии {session_id} не найдены")
                return []
            
            # 2. Извлекаем необходимые поля
            target_area = session_data.get('target_area')
            preferred_activities = session_data.get('preferred_activities')
            
            if not target_area:
                print("⚠️ target_area не найден в данных сессии")
                return []
            
            if not preferred_activities:
                print("⚠️ preferred_activities не найден в данных сессии")
                return []
            
            print(f"📊 Данные для рекомендаций:")
            print(f"   Целевая область: {target_area}")
            print(f"   Предпочтительные активности: {preferred_activities}")
            
            # 3. Создаем эмбеддинг для preferred_activities
            embedding = await self.embeddings_service.create_embedding(preferred_activities)
            if embedding is None:
                print("❌ Не удалось создать эмбеддинг для preferred_activities")
                return []
            
            print(f"✅ Эмбеддинг создан: размерность {embedding.shape}")
            
            # 4. Выполняем гибридный поиск в Qdrant
            recommendations = await self.qdrant_service.search_similar_vacancies(
                embedding=embedding,
                target_specialization=target_area,
                limit=5
            )
            
            print(f"🎯 Найдено {len(recommendations)} рекомендаций")
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Ошибка получения рекомендаций: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_career_consultation_and_recommendations(self, session_id: UUID) -> Optional[CareerRecommendationResult]:
        """
        Получает полную карьерную консультацию и рекомендации вакансий.
        
        Args:
            session_id: ID чат-сессии
            
        Returns:
            CareerRecommendationResult с консультацией и рекомендациями или None при ошибке
        """
        try:
            # 1. Получаем данные сессии
            session_data = await self._get_session_data(session_id)
            if not session_data:
                print(f"⚠️ Данные сессии {session_id} не найдены")
                return None
            
            # 2. Получаем рекомендации вакансий
            print("🔍 Получение рекомендаций вакансий...")
            vacancy_recommendations = await self.get_recommendations_for_session(session_id)
            
            if not vacancy_recommendations:
                print("⚠️ Рекомендации вакансий не найдены")
                return None
            
            # 3. Получаем подробные данные вакансий из CSV
            hh_ids = [rec.hh_id for rec in vacancy_recommendations]
            print(f"📋 Загрузка деталей для вакансий: {hh_ids}")
            
            vacancy_details = vacancy_service.get_vacancies_by_ids(hh_ids)
            print(f"✅ Загружено {len(vacancy_details)} детальных описаний вакансий")
            
            # 4. Получаем карьерную консультацию
            print("🤖 Получение карьерной консультации от ChatGPT...")
            career_consultation = await self.career_consultation_service.get_career_consultation(
                user_data=session_data,
                vacancies=vacancy_details
            )
            
            print(f"✅ Карьерная консультация получена (длина: {len(career_consultation)} символов)")
            
            return CareerRecommendationResult(
                career_consultation=career_consultation,
                vacancy_recommendations=vacancy_recommendations
            )
            
        except Exception as e:
            print(f"❌ Ошибка получения карьерной консультации: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _get_session_data(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Получает collected_data из чат-сессии."""
        try:
            # Получаем сессию через репозиторий
            session = await self.chat_repo.get_session(session_id)
            if not session:
                return None
            
            # Извлекаем collected_data (это должен быть dict)
            collected_data = getattr(session, 'collected_data', {})
            if not isinstance(collected_data, dict):
                print(f"⚠️ collected_data не является словарем: {type(collected_data)}")
                return {}
            
            return collected_data
            
        except Exception as e:
            print(f"❌ Ошибка получения данных сессии: {e}")
            return None
    
    async def test_services(self) -> bool:
        """Тестирует доступность всех сервисов."""
        print("🧪 Тестирование сервисов рекомендаций...")
        
        # Тест Qdrant подключения
        if not self.qdrant_service.test_connection():
            return False
        
        if not self.qdrant_service.check_collection():
            return False
        
        # Тест создания эмбеддинга
        test_text = "Разработка веб-приложений на Python"
        embedding = await self.embeddings_service.create_embedding(test_text)
        if embedding is None:
            print("❌ Не удалось создать тестовый эмбеддинг")
            return False
        
        print(f"✅ Тестовый эмбеддинг создан: {embedding.shape}")
        
        # Тест поиска
        test_recommendations = await self.qdrant_service.search_test_query(test_text, embedding)
        if not test_recommendations:
            print("⚠️ Тестовый поиск не вернул результатов")
        else:
            print(f"✅ Тестовый поиск: {len(test_recommendations)} результатов")
        
        print("🎉 Все сервисы работают!")
        return True
