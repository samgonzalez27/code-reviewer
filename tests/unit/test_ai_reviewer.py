"""
Unit tests for AI-powered code reviewer.

Tests the AIReviewer class with mocked OpenAI API responses
to ensure proper integration and error handling.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types import CompletionUsage

from src.services.ai_reviewer import AIReviewer
from src.services.review_engine import ReviewStrategy
from src.models.code_models import ParsedCode, CodeMetadata
from src.models.review_models import Severity, IssueCategory


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
def code_with_syntax_errors():
    """Create ParsedCode with syntax errors."""
    return ParsedCode(
        content="def broken(\n",
        language="python",
        metadata=CodeMetadata(line_count=1),
        has_syntax_errors=True,
        syntax_errors=["Line 1: unexpected EOF while parsing"]
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
# Test AIReviewer Initialization
# ============================================================================

class TestAIReviewerInitialization:
    """Test AIReviewer initialization and configuration."""
    
    def test_ai_reviewer_implements_review_strategy(self, mock_openai_client):
        """AIReviewer should implement ReviewStrategy interface."""
        reviewer = AIReviewer(client=mock_openai_client)
        assert isinstance(reviewer, ReviewStrategy)
    
    def test_ai_reviewer_accepts_openai_client(self, mock_openai_client):
        """AIReviewer should accept OpenAI client via constructor."""
        reviewer = AIReviewer(client=mock_openai_client)
        assert reviewer.client == mock_openai_client
    
    def test_ai_reviewer_creates_client_from_env(self):
        """AIReviewer should create client from environment if not provided."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.services.ai_reviewer.OpenAI') as mock_openai_class:
                reviewer = AIReviewer()
                mock_openai_class.assert_called_once_with(api_key='test-key')
    
    def test_ai_reviewer_raises_error_if_no_api_key(self):
        """AIReviewer should raise error if no API key available."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                AIReviewer()
    
    def test_ai_reviewer_accepts_configuration(self, mock_openai_client):
        """AIReviewer should accept and store configuration."""
        config = {
            "model": "gpt-4",
            "temperature": 0.5,
            "max_tokens": 1000,
            "timeout": 60
        }
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        assert reviewer.model == "gpt-4"
        assert reviewer.temperature == 0.5
        assert reviewer.max_tokens == 1000
        assert reviewer.timeout == 60
    
    def test_ai_reviewer_uses_default_configuration(self, mock_openai_client):
        """AIReviewer should use sensible defaults if no config provided."""
        reviewer = AIReviewer(client=mock_openai_client)
        assert reviewer.model == "gpt-4o-mini"
        assert reviewer.temperature == 0.3
        assert reviewer.max_tokens == 2000
        assert reviewer.timeout == 30
    
    def test_ai_reviewer_accepts_custom_system_prompt(self, mock_openai_client):
        """AIReviewer should accept custom system prompt."""
        custom_prompt = "You are a security-focused code reviewer."
        config = {"system_prompt": custom_prompt}
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        assert reviewer.system_prompt == custom_prompt


# ============================================================================
# Test AIReviewer Basic Review
# ============================================================================

class TestAIReviewerBasicReview:
    """Test basic review functionality."""
    
    def test_review_returns_review_result(self, mock_openai_client, simple_parsed_code):
        """Review should return a ReviewResult object."""
        # Mock API response with no issues
        mock_response = create_mock_response('{"issues": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(simple_parsed_code)
        
        from src.models.review_models import ReviewResult
        assert isinstance(result, ReviewResult)
        assert result.reviewer_name == "AIReviewer"
    
    def test_review_calls_openai_api(self, mock_openai_client, simple_parsed_code):
        """Review should call OpenAI chat completion API."""
        mock_response = create_mock_response('{"issues": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        reviewer.review(simple_parsed_code)
        
        mock_openai_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["role"] == "user"
        assert "python" in call_kwargs["messages"][1]["content"].lower()
    
    def test_review_includes_code_in_prompt(self, mock_openai_client, simple_parsed_code):
        """Review should include the code content in the prompt."""
        mock_response = create_mock_response('{"issues": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        reviewer.review(simple_parsed_code)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        user_message = call_kwargs["messages"][1]["content"]
        
        assert "def hello():" in user_message
        assert "return 'Hello, World!'" in user_message
    
    def test_review_includes_metadata_in_prompt(self, mock_openai_client, simple_parsed_code):
        """Review should include code metadata in the prompt."""
        mock_response = create_mock_response('{"issues": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        reviewer.review(simple_parsed_code)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        user_message = call_kwargs["messages"][1]["content"]
        
        assert "Lines: 2" in user_message
        assert "Functions: 1" in user_message
        assert "Classes: 0" in user_message


# ============================================================================
# Test AIReviewer Response Parsing
# ============================================================================

class TestAIReviewerResponseParsing:
    """Test parsing of AI responses into ReviewIssue objects."""
    
    def test_parse_response_with_single_issue(self, mock_openai_client, simple_parsed_code):
        """Should parse AI response with single issue correctly."""
        response_content = '''{"issues": [
            {
                "severity": "medium",
                "category": "best_practices",
                "message": "Function lacks type hints",
                "line_number": 1,
                "suggestion": "Add type hints for parameters and return value"
            }
        ]}'''
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(simple_parsed_code)
        
        assert result.total_issues == 1
        assert result.medium_count == 1
        issue = result.issues[0]
        assert issue.severity == Severity.MEDIUM
        assert issue.category == IssueCategory.BEST_PRACTICES
        assert "type hints" in issue.message
        assert issue.line_number == 1
    
    def test_parse_response_with_multiple_issues(self, mock_openai_client, simple_parsed_code):
        """Should parse AI response with multiple issues."""
        response_content = '''{"issues": [
            {
                "severity": "low",
                "category": "documentation",
                "message": "Missing docstring",
                "line_number": 1
            },
            {
                "severity": "high",
                "category": "security",
                "message": "Potential injection risk",
                "line_number": 2
            }
        ]}'''
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(simple_parsed_code)
        
        assert result.total_issues == 2
        assert result.low_count == 1
        assert result.high_count == 1
    
    def test_parse_response_array_format(self, mock_openai_client, simple_parsed_code):
        """Should handle response as direct array (without 'issues' key)."""
        response_content = '''[
            {
                "severity": "info",
                "category": "style",
                "message": "Consider using single quotes",
                "line_number": 2
            }
        ]'''
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(simple_parsed_code)
        
        assert result.total_issues == 1
        assert result.info_count == 1
    
    def test_parse_response_with_markdown_json(self, mock_openai_client, simple_parsed_code):
        """Should extract JSON from markdown code blocks."""
        response_content = '''Here are the issues I found:

```json
[
    {
        "severity": "critical",
        "category": "security",
        "message": "Hardcoded secret detected",
        "line_number": 5
    }
]
```

These should be addressed immediately.'''
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(simple_parsed_code)
        
        assert result.total_issues == 1
        assert result.critical_count == 1
    
    def test_parse_response_empty_issues(self, mock_openai_client, simple_parsed_code):
        """Should handle empty issues array gracefully."""
        response_content = '{"issues": []}'
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(simple_parsed_code)
        
        assert result.total_issues == 0
    
    def test_parse_response_malformed_json(self, mock_openai_client, simple_parsed_code):
        """Should handle malformed JSON gracefully without crashing."""
        response_content = 'This is not valid JSON at all!'
        
        mock_response = create_mock_response(response_content)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(simple_parsed_code)
        
        # Should return empty result, not crash
        assert result.total_issues == 0


# ============================================================================
# Test AIReviewer Error Handling
# ============================================================================

class TestAIReviewerErrorHandling:
    """Test error handling and edge cases."""
    
    def test_review_skips_code_with_syntax_errors(self, mock_openai_client, code_with_syntax_errors):
        """Should skip AI review if code has syntax errors."""
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(code_with_syntax_errors)
        
        # Should not call API
        mock_openai_client.chat.completions.create.assert_not_called()
        
        # Should add info message about skipping
        assert result.total_issues == 1
        assert result.info_count == 1
        assert "syntax errors" in result.issues[0].message.lower()
    
    def test_review_handles_api_exception(self, mock_openai_client, simple_parsed_code):
        """Should handle API exceptions gracefully."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(simple_parsed_code)
        
        # Should return result with error message, not crash
        assert result.total_issues == 1
        assert "AI review failed" in result.issues[0].message
        assert "API Error" in result.issues[0].message
    
    def test_review_handles_timeout(self, mock_openai_client, simple_parsed_code):
        """Should handle API timeout gracefully."""
        from openai import APITimeoutError
        mock_openai_client.chat.completions.create.side_effect = APITimeoutError("Timeout")
        
        reviewer = AIReviewer(client=mock_openai_client)
        result = reviewer.review(simple_parsed_code)
        
        assert result.total_issues == 1
        assert "AI review failed" in result.issues[0].message


# ============================================================================
# Test AIReviewer Token Usage Tracking
# ============================================================================

class TestAIReviewerUsageTracking:
    """Test token usage and cost tracking."""
    
    def test_tracks_token_usage(self, mock_openai_client, simple_parsed_code):
        """Should track token usage from API response."""
        mock_response = create_mock_response(
            '{"issues": []}',
            prompt_tokens=150,
            completion_tokens=50
        )
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        reviewer.review(simple_parsed_code)
        
        assert reviewer.total_tokens_used == 200
    
    def test_tracks_cumulative_usage(self, mock_openai_client, simple_parsed_code):
        """Should track cumulative token usage across multiple reviews."""
        mock_response1 = create_mock_response('{"issues": []}', 100, 50)
        mock_response2 = create_mock_response('{"issues": []}', 120, 60)
        
        mock_openai_client.chat.completions.create.side_effect = [
            mock_response1,
            mock_response2
        ]
        
        reviewer = AIReviewer(client=mock_openai_client)
        reviewer.review(simple_parsed_code)
        reviewer.review(simple_parsed_code)
        
        assert reviewer.total_tokens_used == 330  # 150 + 180
    
    def test_get_usage_stats(self, mock_openai_client, simple_parsed_code):
        """Should provide usage statistics."""
        mock_response = create_mock_response('{"issues": []}', 100, 50)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client)
        reviewer.review(simple_parsed_code)
        
        stats = reviewer.get_usage_stats()
        assert stats["total_tokens"] == 150
        assert "estimated_cost_usd" in stats
        assert stats["model"] == "gpt-4o-mini"
    
    def test_estimates_cost_for_gpt4o(self, mock_openai_client, simple_parsed_code):
        """Should estimate cost correctly for GPT-4o model."""
        config = {"model": "gpt-4o"}
        mock_response = create_mock_response('{"issues": []}', 1000, 500)
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        reviewer.review(simple_parsed_code)
        
        stats = reviewer.get_usage_stats()
        # 1000 * $2.50/1M + 500 * $10/1M = $0.0025 + $0.005 = $0.0075
        assert stats["estimated_cost_usd"] > 0
        assert stats["estimated_cost_usd"] < 0.01


# ============================================================================
# Test AIReviewer Configuration Options
# ============================================================================

class TestAIReviewerConfiguration:
    """Test various configuration options."""
    
    def test_uses_configured_model(self, mock_openai_client, simple_parsed_code):
        """Should use the model specified in configuration."""
        config = {"model": "gpt-4"}
        mock_response = create_mock_response('{"issues": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        reviewer.review(simple_parsed_code)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
    
    def test_uses_configured_temperature(self, mock_openai_client, simple_parsed_code):
        """Should use the temperature specified in configuration."""
        config = {"temperature": 0.7}
        mock_response = create_mock_response('{"issues": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        reviewer.review(simple_parsed_code)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.7
    
    def test_uses_configured_max_tokens(self, mock_openai_client, simple_parsed_code):
        """Should use the max_tokens specified in configuration."""
        config = {"max_tokens": 500}
        mock_response = create_mock_response('{"issues": []}')
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        reviewer = AIReviewer(client=mock_openai_client, config=config)
        reviewer.review(simple_parsed_code)
        
        call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
        assert call_kwargs["max_tokens"] == 500
