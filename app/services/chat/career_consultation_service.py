"""
Сервис карьерной консультации с использованием Yandex GPT
"""
import logging
from typing import Dict, List, Optional
from yandex_cloud_ml_sdk import YCloudML
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type

from app.core.settings import settings
from app.services.vacancies.vacancy_service import VacancyData

logger = logging.getLogger(__name__)

class CareerConsultationService:
    """Сервис для получения карьерной консультации от Yandex GPT"""
    
    def __init__(self, model: str = "yandexgpt"):
        self.model = model
        api_key = settings.yandex_gpt_api_key
        folder_id = settings.yandex_gpt_folder_id
        if not api_key:
            raise ValueError("Yandex GPT API ключ не найден в настройках")
        if not folder_id:
            raise ValueError("Yandex GPT folder_id не найден в настройках")
        self.sdk = YCloudML(folder_id=folder_id, auth=api_key)
    
    @retry(
        wait=wait_exponential_jitter(initial=2, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((Exception,))
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
            # Формируем контекст для Yandex GPT
            user_context = self._build_user_context(user_data)
            vacancies_context = self._build_vacancies_context(vacancies)
            
            system_prompt = "Ты опытный карьерный консультант в IT-сфере. Твоя задача - предоставить персонализированную карьерную консультацию на основе опыта пользователя и анализа подходящих ему вакансий."
            user_prompt = self._build_consultation_prompt(user_context, vacancies_context)
            
            logger.info(f"🤖 Отправляем запрос к Yandex GPT ({self.model})")
            
            messages = [
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_prompt},
            ]
            
            result = await self.sdk.models.completions(self.model).configure(temperature=0.5).run_async(messages)
            
            consultation = result.alternatives[0].text.strip()
            
            logger.info(f"✅ Получена карьерная консультация (длина: {len(consultation)} символов)")
            
            return consultation
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения карьерной консультации: {e}")
            return self._get_fallback_consultation()
    
    def _build_user_context(self, user_data: Dict) -> str:
        """Формирует контекст пользователя для Yandex GPT"""
        context_parts = []
        
        # Текущий профиль
        professional_area = user_data.get('professional_area', 'Не указано')
        current_position = user_data.get('current_position', 'Не указано')
        years_experience = user_data.get('years_experience', 'Не указано')
        context_parts.append(f"Профессиональная сфера: {professional_area}")
        context_parts.append(f"Текущая должность: {current_position}")
        context_parts.append(f"Опыт работы: {years_experience} лет")
        
        # Опыт и проекты
        work_experience_projects = user_data.get('work_experience_projects', '')
        if work_experience_projects:
            context_parts.append(f"Опыт работы и проекты: {work_experience_projects}")
        
        # Карьерные цели
        target_area = user_data.get('target_area', 'Не указано')
        preferred_activities = user_data.get('preferred_activities', 'Не указано')
        position_level_ambitions = user_data.get('position_level_ambitions', 'Не указано')
        salary_expectations = user_data.get('salary_expectations', 'Не указано')
        
        context_parts.append(f"Желаемая область: {target_area}")
        context_parts.append(f"Интересные активности: {preferred_activities}")
        context_parts.append(f"Амбиции по уровню: {position_level_ambitions}")
        context_parts.append(f"Ожидания по зарплате: {salary_expectations} руб/мес")
        
        # Компетенции
        current_skills = user_data.get('current_skills', 'Не указано')
        tools_experience = user_data.get('tools_experience', 'Не указано')
        soft_skills = user_data.get('soft_skills', 'Не указано')
        education = user_data.get('education', 'Не указано')
        
        context_parts.append(f"Технические навыки: {current_skills}")
        context_parts.append(f"Инструменты и технологии: {tools_experience}")
        context_parts.append(f"Soft skills: {soft_skills}")
        context_parts.append(f"Образование: {education}")
        
        return "\n".join(context_parts)
    
    def _build_vacancies_context(self, vacancies: List[VacancyData]) -> str:
        """Формирует контекст вакансий для Yandex GPT"""
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
        """Формирует prompt для Yandex GPT"""
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

