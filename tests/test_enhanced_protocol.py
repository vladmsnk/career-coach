"""
Tests for enhanced WebSocket protocol with metadata
"""
import pytest
import asyncio
from uuid import uuid4

from app.api.v1.routes.chat import WebSocketHandler
from app.domain.chat.questions import QUESTIONS
from tests.test_chat import InMemoryChatRepository


class MockWebSocket:
    """Mock WebSocket for testing enhanced protocol"""
    def __init__(self):
        self.sent_messages = []
        self.received_messages = ["IT"]  # Default answer
        self.message_index = 0
    
    async def send_json(self, data):
        self.sent_messages.append(data)
        return True  # Simulate successful send
    
    async def receive_text(self):
        if self.message_index < len(self.received_messages):
            message = self.received_messages[self.message_index]
            self.message_index += 1
            return message
        return "Default Answer"


class TestEnhancedWebSocketProtocol:
    """Test enhanced WebSocket protocol with metadata"""

    @pytest.mark.asyncio
    async def test_enhanced_question_format_select(self):
        """Test enhanced format for select questions"""
        mock_ws = MockWebSocket()
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        # Create session
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Get first question (select type)
        question = QUESTIONS[0]  # current_sphere - select
        question_with_meta = {**question, "total_questions": len(QUESTIONS)}
        
        # Test question cycle
        result = await handler.handle_question_cycle(question_with_meta, session.id, None)
        
        # Check that question was sent with enhanced format
        assert len(mock_ws.sent_messages) == 1
        sent_question = mock_ws.sent_messages[0]
        
        # Check basic fields (backward compatibility)
        assert sent_question["id"] == question["id"]
        assert sent_question["prompt"] == question["prompt"]
        
        # Check new metadata fields
        assert sent_question["type"] == "select"
        assert sent_question["module"] == "context"
        assert sent_question["module_title"] == "Определение стартового контекста"
        assert "options" in sent_question
        assert "IT" in sent_question["options"]
        
        # Check progress
        assert sent_question["progress"]["current"] == 1
        assert sent_question["progress"]["total"] == len(QUESTIONS)

    @pytest.mark.asyncio
    async def test_enhanced_question_format_multiselect(self):
        """Test enhanced format for multiselect questions"""
        mock_ws = MockWebSocket()
        mock_ws.received_messages = ["Техническая работа"]
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Find multiselect question (preferred_activities)
        multiselect_question = None
        for q in QUESTIONS:
            if q.get("type") == "multiselect":
                multiselect_question = q
                break
        
        assert multiselect_question is not None
        question_with_meta = {**multiselect_question, "total_questions": len(QUESTIONS)}
        
        result = await handler.handle_question_cycle(question_with_meta, session.id, None)
        
        sent_question = mock_ws.sent_messages[0]
        assert sent_question["type"] == "multiselect"
        assert sent_question["multiple"] is True
        assert "options" in sent_question
        assert "Техническая работа" in sent_question["options"]

    @pytest.mark.asyncio
    async def test_enhanced_question_format_number(self):
        """Test enhanced format for number questions"""
        mock_ws = MockWebSocket()
        mock_ws.received_messages = ["5"]
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Find number question (years_in_sphere)
        number_question = None
        for q in QUESTIONS:
            if q.get("type") == "number":
                number_question = q
                break
        
        assert number_question is not None
        question_with_meta = {**number_question, "total_questions": len(QUESTIONS)}
        
        result = await handler.handle_question_cycle(question_with_meta, session.id, None)
        
        sent_question = mock_ws.sent_messages[0]
        assert sent_question["type"] == "number"
        assert "constraints" in sent_question
        assert sent_question["constraints"]["min"] == 0
        assert sent_question["constraints"]["max"] == 50

    @pytest.mark.asyncio
    async def test_enhanced_question_format_range(self):
        """Test enhanced format for range questions"""
        mock_ws = MockWebSocket()
        mock_ws.received_messages = ["100000"]
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Find range question (salary_expectations)
        range_question = None
        for q in QUESTIONS:
            if q.get("type") == "range":
                range_question = q
                break
        
        assert range_question is not None
        question_with_meta = {**range_question, "total_questions": len(QUESTIONS)}
        
        result = await handler.handle_question_cycle(question_with_meta, session.id, None)
        
        sent_question = mock_ws.sent_messages[0]
        assert sent_question["type"] == "range"
        assert "constraints" in sent_question
        assert sent_question["constraints"]["min"] == 30000
        assert sent_question["constraints"]["max"] == 500000
        assert sent_question["constraints"]["step"] == 10000

    @pytest.mark.asyncio
    async def test_enhanced_question_format_text(self):
        """Test enhanced format for text questions"""
        mock_ws = MockWebSocket()
        mock_ws.received_messages = ["Проект описание"]
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Find text question (key_projects)
        text_question = None
        for q in QUESTIONS:
            if q.get("type") == "text":
                text_question = q
                break
        
        assert text_question is not None
        question_with_meta = {**text_question, "total_questions": len(QUESTIONS)}
        
        result = await handler.handle_question_cycle(question_with_meta, session.id, None)
        
        sent_question = mock_ws.sent_messages[0]
        assert sent_question["type"] == "text"
        assert "constraints" in sent_question
        assert sent_question["constraints"]["max_length"] == 500

    @pytest.mark.asyncio
    async def test_enhanced_question_format_string(self):
        """Test enhanced format for string questions"""
        mock_ws = MockWebSocket()
        mock_ws.received_messages = ["Developer"]
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Find string question (current_position)
        string_question = None
        for q in QUESTIONS:
            if q.get("type") == "string":
                string_question = q
                break
        
        assert string_question is not None
        question_with_meta = {**string_question, "total_questions": len(QUESTIONS)}
        
        result = await handler.handle_question_cycle(question_with_meta, session.id, None)
        
        sent_question = mock_ws.sent_messages[0]
        assert sent_question["type"] == "string"
        assert "constraints" in sent_question
        assert sent_question["constraints"]["max_length"] == 100

    @pytest.mark.asyncio
    async def test_progress_calculation(self):
        """Test progress calculation for different questions"""
        mock_ws = MockWebSocket()
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Test different questions with their progress
        for idx, question in enumerate(QUESTIONS[:3]):  # Test first 3
            mock_ws.sent_messages.clear()
            mock_ws.message_index = 0
            
            question_with_meta = {**question, "total_questions": len(QUESTIONS)}
            
            result = await handler.handle_question_cycle(question_with_meta, session.id, None)
            
            sent_question = mock_ws.sent_messages[0]
            expected_current = question["global_index"] + 1
            
            assert sent_question["progress"]["current"] == expected_current
            assert sent_question["progress"]["total"] == len(QUESTIONS)

    @pytest.mark.asyncio
    async def test_module_information(self):
        """Test module information in questions"""
        mock_ws = MockWebSocket()
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Test questions from different modules
        modules_tested = set()
        
        for question in QUESTIONS:
            if question["module"] not in modules_tested:
                mock_ws.sent_messages.clear()
                mock_ws.message_index = 0
                
                question_with_meta = {**question, "total_questions": len(QUESTIONS)}
                
                result = await handler.handle_question_cycle(question_with_meta, session.id, None)
                
                sent_question = mock_ws.sent_messages[0]
                assert sent_question["module"] == question["module"]
                assert sent_question["module_title"] == question["module_title"]
                
                modules_tested.add(question["module"])
        
        # Should have tested all 3 modules
        assert len(modules_tested) == 3
        assert modules_tested == {"context", "goals", "skills"}

    @pytest.mark.asyncio
    async def test_backward_compatibility_fields(self):
        """Test that old required fields are still present"""
        mock_ws = MockWebSocket()
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        question = QUESTIONS[0]
        question_with_meta = {**question, "total_questions": len(QUESTIONS)}
        
        result = await handler.handle_question_cycle(question_with_meta, session.id, None)
        
        sent_question = mock_ws.sent_messages[0]
        
        # Check that old client required fields are still there
        assert "id" in sent_question
        assert "prompt" in sent_question
        
        # These are the only fields old client expects
        # All new fields are optional and should be ignored by old clients


if __name__ == "__main__":
    pytest.main([__file__])
