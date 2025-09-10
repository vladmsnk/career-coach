"""
Tests for session data functionality (current_module and collected_data)
"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.domain.chat.entities import ChatSession
from tests.test_chat import InMemoryChatRepository


class TestSessionDataFunctionality:
    """Test session data fields and methods"""

    def test_chat_session_fields_and_defaults(self):
        """Test ChatSession fields and default values"""
        session_id = uuid4()
        user_id = uuid4()
        now = datetime.utcnow()
        
        # Test with explicit values
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            created_at=now,
            status="active",
            question_index=1,
            answers_count=0,
            current_module="career_goals",
            collected_data={"test_question": "test_answer"}
        )
        
        assert session.current_module == "career_goals"
        assert session.collected_data == {"test_question": "test_answer"}
        
        # Test default values
        default_session = ChatSession(
            id=session_id,
            user_id=user_id,
            created_at=now,
            status="active",
            question_index=1,
            answers_count=0
        )
        
        assert default_session.current_module == "current_profile"
        assert default_session.collected_data == {}

    @pytest.mark.asyncio
    async def test_repository_session_data_operations(self):
        """Test repository create and update operations for session data"""
        repo = InMemoryChatRepository()
        user_id = uuid4()
        
        # Create session with default values
        session = await repo.create_session(user_id)
        assert session.current_module == "current_profile"
        assert session.collected_data == {}
        
        # Update session data with multiple questions
        questions_and_answers = [
            ("professional_area", "Бэкенд-разработчик"),
            ("current_position", "Senior Python Developer"),
            ("years_experience", "5"),
            ("target_area", "Фулстек-разработчик"),
            ("current_skills", "Python, FastAPI, PostgreSQL")
        ]
        
        for question_id, answer in questions_and_answers:
            await repo.update_session_data(session.id, question_id, answer)
        
        # Verify all data is stored
        updated_session = await repo.get_latest_session(user_id)
        assert updated_session is not None
        for question_id, expected_answer in questions_and_answers:
            assert updated_session.collected_data[question_id] == expected_answer

    @pytest.mark.asyncio
    async def test_session_data_persistence_and_errors(self):
        """Test data persistence across updates and error handling"""
        repo = InMemoryChatRepository()
        user_id = uuid4()
        
        session = await repo.create_session(user_id)
        
        # Add collected data
        await repo.update_session_data(session.id, "professional_area", "Бэкенд-разработчик")
        await repo.update_session_data(session.id, "years_experience", "3")
        
        # Update other session fields - data should persist
        updated_session = await repo.update_session(
            session.id,
            status="active",
            question_index=2,
            answers_count=1
        )
        
        # Verify collected data is preserved
        assert updated_session.collected_data["professional_area"] == "Бэкенд-разработчик"
        assert updated_session.collected_data["years_experience"] == "3"
        assert updated_session.question_index == 2
        assert updated_session.answers_count == 1
        
        # Test error handling for nonexistent session
        fake_session_id = uuid4()
        with pytest.raises(KeyError, match="session not found"):
            await repo.update_session_data(fake_session_id, "test_question", "test_answer")


if __name__ == "__main__":
    pytest.main([__file__])