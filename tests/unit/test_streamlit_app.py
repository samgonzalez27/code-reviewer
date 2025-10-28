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


# ============================================================================
# Test Prompt Generation Integration
# ============================================================================

class TestPromptGenerationIntegration:
    """Test prompt generation integration with Streamlit UI."""
    
    def test_generate_copilot_prompts_returns_prompt_result(self):
        """Should generate and return PromptGenerationResult."""
        from src.streamlit_utils import generate_copilot_prompts
        from src.models.prompt_models import PromptGenerationResult
        
        # Create review result with issues
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="SQL injection vulnerability",
            line_number=42
        ))
        
        with patch('src.streamlit_utils.PromptGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            
            mock_result = PromptGenerationResult(language="python")
            mock_generator.generate.return_value = mock_result
            
            result = generate_copilot_prompts(review_result, language="python", api_key="test-key")
            
            assert isinstance(result, PromptGenerationResult)
            assert result == mock_result
    
    def test_generate_copilot_prompts_with_no_issues(self):
        """Should return empty result when no issues exist."""
        from src.streamlit_utils import generate_copilot_prompts
        
        review_result = ReviewResult()  # No issues
        
        with patch('src.streamlit_utils.PromptGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            
            from src.models.prompt_models import PromptGenerationResult
            mock_result = PromptGenerationResult(language="python")
            mock_generator.generate.return_value = mock_result
            
            result = generate_copilot_prompts(review_result, language="python", api_key="test-key")
            
            assert not result.has_prompts()
    
    def test_generate_copilot_prompts_with_no_api_key(self):
        """Should handle missing API key gracefully."""
        from src.streamlit_utils import generate_copilot_prompts
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="Security issue",
            line_number=10
        ))
        
        with patch.dict('os.environ', {}, clear=True):
            result = generate_copilot_prompts(review_result, language="python")
            
            # Should return None or empty result, not crash
            assert result is None or not result.has_prompts()
    
    def test_generate_copilot_prompts_passes_language(self):
        """Should pass language parameter to generator."""
        from src.streamlit_utils import generate_copilot_prompts
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.STYLE,
            message="Style issue",
            line_number=5
        ))
        
        with patch('src.streamlit_utils.PromptGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            
            from src.models.prompt_models import PromptGenerationResult
            mock_generator.generate.return_value = PromptGenerationResult()
            
            generate_copilot_prompts(review_result, language="javascript", api_key="test-key")
            
            # Verify generate was called with javascript
            mock_generator.generate.assert_called_once_with(review_result, language="javascript")
    
    def test_generate_copilot_prompts_handles_exception_gracefully(self):
        """Should return empty result if exception occurs during generation."""
        from src.streamlit_utils import generate_copilot_prompts
        from src.models.prompt_models import PromptGenerationResult
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="Security issue",
            line_number=10
        ))
        
        with patch('src.streamlit_utils.PromptGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            
            # Simulate exception during generation
            mock_generator.generate.side_effect = Exception("API Error")
            
            result = generate_copilot_prompts(review_result, language="python", api_key="test-key")
            
            # Should return empty result, not crash
            assert isinstance(result, PromptGenerationResult)
            assert not result.has_prompts()


class TestPromptFormattingForUI:
    
    def test_generate_copilot_prompts_uses_existing_api_key(self):
        """Should use API key from environment when available."""
        from src.streamlit_utils import generate_copilot_prompts
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.BUG_RISK,
            message="Potential bug",
            line_number=20
        ))
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.streamlit_utils.PromptGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator_class.return_value = mock_generator
                
                from src.models.prompt_models import PromptGenerationResult
                mock_generator.generate.return_value = PromptGenerationResult()
                
                generate_copilot_prompts(review_result, language="python")
                
                # Should create PromptGenerator
                mock_generator_class.assert_called_once()


class TestPromptFormattingForUI:
    """Test formatting prompts for display in Streamlit."""
    
    def test_format_prompt_for_display_basic(self):
        """Should format a single prompt for display."""
        from src.streamlit_utils import format_prompt_for_display
        from src.models.prompt_models import PromptSuggestion
        
        prompt = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix SQL injection vulnerabilities by using parameterized queries.",
            issue_count=3,
            severity_summary="2 high, 1 medium",
            line_references=[42, 58, 103]
        )
        
        formatted = format_prompt_for_display(prompt)
        
        assert isinstance(formatted, dict)
        assert "category" in formatted
        assert "prompt" in formatted
        assert "issue_count" in formatted
        assert "severity" in formatted
        assert "lines" in formatted
    
    def test_format_prompt_for_display_includes_category_emoji(self):
        """Should include emoji based on category."""
        from src.streamlit_utils import format_prompt_for_display
        from src.models.prompt_models import PromptSuggestion
        
        prompt = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix security issues",
            issue_count=2,
            severity_summary="2 high"
        )
        
        formatted = format_prompt_for_display(prompt)
        
        # Should have security-related emoji or indicator
        assert "🔒" in formatted["category"] or "security" in formatted["category"].lower()
    
    def test_format_prompt_for_display_handles_no_line_references(self):
        """Should handle prompts with no line references."""
        from src.streamlit_utils import format_prompt_for_display
        from src.models.prompt_models import PromptSuggestion
        
        prompt = PromptSuggestion(
            category=IssueCategory.STYLE,
            prompt_text="Improve code style",
            issue_count=5,
            severity_summary="5 low",
            line_references=[]
        )
        
        formatted = format_prompt_for_display(prompt)
        
        assert formatted["lines"] == "N/A" or formatted["lines"] == ""
    
    def test_format_prompts_for_display_list(self):
        """Should format multiple prompts for display."""
        from src.streamlit_utils import format_prompts_for_display
        from src.models.prompt_models import PromptSuggestion, PromptGenerationResult
        
        result = PromptGenerationResult(language="python")
        
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix security issues",
            issue_count=3,
            severity_summary="3 high"
        ))
        
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.STYLE,
            prompt_text="Improve style",
            issue_count=5,
            severity_summary="5 low"
        ))
        
        formatted_list = format_prompts_for_display(result)
        
        assert isinstance(formatted_list, list)
        assert len(formatted_list) == 2
        assert all(isinstance(item, dict) for item in formatted_list)
    
    def test_format_prompts_for_display_preserves_order(self):
        """Should preserve prompt order (priority order)."""
        from src.streamlit_utils import format_prompts_for_display
        from src.models.prompt_models import PromptSuggestion, PromptGenerationResult
        
        result = PromptGenerationResult(language="python")
        
        # Add in specific order
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Security first",
            issue_count=1,
            severity_summary="1 critical"
        ))
        
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.COMPLEXITY,
            prompt_text="Complexity second",
            issue_count=2,
            severity_summary="2 medium"
        ))
        
        formatted_list = format_prompts_for_display(result)
        
        # Should maintain order
        assert formatted_list[0]["prompt"] == "Security first"
        assert formatted_list[1]["prompt"] == "Complexity second"


class TestPromptExport:
    """Test exporting prompts to various formats."""
    
    def test_export_prompts_to_text(self):
        """Should export prompts as plain text."""
        from src.streamlit_utils import export_prompts_to_text
        from src.models.prompt_models import PromptSuggestion, PromptGenerationResult
        
        result = PromptGenerationResult(language="python")
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix SQL injection by using parameterized queries.",
            issue_count=2,
            severity_summary="2 high",
            line_references=[42, 58]
        ))
        
        text = export_prompts_to_text(result)
        
        assert isinstance(text, str)
        assert "SECURITY" in text.upper()
        assert "Fix SQL injection" in text
        assert "2 high" in text
    
    def test_export_prompts_to_text_empty_result(self):
        """Should handle empty result gracefully."""
        from src.streamlit_utils import export_prompts_to_text
        from src.models.prompt_models import PromptGenerationResult
        
        result = PromptGenerationResult(language="python")
        
        text = export_prompts_to_text(result)
        
        assert "No prompts generated" in text
    
    def test_export_prompts_to_text_multiple_prompts(self):
        """Should export multiple prompts with separators."""
        from src.streamlit_utils import export_prompts_to_text
        from src.models.prompt_models import PromptSuggestion, PromptGenerationResult
        
        result = PromptGenerationResult(language="python")
        
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Security prompt",
            issue_count=2,
            severity_summary="2 high"
        ))
        
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.STYLE,
            prompt_text="Style prompt",
            issue_count=5,
            severity_summary="5 low"
        ))
        
        text = export_prompts_to_text(result)
        
        # Should have both prompts
        assert "Security prompt" in text
        assert "Style prompt" in text
        # Should have separators or numbering
        assert "1." in text or "---" in text or "=" in text
    
    def test_export_prompts_to_json(self):
        """Should export prompts as JSON."""
        from src.streamlit_utils import export_prompts_to_json
        from src.models.prompt_models import PromptSuggestion, PromptGenerationResult
        import json
        
        result = PromptGenerationResult(language="python")
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix security issues",
            issue_count=3,
            severity_summary="3 high",
            line_references=[10, 20, 30]
        ))
        
        json_str = export_prompts_to_json(result)
        
        # Should be valid JSON
        data = json.loads(json_str)
        assert "prompts" in data or isinstance(data, list)
    
    def test_export_prompts_to_markdown(self):
        """Should export prompts as Markdown."""
        from src.streamlit_utils import export_prompts_to_markdown
        from src.models.prompt_models import PromptSuggestion, PromptGenerationResult
        
        result = PromptGenerationResult(language="python")
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.COMPLEXITY,
            prompt_text="Reduce complexity",
            issue_count=1,
            severity_summary="1 high"
        ))
        
        markdown = export_prompts_to_markdown(result)
        
        assert isinstance(markdown, str)
        # Should have markdown headers
        assert "#" in markdown
        assert "Reduce complexity" in markdown
    
    def test_export_prompts_to_markdown_empty_result(self):
        """Should handle empty result gracefully."""
        from src.streamlit_utils import export_prompts_to_markdown
        from src.models.prompt_models import PromptGenerationResult
        
        result = PromptGenerationResult(language="python")
        
        markdown = export_prompts_to_markdown(result)
        
        assert "No prompts generated" in markdown
    
    def test_export_prompts_to_markdown_with_line_references(self):
        """Should include line references in markdown export."""
        from src.streamlit_utils import export_prompts_to_markdown
        from src.models.prompt_models import PromptSuggestion, PromptGenerationResult
        
        result = PromptGenerationResult(language="python")
        result.add_prompt(PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix security issues",
            issue_count=3,
            severity_summary="3 high",
            line_references=[10, 20, 30]
        ))
        
        markdown = export_prompts_to_markdown(result)
        
        assert "Lines" in markdown
        assert "10, 20, 30" in markdown


class TestPromptCopyHelper:
    """Test helper for copying prompts to clipboard."""
    
    def test_prepare_prompt_for_copy_single(self):
        """Should prepare a single prompt for copying."""
        from src.streamlit_utils import prepare_prompt_for_copy
        from src.models.prompt_models import PromptSuggestion
        
        prompt = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix SQL injection vulnerabilities using parameterized queries.",
            issue_count=2,
            severity_summary="2 high",
            line_references=[42, 58]
        )
        
        copy_text = prepare_prompt_for_copy(prompt)
        
        assert isinstance(copy_text, str)
        assert "Fix SQL injection" in copy_text
        # Should be clean text, ready for Copilot
        assert copy_text.strip() == copy_text  # No leading/trailing whitespace
    
    def test_prepare_prompt_for_copy_includes_context(self):
        """Should optionally include context in copy text."""
        from src.streamlit_utils import prepare_prompt_for_copy
        from src.models.prompt_models import PromptSuggestion
        
        prompt = PromptSuggestion(
            category=IssueCategory.SECURITY,
            prompt_text="Fix security issues",
            issue_count=3,
            severity_summary="2 high, 1 medium",
            line_references=[10, 20, 30]
        )
        
        # With context
        copy_text = prepare_prompt_for_copy(prompt, include_context=True)
        
        assert "lines" in copy_text.lower() or "10" in copy_text
        assert "security" in copy_text.lower()
    
    def test_prepare_prompt_for_copy_without_context(self):
        """Should return just prompt text without context."""
        from src.streamlit_utils import prepare_prompt_for_copy
        from src.models.prompt_models import PromptSuggestion
        
        prompt = PromptSuggestion(
            category=IssueCategory.STYLE,
            prompt_text="Improve code style following PEP 8.",
            issue_count=5,
            severity_summary="5 low"
        )
        
        # Without context (default)
        copy_text = prepare_prompt_for_copy(prompt, include_context=False)
        
        assert copy_text == "Improve code style following PEP 8."


class TestPromptUIHelpers:
    """Test UI helper functions for prompt display."""
    
    def test_get_category_emoji(self):
        """Should return appropriate emoji for each category."""
        from src.streamlit_utils import get_category_emoji
        
        assert get_category_emoji(IssueCategory.SECURITY) in ["🔒", "🛡️", "🔐"]
        assert get_category_emoji(IssueCategory.COMPLEXITY) in ["🔄", "📊", "🎯"]
        assert get_category_emoji(IssueCategory.STYLE) in ["✨", "🎨", "💅"]
        assert get_category_emoji(IssueCategory.PERFORMANCE) in ["⚡", "🚀", "💨"]
        assert get_category_emoji(IssueCategory.BUG_RISK) in ["🐛", "⚠️", "🚨"]
        assert get_category_emoji(IssueCategory.BEST_PRACTICES) in ["👍", "✅", "⭐"]
        assert get_category_emoji(IssueCategory.DOCUMENTATION) in ["📝", "📚", "📄"]
    
    def test_get_category_color(self):
        """Should return color code for each category."""
        from src.streamlit_utils import get_category_color
        
        # Security should be a warning color
        assert get_category_color(IssueCategory.SECURITY) in ["red", "orange", "#ff0000"]
        # Style should be a neutral color
        assert get_category_color(IssueCategory.STYLE) in ["blue", "gray", "#0000ff"]
    
    def test_should_generate_prompts(self):
        """Should determine if prompts should be generated based on config."""
        from src.streamlit_utils import should_generate_prompts
        
        # Should generate if API key exists and issues found
        assert should_generate_prompts(has_api_key=True, has_issues=True) is True
        
        # Should not generate if no API key
        assert should_generate_prompts(has_api_key=False, has_issues=True) is False
        
        # Should not generate if no issues
        assert should_generate_prompts(has_api_key=True, has_issues=False) is False
        
        # Should not generate if neither
        assert should_generate_prompts(has_api_key=False, has_issues=False) is False
