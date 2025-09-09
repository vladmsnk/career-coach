INTERVIEW_MODULES = {
    "context": {
        "title": "Определение стартового контекста",
        "questions": [
            {
                "id": "current_sphere", 
                "type": "select", 
                "prompt": "В какой сфере вы работаете?",
                "options": ["IT", "Финансы", "Маркетинг", "Продажи", "HR", "Консалтинг", "Образование", "Здравоохранение", "Производство", "Другое"]
            },
            {
                "id": "current_position", 
                "type": "string", 
                "prompt": "Какая у вас текущая должность?",
                "max_length": 100
            },
            {
                "id": "years_in_sphere", 
                "type": "number", 
                "prompt": "Сколько лет работаете в данной сфере?",
                "min": 0, "max": 50
            },
            {
                "id": "years_in_position", 
                "type": "number", 
                "prompt": "Сколько лет работаете на текущей должности?",
                "min": 0, "max": 50
            },
            {
                "id": "key_projects", 
                "type": "text", 
                "prompt": "Расскажите о 2-3 ключевых проектах или достижениях (кратко)",
                "max_length": 500
            }
        ]
    },
    "goals": {
        "title": "Определение целей",
        "questions": [
            {
                "id": "target_sphere", 
                "type": "select", 
                "prompt": "В какой сфере хотели бы развиваться?",
                "options": ["IT", "Финансы", "Маркетинг", "Продажи", "HR", "Консалтинг", "Образование", "Здравоохранение", "Производство", "Предпринимательство", "Другое"]
            },
            {
                "id": "target_specialization", 
                "type": "string", 
                "prompt": "Какая специализация или направление вас интересует?",
                "max_length": 100
            },
            {
                "id": "preferred_activities", 
                "type": "multiselect", 
                "prompt": "Какие виды деятельности вам интересны? (выберите несколько)",
                "options": ["Управление командой", "Аналитическая работа", "Творческие задачи", "Техническая работа", "Коммуникации с клиентами", "Стратегическое планирование", "Обучение других", "Исследования"]
            },
            {
                "id": "position_ambitions", 
                "type": "string", 
                "prompt": "Какие у вас амбиции по карьерному росту?",
                "max_length": 100
            },
            {
                "id": "salary_expectations", 
                "type": "range", 
                "prompt": "Ваши ожидания по зарплате (в рублях в месяц)?",
                "min": 30000, "max": 500000, "step": 10000
            }
        ]
    },
    "skills": {
        "title": "Определение профессионального уровня",
        "questions": [
            {
                "id": "current_skills", 
                "type": "multiselect", 
                "prompt": "Какими профессиональными навыками вы владеете? (выберите подходящие)",
                "options": ["Лидерство", "Аналитическое мышление", "Программирование", "Дизайн", "Продажи", "Маркетинг", "Финансовый анализ", "Управление проектами", "Переговоры"]
            },
            {
                "id": "tools_experience", 
                "type": "multiselect", 
                "prompt": "Какими инструментами и технологиями владеете?",
                "options": ["Microsoft Excel", "Python", "SQL", "Figma", "CRM системы", "ERP системы", "BI-системы", "Google Analytics", "Adobe Creative Suite", "Jira/Confluence"]
            },
            {
                "id": "soft_skills", 
                "type": "multiselect", 
                "prompt": "Какие soft skills у вас развиты?",
                "options": ["Коммуникация", "Тайм-менеджмент", "Критическое мышление", "Адаптивность", "Эмпатия", "Командная работа", "Решение проблем", "Креативность"]
            },
            {
                "id": "education", 
                "type": "text", 
                "prompt": "Расскажите о своем образовании и пройденных курсах",
                "max_length": 300
            },
            {
                "id": "learning_goals", 
                "type": "text", 
                "prompt": "Какие навыки планируете развивать в ближайшее время?",
                "max_length": 300
            }
        ]
    }
}


def get_all_questions():
    """Возвращает плоский список всех вопросов с метаданными модуля"""
    questions = []
    for module_key, module_data in INTERVIEW_MODULES.items():
        for i, question in enumerate(module_data["questions"]):
            questions.append({
                **question,
                "module": module_key,
                "module_title": module_data["title"],
                "question_index_in_module": i,
                "global_index": len(questions)
            })
    return questions


def get_question_by_global_index(index):
    """Получить вопрос по глобальному индексу"""
    questions = get_all_questions()
    return questions[index] if 0 <= index < len(questions) else None


def get_module_questions(module_key):
    """Получить все вопросы конкретного модуля"""
    if module_key not in INTERVIEW_MODULES:
        return []
    return INTERVIEW_MODULES[module_key]["questions"]


def get_total_questions_count():
    """Получить общее количество вопросов"""
    return len(get_all_questions())


# Для обратной совместимости с существующим кодом
QUESTIONS = get_all_questions()
