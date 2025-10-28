"""
Data models for AI prompt generation.

These Pydantic models represent prompts generated for fixing code issues,
organized by category to help developers address problems effectively.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from src.models.review_models import IssueCategory


class PromptSuggestion(BaseModel):
    """
    Represents a single AI prompt suggestion for fixing code issues.
    
    Each prompt targets a specific category of issues and provides
    context-aware guidance following professional SWE standards.
    """
    category: IssueCategory = Field(description="Category of issues this prompt addresses")
    prompt_text: str = Field(description="The generated prompt text for Copilot")
    issue_count: int = Field(ge=1, description="Number of issues in this category")
    severity_summary: str = Field(
        description="Summary of severity levels (e.g., '2 high, 3 medium')"
    )
    line_references: List[int] = Field(
        default_factory=list,
        description="Line numbers where issues occur"
    )
    
    @field_validator('prompt_text')
    @classmethod
    def validate_prompt_not_empty(cls, v: str) -> str:
        """Ensure prompt text is not empty."""
        if not v or not v.strip():
            raise ValueError("Prompt text cannot be empty")
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "security",
                "prompt_text": "Fix security vulnerabilities in the code...",
                "issue_count": 3,
                "severity_summary": "2 high, 1 medium",
                "line_references": [42, 58, 103]
            }
        }
    }


class PromptGenerationResult(BaseModel):
    """
    Collection of generated prompts for code issue remediation.
    
    Contains up to 5 prompts, one per issue category, ordered by
    priority (severity and issue count).
    """
    prompts: List[PromptSuggestion] = Field(
        default_factory=list,
        description="List of generated prompts (max 5)"
    )
    total_issues_covered: int = Field(
        default=0,
        ge=0,
        description="Total number of issues covered by all prompts"
    )
    categories_covered: List[IssueCategory] = Field(
        default_factory=list,
        description="List of categories covered by prompts"
    )
    language: str = Field(
        default="python",
        description="Programming language context for prompts"
    )
    
    @field_validator('prompts')
    @classmethod
    def validate_max_prompts(cls, v: List[PromptSuggestion]) -> List[PromptSuggestion]:
        """Ensure no more than 5 prompts."""
        if len(v) > 5:
            raise ValueError("Maximum 5 prompts allowed")
        return v
    
    def add_prompt(self, prompt: PromptSuggestion) -> None:
        """
        Add a prompt suggestion to the result.
        
        Args:
            prompt: The prompt to add
            
        Raises:
            ValueError: If adding would exceed 5 prompts
        """
        if len(self.prompts) >= 5:
            raise ValueError("Cannot add more than 5 prompts")
        
        self.prompts.append(prompt)
        self.total_issues_covered += prompt.issue_count
        
        if prompt.category not in self.categories_covered:
            self.categories_covered.append(prompt.category)
    
    def get_prompt_by_category(self, category: IssueCategory) -> Optional[PromptSuggestion]:
        """
        Get prompt for a specific category.
        
        Args:
            category: The issue category to find
            
        Returns:
            The prompt for that category, or None if not found
        """
        for prompt in self.prompts:
            if prompt.category == category:
                return prompt
        return None
    
    def has_prompts(self) -> bool:
        """Check if any prompts were generated."""
        return len(self.prompts) > 0
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "prompts": [
                    {
                        "category": "security",
                        "prompt_text": "Fix security issues...",
                        "issue_count": 3,
                        "severity_summary": "2 high, 1 medium",
                        "line_references": [42, 58]
                    }
                ],
                "total_issues_covered": 3,
                "categories_covered": ["security"],
                "language": "python"
            }
        }
    }
