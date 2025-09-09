"""
Tests for answer validation functionality
"""
import pytest
from app.api.v1.routes.chat import WebSocketHandler
from tests.test_chat import InMemoryChatRepository


class MockWebSocket:
    """Mock WebSocket for testing validation methods"""
    def __init__(self):
        self.sent_messages = []
    
    async def send_json(self, data):
        self.sent_messages.append(data)


class TestAnswerValidation:
    """Test core answer validation functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_ws = MockWebSocket()
        self.repo = InMemoryChatRepository()
        self.handler = WebSocketHandler(self.mock_ws, self.repo)

    def test_select_question_validation(self):
        """Test select question validation - valid and invalid answers"""
        question = {
            "id": "current_sphere",
            "type": "select",
            "options": ["IT", "Финансы", "Маркетинг"],
            "prompt": "В какой сфере работаете?"
        }
        
        # Valid answer
        assert self.handler.validate_answer("IT", question) is None
        
        # Invalid answer
        result = self.handler.validate_answer("Спорт", question)
        assert "Выберите один из вариантов" in result

    def test_multiselect_question_validation(self):
        """Test multiselect question validation"""
        question = {
            "id": "skills",
            "type": "multiselect",
            "options": ["Python", "Java", "JavaScript"],
            "prompt": "Какие языки знаете?"
        }
        
        # Valid answer
        assert self.handler.validate_answer("Python, Java", question) is None
        
        # Empty answer
        assert "Выберите хотя бы один вариант" in self.handler.validate_answer("", question)
        
        # Invalid option
        result = self.handler.validate_answer("Python, C++", question)
        assert "Недопустимые варианты: C++" in result

    def test_number_question_validation(self):
        """Test number question validation"""
        question = {
            "id": "years",
            "type": "number",
            "min": 0,
            "max": 50,
            "prompt": "Сколько лет опыта?"
        }
        
        # Valid answers
        assert self.handler.validate_answer("5", question) is None
        assert self.handler.validate_answer("0", question) is None
        assert self.handler.validate_answer("50", question) is None
        
        # Invalid range
        assert "Число должно быть от 0 до 50" in self.handler.validate_answer("-1", question)
        assert "Число должно быть от 0 до 50" in self.handler.validate_answer("51", question)
        
        # Non-numeric
        assert "Введите корректное число" in self.handler.validate_answer("abc", question)

    def test_range_question_validation(self):
        """Test range question validation"""
        question = {
            "id": "salary",
            "type": "range",
            "min": 30000,
            "max": 500000,
            "prompt": "Ожидаемая зарплата?"
        }
        
        # Valid answer
        assert self.handler.validate_answer("100000", question) is None
        
        # Invalid range
        result = self.handler.validate_answer("20000", question)
        assert "Значение должно быть от 30000 до 500000" in result

    def test_string_question_validation(self):
        """Test string question validation"""
        question = {
            "id": "position",
            "type": "string",
            "max_length": 10,
            "prompt": "Ваша должность?"
        }
        
        # Valid answer
        assert self.handler.validate_answer("Developer", question) is None
        
        # Empty answer
        assert "Ответ не может быть пустым" in self.handler.validate_answer("", question)
        
        # Too long
        result = self.handler.validate_answer("Very Long Position Title", question)
        assert "Максимальная длина: 10 символов" in result

    def test_text_question_validation(self):
        """Test text question validation"""
        question = {
            "id": "description",
            "type": "text",
            "max_length": 20,
            "prompt": "Опишите проект"
        }
        
        # Valid answer
        assert self.handler.validate_answer("Короткий текст", question) is None
        
        # Too long
        result = self.handler.validate_answer("Это был очень интересный и сложный проект", question)
        assert "Максимальная длина: 20 символов" in result

    def test_answer_normalization(self):
        """Test answer normalization functionality"""
        # String normalization
        result = self.handler.normalize_answer("  Hello World  ", "string")
        assert result == "hello world"
        
        # Multiselect normalization
        result = self.handler.normalize_answer("Python, Java, JavaScript", "multiselect")
        assert result == "java,javascript,python"  # Sorted and lowercase
        
        # Case-insensitive normalization
        result1 = self.handler.normalize_answer("IT", "string")
        result2 = self.handler.normalize_answer("it", "string")
        assert result1 == result2 == "it"

    def test_unknown_question_type_defaults_to_string(self):
        """Test that unknown question types default to string validation"""
        question = {
            "id": "unknown",
            "type": "unknown_type",
            "prompt": "Unknown question?"
        }
        
        result = self.handler.validate_answer("Some answer", question)
        assert result is None  # Defaults to string validation


if __name__ == "__main__":
    pytest.main([__file__])