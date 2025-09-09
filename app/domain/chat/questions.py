INTERVIEW_MODULES = {
    "context": {
        "title": "Определение стартового контекста",
        "questions": [
            {
                "id": "current_position", 
                "type": "select", 
                "prompt": "Какая у вас текущая должность?",
                "options": [
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
            },
            {
                "id": "years_in_position", 
                "type": "number", 
                "prompt": "Сколько лет вы работаете на этой должности?",
                "min": 0, "max": 50
            },
            {
                "id": "key_projects", 
                "type": "text", 
                "prompt": "Расскажите о 2-3 ключевых IT-проектах или достижениях (стек технологий, роль, результат)",
                "max_length": 500
            }
        ]
    },
    "goals": {
        "title": "Определение целей",
        "questions": [
            {
                "id": "target_specialization", 
                "type": "select", 
                "prompt": "В какой IT-специализации или направлении вы хотите развиваться?",
                "options": [
                    "Бэкенд-разработчик", "Фронтенд-разработчик", "Фулстек-разработчик",
                    "ML-разработчик", "Machine Learning Engineer", "Data Engineer", 
                    "Data Scientist", "AI Engineer",
                    "DevOps-инженер", "Системный администратор", "Инженер по информационной безопасности",
                    "iOS-разработчик", "Android-разработчик", "Разработчик мобильных приложений", 
                    "Тестировщик", "QA Engineer", "Test Automation Engineer",
                    "Системный разработчик", "Embedded-разработчик",
                    "Технический лидер", "Tech Lead", "Team Lead", 
                    "Архитектор ПО", "Solution Architect", "Enterprise Architect",
                    "Продакт-менеджер", "Технический менеджер", "Engineering Manager",
                    "Системный аналитик", "Бизнес-аналитик", "Аналитик данных",
                    "UX/UI дизайнер", "Product Designer"
                ]
            },
            {
                "id": "preferred_activities", 
                "type": "multiselect", 
                "prompt": "Какие виды деятельности в IT вам интересны? (выберите несколько)",
                "options": [
                    "Разработка ПО", "Машинное обучение / AI", "Инфраструктура и DevOps", 
                    "Управление командой", "Системный анализ", "Работа с данными / Data Science",
                    "Кибербезопасность", "Продакт-менеджмент", "Тестирование и контроль качества",
                    "UX/UI дизайн", "Исследования и новые технологии"
                ]
            },
            {
                "id": "position_ambitions", 
                "type": "string", 
                "prompt": "Кем вы хотите стать через 3–5 лет в IT? (например, Senior Developer, Team Lead, Архитектор, Data Scientist, CTO)",
                "max_length": 100
            },
            {
                "id": "salary_expectations", 
                "type": "range", 
                "prompt": "Ваши ожидания по зарплате (в рублях в месяц)?",
                "min": 60000, "max": 700000, "step": 20000
            }
        ]
    },
    "skills": {
        "title": "Определение профессионального уровня",
        "questions": [
            {
                "id": "current_skills", 
                "type": "multiselect", 
                "prompt": "Какими ключевыми IT-навыками вы владеете?",
                "options": [
                    "Программирование", "Алгоритмы и структуры данных", "DevOps практики", 
                    "Администрирование систем", "Работа с базами данных", "Тестирование", 
                    "Машинное обучение", "Data Engineering", "Кибербезопасность", "Проектирование архитектуры"
                ]
            },
            {
                "id": "tools_experience", 
                "type": "multiselect", 
                "prompt": "Какими технологиями и инструментами вы владеете?",
                "options": [
                    "Python", "Go", "Java", "JavaScript/TypeScript", "SQL", "PostgreSQL", "MongoDB", 
                    "Docker", "Kubernetes", "CI/CD (GitHub Actions, GitLab CI)", "Linux/Unix", 
                    "Figma", "Jira/Confluence", "TensorFlow / PyTorch", "Spark", "Hadoop"
                ]
            },
            {
                "id": "soft_skills", 
                "type": "multiselect", 
                "prompt": "Какие soft skills помогают вам в IT-работе?",
                "options": [
                    "Коммуникация", "Тайм-менеджмент", "Критическое мышление", 
                    "Адаптивность", "Эмпатия", "Командная работа", 
                    "Решение проблем", "Креативность"
                ]
            },
            {
                "id": "education", 
                "type": "text", 
                "prompt": "Расскажите о своем IT-образовании (университет, курсы, сертификаты)",
                "max_length": 300
            },
            {
                "id": "learning_goals", 
                "type": "text", 
                "prompt": "Какие технологии или навыки планируете изучать в ближайшее время?",
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
