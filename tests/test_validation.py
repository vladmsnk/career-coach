"""
Tests for answer validation functionality
"""
import pytest
from uuid import uuid4

from app.api.v1.routes.chat import WebSocketHandler
from tests.test_chat import InMemoryChatRepository


class MockWebSocket:
    """Mock WebSocket for testing validation methods"""
    def __init__(self):
        self.sent_messages = []
    
    async def send_json(self, data):
        self.sent_messages.append(data)


class TestAnswerValidation:
    """Test answer validation methods"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_ws = MockWebSocket()
        self.repo = InMemoryChatRepository()
        self.handler = WebSocketHandler(self.mock_ws, self.repo)

    def test_validate_select_question_valid_answer(self):
        """Test select question with valid answer"""
        question = {
            "id": "current_sphere",
            "type": "select",
            "options": ["IT", "Финансы", "Маркетинг"],
            "prompt": "В какой сфере работаете?"
        }
        
        result = self.handler.validate_answer("IT", question)
        assert result is None  # No error

    def test_validate_select_question_invalid_answer(self):
        """Test select question with invalid answer"""
        question = {
            "id": "current_sphere",
            "type": "select",
            "options": ["IT", "Финансы", "Маркетинг"],
            "prompt": "В какой сфере работаете?"
        }
        
        result = self.handler.validate_answer("Спорт", question)
        assert result == "Выберите один из вариантов: IT, Финансы, Маркетинг"

    def test_validate_multiselect_question_valid_answer(self):
        """Test multiselect question with valid answer"""
        question = {
            "id": "skills",
            "type": "multiselect",
            "options": ["Python", "Java", "JavaScript"],
            "prompt": "Какие языки знаете?"
        }
        
        result = self.handler.validate_answer("Python, Java", question)
        assert result is None  # No error

    def test_validate_multiselect_question_empty_answer(self):
        """Test multiselect question with empty answer"""
        question = {
            "id": "skills",
            "type": "multiselect",
            "options": ["Python", "Java", "JavaScript"],
            "prompt": "Какие языки знаете?"
        }
        
        result = self.handler.validate_answer("", question)
        assert result == "Выберите хотя бы один вариант"
        
        result = self.handler.validate_answer(",,,", question)
        assert result == "Выберите хотя бы один вариант"

    def test_validate_multiselect_question_invalid_option(self):
        """Test multiselect question with invalid option"""
        question = {
            "id": "skills",
            "type": "multiselect",
            "options": ["Python", "Java", "JavaScript"],
            "prompt": "Какие языки знаете?"
        }
        
        result = self.handler.validate_answer("Python, C++", question)
        assert result == "Недопустимые варианты: C++"
        
        result = self.handler.validate_answer("Ruby, Go, Python", question)
        assert result == "Недопустимые варианты: Ruby, Go"

    def test_validate_number_question_valid_answer(self):
        """Test number question with valid answer"""
        question = {
            "id": "years",
            "type": "number",
            "min": 0,
            "max": 50,
            "prompt": "Сколько лет опыта?"
        }
        
        result = self.handler.validate_answer("5", question)
        assert result is None  # No error
        
        result = self.handler.validate_answer("0", question)
        assert result is None  # Boundary value
        
        result = self.handler.validate_answer("50", question)
        assert result is None  # Boundary value

    def test_validate_number_question_invalid_range(self):
        """Test number question with out-of-range answer"""
        question = {
            "id": "years",
            "type": "number",
            "min": 0,
            "max": 50,
            "prompt": "Сколько лет опыта?"
        }
        
        result = self.handler.validate_answer("-1", question)
        assert result == "Число должно быть от 0 до 50"
        
        result = self.handler.validate_answer("51", question)
        assert result == "Число должно быть от 0 до 50"

    def test_validate_number_question_non_numeric(self):
        """Test number question with non-numeric answer"""
        question = {
            "id": "years",
            "type": "number",
            "min": 0,
            "max": 50,
            "prompt": "Сколько лет опыта?"
        }
        
        result = self.handler.validate_answer("abc", question)
        assert result == "Введите корректное число"
        
        result = self.handler.validate_answer("5.5", question)
        assert result == "Введите корректное число"

    def test_validate_range_question_valid_answer(self):
        """Test range question with valid answer"""
        question = {
            "id": "salary",
            "type": "range",
            "min": 30000,
            "max": 500000,
            "prompt": "Ожидаемая зарплата?"
        }
        
        result = self.handler.validate_answer("100000", question)
        assert result is None  # No error

    def test_validate_range_question_invalid_range(self):
        """Test range question with out-of-range answer"""
        question = {
            "id": "salary",
            "type": "range",
            "min": 30000,
            "max": 500000,
            "prompt": "Ожидаемая зарплата?"
        }
        
        result = self.handler.validate_answer("20000", question)
        assert result == "Значение должно быть от 30000 до 500000"
        
        result = self.handler.validate_answer("600000", question)
        assert result == "Значение должно быть от 30000 до 500000"

    def test_validate_string_question_valid_answer(self):
        """Test string question with valid answer"""
        question = {
            "id": "position",
            "type": "string",
            "max_length": 100,
            "prompt": "Ваша должность?"
        }
        
        result = self.handler.validate_answer("Senior Developer", question)
        assert result is None  # No error

    def test_validate_string_question_empty_answer(self):
        """Test string question with empty answer"""
        question = {
            "id": "position",
            "type": "string",
            "max_length": 100,
            "prompt": "Ваша должность?"
        }
        
        result = self.handler.validate_answer("", question)
        assert result == "Ответ не может быть пустым"
        
        result = self.handler.validate_answer("   ", question)
        assert result == "Ответ не может быть пустым"

    def test_validate_string_question_too_long(self):
        """Test string question with too long answer"""
        question = {
            "id": "position",
            "type": "string",
            "max_length": 10,
            "prompt": "Ваша должность?"
        }
        
        result = self.handler.validate_answer("Very Long Position Title", question)
        assert result == "Максимальная длина: 10 символов"

    def test_validate_text_question_valid_answer(self):
        """Test text question with valid answer"""
        question = {
            "id": "description",
            "type": "text",
            "max_length": 500,
            "prompt": "Опишите проект"
        }
        
        result = self.handler.validate_answer("Это был интересный проект...", question)
        assert result is None  # No error

    def test_validate_text_question_too_long(self):
        """Test text question with too long answer"""
        question = {
            "id": "description",
            "type": "text",
            "max_length": 20,
            "prompt": "Опишите проект"
        }
        
        result = self.handler.validate_answer("Это был очень интересный и сложный проект", question)
        assert result == "Максимальная длина: 20 символов"

    def test_validate_unknown_question_type(self):
        """Test validation with unknown question type defaults to string"""
        question = {
            "id": "unknown",
            "type": "unknown_type",
            "prompt": "Unknown question?"
        }
        
        result = self.handler.validate_answer("Some answer", question)
        assert result is None  # Defaults to string validation

    def test_validate_question_without_type(self):
        """Test validation without question type defaults to string"""
        question = {
            "id": "no_type",
            "prompt": "No type question?"
        }
        
        result = self.handler.validate_answer("Some answer", question)
        assert result is None  # Defaults to string validation


class TestAnswerNormalization:
    """Test answer normalization methods"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_ws = MockWebSocket()
        self.repo = InMemoryChatRepository()
        self.handler = WebSocketHandler(self.mock_ws, self.repo)

    def test_normalize_string_answer(self):
        """Test string answer normalization"""
        result = self.handler.normalize_answer("  Hello World  ", "string")
        assert result == "hello world"

    def test_normalize_multiselect_answer(self):
        """Test multiselect answer normalization"""
        result = self.handler.normalize_answer("Python, Java, JavaScript", "multiselect")
        assert result == "java,javascript,python"  # Sorted and lowercase
        
        result = self.handler.normalize_answer("  Python  ,  Java  ", "multiselect")
        assert result == "java,python"  # Trimmed, sorted, lowercase

    def test_normalize_empty_answer(self):
        """Test normalization of empty answer"""
        result = self.handler.normalize_answer("", "string")
        assert result == ""
        
        result = self.handler.normalize_answer(None, "string")
        assert result is None

    def test_normalize_multiselect_with_empty_items(self):
        """Test multiselect normalization with empty items"""
        result = self.handler.normalize_answer("Python,,Java,", "multiselect")
        assert result == "java,python"  # Empty items filtered out

    def test_normalize_number_answer(self):
        """Test number answer normalization (treated as string)"""
        result = self.handler.normalize_answer("123", "number")
        assert result == "123"

    def test_normalize_case_insensitive(self):
        """Test case-insensitive normalization"""
        result1 = self.handler.normalize_answer("IT", "string")
        result2 = self.handler.normalize_answer("it", "string")
        result3 = self.handler.normalize_answer("It", "string")
        
        assert result1 == result2 == result3 == "it"


class TestValidationErrorHandling:
    """Test validation error handling in question cycle"""

    def test_validation_error_structure(self):
        """Test that validation errors have correct structure"""
        mock_ws = MockWebSocket()
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        question = {
            "id": "test",
            "type": "select",
            "options": ["A", "B", "C"],
            "prompt": "Test question"
        }
        
        error_message = handler.validate_answer("D", question)
        assert error_message is not None
        assert "Выберите один из вариантов" in error_message


if __name__ == "__main__":
    pytest.main([__file__])
