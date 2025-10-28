"""
Unit tests for prompt generation models.
"""
import pytest
from pydantic import ValidationError
from src.models.prompt_models import PromptSuggestion, PromptGenerationResult
from src.models.review_models import IssueCategory


class TestPromptSuggestion:
    """Test PromptSuggestion model."""
    
    def test_create_valid_prompt_suggestion(self):
        """Should create a valid prompt suggestion."""
        prompt = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix the security vulnerabilities in your code",
            issue_count=3,
            severity_summary="2 high, 1 medium",
            line_references=[42, 58, 103]
        )
        
        assert prompt.category == IssueCategory.SECURITY
        assert prompt.prompt_text == "Fix the security vulnerabilities in your code"
        assert prompt.issue_count == 3
        assert prompt.severity_summary == "2 high, 1 medium"
        assert prompt.line_references == [42, 58, 103]
    
    def test_prompt_suggestion_with_minimal_fields(self):
        """Should create prompt with only required fields."""
        prompt = PromptSuggestion(
            category=IssueCategory.STYLE,
            prompt_text="Improve code style",
            issue_count=5,
            severity_summary="5 low"
        )
        
        assert prompt.category == IssueCategory.STYLE
        assert prompt.line_references == []
    
    def test_prompt_text_trimmed(self):
        """Prompt text should be trimmed of whitespace."""
        prompt = PromptSuggestion(
            category=IssueCategory.COMPLEXITY,
            prompt_text="  Reduce complexity  ",
            issue_count=2,
            severity_summary="2 medium"
        )
        
        assert prompt.prompt_text == "Reduce complexity"
    
    def test_empty_prompt_text_raises_error(self):
        """Should reject empty prompt text."""
        with pytest.raises(ValidationError):
            PromptSuggestion(
                category=IssueCategory.SECURITY,
                prompt_text="",
                issue_count=1,
                severity_summary="1 high"
            )
    
    def test_whitespace_only_prompt_text_raises_error(self):
        """Should reject whitespace-only prompt text."""
        with pytest.raises(ValidationError):
            PromptSuggestion(
                category=IssueCategory.SECURITY,
                prompt_text="   ",
                issue_count=1,
                severity_summary="1 high"
            )
    
    def test_negative_issue_count_raises_error(self):
        """Should reject negative issue count."""
        with pytest.raises(ValidationError):
            PromptSuggestion(
                category=IssueCategory.SECURITY,
                prompt_text="Fix issues",
                issue_count=-1,
                severity_summary="invalid"
            )
    
    def test_zero_issue_count_raises_error(self):
        """Should reject zero issue count."""
        with pytest.raises(ValidationError):
            PromptSuggestion(
                category=IssueCategory.SECURITY,
                prompt_text="Fix issues",
                issue_count=0,
                severity_summary="none"
            )


class TestPromptGenerationResult:
    """Test PromptGenerationResult model."""
    
    def test_create_empty_result(self):
        """Should create an empty result."""
        result = PromptGenerationResult()
        
        assert result.prompts == []
        assert result.total_issues_covered == 0
        assert result.categories_covered == []
        assert result.language == "python"
        assert not result.has_prompts()
    
    def test_create_result_with_language(self):
        """Should create result with specified language."""
        result = PromptGenerationResult(language="javascript")
        
        assert result.language == "javascript"
    
    def test_add_single_prompt(self):
        """Should add a single prompt to result."""
        result = PromptGenerationResult()
        prompt = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix security issues",
            issue_count=3,
            severity_summary="3 high"
        )
        
        result.add_prompt(prompt)
        
        assert len(result.prompts) == 1
        assert result.total_issues_covered == 3
        assert IssueCategory.SECURITY in result.categories_covered
        assert result.has_prompts()
    
    def test_add_multiple_prompts(self):
        """Should add multiple prompts to result."""
        result = PromptGenerationResult()
        
        prompt1 = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix security issues",
            issue_count=3,
            severity_summary="3 high"
        )
        
        prompt2 = PromptSuggestion(
            category=IssueCategory.STYLE,
            prompt_text="Improve code style",
            issue_count=5,
            severity_summary="5 low"
        )
        
        result.add_prompt(prompt1)
        result.add_prompt(prompt2)
        
        assert len(result.prompts) == 2
        assert result.total_issues_covered == 8
        assert IssueCategory.SECURITY in result.categories_covered
        assert IssueCategory.STYLE in result.categories_covered
    
    def test_add_prompt_updates_total_issues(self):
        """Adding prompts should update total issues covered."""
        result = PromptGenerationResult()
        
        for i in range(3):
            prompt = PromptSuggestion(
                category=list(IssueCategory)[i],
                prompt_text=f"Fix {list(IssueCategory)[i].value} issues",
                issue_count=i + 1,
                severity_summary=f"{i+1} issues"
            )
            result.add_prompt(prompt)
        
        assert result.total_issues_covered == 6  # 1 + 2 + 3
    
    def test_cannot_add_more_than_five_prompts(self):
        """Should raise error when adding more than 5 prompts."""
        result = PromptGenerationResult()
        
        # Add 5 prompts
        categories = list(IssueCategory)[:5]
        for category in categories:
            prompt = PromptSuggestion(
                category=category,
                prompt_text=f"Fix {category.value} issues",
                issue_count=1,
                severity_summary="1 issue"
            )
            result.add_prompt(prompt)
        
        # Try to add 6th prompt
        with pytest.raises(ValueError, match="Cannot add more than 5 prompts"):
            prompt6 = PromptSuggestion(
                category=IssueCategory.BUG_RISK,
                prompt_text="Fix bugs",
                issue_count=1,
                severity_summary="1 issue"
            )
            result.add_prompt(prompt6)
    
    def test_validation_rejects_more_than_five_prompts(self):
        """Pydantic validation should reject more than 5 prompts."""
        prompts = [
            PromptSuggestion(
                category=cat,
                prompt_text=f"Fix {cat.value}",
                issue_count=1,
                severity_summary="1 issue"
            )
            for cat in list(IssueCategory)[:6]
        ]
        
        with pytest.raises(ValidationError, match="Maximum 5 prompts allowed"):
            PromptGenerationResult(prompts=prompts)
    
    def test_get_prompt_by_category_found(self):
        """Should retrieve prompt by category."""
        result = PromptGenerationResult()
        
        security_prompt = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix security issues",
            issue_count=2,
            severity_summary="2 high"
        )
        
        style_prompt = PromptSuggestion(
            category=IssueCategory.STYLE,
            prompt_text="Fix style issues",
            issue_count=3,
            severity_summary="3 low"
        )
        
        result.add_prompt(security_prompt)
        result.add_prompt(style_prompt)
        
        found = result.get_prompt_by_category(IssueCategory.SECURITY)
        
        assert found is not None
        assert found.category == IssueCategory.SECURITY
        assert found.prompt_text == "Fix security issues"
    
    def test_get_prompt_by_category_not_found(self):
        """Should return None for category not in results."""
        result = PromptGenerationResult()
        
        prompt = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix security issues",
            issue_count=2,
            severity_summary="2 high"
        )
        result.add_prompt(prompt)
        
        found = result.get_prompt_by_category(IssueCategory.PERFORMANCE)
        
        assert found is None
    
    def test_categories_covered_no_duplicates(self):
        """Categories covered should not have duplicates even if same category added twice."""
        result = PromptGenerationResult()
        
        # This shouldn't happen in practice, but test the model behavior
        prompt1 = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="First security prompt",
            issue_count=2,
            severity_summary="2 high"
        )
        
        result.add_prompt(prompt1)
        
        # Manually add another security prompt to test
        prompt2 = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Second security prompt",
            issue_count=1,
            severity_summary="1 medium"
        )
        
        result.prompts.append(prompt2)  # Bypass add_prompt to test edge case
        result.total_issues_covered += prompt2.issue_count
        
        # Should still only have one SECURITY category
        assert result.categories_covered.count(IssueCategory.SECURITY) == 1
    
    def test_validate_max_prompts_accepts_valid_list(self):
        """Validator should accept and return valid lists of 5 or fewer prompts."""
        # Test that the validator returns the list when valid
        prompts = [
            PromptSuggestion(
                category=cat,
                prompt_text=f"Fix {cat.value}",
                issue_count=1,
                severity_summary="1 issue"
            )
            for cat in list(IssueCategory)[:5]
        ]
        
        # Call validator directly - should return the list unchanged
        result = PromptGenerationResult.validate_max_prompts(prompts)
        assert result == prompts
        assert len(result) == 5
