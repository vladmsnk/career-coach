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
    async def test_enhanced_question_formats(self):
        """Test enhanced format for different question types"""
        mock_ws = MockWebSocket()
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Test different question types
        test_cases = [
            ("select", ["IT"], "options"),
            ("multiselect", ["Техническая работа"], "options"),
            ("number", ["5"], "constraints"),
            ("range", ["100000"], "constraints"),
            ("string", ["Developer"], "constraints"),
            ("text", ["Проект описание"], "constraints")
        ]
        
        for question_type, answer, expected_field in test_cases:
            # Find question of this type
            question = next((q for q in QUESTIONS if q.get("type") == question_type), None)
            if not question:
                continue
                
            mock_ws.sent_messages.clear()
            mock_ws.message_index = 0
            mock_ws.received_messages = answer
            
            question_with_meta = {**question, "total_questions": len(QUESTIONS)}
            result = await handler.handle_question_cycle(question_with_meta, session.id, None)
            
            # Verify enhanced format
            sent_question = mock_ws.sent_messages[0]
            assert sent_question["type"] == question_type
            assert sent_question["module"] == question["module"]
            assert expected_field in sent_question

    @pytest.mark.asyncio
    async def test_progress_calculation(self):
        """Test progress calculation for different questions"""
        mock_ws = MockWebSocket()
        repo = InMemoryChatRepository()
        handler = WebSocketHandler(mock_ws, repo)
        
        user_id = uuid4()
        session = await repo.create_session(user_id)
        
        # Answers corresponding to question types: select, string, number
        test_answers = ["IT", "Developer", "5"]
        
        # Test different questions with their progress
        for idx, question in enumerate(QUESTIONS[:3]):  # Test first 3
            mock_ws.sent_messages.clear()
            mock_ws.message_index = 0
            # Set appropriate answer for each question type
            mock_ws.received_messages = [test_answers[idx]]
            
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
                
                # Set appropriate answer based on question type
                if question["type"] == "select":
                    mock_ws.received_messages = ["IT"]  # Valid for both context and goals modules
                elif question["type"] == "multiselect":
                    # For skills module: use first valid option
                    first_option = question.get("options", ["Программирование"])[0]
                    mock_ws.received_messages = [first_option]
                elif question["type"] == "string":
                    mock_ws.received_messages = ["Test String"]
                elif question["type"] == "number":
                    mock_ws.received_messages = ["5"]
                elif question["type"] == "range":
                    mock_ws.received_messages = ["100000"]
                else:
                    mock_ws.received_messages = ["Default Answer"]
                
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
