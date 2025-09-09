"""
Сервис для работы с Qdrant векторной базой данных.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue


@dataclass
class VacancyRecommendation:
    """Модель рекомендации вакансии."""
    hh_id: str
    title: str
    company: str
    score: float
    url: Optional[str] = None
    category: Optional[str] = None


class QdrantService:
    """Сервис для поиска в Qdrant коллекции."""
    
    def __init__(self, url: str = "http://localhost:6333", collection_name: str = "vacancies_tasks"):
        self.url = url
        self.collection_name = collection_name
        self.client = QdrantClient(url=url)
    
    def test_connection(self) -> bool:
        """Проверяет подключение к Qdrant."""
        try:
            collections = self.client.get_collections()
            print(f"✅ Qdrant подключен. Коллекций: {len(collections.collections)}")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к Qdrant: {e}")
            return False
    
    def check_collection(self) -> bool:
        """Проверяет существование коллекции."""
        try:
            info = self.client.get_collection(self.collection_name)
            count = self.client.count(self.collection_name).count
            print(f"✅ Коллекция {self.collection_name} найдена. Векторов: {count}")
            return True
        except Exception as e:
            print(f"❌ Коллекция {self.collection_name} не найдена: {e}")
            return False
    
    # Маппинг специализаций из чата к категориям в Qdrant
    SPECIALIZATION_MAPPING = {
        "Бэкенд-разработчик": ["Бэкенд-разработчик"],
        "Фронтенд-разработчик": ["Фронтенд-разработчик"],
        "Фулстек-разработчик": ["Бэкенд-разработчик", "Фронтенд-разработчик", "Фулстек-разработчик"],
        "ML-разработчик": ["ML-разработчик", "Machine Learning Engineer"],
        "Machine Learning Engineer": ["Machine Learning Engineer", "ML-разработчик"],
        "Data Engineer": ["Data Engineer", "Инженер данных"],
        "Data Scientist": ["Data Scientist"],
        "AI Engineer": ["AI Engineer", "ML-разработчик"],
        "DevOps-инженер": ["DevOps-инженер"],
        "iOS-разработчик": ["iOS-разработчик"],
        "Android-разработчик": ["Android-разработчик"],
        "Разработчик мобильных приложений": ["iOS-разработчик", "Android-разработчик", "Разработчик мобильных приложений"],
        "Тестировщик": ["Тестировщик", "QA Engineer"],
        "QA Engineer": ["QA Engineer", "Тестировщик"],
        "Test Automation Engineer": ["Test Automation Engineer", "Тестировщик"],
        "Системный администратор": ["Системный администратор"],
        "Технический лидер": ["Tech Lead", "Team Lead", "Технический лидер"],
        "Tech Lead": ["Tech Lead", "Team Lead"],
        "Team Lead": ["Team Lead", "Tech Lead"],
        "Архитектор ПО": ["Solution Architect", "Enterprise Architect", "Архитектор ПО"],
        "Solution Architect": ["Solution Architect", "Архитектор ПО"],
        "Enterprise Architect": ["Enterprise Architect", "Архитектор ПО"],
        "Продакт-менеджер": ["Продакт-менеджер"],
        "Технический менеджер": ["Engineering Manager", "Технический менеджер"],
        "Engineering Manager": ["Engineering Manager", "Технический менеджер"],
        "Системный аналитик": ["Системный аналитик"],
        "Бизнес-аналитик": ["Бизнес-аналитик"],
        "UX/UI дизайнер": ["UX/UI дизайнер", "Product Designer"],
        "Product Designer": ["Product Designer", "UX/UI дизайнер"]
    }
    
    def _get_filter_categories(self, target_specialization: str) -> List[str]:
        """Получает список категорий для фильтрации по специализации."""
        return self.SPECIALIZATION_MAPPING.get(
            target_specialization, 
            [target_specialization]  # Fallback к исходному значению
        )
    
    async def search_similar_vacancies(
        self, 
        embedding: np.ndarray, 
        target_specialization: str,
        limit: int = 5
    ) -> List[VacancyRecommendation]:
        """
        Выполняет гибридный поиск: фильтр по категории + векторный поиск по эмбеддингу.
        
        Args:
            embedding: Нормализованный вектор эмбеддинга
            target_specialization: Целевая специализация
            limit: Количество результатов
            
        Returns:
            Список рекомендаций вакансий
        """
        try:
            # Получаем категории для фильтрации
            filter_categories = self._get_filter_categories(target_specialization)
            
            print(f"🔍 Поиск для специализации: {target_specialization}")
            print(f"📋 Фильтр категорий: {filter_categories}")
            
            # Создаем фильтр по категориям
            filter_condition = Filter(
                should=[
                    FieldCondition(
                        key="raw_category",
                        match=MatchValue(value=category)
                    )
                    for category in filter_categories
                ]
            )
            
            # Выполняем поиск
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=("tasks", embedding.tolist()),
                query_filter=filter_condition,
                limit=limit,
                with_payload=True
            )
            
            # Преобразуем результаты
            recommendations = []
            for result in search_results:
                payload = result.payload or {}
                
                hh_id = payload.get('hh_id', 'unknown')
                title = payload.get('title', 'Без названия')
                company = payload.get('company', 'Без компании')
                url = payload.get('url')
                category = payload.get('raw_category', 'Без категории')
                
                recommendation = VacancyRecommendation(
                    hh_id=str(hh_id),
                    title=title,
                    company=company,
                    score=result.score,
                    url=url,
                    category=category
                )
                recommendations.append(recommendation)
            
            print(f"✅ Найдено {len(recommendations)} рекомендаций")
            return recommendations
            
        except Exception as e:
            print(f"❌ Ошибка поиска в Qdrant: {e}")
            return []
    
    async def search_test_query(self, query: str, embedding: np.ndarray) -> List[VacancyRecommendation]:
        """Тестовый поиск без фильтров."""
        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=("tasks", embedding.tolist()),
                limit=3,
                with_payload=True
            )
            
            recommendations = []
            for result in search_results:
                payload = result.payload or {}
                recommendation = VacancyRecommendation(
                    hh_id=str(payload.get('hh_id', 'unknown')),
                    title=payload.get('title', 'Без названия'),
                    company=payload.get('company', 'Без компании'),
                    score=result.score,
                    url=payload.get('url'),
                    category=payload.get('raw_category', 'Без категории')
                )
                recommendations.append(recommendation)
            
            return recommendations
        except Exception as e:
            print(f"❌ Ошибка тестового поиска: {e}")
            return []
