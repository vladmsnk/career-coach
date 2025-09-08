"""
Tests for the new session data functionality (current_module and collected_data)
"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.domain.chat.entities import ChatSession
from tests.test_chat import InMemoryChatRepository


class TestSessionDataFunctionality:
    """Test new fields and methods for session data"""

    def test_chat_session_with_new_fields(self):
        """Test that ChatSession can be created with new fields"""
        session_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()
        
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            created_at=now,
            status="active",
            question_index=1,
            answers_count=0,
            current_module="context",
            collected_data={"test_question": "test_answer"}
        )
        
        assert session.id == session_id
        assert session.user_id == user_id
        assert session.current_module == "context"
        assert session.collected_data == {"test_question": "test_answer"}

    def test_chat_session_default_values(self):
        """Test that ChatSession has correct default values"""
        session_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()
        
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            created_at=now,
            status="active",
            question_index=1,
            answers_count=0
        )
        
        assert session.current_module == "context"
        assert session.collected_data == {}

    @pytest.mark.asyncio
    async def test_repository_create_session_with_new_fields(self):
        """Test that repository creates sessions with new fields"""
        repo = InMemoryChatRepository()
        user_id = uuid4()
        
        session = await repo.create_session(user_id)
        
        assert session.current_module == "context"
        assert session.collected_data == {}
        assert session.status == "active"
        assert session.question_index == 0
        assert session.answers_count == 0

    @pytest.mark.asyncio
    async def test_update_session_data_method(self):
        """Test the new update_session_data method"""
        repo = InMemoryChatRepository()
        user_id = uuid4()
        
        # Create session
        session = await repo.create_session(user_id)
        
        # Update session data
        await repo.update_session_data(session.id, "current_sphere", "IT")
        await repo.update_session_data(session.id, "current_position", "Developer")
        
        # Get session and verify data
        updated_session = await repo.get_latest_session(user_id)
        assert updated_session is not None
        assert updated_session.collected_data["current_sphere"] == "IT"
        assert updated_session.collected_data["current_position"] == "Developer"

    @pytest.mark.asyncio
    async def test_update_session_data_multiple_questions(self):
        """Test updating session data with multiple questions"""
        repo = InMemoryChatRepository()
        user_id = uuid4()
        
        session = await repo.create_session(user_id)
        
        # Simulate answering multiple questions
        questions_and_answers = [
            ("current_sphere", "IT"),
            ("current_position", "Senior Developer"),
            ("years_in_sphere", "5"),
            ("target_sphere", "IT"),
            ("preferred_activities", "Programming, Mentoring")
        ]
        
        for question_id, answer in questions_and_answers:
            await repo.update_session_data(session.id, question_id, answer)
        
        # Verify all data is stored
        updated_session = await repo.get_latest_session(user_id)
        assert updated_session is not None
        
        for question_id, expected_answer in questions_and_answers:
            assert updated_session.collected_data[question_id] == expected_answer

    @pytest.mark.asyncio
    async def test_update_session_data_nonexistent_session(self):
        """Test that updating data for nonexistent session raises error"""
        repo = InMemoryChatRepository()
        fake_session_id = uuid4()
        
        with pytest.raises(KeyError, match="session not found"):
            await repo.update_session_data(fake_session_id, "test_question", "test_answer")

    @pytest.mark.asyncio
    async def test_collected_data_persists_across_session_updates(self):
        """Test that collected_data persists when updating other session fields"""
        repo = InMemoryChatRepository()
        user_id = uuid4()
        
        session = await repo.create_session(user_id)
        
        # Add some collected data
        await repo.update_session_data(session.id, "current_sphere", "IT")
        await repo.update_session_data(session.id, "current_position", "Developer")
        
        # Update other session fields
        updated_session = await repo.update_session(
            session.id,
            status="active",
            question_index=2,
            answers_count=1
        )
        
        # Verify collected data is preserved
        assert updated_session.collected_data["current_sphere"] == "IT"
        assert updated_session.collected_data["current_position"] == "Developer"
        assert updated_session.question_index == 2
        assert updated_session.answers_count == 1


if __name__ == "__main__":
    pytest.main([__file__])
