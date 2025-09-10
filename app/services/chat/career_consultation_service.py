"""
Сервис карьерной консультации с использованием ChatGPT
"""
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type
from openai import APIError, RateLimitError, APITimeoutError

from app.core.settings import settings
from app.services.vacancies.vacancy_service import VacancyData

logger = logging.getLogger(__name__)

class CareerConsultationService:
    """Сервис для получения карьерной консультации от ChatGPT"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API ключ не найден в настройках")
        self.client = AsyncOpenAI(api_key=api_key)
    
    @retry(
        wait=wait_exponential_jitter(initial=2, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError))
    )
    async def get_career_consultation(
        self, 
        user_data: Dict,
        vacancies: List[VacancyData]
    ) -> str:
        """
        Получает карьерную консультацию на основе данных пользователя и подходящих вакансий
        
        Args:
            user_data: Собранные данные пользователя из чата
            vacancies: Список подходящих вакансий
            
        Returns:
            Текст карьерной консультации
        """
        try:
            # Формируем контекст для ChatGPT
            user_context = self._build_user_context(user_data)
            vacancies_context = self._build_vacancies_context(vacancies)
            
            prompt = self._build_consultation_prompt(user_context, vacancies_context)
            
            logger.info(f"🤖 Отправляем запрос к ChatGPT ({self.model})")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты опытный карьерный консультант в IT-сфере. Твоя задача - предоставить персонализированную карьерную консультацию на основе опыта пользователя и анализа подходящих ему вакансий."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            consultation = response.choices[0].message.content.strip()
            
            logger.info(f"✅ Получена карьерная консультация (длина: {len(consultation)} символов)")
            
            return consultation
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения карьерной консультации: {e}")
            return self._get_fallback_consultation()
    
    def _build_user_context(self, user_data: Dict) -> str:
        """Формирует контекст пользователя для ChatGPT"""
        context_parts = []
        
        # Текущая позиция и опыт
        current_position = user_data.get('current_position', 'Не указано')
        years_in_position = user_data.get('years_in_position', 'Не указано')
        context_parts.append(f"Текущая должность: {current_position} (стаж: {years_in_position} лет)")
        
        # Ключевые проекты
        key_projects = user_data.get('key_projects', '')
        if key_projects:
            context_parts.append(f"Ключевые проекты: {key_projects}")
        
        # Цели
        target_specialization = user_data.get('target_specialization', 'Не указано')
        preferred_activities = user_data.get('preferred_activities', 'Не указано')
        position_ambitions = user_data.get('position_ambitions', 'Не указано')
        salary_expectations = user_data.get('salary_expectations', 'Не указано')
        
        context_parts.append(f"Желаемая специализация: {target_specialization}")
        context_parts.append(f"Интересные активности: {preferred_activities}")
        context_parts.append(f"Карьерные амбиции (3-5 лет): {position_ambitions}")
        context_parts.append(f"Ожидания по зарплате: {salary_expectations} руб/мес")
        
        # Навыки
        current_skills = user_data.get('current_skills', 'Не указано')
        tools_experience = user_data.get('tools_experience', 'Не указано')
        soft_skills = user_data.get('soft_skills', 'Не указано')
        
        context_parts.append(f"Технические навыки: {current_skills}")
        context_parts.append(f"Инструменты и технологии: {tools_experience}")
        context_parts.append(f"Soft skills: {soft_skills}")
        
        # Образование и планы обучения
        education = user_data.get('education', '')
        learning_goals = user_data.get('learning_goals', '')
        
        if education:
            context_parts.append(f"Образование: {education}")
        if learning_goals:
            context_parts.append(f"Планы обучения: {learning_goals}")
        
        return "\n".join(context_parts)
    
    def _build_vacancies_context(self, vacancies: List[VacancyData]) -> str:
        """Формирует контекст вакансий для ChatGPT"""
        if not vacancies:
            return "Подходящие вакансии не найдены."
        
        vacancies_parts = []
        
        for i, vacancy in enumerate(vacancies, 1):
            vacancy_info = [
                f"Вакансия {i}:",
                f"  Название: {vacancy.title}",
                f"  Компания: {vacancy.company}",
                f"  Описание: {vacancy.job_description[:500]}{'...' if len(vacancy.job_description) > 500 else ''}"
            ]
            vacancies_parts.append("\n".join(vacancy_info))
        
        return "\n\n".join(vacancies_parts)
    
    def _build_consultation_prompt(self, user_context: str, vacancies_context: str) -> str:
        """Формирует prompt для ChatGPT"""
        return f"""
Пожалуйста, проведи карьерную консультацию для IT-специалиста на основе следующих данных:

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
{user_context}

ПОДХОДЯЩИЕ ВАКАНСИИ:
{vacancies_context}

ЗАДАНИЕ:
На основе анализа профиля пользователя и подходящих вакансий предоставь персонализированную карьерную консультацию, которая включает:

1. **Оценку текущего профиля**: Кратко оцени сильные стороны и соответствие целям
2. **Анализ возможностей**: Как подходящие вакансии соотносятся с целями пользователя
3. **Точки роста**: Конкретные области для развития (максимум 4-5 пунктов)
4. **Рекомендации по обучению**: Конкретные технологии, инструменты или навыки для изучения
5. **Практические шаги**: 2-3 конкретных действия для достижения карьерных целей

Ответ должен быть структурированным, практичным и не превышать 1200 символов. Используй дружелюбный, но профессиональный тон.
"""
    
    def _get_fallback_consultation(self) -> str:
        """Возвращает консультацию по умолчанию в случае ошибки"""
        return """
🎯 **Карьерная консультация**

К сожалению, не удалось получить персонализированную консультацию от AI-советника. 

**Общие рекомендации:**
• Продолжайте развивать технические навыки в выбранном направлении
• Работайте над soft skills - они критически важны для карьерного роста
• Изучайте новые технологии и инструменты в своей области
• Участвуйте в проектах, которые расширяют ваш опыт
• Рассмотрите возможности менторства или обучения других

Обратитесь к карьерному консультанту для более детального анализа вашего профессионального пути.
"""
