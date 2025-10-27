"""
Unit tests for AIReviewer with auto-fix generation integration.

Tests the extended AIReviewer functionality that generates automated
fixes for detected issues.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types import CompletionUsage

from src.services.ai_reviewer import AIReviewer
from src.models.code_models import ParsedCode, CodeMetadata
from src.models.review_models import ReviewIssue, ReviewResult, Severity, IssueCategory
from src.models.code_fix_models import CodeFixResult, FixConfidence


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    return Mock(spec=OpenAI)


@pytest.fixture
def simple_parsed_code():
    """Create a simple ParsedCode object for testing."""
    return ParsedCode(
        content="def hello():\n    return 'Hello, World!'\n",
        language="python",
        metadata=CodeMetadata(
            line_count=2,
            function_count=1,
            class_count=0,
            comment_count=0,
            import_count=0,
            complexity=1.0,
            function_names=["hello"],
            class_names=[],
            has_docstrings=False,
            docstring_count=0,
            comment_ratio=0.0,
            blank_line_count=0,
            code_line_count=2,
        ),
        has_syntax_errors=False,
        syntax_errors=[]
    )


@pytest.fixture
def mock_code_fixer():
    """Create a mock CodeFixer."""
    from unittest.mock import Mock
    return Mock()


def create_mock_response(content: str, prompt_tokens: int = 100, completion_tokens: int = 200):
    """Helper to create mock ChatCompletion response."""
    mock_message = ChatCompletionMessage(
        role="assistant",
        content=content
    )
    
    mock_choice = Choice(
        finish_reason="stop",
        index=0,
        message=mock_message
    )
    
    mock_usage = CompletionUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )
    
    return ChatCompletion(
        id="test-completion-id",
        created=1234567890,
        model="gpt-4o-mini",
        object="chat.completion",
        choices=[mock_choice],
        usage=mock_usage
    )


# ============================================================================
# Test AIReviewer with Auto-Fix Configuration
# ============================================================================

class TestAIReviewerAutoFixConfiguration:
    """Test AIReviewer configuration for auto-fix generation."""
    
    def test_ai_reviewer_accepts_enable_auto_fix_config(self, mock_openai_client):
        """Should accept enable_auto_fix configuration option."""
        config = {"enable_auto_fix": True}
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        
        assert reviewer.enable_auto_fix is True
    
    def test_ai_reviewer_auto_fix_disabled_by_default(self, mock_openai_client):
        """Auto-fix should be disabled by default."""
        reviewer = AIReviewer(client=mock_openai_client)
        
        assert reviewer.enable_auto_fix is False
    
    def test_ai_reviewer_accepts_code_fixer_instance(self, mock_openai_client, mock_code_fixer):
        """Should accept a CodeFixer instance via configuration."""
        config = {"enable_auto_fix": True, "code_fixer": mock_code_fixer}
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        
        assert reviewer.code_fixer == mock_code_fixer
    
    def test_ai_reviewer_creates_code_fixer_if_not_provided(self, mock_openai_client):
        """Should create CodeFixer instance if auto-fix enabled but none provided."""
        config = {"enable_auto_fix": True}
        
        with patch('src.services.code_fixer.CodeFixer') as mock_fixer_class:
            reviewer = AIReviewer(client=mock_openai_client, config=config)
            # Should create CodeFixer with same client
            mock_fixer_class.assert_called_once()
    
    def test_ai_reviewer_no_code_fixer_when_auto_fix_disabled(self, mock_openai_client):
        """Should not create CodeFixer when auto-fix is disabled."""
        config = {"enable_auto_fix": False}
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        
        assert not hasattr(reviewer, 'code_fixer') or reviewer.code_fixer is None


# ============================================================================
# Test AIReviewer Review with Auto-Fix Generation
# ============================================================================

class TestAIReviewerReviewWithAutoFix:
    """Test review process with auto-fix generation enabled."""
    
    def test_review_with_auto_fix_returns_extended_result(self, mock_openai_client, simple_parsed_code):
        """Review with auto-fix should return ReviewResult with fix data."""
        review_response = '''{
            "issues": [{
                "severity": "medium",
                "category": "best_practices",
                "message": "Missing type hints",
                "line_number": 1
            }]
        }'''
        
        fix_response = '''{
            "fixes": [{
                "issue_description": "Missing type hints",
                "original_code": "def hello():",
                "fixed_code": "def hello() -> str:",
                "line_start": 1,
                "line_end": 1,
                "confidence": "high"
            }]
        }'''
        
        mock_openai_client.chat.completions.create.side_effect = [
            create_mock_response(review_response),
            create_mock_response(fix_response)
        ]
        
        config = {"enable_auto_fix": True}
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        result = reviewer.review(simple_parsed_code)
        
        # Should have both review issues and fixes
        assert result.total_issues == 1
        assert hasattr(result, 'fix_result')
        assert result.fix_result is not None
        assert isinstance(result.fix_result, CodeFixResult)
    
    def test_review_with_auto_fix_calls_code_fixer(self, mock_openai_client, mock_code_fixer, simple_parsed_code):
        """Review should call CodeFixer when auto-fix enabled and issues found."""
        review_response = '''{
            "issues": [{
                "severity": "medium",
                "category": "best_practices",
                "message": "Missing type hints",
                "line_number": 1
            }]
        }'''
        
        mock_openai_client.chat.completions.create.return_value = create_mock_response(review_response)
        mock_code_fixer.generate_fixes.return_value = CodeFixResult()
        
        config = {"enable_auto_fix": True, "code_fixer": mock_code_fixer}
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        result = reviewer.review(simple_parsed_code)
        
        # Should call generate_fixes with parsed code and issues
        mock_code_fixer.generate_fixes.assert_called_once()
        call_args = mock_code_fixer.generate_fixes.call_args[0]
        assert call_args[0] == simple_parsed_code
        assert len(call_args[1]) == 1  # One issue
    
    def test_review_with_auto_fix_disabled_no_fixes(self, mock_openai_client, simple_parsed_code):
        """Review should not generate fixes when auto-fix disabled."""
        review_response = '''{
            "issues": [{
                "severity": "medium",
                "category": "best_practices",
                "message": "Missing type hints",
                "line_number": 1
            }]
        }'''
        
        mock_openai_client.chat.completions.create.return_value = create_mock_response(review_response)
        
        config = {"enable_auto_fix": False}
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        result = reviewer.review(simple_parsed_code)
        
        # Should have issues but no fixes
        assert result.total_issues == 1
        assert not hasattr(result, 'fix_result') or result.fix_result is None
    
    def test_review_with_auto_fix_no_issues_no_fix_generation(self, mock_openai_client, mock_code_fixer, simple_parsed_code):
        """Should not call CodeFixer when no issues are found."""
        review_response = '{"issues": []}'
        
        mock_openai_client.chat.completions.create.return_value = create_mock_response(review_response)
        
        config = {"enable_auto_fix": True, "code_fixer": mock_code_fixer}
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        result = reviewer.review(simple_parsed_code)
        
        # Should not call generate_fixes when no issues
        mock_code_fixer.generate_fixes.assert_not_called()
    
    def test_review_with_auto_fix_handles_fixer_error(self, mock_openai_client, mock_code_fixer, simple_parsed_code):
        """Should handle CodeFixer errors gracefully."""
        review_response = '''{
            "issues": [{
                "severity": "medium",
                "category": "best_practices",
                "message": "Test issue",
                "line_number": 1
            }]
        }'''
        
        mock_openai_client.chat.completions.create.return_value = create_mock_response(review_response)
        mock_code_fixer.generate_fixes.side_effect = Exception("Fixer error")
        
        config = {"enable_auto_fix": True, "code_fixer": mock_code_fixer}
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        result = reviewer.review(simple_parsed_code)
        
        # Review should still succeed with issues, fix generation just failed
        assert result.total_issues == 1
        # Fix result should indicate error
        assert hasattr(result, 'fix_result')
        if result.fix_result:
            assert result.fix_result.success is False


# ============================================================================
# Test AIReviewer Method: review_with_fixes
# ============================================================================

class TestAIReviewerReviewWithFixesMethod:
    """Test dedicated method for review with fix generation."""
    
    def test_review_with_fixes_method_exists(self, mock_openai_client):
        """AIReviewer should have review_with_fixes method."""
        reviewer = AIReviewer(client=mock_openai_client)
        assert hasattr(reviewer, 'review_with_fixes')
        assert callable(reviewer.review_with_fixes)
    
    def test_review_with_fixes_returns_both_results(self, mock_openai_client, simple_parsed_code):
        """review_with_fixes should return both ReviewResult and CodeFixResult."""
        review_response = '''{
            "issues": [{
                "severity": "medium",
                "category": "best_practices",
                "message": "Test issue",
                "line_number": 1
            }]
        }'''
        
        fix_response = '''{
            "fixes": [{
                "issue_description": "Test issue",
                "original_code": "old",
                "fixed_code": "new",
                "line_start": 1,
                "line_end": 1,
                "confidence": "high"
            }]
        }'''
        
        mock_openai_client.chat.completions.create.side_effect = [
            create_mock_response(review_response),
            create_mock_response(fix_response)
        ]
        
        reviewer = AIReviewer(client=mock_openai_client)
        review_result, fix_result = reviewer.review_with_fixes(simple_parsed_code)
        
        from src.models.review_models import ReviewResult
        assert isinstance(review_result, ReviewResult)
        assert isinstance(fix_result, CodeFixResult)
        assert review_result.total_issues == 1
        assert fix_result.total_fixes == 1
    
    def test_review_with_fixes_accepts_auto_fix_param(self, mock_openai_client, simple_parsed_code):
        """review_with_fixes should accept auto_fix parameter to control behavior."""
        review_response = '{"issues": []}'
        mock_openai_client.chat.completions.create.return_value = create_mock_response(review_response)
        
        reviewer = AIReviewer(client=mock_openai_client)
        
        # Should work with auto_fix=True
        review_result, fix_result = reviewer.review_with_fixes(simple_parsed_code, auto_fix=True)
        assert isinstance(review_result, ReviewResult)
        
        # Should work with auto_fix=False
        review_result, fix_result = reviewer.review_with_fixes(simple_parsed_code, auto_fix=False)
        assert fix_result is None or fix_result.total_fixes == 0


# ============================================================================
# Test AIReviewer Filter Fixable Issues
# ============================================================================

class TestAIReviewerFilterFixableIssues:
    """Test filtering issues to determine which are auto-fixable."""
    
    def test_get_fixable_issues_method_exists(self, mock_openai_client):
        """AIReviewer should have method to filter fixable issues."""
        reviewer = AIReviewer(client=mock_openai_client)
        assert hasattr(reviewer, 'get_fixable_issues')
    
    def test_get_fixable_issues_filters_by_category(self, mock_openai_client):
        """Should filter out non-fixable issue categories."""
        reviewer = AIReviewer(client=mock_openai_client)
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Missing type hints",
                line_number=1
            ),
            ReviewIssue(
                severity=Severity.LOW,
                category=IssueCategory.COMPLEXITY,
                message="Function too complex",
                line_number=5
            ),
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.DOCUMENTATION,
                message="Missing docstring",
                line_number=10
            )
        ]
        
        fixable = reviewer.get_fixable_issues(issues)
        
        # Complexity issues typically not auto-fixable, others might be
        # Implementation will determine exact logic
        assert isinstance(fixable, list)
        # All should be ReviewIssue objects
        for issue in fixable:
            assert isinstance(issue, ReviewIssue)
    
    def test_get_fixable_issues_respects_severity(self, mock_openai_client):
        """Should respect minimum severity for auto-fix."""
        reviewer = AIReviewer(client=mock_openai_client)
        
        issues = [
            ReviewIssue(
                severity=Severity.CRITICAL,
                category=IssueCategory.SECURITY,
                message="SQL injection risk",
                line_number=1
            ),
            ReviewIssue(
                severity=Severity.INFO,
                category=IssueCategory.STYLE,
                message="Prefer single quotes",
                line_number=2
            )
        ]
        
        # May want to auto-fix critical security issues but not info-level style
        fixable = reviewer.get_fixable_issues(issues, min_severity=Severity.MEDIUM)
        
        # Should only include issues >= MEDIUM severity
        assert all(
            issue.severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM]
            for issue in fixable
        )
    
    def test_get_fixable_issues_excludes_issues_without_line_numbers(self, mock_openai_client):
        """Should exclude issues without line numbers (can't fix without location)."""
        reviewer = AIReviewer(client=mock_openai_client)
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="With line number",
                line_number=1
            ),
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Without line number",
                line_number=None
            )
        ]
        
        fixable = reviewer.get_fixable_issues(issues)
        
        # Should only include issues with line numbers
        assert all(issue.line_number is not None for issue in fixable)


# ============================================================================
# Test AIReviewer Fix Application
# ============================================================================

class TestAIReviewerFixApplication:
    """Test applying generated fixes to code."""
    
    def test_apply_fixes_method_exists(self, mock_openai_client):
        """AIReviewer should have method to apply fixes."""
        reviewer = AIReviewer(client=mock_openai_client)
        assert hasattr(reviewer, 'apply_fixes')
    
    def test_apply_fixes_returns_modified_code(self, mock_openai_client, simple_parsed_code):
        """apply_fixes should return modified code with fixes applied."""
        from src.models.code_fix_models import CodeFix
        
        fixes = CodeFixResult()
        fixes.add_fix(CodeFix(
            issue_description="Add type hint",
            original_code="def hello():",
            fixed_code="def hello() -> str:",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.HIGH
        ))
        
        reviewer = AIReviewer(client=mock_openai_client)
        modified_code = reviewer.apply_fixes(simple_parsed_code, fixes)
        
        assert isinstance(modified_code, str)
        assert "-> str:" in modified_code
    
    def test_apply_fixes_only_high_confidence(self, mock_openai_client, simple_parsed_code):
        """Should only apply high confidence fixes by default."""
        from src.models.code_fix_models import CodeFix
        
        fixes = CodeFixResult()
        fixes.add_fix(CodeFix(
            issue_description="High confidence fix",
            original_code="def hello():",
            fixed_code="def hello() -> str:",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.HIGH
        ))
        fixes.add_fix(CodeFix(
            issue_description="Low confidence fix",
            original_code="return 'Hello, World!'",
            fixed_code='return "Hello, World!"',
            line_start=2,
            line_end=2,
            confidence=FixConfidence.LOW
        ))
        
        reviewer = AIReviewer(client=mock_openai_client)
        modified_code = reviewer.apply_fixes(simple_parsed_code, fixes, min_confidence=FixConfidence.HIGH)
        
        # Should apply high confidence but not low
        assert "-> str:" in modified_code
        assert "'" in modified_code  # Original single quotes preserved
    
    def test_apply_fixes_accepts_confidence_threshold(self, mock_openai_client, simple_parsed_code):
        """Should accept min_confidence parameter."""
        from src.models.code_fix_models import CodeFix
        
        fixes = CodeFixResult()
        fixes.add_fix(CodeFix(
            issue_description="Medium confidence fix",
            original_code="def hello():",
            fixed_code="def hello() -> str:",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.MEDIUM
        ))
        
        reviewer = AIReviewer(client=mock_openai_client)
        
        # Should apply when min_confidence is MEDIUM or lower
        modified_code = reviewer.apply_fixes(simple_parsed_code, fixes, min_confidence=FixConfidence.MEDIUM)
        assert "-> str:" in modified_code
    
    def test_apply_fixes_handles_multiple_fixes(self, mock_openai_client):
        """Should handle applying multiple fixes in order."""
        code = ParsedCode(
            content="def func1():\n    pass\n\ndef func2():\n    pass\n",
            language="python",
            metadata=CodeMetadata(line_count=5),
            has_syntax_errors=False,
            syntax_errors=[]
        )
        
        from src.models.code_fix_models import CodeFix
        fixes = CodeFixResult()
        fixes.add_fix(CodeFix(
            issue_description="Fix 1",
            original_code="def func1():",
            fixed_code="def func1() -> None:",
            line_start=1,
            line_end=1,
            confidence=FixConfidence.HIGH
        ))
        fixes.add_fix(CodeFix(
            issue_description="Fix 2",
            original_code="def func2():",
            fixed_code="def func2() -> None:",
            line_start=4,
            line_end=4,
            confidence=FixConfidence.HIGH
        ))
        
        reviewer = AIReviewer(client=mock_openai_client)
        modified_code = reviewer.apply_fixes(code, fixes)
        
        # Both fixes should be applied
        assert modified_code.count("-> None:") == 2
    
    def test_apply_fixes_returns_original_on_error(self, mock_openai_client, simple_parsed_code):
        """Should return original code if fix application fails."""
        from src.models.code_fix_models import CodeFix
        
        # Invalid fix that can't be applied
        fixes = CodeFixResult()
        fixes.add_fix(CodeFix(
            issue_description="Bad fix",
            original_code="code that doesn't exist",
            fixed_code="replacement",
            line_start=999,
            line_end=999,
            confidence=FixConfidence.HIGH
        ))
        
        reviewer = AIReviewer(client=mock_openai_client)
        modified_code = reviewer.apply_fixes(simple_parsed_code, fixes)
        
        # Should return original code, not crash
        assert modified_code == simple_parsed_code.content
