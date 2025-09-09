"""
Tests for the modular questions structure
"""
import pytest
from app.domain.chat.questions import (
    INTERVIEW_MODULES,
    QUESTIONS,
    get_all_questions,
)


class TestInterviewModules:
    """Test the modular interview structure"""
    
    def test_interview_modules_structure(self):
        """Test that INTERVIEW_MODULES has correct structure"""
        assert isinstance(INTERVIEW_MODULES, dict)
        assert len(INTERVIEW_MODULES) == 3
        
        # Check module keys
        expected_modules = {"context", "goals", "skills"}
        assert set(INTERVIEW_MODULES.keys()) == expected_modules
        
        # Check each module has title and questions
        for module_key, module_data in INTERVIEW_MODULES.items():
            assert "title" in module_data
            assert "questions" in module_data
            assert isinstance(module_data["title"], str)
            assert isinstance(module_data["questions"], list)
            assert len(module_data["questions"]) == 5  # Each module has 5 questions
    
    def test_question_structure_and_types(self):
        """Test that each question has required fields and valid types"""
        valid_types = {"string", "text", "number", "select", "multiselect", "range"}
        
        for module_key, module_data in INTERVIEW_MODULES.items():
            for question in module_data["questions"]:
                # Required fields
                assert "id" in question
                assert "type" in question
                assert "prompt" in question
                assert question["type"] in valid_types
                
                # Type-specific validations
                if question["type"] in ["select", "multiselect"]:
                    assert "options" in question
                    assert len(question["options"]) > 0
                
                if question["type"] in ["number", "range"]:
                    assert "min" in question
                    assert "max" in question
                    assert question["min"] <= question["max"]
                
                if question["type"] in ["string", "text"]:
                    if "max_length" in question:
                        assert question["max_length"] > 0


class TestQuestionsIntegration:
    """Test questions integration and utility functions"""
    
    def test_get_all_questions_structure(self):
        """Test get_all_questions function and metadata"""
        questions = get_all_questions()
        
        # Should return 15 questions total (5 per module)
        assert len(questions) == 15
        
        # Each question should have module metadata
        for i, question in enumerate(questions):
            assert "module" in question
            assert "module_title" in question
            assert "global_index" in question
            assert question["global_index"] == i
            
            # Check module assignment
            if i < 5:
                assert question["module"] == "context"
            elif i < 10:
                assert question["module"] == "goals"
            else:
                assert question["module"] == "skills"
    
    def test_questions_backward_compatibility(self):
        """Test QUESTIONS constant and unique IDs"""
        # QUESTIONS constant should exist
        assert QUESTIONS is not None
        assert isinstance(QUESTIONS, list)
        assert len(QUESTIONS) == 15
        
        # All question IDs should be unique
        question_ids = [q["id"] for q in QUESTIONS]
        assert len(question_ids) == len(set(question_ids))
        
        # First question should have basic and new fields
        first_question = QUESTIONS[0]
        assert "id" in first_question
        assert "prompt" in first_question
        assert "module" in first_question
        assert "global_index" in first_question


if __name__ == "__main__":
    pytest.main([__file__])