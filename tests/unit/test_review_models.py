"""
Unit tests for review data models.

This module tests the ReviewResult, ReviewIssue, Severity, and IssueCategory models.
"""
import pytest
from datetime import datetime
from src.models.review_models import (
    ReviewResult,
    ReviewIssue,
    Severity,
    IssueCategory,
)


class TestReviewIssue:
    """Test ReviewIssue model."""
    
    def test_create_basic_issue(self):
        """Test creating a basic ReviewIssue."""
        issue = ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="Test issue"
        )
        
        assert issue.severity == Severity.HIGH
        assert issue.category == IssueCategory.SECURITY
        assert issue.message == "Test issue"
    
    def test_issue_with_location_info(self):
        """Test ReviewIssue with location information."""
        issue = ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.STYLE,
            message="Style issue",
            line_number=42,
            column_number=10,
            code_snippet="bad_code = 1"
        )
        
        assert issue.line_number == 42
        assert issue.column_number == 10
        assert issue.code_snippet == "bad_code = 1"
    
    def test_issue_with_suggestion(self):
        """Test ReviewIssue with suggestion."""
        issue = ReviewIssue(
            severity=Severity.LOW,
            category=IssueCategory.BEST_PRACTICES,
            message="Use better naming",
            suggestion="Rename to descriptive_name"
        )
        
        assert issue.suggestion == "Rename to descriptive_name"
    
    def test_issue_with_rule_id_and_docs(self):
        """Test ReviewIssue with rule ID and documentation URL."""
        issue = ReviewIssue(
            severity=Severity.INFO,
            category=IssueCategory.DOCUMENTATION,
            message="Missing docstring",
            rule_id="DOC001",
            documentation_url="https://docs.example.com/DOC001"
        )
        
        assert issue.rule_id == "DOC001"
        assert issue.documentation_url == "https://docs.example.com/DOC001"
    
    def test_is_critical_method(self):
        """Test is_critical method."""
        critical_issue = ReviewIssue(
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            message="Critical"
        )
        high_issue = ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="High"
        )
        
        assert critical_issue.is_critical() is True
        assert high_issue.is_critical() is False
    
    def test_is_high_priority_method(self):
        """Test is_high_priority method."""
        critical_issue = ReviewIssue(
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            message="Critical"
        )
        high_issue = ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="High"
        )
        medium_issue = ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.STYLE,
            message="Medium"
        )
        
        assert critical_issue.is_high_priority() is True
        assert high_issue.is_high_priority() is True
        assert medium_issue.is_high_priority() is False


class TestReviewResultCreation:
    """Test ReviewResult creation and basic properties."""
    
    def test_create_empty_result(self):
        """Test creating an empty ReviewResult."""
        result = ReviewResult()
        
        assert result.total_issues == 0
        assert result.critical_count == 0
        assert result.high_count == 0
        assert result.medium_count == 0
        assert result.low_count == 0
        assert result.info_count == 0
        assert result.quality_score == 100.0
        assert result.passed is True
        assert len(result.issues) == 0
    
    def test_result_with_custom_reviewer_name(self):
        """Test ReviewResult with custom reviewer name."""
        result = ReviewResult(reviewer_name="TestReviewer")
        
        assert result.reviewer_name == "TestReviewer"
    
    def test_result_with_timestamp(self):
        """Test ReviewResult with timestamp."""
        timestamp = datetime.now().isoformat()
        result = ReviewResult(review_timestamp=timestamp)
        
        assert result.review_timestamp == timestamp
    
    def test_quality_score_validation(self):
        """Test that quality score is validated."""
        # Pydantic V2 validates at the field level, so we check for validation error
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError, match="less than or equal to 100"):
            ReviewResult(quality_score=150.0)
        
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            ReviewResult(quality_score=-10.0)
    
    def test_quality_score_validator_method_directly(self):
        """Test the validator method directly to cover the ValueError path."""
        # This tests the actual validator logic beyond Pydantic's field constraints
        with pytest.raises(ValueError, match="between 0 and 100"):
            ReviewResult.validate_quality_score(150.0)
        
        with pytest.raises(ValueError, match="between 0 and 100"):
            ReviewResult.validate_quality_score(-10.0)
        
        # Test valid value returns correctly
        assert ReviewResult.validate_quality_score(50.0) == 50.0
        assert ReviewResult.validate_quality_score(0.0) == 0.0
        assert ReviewResult.validate_quality_score(100.0) == 100.0


class TestReviewResultAddIssue:
    """Test adding issues to ReviewResult."""
    
    def test_add_single_issue(self):
        """Test adding a single issue."""
        result = ReviewResult()
        issue = ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="Security issue"
        )
        
        result.add_issue(issue)
        
        assert result.total_issues == 1
        assert result.high_count == 1
        assert len(result.issues) == 1
    
    def test_add_multiple_issues(self):
        """Test adding multiple issues."""
        result = ReviewResult()
        
        result.add_issue(ReviewIssue(
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            message="Critical"
        ))
        result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="High"
        ))
        result.add_issue(ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.STYLE,
            message="Medium"
        ))
        
        assert result.total_issues == 3
        assert result.critical_count == 1
        assert result.high_count == 1
        assert result.medium_count == 1
    
    def test_add_issue_updates_all_severity_counts(self):
        """Test that add_issue updates all severity counts correctly."""
        result = ReviewResult()
        
        result.add_issue(ReviewIssue(severity=Severity.CRITICAL, category=IssueCategory.SECURITY, message="1"))
        result.add_issue(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="2"))
        result.add_issue(ReviewIssue(severity=Severity.MEDIUM, category=IssueCategory.STYLE, message="3"))
        result.add_issue(ReviewIssue(severity=Severity.LOW, category=IssueCategory.STYLE, message="4"))
        result.add_issue(ReviewIssue(severity=Severity.INFO, category=IssueCategory.DOCUMENTATION, message="5"))
        
        assert result.critical_count == 1
        assert result.high_count == 1
        assert result.medium_count == 1
        assert result.low_count == 1
        assert result.info_count == 1
        assert result.total_issues == 5


class TestReviewResultQueryMethods:
    """Test ReviewResult query methods."""
    
    def test_has_critical_issues(self):
        """Test has_critical_issues method."""
        result = ReviewResult()
        
        assert result.has_critical_issues() is False
        
        result.add_issue(ReviewIssue(
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            message="Critical"
        ))
        
        assert result.has_critical_issues() is True
    
    def test_has_high_priority_issues(self):
        """Test has_high_priority_issues method."""
        result = ReviewResult()
        
        assert result.has_high_priority_issues() is False
        
        result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="High"
        ))
        
        assert result.has_high_priority_issues() is True
        
        # Test with critical
        result2 = ReviewResult()
        result2.add_issue(ReviewIssue(
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            message="Critical"
        ))
        
        assert result2.has_high_priority_issues() is True
    
    def test_get_issues_by_severity(self):
        """Test get_issues_by_severity method."""
        result = ReviewResult()
        
        result.add_issue(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="High1"))
        result.add_issue(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="High2"))
        result.add_issue(ReviewIssue(severity=Severity.MEDIUM, category=IssueCategory.STYLE, message="Medium"))
        
        high_issues = result.get_issues_by_severity(Severity.HIGH)
        medium_issues = result.get_issues_by_severity(Severity.MEDIUM)
        low_issues = result.get_issues_by_severity(Severity.LOW)
        
        assert len(high_issues) == 2
        assert len(medium_issues) == 1
        assert len(low_issues) == 0
        assert all(issue.severity == Severity.HIGH for issue in high_issues)
    
    def test_get_issues_by_category(self):
        """Test get_issues_by_category method."""
        result = ReviewResult()
        
        result.add_issue(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="Sec1"))
        result.add_issue(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="Sec2"))
        result.add_issue(ReviewIssue(severity=Severity.MEDIUM, category=IssueCategory.STYLE, message="Style"))
        
        security_issues = result.get_issues_by_category(IssueCategory.SECURITY)
        style_issues = result.get_issues_by_category(IssueCategory.STYLE)
        complexity_issues = result.get_issues_by_category(IssueCategory.COMPLEXITY)
        
        assert len(security_issues) == 2
        assert len(style_issues) == 1
        assert len(complexity_issues) == 0
        assert all(issue.category == IssueCategory.SECURITY for issue in security_issues)


class TestReviewResultScoring:
    """Test ReviewResult quality scoring."""
    
    def test_calculate_quality_score_no_issues(self):
        """Test quality score calculation with no issues."""
        result = ReviewResult()
        score = result.calculate_quality_score()
        
        assert score == 100.0
    
    def test_calculate_quality_score_with_critical(self):
        """Test quality score calculation with critical issue."""
        result = ReviewResult()
        result.add_issue(ReviewIssue(
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            message="Critical"
        ))
        
        score = result.calculate_quality_score()
        
        # 100 - 20 = 80
        assert score == 80.0
    
    def test_calculate_quality_score_with_multiple_severities(self):
        """Test quality score calculation with multiple severities."""
        result = ReviewResult()
        result.add_issue(ReviewIssue(severity=Severity.CRITICAL, category=IssueCategory.SECURITY, message="C"))  # -20
        result.add_issue(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="H"))  # -10
        result.add_issue(ReviewIssue(severity=Severity.MEDIUM, category=IssueCategory.STYLE, message="M"))  # -5
        result.add_issue(ReviewIssue(severity=Severity.LOW, category=IssueCategory.STYLE, message="L"))  # -2
        result.add_issue(ReviewIssue(severity=Severity.INFO, category=IssueCategory.DOCUMENTATION, message="I"))  # -1
        
        score = result.calculate_quality_score()
        
        # 100 - 20 - 10 - 5 - 2 - 1 = 62
        assert score == 62.0
    
    def test_calculate_quality_score_never_negative(self):
        """Test that quality score never goes below 0."""
        result = ReviewResult()
        
        # Add enough issues to go below 0
        for _ in range(10):
            result.add_issue(ReviewIssue(
                severity=Severity.CRITICAL,
                category=IssueCategory.SECURITY,
                message="Critical"
            ))
        
        score = result.calculate_quality_score()
        
        assert score == 0.0
        assert score >= 0.0
    
    def test_calculate_quality_score_never_above_100(self):
        """Test that quality score never goes above 100."""
        result = ReviewResult()
        score = result.calculate_quality_score()
        
        assert score <= 100.0


class TestReviewResultUpdateStatistics:
    """Test ReviewResult update_statistics method."""
    
    def test_update_statistics_recalculates_counts(self):
        """Test that update_statistics recalculates all counts."""
        result = ReviewResult()
        
        # Manually add issues to list (bypassing add_issue)
        result.issues.append(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="H"))
        result.issues.append(ReviewIssue(severity=Severity.MEDIUM, category=IssueCategory.STYLE, message="M"))
        
        # Stats should be out of sync
        assert result.total_issues == 0
        
        # Update statistics
        result.update_statistics()
        
        assert result.total_issues == 2
        assert result.high_count == 1
        assert result.medium_count == 1
    
    def test_update_statistics_calculates_quality_score(self):
        """Test that update_statistics calculates quality score."""
        result = ReviewResult()
        
        result.issues.append(ReviewIssue(severity=Severity.CRITICAL, category=IssueCategory.SECURITY, message="C"))
        
        result.update_statistics()
        
        assert result.quality_score == 80.0
    
    def test_update_statistics_sets_passed_flag(self):
        """Test that update_statistics sets the passed flag."""
        result = ReviewResult()
        
        # No critical issues - should pass
        result.issues.append(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="H"))
        result.update_statistics()
        
        assert result.passed is True
        
        # Add critical issue - should fail
        result.issues.append(ReviewIssue(severity=Severity.CRITICAL, category=IssueCategory.SECURITY, message="C"))
        result.update_statistics()
        
        assert result.passed is False


class TestReviewResultGetSummary:
    """Test ReviewResult get_summary method."""
    
    def test_get_summary_structure(self):
        """Test that get_summary returns correct structure."""
        result = ReviewResult()
        summary = result.get_summary()
        
        assert isinstance(summary, dict)
        assert "total_issues" in summary
        assert "quality_score" in summary
        assert "passed" in summary
        assert "severity_breakdown" in summary
        assert "has_critical" in summary
    
    def test_get_summary_values(self):
        """Test that get_summary returns correct values."""
        result = ReviewResult()
        result.add_issue(ReviewIssue(severity=Severity.CRITICAL, category=IssueCategory.SECURITY, message="C"))
        result.add_issue(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="H"))
        result.add_issue(ReviewIssue(severity=Severity.MEDIUM, category=IssueCategory.STYLE, message="M"))
        
        # Update statistics to calculate quality score
        result.update_statistics()
        
        summary = result.get_summary()
        
        assert summary["total_issues"] == 3
        assert summary["quality_score"] == 65.0  # 100 - 20 - 10 - 5
        assert summary["passed"] is False  # Has critical
        assert summary["has_critical"] is True
    
    def test_get_summary_severity_breakdown(self):
        """Test that get_summary includes correct severity breakdown."""
        result = ReviewResult()
        result.add_issue(ReviewIssue(severity=Severity.CRITICAL, category=IssueCategory.SECURITY, message="C"))
        result.add_issue(ReviewIssue(severity=Severity.HIGH, category=IssueCategory.SECURITY, message="H"))
        
        summary = result.get_summary()
        breakdown = summary["severity_breakdown"]
        
        assert breakdown["critical"] == 1
        assert breakdown["high"] == 1
        assert breakdown["medium"] == 0
        assert breakdown["low"] == 0
        assert breakdown["info"] == 0


class TestSeverityEnum:
    """Test Severity enum."""
    
    def test_all_severity_levels(self):
        """Test that all severity levels are defined."""
        assert Severity.INFO == "info"
        assert Severity.LOW == "low"
        assert Severity.MEDIUM == "medium"
        assert Severity.HIGH == "high"
        assert Severity.CRITICAL == "critical"


class TestIssueCategoryEnum:
    """Test IssueCategory enum."""
    
    def test_all_issue_categories(self):
        """Test that all issue categories are defined."""
        assert IssueCategory.STYLE == "style"
        assert IssueCategory.COMPLEXITY == "complexity"
        assert IssueCategory.SECURITY == "security"
        assert IssueCategory.PERFORMANCE == "performance"
        assert IssueCategory.BEST_PRACTICES == "best_practices"
        assert IssueCategory.DOCUMENTATION == "documentation"
        assert IssueCategory.BUG_RISK == "bug_risk"
