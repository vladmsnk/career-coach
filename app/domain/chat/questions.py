PROFESSIONAL_AREAS = [
    "Бэкенд-разработчик", "ML-разработчик", "Фронтенд-разработчик", "Тестировщик",
    "Разработчик мобильных приложений", "DevOps-инженер", "iOS-разработчик",
    "Machine Learning Engineer", "Системный разработчик", "Android-разработчик",
    "Инженер данных", "Фулстек-разработчик",
    "Продакт-менеджер", "Технический менеджер", "Менеджер проектов в бизнесе",
    "Менеджер проектов", "Категорийный менеджер", "Менеджер контроля качества",
    "Аналитик-разработчик", "Бизнес-аналитик", "Системный аналитик", "Маркетинговый аналитик",
    "Специалист технической поддержки", "Работник Service Desk для сотрудников",
    "Инженер", "Инженер по эксплуатации", "Инженер-конструктор", "IT-специалист дата-центра",
    "Сетевой инженер", "Системный администратор", "Администратор баз данных",
    "Инженер по информационной безопасности"
]

POSITION_LEVELS = [
    "Junior", "Middle", "Senior", "Lead"
]

INTERVIEW_MODULES = {
    "current_profile": {
        "title": "Текущий профессиональный профиль",
        "questions": [
            {
                "id": "professional_area", 
                "type": "select", 
                "prompt": "В какой профессиональной сфере вы работаете?",
                "options": PROFESSIONAL_AREAS
            },
            {
                "id": "current_position", 
                "type": "text", 
                "prompt": "Какая у вас текущая должность или позиция?",
                "max_length": 100
            },
            {
                "id": "years_experience", 
                "type": "number", 
                "prompt": "Сколько лет вы работаете в текущей профессиональной области?",
                "min": 0, "max": 50
            },
            {
                "id": "work_experience_projects", 
                "type": "text", 
                "prompt": "Расскажите о своем опыте работы и реализованных проектах",
                "max_length": 800
            }
        ]
    },
    "career_goals": {
        "title": "Карьерные цели и интересы",
        "questions": [
            {
                "id": "target_area", 
                "type": "select", 
                "prompt": "Какая сфера и специализация вас интересует?",
                "options": PROFESSIONAL_AREAS
            },
            {
                "id": "preferred_activities", 
                "type": "text", 
                "prompt": "Какой вид активностей и профессиональных функций вам интересен? (например: создание продуктов, общение с людьми, аналитика, управление командой)",
                "max_length": 400
            },
            {
                "id": "position_level_ambitions", 
                "type": "select", 
                "prompt": "Какие у вас амбиции по должностному уровню?",
                "options": POSITION_LEVELS
            },
            {
                "id": "salary_expectations", 
                "type": "range", 
                "prompt": "Ваши ожидания по заработной плате (в рублях в месяц)?",
                "min": 60000, "max": 700000, "step": 20000
            }
        ]
    },
    "competencies": {
        "title": "Компетенции и развитие",
        "questions": [
            {
                "id": "current_skills", 
                "type": "text", 
                "prompt": "Опишите ваши текущие умения и компетенции",
                "max_length": 500
            },
            {
                "id": "tools_experience", 
                "type": "text", 
                "prompt": "Какими инструментами и технологиями вы владеете?",
                "max_length": 400
            },
            {
                "id": "soft_skills", 
                "type": "text", 
                "prompt": "Насколько развиты ваши soft-компетенции и какие именно?",
                "max_length": 300
            },
            {
                "id": "education", 
                "type": "text", 
                "prompt": "Какое у вас образование или какие курсы вы прошли?",
                "max_length": 400
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
