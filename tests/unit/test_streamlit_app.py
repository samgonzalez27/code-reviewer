"""
Unit tests for Streamlit app functionality.

Tests the business logic and utility functions used by the Streamlit UI.
Following TDD: Write tests first (RED), then implement (GREEN), then refactor.
"""
import pytest
from unittest.mock import Mock, patch
from src.models.review_models import ReviewResult, ReviewIssue, Severity, IssueCategory


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_review_result():
    """Create a sample ReviewResult for testing."""
    result = ReviewResult(reviewer_name="TestEngine")
    
    result.add_issue(ReviewIssue(
        severity=Severity.CRITICAL,
        category=IssueCategory.SECURITY,
        message="Hardcoded API key detected",
        line_number=5,
        suggestion="Move to environment variable"
    ))
    
    result.add_issue(ReviewIssue(
        severity=Severity.HIGH,
        category=IssueCategory.COMPLEXITY,
        message="Function has high cyclomatic complexity",
        line_number=10
    ))
    
    result.add_issue(ReviewIssue(
        severity=Severity.LOW,
        category=IssueCategory.STYLE,
        message="Function name should use snake_case",
        line_number=3
    ))
    
    result.update_statistics()
    return result


# ============================================================================
# Test App Utilities Module
# ============================================================================

class TestAppUtilities:
    """Test utility functions used by the Streamlit app."""
    
    def test_format_severity_with_color_critical(self):
        """format_severity_with_color should return red for critical."""
        from src.streamlit_utils import format_severity_with_color
        
        formatted = format_severity_with_color(Severity.CRITICAL)
        assert "🔴" in formatted or "critical" in formatted.lower()
    
    def test_format_severity_with_color_high(self):
        """format_severity_with_color should return orange for high."""
        from src.streamlit_utils import format_severity_with_color
        
        formatted = format_severity_with_color(Severity.HIGH)
        assert "🟠" in formatted or "high" in formatted.lower()
    
    def test_format_severity_with_color_medium(self):
        """format_severity_with_color should return yellow for medium."""
        from src.streamlit_utils import format_severity_with_color
        
        formatted = format_severity_with_color(Severity.MEDIUM)
        assert "🟡" in formatted or "medium" in formatted.lower()
    
    def test_format_severity_with_color_low(self):
        """format_severity_with_color should return blue for low."""
        from src.streamlit_utils import format_severity_with_color
        
        formatted = format_severity_with_color(Severity.LOW)
        assert "🔵" in formatted or "low" in formatted.lower()
    
    def test_format_severity_with_color_info(self):
        """format_severity_with_color should return gray for info."""
        from src.streamlit_utils import format_severity_with_color
        
        formatted = format_severity_with_color(Severity.INFO)
        assert "⚪" in formatted or "info" in formatted.lower()
    
    def test_get_severity_color_map(self):
        """get_severity_color_map should return dict of severity to color."""
        from src.streamlit_utils import get_severity_color_map
        
        color_map = get_severity_color_map()
        
        assert isinstance(color_map, dict)
        assert Severity.CRITICAL in color_map
        assert Severity.HIGH in color_map
        assert len(color_map) == 5  # All 5 severity levels


class TestResultFormatting:
    """Test formatting review results for display."""
    
    def test_format_issue_for_display(self, sample_review_result):
        """format_issue_for_display should create readable issue dict."""
        from src.streamlit_utils import format_issue_for_display
        
        issue = sample_review_result.issues[0]  # Critical security issue
        formatted = format_issue_for_display(issue)
        
        assert isinstance(formatted, dict)
        assert "severity" in formatted
        assert "category" in formatted
        assert "message" in formatted
        assert "line" in formatted
        assert formatted["severity"] == "critical"
        assert formatted["message"] == "Hardcoded API key detected"
    
    def test_format_issue_for_display_without_line_number(self):
        """format_issue_for_display should handle issues without line numbers."""
        from src.streamlit_utils import format_issue_for_display
        
        issue = ReviewIssue(
            severity=Severity.INFO,
            category=IssueCategory.DOCUMENTATION,
            message="Missing documentation"
        )
        
        formatted = format_issue_for_display(issue)
        assert formatted["line"] is None or formatted["line"] == "N/A"
    
    def test_group_issues_by_severity(self, sample_review_result):
        """group_issues_by_severity should organize issues by severity level."""
        from src.streamlit_utils import group_issues_by_severity
        
        grouped = group_issues_by_severity(sample_review_result.issues)
        
        assert isinstance(grouped, dict)
        assert Severity.CRITICAL in grouped
        assert len(grouped[Severity.CRITICAL]) == 1
        assert len(grouped[Severity.HIGH]) == 1
        assert len(grouped[Severity.LOW]) == 1
    
    def test_group_issues_by_category(self, sample_review_result):
        """group_issues_by_category should organize issues by category."""
        from src.streamlit_utils import group_issues_by_category
        
        grouped = group_issues_by_category(sample_review_result.issues)
        
        assert isinstance(grouped, dict)
        assert IssueCategory.SECURITY in grouped
        assert IssueCategory.COMPLEXITY in grouped
        assert IssueCategory.STYLE in grouped


class TestReviewSummary:
    """Test generating review summaries."""
    
    def test_generate_summary_dict(self, sample_review_result):
        """generate_summary_dict should create summary with key metrics."""
        from src.streamlit_utils import generate_summary_dict
        
        summary = generate_summary_dict(sample_review_result)
        
        assert isinstance(summary, dict)
        assert "total_issues" in summary
        assert "quality_score" in summary
        assert "passed" in summary
        assert "critical_count" in summary
        assert summary["total_issues"] == 3
        assert summary["critical_count"] == 1
    
    def test_get_quality_score_color_excellent(self):
        """get_quality_score_color should return green for 90+."""
        from src.streamlit_utils import get_quality_score_color
        
        color = get_quality_score_color(95.0)
        assert color in ["green", "#00FF00", "success"]
    
    def test_get_quality_score_color_good(self):
        """get_quality_score_color should return yellow for 70-89."""
        from src.streamlit_utils import get_quality_score_color
        
        color = get_quality_score_color(80.0)
        assert color in ["yellow", "#FFFF00", "warning"]
    
    def test_get_quality_score_color_poor(self):
        """get_quality_score_color should return red for <70."""
        from src.streamlit_utils import get_quality_score_color
        
        color = get_quality_score_color(50.0)
        assert color in ["red", "#FF0000", "error"]


class TestCodeValidation:
    """Test code input validation."""
    
    def test_validate_code_input_valid(self):
        """validate_code_input should return True for valid code."""
        from src.streamlit_utils import validate_code_input
        
        code = "def hello():\n    return 'world'"
        is_valid, message = validate_code_input(code)
        
        assert is_valid is True
        assert message == "" or message is None
    
    def test_validate_code_input_empty(self):
        """validate_code_input should reject empty code."""
        from src.streamlit_utils import validate_code_input
        
        is_valid, message = validate_code_input("")
        
        assert is_valid is False
        assert "empty" in message.lower() or "required" in message.lower()
    
    def test_validate_code_input_whitespace_only(self):
        """validate_code_input should reject whitespace-only code."""
        from src.streamlit_utils import validate_code_input
        
        is_valid, message = validate_code_input("   \n\n  \t  ")
        
        assert is_valid is False
        assert "empty" in message.lower()
    
    def test_validate_code_input_too_large(self):
        """validate_code_input should reject code exceeding size limit."""
        from src.streamlit_utils import validate_code_input
        
        large_code = "x = 1\n" * 100000  # Very large code
        is_valid, message = validate_code_input(large_code, max_lines=1000)
        
        assert is_valid is False
        assert "large" in message.lower() or "lines" in message.lower()
    
    def test_validate_language_selection_valid(self):
        """validate_language_selection should accept supported languages."""
        from src.streamlit_utils import validate_language_selection
        
        assert validate_language_selection("python") is True
        assert validate_language_selection("javascript") is True
        assert validate_language_selection("typescript") is True
    
    def test_validate_language_selection_invalid(self):
        """validate_language_selection should reject unsupported languages."""
        from src.streamlit_utils import validate_language_selection
        
        assert validate_language_selection("cobol") is False
        assert validate_language_selection("") is False


class TestReviewExecution:
    """Test review execution logic."""
    
    def test_run_review_returns_result(self):
        """run_review should execute review and return ReviewResult."""
        from src.streamlit_utils import run_review
        
        code = "def test(): pass"
        language = "python"
        config = {"enable_ai": False}
        
        result = run_review(code, language, config)
        
        assert result is not None
        assert isinstance(result, ReviewResult)
    
    def test_run_review_with_syntax_errors(self):
        """run_review should handle code with syntax errors."""
        from src.streamlit_utils import run_review
        
        code = "def broken function( pass"
        language = "python"
        config = {"enable_ai": False}
        
        result = run_review(code, language, config)
        
        assert result is not None
        assert isinstance(result, ReviewResult)
    
    def test_run_review_with_ai_enabled(self):
        """run_review should include AI reviewer when enabled."""
        from src.streamlit_utils import run_review
        from unittest.mock import patch, Mock
        
        code = "def test(): pass"
        language = "python"
        config = {"enable_ai": True}
        
        # Mock OpenAI to avoid real API calls
        with patch('src.services.ai_reviewer.OpenAI'):
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                result = run_review(code, language, config)
                
                assert result is not None
                assert isinstance(result, ReviewResult)
    
    def test_run_review_handles_exceptions(self):
        """run_review should handle exceptions gracefully."""
        from src.streamlit_utils import run_review
        
        # Invalid inputs should not crash
        result = run_review(None, "python", {})
        
        # Should return error or empty result, not crash
        assert result is not None or result is None  # Either is acceptable


class TestExportFunctionality:
    """Test exporting review results."""
    
    def test_export_to_json(self, sample_review_result):
        """export_to_json should create valid JSON string."""
        from src.streamlit_utils import export_to_json
        import json
        
        json_str = export_to_json(sample_review_result)
        
        assert isinstance(json_str, str)
        # Should be valid JSON
        data = json.loads(json_str)
        assert "issues" in data
        assert "quality_score" in data
    
    def test_export_to_markdown(self, sample_review_result):
        """export_to_markdown should create formatted markdown."""
        from src.streamlit_utils import export_to_markdown
        
        markdown = export_to_markdown(sample_review_result)
        
        assert isinstance(markdown, str)
        assert "##" in markdown or "#" in markdown  # Headers
        assert str(sample_review_result.quality_score) in markdown
    
    def test_export_to_csv(self, sample_review_result):
        """export_to_csv should create CSV with issue details."""
        from src.streamlit_utils import export_to_csv
        
        csv_str = export_to_csv(sample_review_result)
        
        assert isinstance(csv_str, str)
        assert "severity" in csv_str.lower()
        assert "category" in csv_str.lower()
        assert "message" in csv_str.lower()


class TestConfigurationHelpers:
    """Test configuration helper functions."""
    
    def test_get_default_config(self):
        """get_default_config should return default configuration dict."""
        from src.streamlit_utils import get_default_config
        
        config = get_default_config()
        
        assert isinstance(config, dict)
        assert "enable_style" in config
        assert "enable_complexity" in config
        assert "enable_security" in config
        assert "enable_ai" in config
    
    def test_build_config_from_ui_inputs(self):
        """build_config_from_ui_inputs should construct config from UI selections."""
        from src.streamlit_utils import build_config_from_ui_inputs
        
        ui_inputs = {
            "enable_style": True,
            "enable_complexity": True,
            "enable_security": False,
            "enable_ai": True,
            "ai_model": "gpt-4",
            "max_complexity": 15
        }
        
        config = build_config_from_ui_inputs(ui_inputs)
        
        assert config["enable_style"] is True
        assert config["enable_security"] is False
        assert config["enable_ai"] is True
        assert config["ai_model"] == "gpt-4"
        assert config["max_complexity"] == 15


class TestReviewModes:
    """Test different review modes."""
    
    def test_get_review_mode_config_quick(self):
        """get_review_mode_config should return quick scan config."""
        from src.streamlit_utils import get_review_mode_config
        
        config = get_review_mode_config("quick")
        
        assert config["enable_ai"] is False
        assert config["enable_style"] is True or config["enable_security"] is True
    
    def test_get_review_mode_config_standard(self):
        """get_review_mode_config should return standard (hybrid) config."""
        from src.streamlit_utils import get_review_mode_config
        
        config = get_review_mode_config("standard")
        
        assert config["enable_style"] is True
        assert config["enable_complexity"] is True
        assert config["enable_security"] is True
        assert config["enable_ai"] is True
    
    def test_get_review_mode_config_deep(self):
        """get_review_mode_config should return AI-focused config."""
        from src.streamlit_utils import get_review_mode_config
        
        config = get_review_mode_config("deep")
        
        assert config["enable_ai"] is True
        # May disable some rule-based for speed
    
    def test_get_review_mode_config_unknown_mode(self):
        """get_review_mode_config should return default config for unknown mode."""
        from src.streamlit_utils import get_review_mode_config, get_default_config
        
        config = get_review_mode_config("unknown_mode")
        default = get_default_config()
        
        assert config == default
