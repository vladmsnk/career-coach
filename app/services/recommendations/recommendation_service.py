"""
Основной сервис для получения рекомендаций вакансий.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.services.recommendations.embeddings_service import EmbeddingsService
from app.services.recommendations.qdrant_service import QdrantService, VacancyRecommendation
from app.domain.chat.repositories import ChatRepository


class RecommendationService:
    """Сервис для получения персонализированных рекомендаций вакансий."""
    
    def __init__(self, chat_repo: ChatRepository):
        self.chat_repo = chat_repo
        self.embeddings_service = EmbeddingsService()
        self.qdrant_service = QdrantService()
    
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
            target_specialization = session_data.get('target_specialization')
            preferred_activities = session_data.get('preferred_activities')
            
            if not target_specialization:
                print("⚠️ target_specialization не найден в данных сессии")
                return []
            
            if not preferred_activities:
                print("⚠️ preferred_activities не найден в данных сессии")
                return []
            
            print(f"📊 Данные для рекомендаций:")
            print(f"   Специализация: {target_specialization}")
            print(f"   Активности: {preferred_activities}")
            
            # 3. Создаем эмбеддинг для preferred_activities
            embedding = await self.embeddings_service.create_embedding(preferred_activities)
            if embedding is None:
                print("❌ Не удалось создать эмбеддинг для preferred_activities")
                return []
            
            print(f"✅ Эмбеддинг создан: размерность {embedding.shape}")
            
            # 4. Выполняем гибридный поиск в Qdrant
            recommendations = await self.qdrant_service.search_similar_vacancies(
                embedding=embedding,
                target_specialization=target_specialization,
                limit=5
            )
            
            print(f"🎯 Найдено {len(recommendations)} рекомендаций")
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Ошибка получения рекомендаций: {e}")
            import traceback
            traceback.print_exc()
            return []
    
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
