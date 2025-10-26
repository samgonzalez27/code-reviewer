"""
Unit tests for code fix data models.

Tests the Pydantic models that represent code fixes, fix suggestions,
and fix results.
"""
import pytest
from pydantic import ValidationError

from src.models.code_fix_models import (
    CodeFix,
    FixStatus,
    FixConfidence,
    CodeFixResult,
)
from src.models.review_models import Severity, IssueCategory


# ============================================================================
# Test FixStatus Enum
# ============================================================================

class TestFixStatusEnum:
    """Test FixStatus enumeration."""
    
    def test_fix_status_values(self):
        """FixStatus should have expected values."""
        assert FixStatus.SUGGESTED == "suggested"
        assert FixStatus.APPLIED == "applied"
        assert FixStatus.REJECTED == "rejected"
        assert FixStatus.PENDING == "pending"


# ============================================================================
# Test FixConfidence Enum
# ============================================================================

class TestFixConfidenceEnum:
    """Test FixConfidence enumeration."""
    
    def test_fix_confidence_values(self):
        """FixConfidence should have expected confidence levels."""
        assert FixConfidence.LOW == "low"
        assert FixConfidence.MEDIUM == "medium"
        assert FixConfidence.HIGH == "high"
        assert FixConfidence.VERIFIED == "verified"


# ============================================================================
# Test CodeFix Model
# ============================================================================

class TestCodeFixModel:
    """Test CodeFix data model."""
    
    def test_code_fix_minimal_creation(self):
        """Should create CodeFix with minimal required fields."""
        fix = CodeFix(
            issue_description="Missing type hints",
            original_code="def hello():",
            fixed_code="def hello() -> None:",
            line_start=1,
            line_end=1
        )
        
        assert fix.issue_description == "Missing type hints"
        assert fix.original_code == "def hello():"
        assert fix.fixed_code == "def hello() -> None:"
        assert fix.line_start == 1
        assert fix.line_end == 1
    
    def test_code_fix_with_full_fields(self):
        """Should create CodeFix with all optional fields."""
        fix = CodeFix(
            issue_description="Security vulnerability",
            original_code="password = 'admin123'",
            fixed_code="password = os.getenv('PASSWORD')",
            line_start=5,
            line_end=5,
            explanation="Hardcoded credentials should be moved to environment variables",
            confidence=FixConfidence.HIGH,
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            status=FixStatus.SUGGESTED,
            diff="- password = 'admin123'\n+ password = os.getenv('PASSWORD')"
        )
        
        assert fix.explanation == "Hardcoded credentials should be moved to environment variables"
        assert fix.confidence == FixConfidence.HIGH
        assert fix.severity == Severity.CRITICAL
        assert fix.category == IssueCategory.SECURITY
        assert fix.status == FixStatus.SUGGESTED
        assert fix.diff is not None
    
    def test_code_fix_default_values(self):
        """Should use appropriate defaults for optional fields."""
        fix = CodeFix(
            issue_description="Test issue",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1
        )
        
        assert fix.confidence == FixConfidence.MEDIUM
        assert fix.severity == Severity.INFO
        assert fix.category == IssueCategory.BEST_PRACTICES
        assert fix.status == FixStatus.SUGGESTED
        assert fix.explanation is None
        assert fix.diff is None
    
    def test_code_fix_requires_issue_description(self):
        """Should require issue_description field."""
        with pytest.raises(ValidationError):
            CodeFix(
                original_code="old",
                fixed_code="new",
                line_start=1,
                line_end=1
            )
    
    def test_code_fix_requires_original_code(self):
        """Should require original_code field."""
        with pytest.raises(ValidationError):
            CodeFix(
                issue_description="Test",
                fixed_code="new",
                line_start=1,
                line_end=1
            )
    
    def test_code_fix_requires_fixed_code(self):
        """Should require fixed_code field."""
        with pytest.raises(ValidationError):
            CodeFix(
                issue_description="Test",
                original_code="old",
                line_start=1,
                line_end=1
            )
    
    def test_code_fix_requires_line_start(self):
        """Should require line_start field."""
        with pytest.raises(ValidationError):
            CodeFix(
                issue_description="Test",
                original_code="old",
                fixed_code="new",
                line_end=1
            )
    
    def test_code_fix_requires_line_end(self):
        """Should require line_end field."""
        with pytest.raises(ValidationError):
            CodeFix(
                issue_description="Test",
                original_code="old",
                fixed_code="new",
                line_start=1
            )
    
    def test_code_fix_line_numbers_must_be_positive(self):
        """Line numbers should be positive integers."""
        with pytest.raises(ValidationError):
            CodeFix(
                issue_description="Test",
                original_code="old",
                fixed_code="new",
                line_start=0,
                line_end=1
            )
    
    def test_code_fix_multi_line_range(self):
        """Should support multi-line code fixes."""
        fix = CodeFix(
            issue_description="Refactor function",
            original_code="def foo():\n    pass\n    pass",
            fixed_code="def foo() -> None:\n    pass",
            line_start=10,
            line_end=12
        )
        
        assert fix.line_start == 10
        assert fix.line_end == 12
        assert "\n" in fix.original_code
        assert "\n" in fix.fixed_code
    
    def test_code_fix_is_high_confidence(self):
        """Should identify high confidence fixes."""
        fix_high = CodeFix(
            issue_description="Test",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.HIGH
        )
        
        fix_verified = CodeFix(
            issue_description="Test",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.VERIFIED
        )
        
        fix_medium = CodeFix(
            issue_description="Test",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.MEDIUM
        )
        
        assert fix_high.is_high_confidence() is True
        assert fix_verified.is_high_confidence() is True
        assert fix_medium.is_high_confidence() is False
    
    def test_code_fix_is_critical(self):
        """Should identify critical severity fixes."""
        fix = CodeFix(
            issue_description="Security issue",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1,
            severity=Severity.CRITICAL
        )
        
        assert fix.is_critical() is True
    
    def test_code_fix_apply_status_change(self):
        """Should allow changing fix status."""
        fix = CodeFix(
            issue_description="Test",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1
        )
        
        assert fix.status == FixStatus.SUGGESTED
        
        # Simulate applying the fix
        fix.status = FixStatus.APPLIED
        assert fix.status == FixStatus.APPLIED


# ============================================================================
# Test CodeFixResult Model
# ============================================================================

class TestCodeFixResultModel:
    """Test CodeFixResult data model."""
    
    def test_code_fix_result_creation(self):
        """Should create CodeFixResult with default values."""
        result = CodeFixResult()
        
        assert result.fixes == []
        assert result.total_fixes == 0
        assert result.high_confidence_count == 0
        assert result.medium_confidence_count == 0
        assert result.low_confidence_count == 0
        assert result.applied_count == 0
        assert result.success is True
        assert result.fixer_name == "CodeFixer"
    
    def test_code_fix_result_add_fix(self):
        """Should add fix and update statistics."""
        result = CodeFixResult()
        
        fix = CodeFix(
            issue_description="Test issue",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.HIGH
        )
        
        result.add_fix(fix)
        
        assert len(result.fixes) == 1
        assert result.total_fixes == 1
        assert result.high_confidence_count == 1
    
    def test_code_fix_result_add_multiple_fixes(self):
        """Should handle multiple fixes with different confidence levels."""
        result = CodeFixResult()
        
        fix1 = CodeFix(
            issue_description="Issue 1",
            original_code="old1",
            fixed_code="new1",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.HIGH
        )
        
        fix2 = CodeFix(
            issue_description="Issue 2",
            original_code="old2",
            fixed_code="new2",
            line_start=2,
            line_end=2,
            confidence=FixConfidence.MEDIUM
        )
        
        fix3 = CodeFix(
            issue_description="Issue 3",
            original_code="old3",
            fixed_code="new3",
            line_start=3,
            line_end=3,
            confidence=FixConfidence.LOW
        )
        
        result.add_fix(fix1)
        result.add_fix(fix2)
        result.add_fix(fix3)
        
        assert result.total_fixes == 3
        assert result.high_confidence_count == 1
        assert result.medium_confidence_count == 1
        assert result.low_confidence_count == 0  # LOW confidence shouldn't be counted separately
    
    def test_code_fix_result_update_statistics(self):
        """Should recalculate statistics from current fixes."""
        result = CodeFixResult()
        
        # Add fixes directly to list (bypass add_fix)
        result.fixes = [
            CodeFix(
                issue_description="Fix 1",
                original_code="old",
                fixed_code="new",
                line_start=1,
                line_end=1,
                confidence=FixConfidence.HIGH,
                status=FixStatus.APPLIED
            ),
            CodeFix(
                issue_description="Fix 2",
                original_code="old",
                fixed_code="new",
                line_start=2,
                line_end=2,
                confidence=FixConfidence.MEDIUM,
                status=FixStatus.SUGGESTED
            ),
        ]
        
        result.update_statistics()
        
        assert result.total_fixes == 2
        assert result.high_confidence_count == 1
        assert result.medium_confidence_count == 1
        assert result.applied_count == 1
    
    def test_code_fix_result_get_fixes_by_confidence(self):
        """Should filter fixes by confidence level."""
        result = CodeFixResult()
        
        high_fix = CodeFix(
            issue_description="High",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.HIGH
        )
        
        medium_fix = CodeFix(
            issue_description="Medium",
            original_code="old",
            fixed_code="new",
            line_start=2,
            line_end=2,
            confidence=FixConfidence.MEDIUM
        )
        
        result.add_fix(high_fix)
        result.add_fix(medium_fix)
        
        high_fixes = result.get_fixes_by_confidence(FixConfidence.HIGH)
        assert len(high_fixes) == 1
        assert high_fixes[0].issue_description == "High"
        
        medium_fixes = result.get_fixes_by_confidence(FixConfidence.MEDIUM)
        assert len(medium_fixes) == 1
        assert medium_fixes[0].issue_description == "Medium"
    
    def test_code_fix_result_get_fixes_by_status(self):
        """Should filter fixes by status."""
        result = CodeFixResult()
        
        suggested_fix = CodeFix(
            issue_description="Suggested",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1,
            status=FixStatus.SUGGESTED
        )
        
        applied_fix = CodeFix(
            issue_description="Applied",
            original_code="old",
            fixed_code="new",
            line_start=2,
            line_end=2,
            status=FixStatus.APPLIED
        )
        
        result.add_fix(suggested_fix)
        result.add_fix(applied_fix)
        
        suggested_fixes = result.get_fixes_by_status(FixStatus.SUGGESTED)
        assert len(suggested_fixes) == 1
        assert suggested_fixes[0].issue_description == "Suggested"
    
    def test_code_fix_result_get_high_confidence_fixes(self):
        """Should get only high and verified confidence fixes."""
        result = CodeFixResult()
        
        result.add_fix(CodeFix(
            issue_description="High",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.HIGH
        ))
        
        result.add_fix(CodeFix(
            issue_description="Verified",
            original_code="old",
            fixed_code="new",
            line_start=2,
            line_end=2,
            confidence=FixConfidence.VERIFIED
        ))
        
        result.add_fix(CodeFix(
            issue_description="Medium",
            original_code="old",
            fixed_code="new",
            line_start=3,
            line_end=3,
            confidence=FixConfidence.MEDIUM
        ))
        
        high_confidence = result.get_high_confidence_fixes()
        assert len(high_confidence) == 2
    
    def test_code_fix_result_has_fixes(self):
        """Should indicate if result has any fixes."""
        result = CodeFixResult()
        assert result.has_fixes() is False
        
        result.add_fix(CodeFix(
            issue_description="Test",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1
        ))
        
        assert result.has_fixes() is True
    
    def test_code_fix_result_get_summary(self):
        """Should provide summary statistics."""
        result = CodeFixResult()
        
        result.add_fix(CodeFix(
            issue_description="Fix 1",
            original_code="old",
            fixed_code="new",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.HIGH,
            status=FixStatus.APPLIED
        ))
        
        result.add_fix(CodeFix(
            issue_description="Fix 2",
            original_code="old",
            fixed_code="new",
            line_start=2,
            line_end=2,
            confidence=FixConfidence.MEDIUM
        ))
        
        summary = result.get_summary()
        
        assert summary["total_fixes"] == 2
        assert summary["high_confidence_count"] == 1
        assert summary["medium_confidence_count"] == 1
        assert summary["applied_count"] == 1
        assert summary["success"] is True
    
    def test_code_fix_result_error_handling(self):
        """Should handle errors in fix generation."""
        result = CodeFixResult(
            success=False,
            error_message="API timeout occurred"
        )
        
        assert result.success is False
        assert result.error_message == "API timeout occurred"
        assert result.total_fixes == 0
