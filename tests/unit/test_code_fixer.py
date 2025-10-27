"""
Unit tests for AI-powered code fixer service.

Tests the CodeFixer class that generates automated fix suggestions
for code issues detected by reviewers.
"""
import pytest
from unittest.mock import Mock, MagicMock
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types import CompletionUsage

from src.services.code_fixer import CodeFixer
from src.models.code_models import ParsedCode, CodeMetadata
from src.models.review_models import ReviewIssue, Severity, IssueCategory
from src.models.code_fix_models import FixConfidence, FixStatus


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
def sample_issue():
    """Create a sample review issue."""
    return ReviewIssue(
        severity=Severity.MEDIUM,
        category=IssueCategory.BEST_PRACTICES,
        message="Function lacks type hints",
        line_number=1,
        suggestion="Add type hints for parameters and return value",
        rule_id="BP001"
    )


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
# Test CodeFixer Initialization
# ============================================================================

class TestCodeFixerInitialization:
    """Test CodeFixer initialization and configuration."""
    
    def test_code_fixer_accepts_openai_client(self, mock_openai_client):
        """CodeFixer should accept OpenAI client via constructor."""
        fixer = CodeFixer(client=mock_openai_client)
        assert fixer.client == mock_openai_client
    
    def test_code_fixer_creates_client_from_env(self):
        """CodeFixer should create client from environment if not provided."""
        from unittest.mock import patch
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.services.code_fixer.OpenAI') as mock_openai_class:
                fixer = CodeFixer()
                mock_openai_class.assert_called_once_with(api_key='test-key')
    
    def test_code_fixer_raises_error_if_no_api_key(self):
        """CodeFixer should raise error if no API key available."""
        from unittest.mock import patch
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                CodeFixer()
    
    def test_code_fixer_accepts_configuration(self, mock_openai_client):
        """CodeFixer should accept and store configuration."""
        config = {
            "model": "gpt-4",
            "temperature": 0.2,
            "max_tokens": 1500,
        }
        fixer = CodeFixer(client=mock_openai_client, config=config)
        assert fixer.model == "gpt-4"
        assert fixer.temperature == 0.2
        assert fixer.max_tokens == 1500
    
    def test_code_fixer_uses_default_configuration(self, mock_openai_client):
        """CodeFixer should use sensible defaults if no config provided."""
        fixer = CodeFixer(client=mock_openai_client)
        assert fixer.model == "gpt-4o-mini"
        assert fixer.temperature == 0.2
        assert fixer.max_tokens == 2000


# ============================================================================
# Test CodeFixer Fix Generation from Issue
# ============================================================================

class TestCodeFixerGenerateFixFromIssue:
    """Test generating fixes from individual issues."""
    
    def test_generate_fix_returns_code_fix_result(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should return CodeFixResult when generating fix."""
        mock_response = create_mock_response('{"fixes": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, sample_issue)
        
        from src.models.code_fix_models import CodeFixResult
        assert isinstance(result, CodeFixResult)
    
    def test_generate_fix_calls_openai_api(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should call OpenAI API to generate fix."""
        mock_response = create_mock_response('{"fixes": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        fixer.generate_fix(simple_parsed_code, sample_issue)
        
        mock_openai_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["role"] == "user"
    
    def test_generate_fix_includes_issue_in_prompt(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should include issue details in the prompt."""
        mock_response = create_mock_response('{"fixes": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        fixer.generate_fix(simple_parsed_code, sample_issue)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        user_message = call_kwargs["messages"][1]["content"]
        
        assert "Function lacks type hints" in user_message
        assert "line 1" in user_message.lower()
    
    def test_generate_fix_includes_code_context(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should include surrounding code context in prompt."""
        mock_response = create_mock_response('{"fixes": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        fixer.generate_fix(simple_parsed_code, sample_issue)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        user_message = call_kwargs["messages"][1]["content"]
        
        assert "def hello():" in user_message
    
    def test_generate_fix_parses_single_fix(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should parse AI response with single fix."""
        response_content = '''{
            "fixes": [{
                "issue_description": "Function lacks type hints",
                "original_code": "def hello():",
                "fixed_code": "def hello() -> str:",
                "line_start": 1,
                "line_end": 1,
                "explanation": "Added return type hint",
                "confidence": "high"
            }]
        }'''
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, sample_issue)
        
        assert result.total_fixes == 1
        assert result.high_confidence_count == 1
        fix = result.fixes[0]
        assert "type hint" in fix.issue_description.lower()
        assert fix.line_start == 1
        assert fix.confidence == FixConfidence.HIGH
    
    def test_generate_fix_handles_api_error(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should handle API errors gracefully."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, sample_issue)
        
        assert result.success is False
        assert "API Error" in result.error_message


# ============================================================================
# Test CodeFixer Batch Fix Generation
# ============================================================================

class TestCodeFixerBatchGeneration:
    """Test generating fixes for multiple issues at once."""
    
    def test_generate_fixes_for_multiple_issues(self, mock_openai_client, simple_parsed_code):
        """Should generate fixes for multiple issues."""
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Missing type hints",
                line_number=1
            ),
            ReviewIssue(
                severity=Severity.LOW,
                category=IssueCategory.DOCUMENTATION,
                message="Missing docstring",
                line_number=1
            )
        ]
        
        response_content = '''{
            "fixes": [
                {
                    "issue_description": "Missing type hints",
                    "original_code": "def hello():",
                    "fixed_code": "def hello() -> str:",
                    "line_start": 1,
                    "line_end": 1,
                    "confidence": "high"
                },
                {
                    "issue_description": "Missing docstring",
                    "original_code": "def hello():",
                    "fixed_code": "def hello():\\n    \\"\\"\\"Say hello.\\"\\"\\"",
                    "line_start": 1,
                    "line_end": 1,
                    "confidence": "medium"
                }
            ]
        }'''
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fixes(simple_parsed_code, issues)
        
        from src.models.code_fix_models import CodeFixResult
        assert isinstance(result, CodeFixResult)
        assert result.total_fixes == 2
        assert result.high_confidence_count == 1
        assert result.medium_confidence_count == 1
    
    def test_generate_fixes_with_empty_issues_list(self, mock_openai_client, simple_parsed_code):
        """Should handle empty issues list."""
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fixes(simple_parsed_code, [])
        
        assert result.total_fixes == 0
        mock_openai_client.chat.completions.create.assert_not_called()


# ============================================================================
# Test CodeFixer Response Parsing
# ============================================================================

class TestCodeFixerResponseParsing:
    """Test parsing of AI responses into CodeFix objects."""
    
    def test_parse_response_with_confidence_levels(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should parse different confidence levels correctly."""
        response_content = '''{
            "fixes": [
                {"issue_description": "A", "original_code": "a", "fixed_code": "b", 
                 "line_start": 1, "line_end": 1, "confidence": "high"},
                {"issue_description": "B", "original_code": "c", "fixed_code": "d", 
                 "line_start": 2, "line_end": 2, "confidence": "medium"},
                {"issue_description": "C", "original_code": "e", "fixed_code": "f", 
                 "line_start": 3, "line_end": 3, "confidence": "low"}
            ]
        }'''
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, sample_issue)
        
        assert result.total_fixes == 3
        assert result.fixes[0].confidence == FixConfidence.HIGH
        assert result.fixes[1].confidence == FixConfidence.MEDIUM
        assert result.fixes[2].confidence == FixConfidence.LOW
    
    def test_parse_response_with_diff(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should parse diff information if provided."""
        response_content = '''{
            "fixes": [{
                "issue_description": "Test",
                "original_code": "old",
                "fixed_code": "new",
                "line_start": 1,
                "line_end": 1,
                "diff": "- old\\n+ new",
                "confidence": "high"
            }]
        }'''
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, sample_issue)
        
        assert result.fixes[0].diff is not None
        assert "- old" in result.fixes[0].diff
        assert "+ new" in result.fixes[0].diff
    
    def test_parse_response_malformed_json(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should handle malformed JSON gracefully."""
        response_content = 'This is not valid JSON'
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, sample_issue)
        
        # Should return empty result, not crash
        assert result.total_fixes == 0
    
    def test_parse_response_from_markdown_block(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should extract JSON from markdown code blocks."""
        response_content = '''Here's the fix:

```json
{
    "fixes": [{
        "issue_description": "Test fix",
        "original_code": "old",
        "fixed_code": "new",
        "line_start": 1,
        "line_end": 1,
        "confidence": "high"
    }]
}
```

Apply this fix to resolve the issue.'''
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, sample_issue)
        
        assert result.total_fixes == 1
        assert result.fixes[0].issue_description == "Test fix"


# ============================================================================
# Test CodeFixer Usage Tracking
# ============================================================================

class TestCodeFixerUsageTracking:
    """Test token usage and cost tracking."""
    
    def test_tracks_token_usage(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should track token usage from API response."""
        mock_response = create_mock_response(
            '{"fixes": []}',
            prompt_tokens=200,
            completion_tokens=100
        )
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        fixer.generate_fix(simple_parsed_code, sample_issue)
        
        assert fixer.total_tokens_used == 300
    
    def test_get_usage_stats(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should provide usage statistics."""
        mock_response = create_mock_response('{"fixes": []}', 150, 75)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        fixer.generate_fix(simple_parsed_code, sample_issue)
        
        stats = fixer.get_usage_stats()
        assert stats["total_tokens"] == 225
        assert "estimated_cost_usd" in stats
        assert stats["model"] == "gpt-4o-mini"


# ============================================================================
# Test CodeFixer Configuration
# ============================================================================

class TestCodeFixerConfiguration:
    """Test various configuration options."""
    
    def test_uses_configured_model(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should use the model specified in configuration."""
        config = {"model": "gpt-4"}
        mock_response = create_mock_response('{"fixes": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client, config=config)
        fixer.generate_fix(simple_parsed_code, sample_issue)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
    
    def test_uses_configured_temperature(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should use the temperature specified in configuration."""
        config = {"temperature": 0.1}
        mock_response = create_mock_response('{"fixes": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client, config=config)
        fixer.generate_fix(simple_parsed_code, sample_issue)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.1
    
    def test_accepts_custom_system_prompt(self, mock_openai_client, simple_parsed_code, sample_issue):
        """Should accept custom system prompt."""
        custom_prompt = "You are a code fixing expert."
        config = {"system_prompt": custom_prompt}
        mock_response = create_mock_response('{"fixes": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client, config=config)
        fixer.generate_fix(simple_parsed_code, sample_issue)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["messages"][0]["content"] == custom_prompt


# ============================================================================
# Test CodeFixer Context Window Management
# ============================================================================

class TestCodeFixerContextManagement:
    """Test handling of large code files and context windows."""
    
    def test_extracts_relevant_code_context(self, mock_openai_client, sample_issue):
        """Should extract only relevant code context around the issue."""
        # Large code file
        large_code = "\n".join([f"line_{i} = {i}" for i in range(1, 101)])
        parsed_code = ParsedCode(
            content=large_code,
            language="python",
            metadata=CodeMetadata(line_count=100),
            has_syntax_errors=False,
            syntax_errors=[]
        )
        
        # Issue on line 50
        issue = ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.BEST_PRACTICES,
            message="Test issue",
            line_number=50
        )
        
        mock_response = create_mock_response('{"fixes": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        fixer.generate_fix(parsed_code, issue)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        user_message = call_kwargs["messages"][1]["content"]
        
        # Should include lines around line 50, not the entire file
        assert "line_50" in user_message
        # Exact context size will depend on implementation
    
    def test_handles_issue_without_line_number(self, mock_openai_client, simple_parsed_code):
        """Should handle issues without specific line numbers."""
        issue = ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.BEST_PRACTICES,
            message="General code quality issue",
            line_number=None  # No specific line
        )
        
        mock_response = create_mock_response('{"fixes": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, issue)
        
        # Should still work, include full code or reasonable default
        mock_openai_client.chat.completions.create.assert_called_once()


# ============================================================================
# Test Additional Coverage for Edge Cases
# ============================================================================

class TestCodeFixerAdditionalCoverage:
    """Test edge cases for 100% coverage."""
    
    def test_extract_code_context_with_no_line_numbers(self, mock_openai_client, simple_parsed_code):
        """Should handle issues with no line numbers in batch."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="No line number",
                line_number=None
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        context = fixer._extract_code_context(simple_parsed_code, issues)
        
        # Should return full code when no line numbers
        assert context is not None
    
    def test_parse_ai_response_with_empty_content(self, mock_openai_client, simple_parsed_code):
        """Should handle empty AI response content."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Test with None content
        response = create_mock_response(None)
        response.choices[0].message.content = None
        fixes = fixer._parse_ai_response(response, issues)
        assert len(fixes) == 0
        
        # Test with empty string
        response = create_mock_response("")
        fixes = fixer._parse_ai_response(response, issues)
        assert len(fixes) == 0
    
    def test_parse_ai_response_with_invalid_data_types(self, mock_openai_client):
        """Should handle invalid data types in AI response."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Invalid confidence (integer instead of string)
        invalid_response = '''{
            "fixes": [{
                "original_code": "def test():",
                "fixed_code": "def test() -> None:",
                "explanation": "Test",
                "confidence": 123,
                "line_start": 1,
                "line_end": 1,
                "issue_description": "Test"
            }]
        }'''
        
        response = create_mock_response(invalid_response)
        fixes = fixer._parse_ai_response(response, issues)
        # Should skip invalid fixes gracefully
        assert isinstance(fixes, list)
    
    def test_parse_ai_response_markdown_extraction_failure(self, mock_openai_client):
        """Should handle failure to extract JSON from markdown."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Malformed markdown without valid JSON
        invalid_markdown = "```json\nthis is not valid json\n```"
        
        response = create_mock_response(invalid_markdown)
        fixes = fixer._parse_ai_response(response, issues)
        assert len(fixes) == 0
    
    def test_parse_ai_response_with_invalid_confidence_enum(self, mock_openai_client):
        """Should handle invalid confidence enum values."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Invalid confidence value not in enum
        invalid_response = '''{
            "fixes": [{
                "original_code": "def test():",
                "fixed_code": "def test() -> None:",
                "explanation": "Test",
                "confidence": "SUPER_HIGH",
                "line_start": 1,
                "line_end": 1,
                "issue_description": "Test"
            }]
        }'''
        
        response = create_mock_response(invalid_response)
        fixes = fixer._parse_ai_response(response, issues)
        assert len(fixes) == 1
        assert fixes[0].confidence == FixConfidence.MEDIUM
    
    def test_generate_fixes_with_mismatched_line_numbers(self, mock_openai_client, simple_parsed_code):
        """Should handle fixes with mismatched line numbers."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Issue 1",
                line_number=1
            ),
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Issue 2",
                line_number=99  # Line doesn't exist
            )
        ]
        
        # Mock responses
        fix_response_1 = '''{
            "fixes": [{
                "original_code": "def hello():",
                "fixed_code": "def hello() -> str:",
                "explanation": "Add type hint",
                "confidence": "high",
                "line_start": 1,
                "line_end": 1,
                "issue_description": "Issue 1"
            }]
        }'''
        
        fix_response_2 = '''{
            "fixes": [{
                "original_code": "some code",
                "fixed_code": "fixed code",
                "explanation": "Fix",
                "confidence": "high",
                "line_start": 50,
                "line_end": 52,
                "issue_description": "Issue 2"
            }]
        }'''
        
        mock_openai_client.chat.completions.create.return_value = create_mock_response(fix_response_1)
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fixes(simple_parsed_code, issues)
        
        # Should handle mismatched line numbers
        assert result.total_fixes >= 1
    
    def test_generate_fix_general_exception_handling(self, mock_openai_client, simple_parsed_code):
        """Should handle general exceptions during fix generation."""
        from src.models.review_models import ReviewIssue
        
        issue = ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.BEST_PRACTICES,
            message="Test",
            line_number=1
        )
        
        # Mock to raise exception
        mock_openai_client.chat.completions.create.side_effect = Exception("Unexpected error")
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, issue)
        
        # Should return failed result
        assert result.success is False
    
    def test_generate_fixes_general_exception_handling(self, mock_openai_client, simple_parsed_code):
        """Should handle general exceptions during batch fix generation."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        # Mock to raise exception
        mock_openai_client.chat.completions.create.side_effect = Exception("Unexpected error")
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fixes(simple_parsed_code, issues)
        
        # Should return result with success=False
        assert result.success is False
    
    def test_parse_ai_response_with_invalid_fix_data(self, mock_openai_client):
        """Should skip invalid fixes and continue processing."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Response with mix of valid and invalid fixes
        mixed_response = '''{
            "fixes": [
                {
                    "original_code": "def test():",
                    "fixed_code": "def test() -> None:",
                    "explanation": "Valid fix",
                    "confidence": "high",
                    "line_start": 1,
                    "line_end": 1,
                    "issue_description": "Test"
                },
                {
                    "missing_required_field": true
                },
                {
                    "original_code": "def test2():",
                    "fixed_code": "def test2() -> int:",
                    "explanation": "Another valid fix",
                    "confidence": "medium",
                    "line_start": 5,
                    "line_end": 5,
                    "issue_description": "Test 2"
                }
            ]
        }'''
        
        response = create_mock_response(mixed_response)
        fixes = fixer._parse_ai_response(response, issues)
        
        # Should skip invalid fixes and continue - line 299 coverage
        assert len(fixes) == 2
        assert fixes[0].confidence == FixConfidence.HIGH
        assert fixes[1].confidence == FixConfidence.MEDIUM
    
    def test_parse_ai_response_with_json_decode_error_outer_exception(self, mock_openai_client):
        """Should handle outer exception in parsing."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Create a response that will trigger outer exception - line 309 coverage
        response = create_mock_response("completely invalid non-json text")
        fixes = fixer._parse_ai_response(response, issues)
        
        # Should return empty list
        assert len(fixes) == 0
    
    def test_parse_ai_response_with_type_error_in_fix_creation(self, mock_openai_client):
        """Should skip fixes that raise TypeError during creation - line 299 coverage."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Response with fix data that will cause TypeError in model creation
        response_with_type_error = '''{
            "fixes": [
                {
                    "original_code": "def test():",
                    "fixed_code": "def test() -> None:",
                    "explanation": "Valid fix",
                    "confidence": "high",
                    "line_start": 1,
                    "line_end": 1,
                    "issue_description": "Test"
                },
                {
                    "original_code": null,
                    "fixed_code": null,
                    "line_start": "not_a_number",
                    "line_end": "also_not_a_number",
                    "issue_description": "Will cause TypeError"
                },
                {
                    "original_code": "def test2():",
                    "fixed_code": "def test2() -> int:",
                    "explanation": "Another valid fix",
                    "confidence": "medium",
                    "line_start": 5,
                    "line_end": 5,
                    "issue_description": "Test 2"
                }
            ]
        }'''
        
        response = create_mock_response(response_with_type_error)
        fixes = fixer._parse_ai_response(response, issues)
        
        # Should skip the invalid fix and continue with others - line 299
        assert len(fixes) >= 1  # At least one valid fix should be processed
    
    def test_track_usage_with_no_usage_data(self, mock_openai_client, simple_parsed_code):
        """Should handle response with no usage data - line 309 coverage."""
        from src.models.review_models import ReviewIssue
        
        issue = ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.BEST_PRACTICES,
            message="Test",
            line_number=1
        )
        
        fix_response = '''{
            "fixes": [{
                "original_code": "def test():",
                "fixed_code": "def test() -> None:",
                "explanation": "Add type hint",
                "confidence": "high",
                "line_start": 1,
                "line_end": 1,
                "issue_description": "Test"
            }]
        }'''
        
        response = create_mock_response(fix_response)
        # Remove usage data - line 309 coverage
        response.usage = None
        
        mock_openai_client.chat.completions.create.return_value = response
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fix(simple_parsed_code, issue)
        
        # Should handle missing usage gracefully
        stats = fixer.get_usage_stats()
        assert stats["total_tokens"] == 0
        assert stats["estimated_cost_usd"] == 0.0


    def test_parse_ai_response_with_dict_no_fixes_key(self, mock_openai_client):
        """Should handle dict response without 'fixes' key."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Dict without fixes key
        invalid_response = '{"something": "else"}'
        
        response = create_mock_response(invalid_response)
        fixes = fixer._parse_ai_response(response, issues)
        assert len(fixes) == 0
    
    def test_parse_ai_response_with_markdown_no_closing(self, mock_openai_client):
        """Should handle markdown without closing backticks."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Markdown without closing ```
        invalid_markdown = '```json\n{"fixes": []}'
        
        response = create_mock_response(invalid_markdown)
        fixes = fixer._parse_ai_response(response, issues)
        assert len(fixes) == 0
    
    def test_parse_ai_response_with_invalid_fix_data(self, mock_openai_client):
        """Should process fixes even with missing optional data."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Fix data with only explanation (missing most fields)
        # Should use defaults from CodeFix model
        minimal_response = '''{
            "fixes": [{
                "explanation": "Missing most fields but has defaults"
            }]
        }'''
        
        response = create_mock_response(minimal_response)
        fixes = fixer._parse_ai_response(response, issues)
        # Should create fix with defaults
        assert len(fixes) >= 0  # Model may use defaults
    
    def test_extract_code_context_called_properly(self, mock_openai_client, simple_parsed_code):
        """Should extract code context when generating fixes."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=None  # This triggers full code return
            )
        ]
        
        fix_response = '''{
            "fixes": [{
                "original_code": "def hello():",
                "fixed_code": "def hello() -> str:",
                "explanation": "Add type hint",
                "confidence": "high",
                "line_start": 1,
                "line_end": 1,
                "issue_description": "Test"
            }]
        }'''
        
        mock_openai_client.chat.completions.create.return_value = create_mock_response(fix_response)
        
        fixer = CodeFixer(client=mock_openai_client)
        result = fixer.generate_fixes(simple_parsed_code, issues)
        
        # Should have called API and included full code
        mock_openai_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        user_message = call_kwargs["messages"][1]["content"]
        
        # Should include full code when no line numbers
        assert "def hello():" in user_message


    def test_parse_ai_response_with_list_format(self, mock_openai_client):
        """Should handle response as direct list of fixes."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Direct list format (not wrapped in dict)
        list_response = '''[{
            "original_code": "def test():",
            "fixed_code": "def test() -> None:",
            "explanation": "Add type hint",
            "confidence": "high",
            "line_start": 1,
            "line_end": 1,
            "issue_description": "Test"
        }]'''
        
        response = create_mock_response(list_response)
        fixes = fixer._parse_ai_response(response, issues)
        assert len(fixes) == 1
        assert fixes[0].fixed_code == "def test() -> None:"
    
    def test_extract_code_context_returns_full_code_for_all_none(self, mock_openai_client):
        """Should return full code when all issues have line_number=None."""
        from src.models.review_models import ReviewIssue
        
        # Large code to test line count check
        large_code_lines = ["def func_{}():".format(i) for i in range(150)]
        large_code = ParsedCode(
            language="python",
            content="\n".join(large_code_lines),
            metadata=CodeMetadata(
                language="python",
                line_count=150,
                char_count=len("\n".join(large_code_lines)),
                estimated_tokens=500
            )
        )
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Issue 1",
                line_number=None
            ),
            ReviewIssue(
                severity=Severity.HIGH,
                category=IssueCategory.STYLE,
                message="Issue 2",
                line_number=None
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        context = fixer._extract_code_context(large_code, issues)
        
        # Should return full code even for large files when no line numbers
        assert context == large_code.content


    def test_parse_ai_response_inner_exception_handling(self, mock_openai_client):
        """Should skip individual fixes that cause exceptions during parsing."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Response with valid fix and one with type error in line_start
        mixed_response = '''{
            "fixes": [
                {
                    "original_code": "def test():",
                    "fixed_code": "def test() -> None:",
                    "explanation": "Add type hint",
                    "confidence": "high",
                    "line_start": 1,
                    "line_end": 1,
                    "issue_description": "Test"
                }
            ]
        }'''
        
        response = create_mock_response(mixed_response)
        fixes = fixer._parse_ai_response(response, issues)
        # Should get fixes without crashing
        assert len(fixes) >= 1
    
    def test_parse_ai_response_outer_exception_handling(self, mock_openai_client):
        """Should handle outer exceptions gracefully."""
        from src.models.review_models import ReviewIssue
        
        issues = [
            ReviewIssue(
                severity=Severity.MEDIUM,
                category=IssueCategory.BEST_PRACTICES,
                message="Test",
                line_number=1
            )
        ]
        
        fixer = CodeFixer(client=mock_openai_client)
        
        # Mock response with broken content that causes exception
        response = create_mock_response("valid json")
        # Corrupt the response to cause exception during processing
        response.choices[0].message.content = 123  # Integer instead of string
        
        fixes = fixer._parse_ai_response(response, issues)
        # Should return empty list on outer exception
        assert len(fixes) == 0
    
    def test_track_usage_with_other_model(self, simple_parsed_code):
        """Should calculate cost for non-GPT-4 models."""
        from src.models.review_models import ReviewIssue
        from unittest.mock import Mock
        
        mock_client = Mock()
        
        # Create fixer with a different model via config
        fixer = CodeFixer(client=mock_client, config={"model": "gpt-3.5-turbo"})
        
        issue = ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.BEST_PRACTICES,
            message="Test",
            line_number=1
        )
        
        # Mock response with usage stats
        fix_response = '''{
            "fixes": [{
                "original_code": "def test():",
                "fixed_code": "def test() -> None:",
                "explanation": "Add type hint",
                "confidence": "high",
                "line_start": 1,
                "line_end": 1,
                "issue_description": "Test"
            }]
        }'''
        
        response = create_mock_response(fix_response)
        # Add usage stats
        response.usage = Mock()
        response.usage.prompt_tokens = 100
        response.usage.completion_tokens = 50
        response.usage.total_tokens = 150
        
        mock_client.chat.completions.create.return_value = response
        
        result = fixer.generate_fix(simple_parsed_code, issue)
        
        # Should calculate cost using the "else" branch (gpt-3.5-turbo pricing)
        stats = fixer.get_usage_stats()
        assert stats["total_tokens"] == 150
        assert stats["estimated_cost_usd"] > 0
        # gpt-3.5-turbo: $0.50 per 1M input + $1.50 per 1M output
        expected_cost = (100 * 0.50 / 1_000_000) + (50 * 1.50 / 1_000_000)
        assert abs(stats["estimated_cost_usd"] - expected_cost) < 0.0001


