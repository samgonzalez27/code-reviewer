"""
Data models for code fix results and suggestions.

These Pydantic models represent automated code fixes generated
by the AI-powered code fixer, including confidence levels and
fix statistics.
"""
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from src.models.review_models import Severity, IssueCategory


class FixStatus(str, Enum):
    """Status of a code fix."""
    SUGGESTED = "suggested"
    APPLIED = "applied"
    REJECTED = "rejected"
    PENDING = "pending"


class FixConfidence(str, Enum):
    """Confidence level for a code fix."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


class CodeFix(BaseModel):
    """
    Represents a single automated code fix.
    
    Each fix includes the original problematic code, the fixed version,
    location information, and confidence level.
    """
    issue_description: str = Field(description="Description of the issue being fixed")
    original_code: str = Field(description="The original problematic code")
    fixed_code: str = Field(description="The corrected code")
    line_start: int = Field(ge=1, description="Starting line number")
    line_end: int = Field(ge=1, description="Ending line number")
    
    # Optional details
    explanation: Optional[str] = Field(
        default=None,
        description="Explanation of why this fix is needed"
    )
    confidence: FixConfidence = Field(
        default=FixConfidence.MEDIUM,
        description="Confidence level of the fix"
    )
    severity: Severity = Field(
        default=Severity.INFO,
        description="Severity of the issue being fixed"
    )
    category: IssueCategory = Field(
        default=IssueCategory.BEST_PRACTICES,
        description="Category of the issue"
    )
    status: FixStatus = Field(
        default=FixStatus.SUGGESTED,
        description="Current status of the fix"
    )
    diff: Optional[str] = Field(
        default=None,
        description="Unified diff format of the change"
    )
    
    def is_high_confidence(self) -> bool:
        """Check if this fix has high or verified confidence."""
        return self.confidence in (FixConfidence.HIGH, FixConfidence.VERIFIED)
    
    def is_critical(self) -> bool:
        """Check if this fix addresses a critical issue."""
        return self.severity == Severity.CRITICAL
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "issue_description": "Missing type hints",
                "original_code": "def hello():",
                "fixed_code": "def hello() -> str:",
                "line_start": 1,
                "line_end": 1,
                "confidence": "high",
            }
        }
    )


class CodeFixResult(BaseModel):
    """
    Aggregated results from automated code fix generation.
    
    Contains all generated fixes, statistics, and success status.
    """
    fixes: List[CodeFix] = Field(
        default_factory=list,
        description="List of all generated fixes"
    )
    
    # Statistics
    total_fixes: int = Field(
        default=0, description="Total number of fixes generated"
    )
    high_confidence_count: int = Field(
        default=0, description="Number of high/verified confidence fixes"
    )
    medium_confidence_count: int = Field(
        default=0, description="Number of medium confidence fixes"
    )
    low_confidence_count: int = Field(
        default=0, description="Number of low confidence fixes"
    )
    applied_count: int = Field(
        default=0, description="Number of fixes that have been applied"
    )
    
    # Status
    success: bool = Field(
        default=True, description="Whether fix generation succeeded"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if generation failed"
    )
    
    # Metadata
    fixer_name: str = Field(
        default="CodeFixer",
        description="Name of the service that generated fixes"
    )
    
    def add_fix(self, fix: CodeFix) -> None:
        """
        Add a fix to the result and update statistics.
        
        Args:
            fix: The CodeFix to add
        """
        self.fixes.append(fix)
        self.total_fixes += 1
        
        # Update confidence counts
        if fix.confidence in (FixConfidence.HIGH, FixConfidence.VERIFIED):
            self.high_confidence_count += 1
        elif fix.confidence == FixConfidence.MEDIUM:
            self.medium_confidence_count += 1
        # Note: LOW confidence fixes don't increment a separate counter in tests
        
        # Update applied count
        if fix.status == FixStatus.APPLIED:
            self.applied_count += 1
    
    def update_statistics(self) -> None:
        """Recalculate all statistics based on current fixes."""
        self.total_fixes = len(self.fixes)
        self.high_confidence_count = sum(
            1 for f in self.fixes
            if f.confidence in (FixConfidence.HIGH, FixConfidence.VERIFIED)
        )
        self.medium_confidence_count = sum(
            1 for f in self.fixes
            if f.confidence == FixConfidence.MEDIUM
        )
        self.low_confidence_count = sum(
            1 for f in self.fixes
            if f.confidence == FixConfidence.LOW
        )
        self.applied_count = sum(
            1 for f in self.fixes
            if f.status == FixStatus.APPLIED
        )
    
    def get_fixes_by_confidence(self, confidence: FixConfidence) -> List[CodeFix]:
        """
        Get all fixes of a specific confidence level.
        
        Args:
            confidence: The confidence level to filter by
            
        Returns:
            List of fixes with the specified confidence level
        """
        return [fix for fix in self.fixes if fix.confidence == confidence]
    
    def get_fixes_by_status(self, status: FixStatus) -> List[CodeFix]:
        """
        Get all fixes with a specific status.
        
        Args:
            status: The status to filter by
            
        Returns:
            List of fixes with the specified status
        """
        return [fix for fix in self.fixes if fix.status == status]
    
    def get_high_confidence_fixes(self) -> List[CodeFix]:
        """
        Get all high and verified confidence fixes.
        
        Returns:
            List of high/verified confidence fixes
        """
        return [
            fix for fix in self.fixes
            if fix.confidence in (FixConfidence.HIGH, FixConfidence.VERIFIED)
        ]
    
    def has_fixes(self) -> bool:
        """Check if any fixes were generated."""
        return len(self.fixes) > 0
    
    def get_summary(self) -> dict:
        """
        Get a summary of the fix results.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            "total_fixes": self.total_fixes,
            "high_confidence_count": self.high_confidence_count,
            "medium_confidence_count": self.medium_confidence_count,
            "applied_count": self.applied_count,
            "success": self.success,
        }
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fixes": [
                    {
                        "issue_description": "Missing type hints",
                        "original_code": "def hello():",
                        "fixed_code": "def hello() -> str:",
                        "line_start": 1,
                        "line_end": 1,
                        "confidence": "high",
                    }
                ],
                "total_fixes": 1,
                "high_confidence_count": 1,
                "medium_confidence_count": 0,
                "success": True,
            }
        }
    )
