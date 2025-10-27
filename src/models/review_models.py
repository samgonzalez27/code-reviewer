"""
Data models for code review results and issues.

These Pydantic models represent the output of the code review process,
including issues found, severity levels, and aggregated results.
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator

if TYPE_CHECKING:
    from src.models.code_fix_models import CodeFixResult


class Severity(str, Enum):
    """Severity levels for review issues."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(str, Enum):
    """Categories of code review issues."""
    STYLE = "style"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BEST_PRACTICES = "best_practices"
    DOCUMENTATION = "documentation"
    BUG_RISK = "bug_risk"


class ReviewIssue(BaseModel):
    """
    Represents a single issue found during code review.
    
    Each issue has a severity, category, description, and optional
    location information and suggestion for fixing.
    """
    severity: Severity = Field(description="Severity level of the issue")
    category: IssueCategory = Field(description="Category of the issue")
    message: str = Field(description="Human-readable description of the issue")
    
    # Location information
    line_number: Optional[int] = Field(
        default=None, description="Line number where issue occurs"
    )
    column_number: Optional[int] = Field(
        default=None, description="Column number where issue occurs"
    )
    code_snippet: Optional[str] = Field(
        default=None, description="Code snippet showing the issue"
    )
    
    # Suggestion for fixing
    suggestion: Optional[str] = Field(
        default=None, description="Suggested fix or improvement"
    )
    
    # Additional context
    rule_id: Optional[str] = Field(
        default=None, description="Identifier for the rule that triggered this issue"
    )
    documentation_url: Optional[str] = Field(
        default=None, description="URL to documentation about this issue"
    )
    
    def is_critical(self) -> bool:
        """Check if this issue is critical severity."""
        return self.severity == Severity.CRITICAL
    
    def is_high_priority(self) -> bool:
        """Check if this issue is high or critical severity."""
        return self.severity in (Severity.HIGH, Severity.CRITICAL)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "severity": "high",
                "category": "security",
                "message": "Hardcoded API key detected",
                "line_number": 42,
                "code_snippet": 'API_KEY = "sk-1234567890abcdef"',
                "suggestion": "Move API key to environment variable",
                "rule_id": "SEC001",
            }
        }
    )


class ReviewResult(BaseModel):
    """
    Aggregated results from code review.
    
    Contains all issues found, statistics, and overall quality score.
    """
    issues: List[ReviewIssue] = Field(default_factory=list, description="List of all issues found")
    
    # Statistics
    total_issues: int = Field(default=0, description="Total number of issues")
    critical_count: int = Field(default=0, description="Number of critical issues")
    high_count: int = Field(default=0, description="Number of high severity issues")
    medium_count: int = Field(default=0, description="Number of medium severity issues")
    low_count: int = Field(default=0, description="Number of low severity issues")
    info_count: int = Field(default=0, description="Number of info-level issues")
    
    # Overall assessment
    quality_score: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Overall quality score (0-100)"
    )
    passed: bool = Field(default=True, description="Whether the code passes review")
    
    # Metadata
    reviewer_name: str = Field(
        default="CodeReviewer",
        description="Name of the reviewer that generated this result"
    )
    review_timestamp: Optional[str] = Field(
        default=None, description="ISO timestamp of when review was performed"
    )
    
    # Auto-fix integration (optional)
    fix_result: Optional[Any] = Field(
        default=None,
        description="Optional CodeFixResult with generated fixes"
    )
    
    @field_validator('quality_score')
    @classmethod
    def validate_quality_score(cls, v: float) -> float:
        """Ensure quality score is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("Quality score must be between 0 and 100")
        return v
    
    def add_issue(self, issue: ReviewIssue) -> None:
        """
        Add an issue to the review result and update statistics.
        
        Args:
            issue: The ReviewIssue to add
        """
        self.issues.append(issue)
        self.total_issues += 1
        
        # Update severity counts
        if issue.severity == Severity.CRITICAL:
            self.critical_count += 1
        elif issue.severity == Severity.HIGH:
            self.high_count += 1
        elif issue.severity == Severity.MEDIUM:
            self.medium_count += 1
        elif issue.severity == Severity.LOW:
            self.low_count += 1
        elif issue.severity == Severity.INFO:
            self.info_count += 1
        
        # Update quality score and passed status
        self.quality_score = self.calculate_quality_score()
        self.passed = not self.has_critical_issues()
    
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return self.critical_count > 0
    
    def has_high_priority_issues(self) -> bool:
        """Check if there are any high or critical issues."""
        return (self.critical_count + self.high_count) > 0
    
    def get_issues_by_severity(self, severity: Severity) -> List[ReviewIssue]:
        """
        Get all issues of a specific severity.
        
        Args:
            severity: The severity level to filter by
            
        Returns:
            List of issues with the specified severity
        """
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_category(self, category: IssueCategory) -> List[ReviewIssue]:
        """
        Get all issues of a specific category.
        
        Args:
            category: The category to filter by
            
        Returns:
            List of issues in the specified category
        """
        return [issue for issue in self.issues if issue.category == category]
    
    def calculate_quality_score(self) -> float:
        """
        Calculate quality score based on issues found.
        
        Formula: Start at 100, deduct points based on severity:
        - Critical: -20 points
        - High: -10 points
        - Medium: -5 points
        - Low: -2 points
        - Info: -1 point
        
        Returns:
            Quality score (0-100)
        """
        score = 100.0
        score -= self.critical_count * 20
        score -= self.high_count * 10
        score -= self.medium_count * 5
        score -= self.low_count * 2
        score -= self.info_count * 1
        
        return max(0.0, min(100.0, score))
    
    def update_statistics(self) -> None:
        """Recalculate all statistics based on current issues."""
        self.total_issues = len(self.issues)
        self.critical_count = sum(1 for i in self.issues if i.severity == Severity.CRITICAL)
        self.high_count = sum(1 for i in self.issues if i.severity == Severity.HIGH)
        self.medium_count = sum(1 for i in self.issues if i.severity == Severity.MEDIUM)
        self.low_count = sum(1 for i in self.issues if i.severity == Severity.LOW)
        self.info_count = sum(1 for i in self.issues if i.severity == Severity.INFO)
        self.quality_score = self.calculate_quality_score()
        self.passed = not self.has_critical_issues()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the review results.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            "total_issues": self.total_issues,
            "quality_score": self.quality_score,
            "passed": self.passed,
            "severity_breakdown": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
            },
            "has_critical": self.has_critical_issues(),
        }
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "issues": [
                    {
                        "severity": "high",
                        "category": "security",
                        "message": "Hardcoded API key detected",
                        "line_number": 42,
                    }
                ],
                "total_issues": 1,
                "critical_count": 0,
                "high_count": 1,
                "medium_count": 0,
                "low_count": 0,
                "info_count": 0,
                "quality_score": 90.0,
                "passed": True,
                "reviewer_name": "SecurityReviewer",
            }
        }
    )
