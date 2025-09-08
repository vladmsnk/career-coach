"""
Tests for the new modular questions structure
"""
import pytest
from app.domain.chat.questions import (
    INTERVIEW_MODULES,
    QUESTIONS,
    get_all_questions,
    get_question_by_global_index,
    get_module_questions,
    get_total_questions_count,
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
    
    def test_question_structure(self):
        """Test that each question has required fields"""
        for module_key, module_data in INTERVIEW_MODULES.items():
            for question in module_data["questions"]:
                # Required fields
                assert "id" in question
                assert "type" in question
                assert "prompt" in question
                
                # Check types
                assert isinstance(question["id"], str)
                assert isinstance(question["type"], str)
                assert isinstance(question["prompt"], str)
                
                # Check valid question types
                valid_types = {"string", "text", "number", "select", "multiselect", "range"}
                assert question["type"] in valid_types
                
                # Type-specific validations
                if question["type"] in ["select", "multiselect"]:
                    assert "options" in question
                    assert isinstance(question["options"], list)
                    assert len(question["options"]) > 0
                
                if question["type"] == "number":
                    assert "min" in question
                    assert "max" in question
                    assert isinstance(question["min"], int)
                    assert isinstance(question["max"], int)
                    assert question["min"] <= question["max"]
                
                if question["type"] == "range":
                    assert "min" in question
                    assert "max" in question
                    assert isinstance(question["min"], int)
                    assert isinstance(question["max"], int)
                    assert question["min"] < question["max"]
                    if "step" in question:
                        assert isinstance(question["step"], int)
                        assert question["step"] > 0
                
                if question["type"] in ["string", "text"]:
                    if "max_length" in question:
                        assert isinstance(question["max_length"], int)
                        assert question["max_length"] > 0


class TestUtilityFunctions:
    """Test utility functions for working with questions"""
    
    def test_get_all_questions(self):
        """Test get_all_questions function"""
        questions = get_all_questions()
        
        # Should return 15 questions total (5 per module)
        assert len(questions) == 15
        
        # Each question should have module metadata
        for i, question in enumerate(questions):
            assert "module" in question
            assert "module_title" in question
            assert "question_index_in_module" in question
            assert "global_index" in question
            
            # Check global index is correct
            assert question["global_index"] == i
            
            # Check module assignment
            if i < 5:
                assert question["module"] == "context"
                assert question["module_title"] == "Определение стартового контекста"
                assert question["question_index_in_module"] == i
            elif i < 10:
                assert question["module"] == "goals"
                assert question["module_title"] == "Определение целей"
                assert question["question_index_in_module"] == i - 5
            else:
                assert question["module"] == "skills"
                assert question["module_title"] == "Определение профессионального уровня"
                assert question["question_index_in_module"] == i - 10
    
    def test_get_question_by_global_index(self):
        """Test get_question_by_global_index function"""
        # Valid indices
        question_0 = get_question_by_global_index(0)
        assert question_0 is not None
        assert question_0["id"] == "current_sphere"
        assert question_0["module"] == "context"
        
        question_5 = get_question_by_global_index(5)
        assert question_5 is not None
        assert question_5["id"] == "target_sphere"
        assert question_5["module"] == "goals"
        
        question_14 = get_question_by_global_index(14)
        assert question_14 is not None
        assert question_14["id"] == "learning_goals"
        assert question_14["module"] == "skills"
        
        # Invalid indices
        assert get_question_by_global_index(-1) is None
        assert get_question_by_global_index(15) is None
        assert get_question_by_global_index(100) is None
    
    def test_get_module_questions(self):
        """Test get_module_questions function"""
        # Valid modules
        context_questions = get_module_questions("context")
        assert len(context_questions) == 5
        assert context_questions[0]["id"] == "current_sphere"
        
        goals_questions = get_module_questions("goals")
        assert len(goals_questions) == 5
        assert goals_questions[0]["id"] == "target_sphere"
        
        skills_questions = get_module_questions("skills")
        assert len(skills_questions) == 5
        assert skills_questions[0]["id"] == "current_skills"
        
        # Invalid module
        invalid_questions = get_module_questions("invalid")
        assert invalid_questions == []
    
    def test_get_total_questions_count(self):
        """Test get_total_questions_count function"""
        total = get_total_questions_count()
        assert total == 15
        assert total == len(get_all_questions())


class TestBackwardCompatibility:
    """Test backward compatibility with existing code"""
    
    def test_questions_constant_exists(self):
        """Test that QUESTIONS constant still exists"""
        assert QUESTIONS is not None
        assert isinstance(QUESTIONS, list)
        assert len(QUESTIONS) == 15
    
    def test_questions_constant_structure(self):
        """Test that QUESTIONS has the expected structure for backward compatibility"""
        # First question should still have basic fields
        first_question = QUESTIONS[0]
        assert "id" in first_question
        assert "prompt" in first_question
        
        # Should also have new metadata fields
        assert "module" in first_question
        assert "module_title" in first_question
        assert "global_index" in first_question
    
    def test_questions_ids_are_unique(self):
        """Test that all question IDs are unique"""
        question_ids = [q["id"] for q in QUESTIONS]
        assert len(question_ids) == len(set(question_ids))
    
    def test_specific_question_types(self):
        """Test specific question types for expected behavior"""
        # Find specific questions by ID
        questions_by_id = {q["id"]: q for q in QUESTIONS}
        
        # Test select questions
        current_sphere = questions_by_id["current_sphere"]
        assert current_sphere["type"] == "select"
        assert "options" in current_sphere
        assert "IT" in current_sphere["options"]
        
        # Test multiselect questions
        preferred_activities = questions_by_id["preferred_activities"]
        assert preferred_activities["type"] == "multiselect"
        assert "options" in preferred_activities
        assert len(preferred_activities["options"]) > 0
        
        # Test number questions
        years_in_sphere = questions_by_id["years_in_sphere"]
        assert years_in_sphere["type"] == "number"
        assert years_in_sphere["min"] == 0
        assert years_in_sphere["max"] == 50
        
        # Test range questions
        salary_expectations = questions_by_id["salary_expectations"]
        assert salary_expectations["type"] == "range"
        assert salary_expectations["min"] == 30000
        assert salary_expectations["max"] == 500000
        assert salary_expectations["step"] == 10000
        
        # Test text questions
        key_projects = questions_by_id["key_projects"]
        assert key_projects["type"] == "text"
        assert key_projects["max_length"] == 500


if __name__ == "__main__":
    pytest.main([__file__])
