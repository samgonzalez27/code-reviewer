"""
Unit tests for AI-powered prompt generator service.
"""
import pytest
from unittest.mock import Mock, patch
from src.models.review_models import ReviewResult, ReviewIssue, Severity, IssueCategory
from src.models.prompt_models import PromptGenerationResult, PromptSuggestion


class TestPromptGeneratorInitialization:
    """Test PromptGenerator initialization."""
    
    def test_prompt_generator_accepts_openai_client(self):
        """Should accept an OpenAI client instance."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        assert generator.client == mock_client
    
    def test_prompt_generator_creates_client_from_env(self):
        """Should create OpenAI client from environment variable."""
        from src.services.prompt_generator import PromptGenerator
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.services.prompt_generator.OpenAI') as mock_openai:
                generator = PromptGenerator()
                
                mock_openai.assert_called_once_with(api_key='test-key')
    
    def test_prompt_generator_raises_error_if_no_api_key(self):
        """Should raise error if no API key and no client provided."""
        from src.services.prompt_generator import PromptGenerator
        
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                PromptGenerator()
    
    def test_prompt_generator_accepts_configuration(self):
        """Should accept and store configuration."""
        from src.services.prompt_generator import PromptGenerator
        
        config = {
            "model": "gpt-4o",
            "temperature": 0.5,
            "max_prompts": 3
        }
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client, config=config)
        
        assert generator.model == "gpt-4o"
        assert generator.temperature == 0.5
        assert generator.max_prompts == 3
    
    def test_prompt_generator_uses_default_configuration(self):
        """Should use default configuration when not provided."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        assert generator.model == "gpt-4o-mini"
        assert generator.temperature == 0.3
        assert generator.max_prompts == 5


class TestPromptGeneratorBasicGeneration:
    """Test basic prompt generation functionality."""
    
    def test_generate_returns_prompt_generation_result(self):
        """Should return PromptGenerationResult instance."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="SQL injection vulnerability",
            line_number=42
        ))
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Fix SQL injection on line 42"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generator.generate(review_result, language="python")
        
        assert isinstance(result, PromptGenerationResult)
    
    def test_generate_with_no_issues_returns_empty_result(self):
        """Should return empty result when no issues to address."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()  # No issues
        
        result = generator.generate(review_result, language="python")
        
        assert not result.has_prompts()
        assert result.total_issues_covered == 0
    
    def test_generate_calls_openai_api(self):
        """Should call OpenAI API to generate prompts."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="Hardcoded API key",
            line_number=10
        ))
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Remove hardcoded credentials"
        mock_client.chat.completions.create.return_value = mock_response
        
        generator.generate(review_result, language="python")
        
        mock_client.chat.completions.create.assert_called_once()
    
    def test_generate_groups_issues_by_category(self):
        """Should group issues by category before generating prompts."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        
        # Add multiple issues in same category
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="SQL injection",
            line_number=42
        ))
        review_result.add_issue(ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.SECURITY,
            message="Hardcoded secret",
            line_number=58
        ))
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Fix all security issues"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generator.generate(review_result, language="python")
        
        # Should have 1 prompt covering both security issues
        security_prompt = result.get_prompt_by_category(IssueCategory.SECURITY)
        assert security_prompt is not None
        assert security_prompt.issue_count == 2


class TestPromptGeneratorPrioritization:
    """Test prompt prioritization logic."""
    
    def test_prioritizes_high_severity_categories(self):
        """Should prioritize categories with higher severity issues."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client, config={"max_prompts": 2})
        
        review_result = ReviewResult()
        
        # Add high severity security issue
        review_result.add_issue(ReviewIssue(
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            message="Security issue",
            line_number=10
        ))
        
        # Add low severity style issues
        for i in range(10):
            review_result.add_issue(ReviewIssue(
                severity=Severity.LOW,
                category=IssueCategory.STYLE,
                message=f"Style issue {i}",
                line_number=i
            ))
        
        # Add medium complexity issue
        review_result.add_issue(ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.COMPLEXITY,
            message="Complex function",
            line_number=50
        ))
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Fix the issues"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generator.generate(review_result, language="python")
        
        # Should generate prompts for security first (critical)
        assert result.get_prompt_by_category(IssueCategory.SECURITY) is not None
        
        # Should have max 2 prompts
        assert len(result.prompts) <= 2
    
    def test_respects_max_prompts_limit(self):
        """Should not exceed max_prompts configuration."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client, config={"max_prompts": 3})
        
        review_result = ReviewResult()
        
        # Add issues in 5 different categories
        categories = [
            IssueCategory.SECURITY,
            IssueCategory.BUG_RISK,
            IssueCategory.PERFORMANCE,
            IssueCategory.STYLE,
            IssueCategory.COMPLEXITY
        ]
        
        for category in categories:
            review_result.add_issue(ReviewIssue(
                severity=Severity.MEDIUM,
                category=category,
                message=f"{category.value} issue",
                line_number=10
            ))
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Fix issues"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generator.generate(review_result, language="python")
        
        # Should only generate 3 prompts
        assert len(result.prompts) == 3


class TestPromptGeneratorPromptContent:
    """Test prompt content generation."""
    
    def test_prompt_includes_python_swe_standards(self):
        """Generated prompts should reference Python SWE best practices."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="SQL injection vulnerability",
            line_number=42
        ))
        
        # Verify the prompt sent to OpenAI mentions Python and professional standards
        def check_prompt_content(*args, **kwargs):
            messages = kwargs.get('messages', [])
            user_message = next((m for m in messages if m['role'] == 'user'), None)
            
            assert user_message is not None
            content = user_message['content']
            assert 'python' in content.lower()
            assert 'professional' in content.lower() or 'swe' in content.lower()
            
            # Return mock response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Fix SQL injection"
            return mock_response
        
        mock_client.chat.completions.create.side_effect = check_prompt_content
        
        generator.generate(review_result, language="python")
    
    def test_prompt_includes_issue_details(self):
        """Generated prompts should include specific issue details."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="Hardcoded API key on line 42",
            line_number=42,
            suggestion="Use environment variables"
        ))
        
        def check_issue_details(*args, **kwargs):
            messages = kwargs.get('messages', [])
            user_message = next((m for m in messages if m['role'] == 'user'), None)
            
            content = user_message['content']
            assert 'security' in content.lower()
            assert '42' in content or 'line' in content.lower()
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Use environment variables for API keys"
            return mock_response
        
        mock_client.chat.completions.create.side_effect = check_issue_details
        
        generator.generate(review_result, language="python")
    
    def test_prompt_is_copilot_ready(self):
        """Generated prompts should be formatted for GitHub Copilot."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.COMPLEXITY,
            message="Function has high cyclomatic complexity",
            line_number=100
        ))
        
        def check_copilot_format(*args, **kwargs):
            messages = kwargs.get('messages', [])
            system_message = next((m for m in messages if m['role'] == 'system'), None)
            
            assert system_message is not None
            content = system_message['content']
            assert 'copilot' in content.lower() or 'github' in content.lower()
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Refactor to reduce complexity"
            return mock_response
        
        mock_client.chat.completions.create.side_effect = check_copilot_format
        
        generator.generate(review_result, language="python")


class TestPromptGeneratorSeveritySummary:
    """Test severity summary generation in prompts."""
    
    def test_severity_summary_single_severity(self):
        """Should generate correct summary for single severity level."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        
        # Add 3 high severity issues in same category
        for i in range(3):
            review_result.add_issue(ReviewIssue(
                severity=Severity.HIGH,
                category=IssueCategory.SECURITY,
                message=f"Security issue {i}",
                line_number=i * 10
            ))
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Fix security issues"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generator.generate(review_result, language="python")
        
        security_prompt = result.get_prompt_by_category(IssueCategory.SECURITY)
        assert security_prompt is not None
        assert "3 high" in security_prompt.severity_summary.lower()
    
    def test_severity_summary_multiple_severities(self):
        """Should generate correct summary for multiple severity levels."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        
        # Add 2 high, 3 medium security issues
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="High severity 1",
            line_number=10
        ))
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="High severity 2",
            line_number=20
        ))
        review_result.add_issue(ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.SECURITY,
            message="Medium severity 1",
            line_number=30
        ))
        review_result.add_issue(ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.SECURITY,
            message="Medium severity 2",
            line_number=40
        ))
        review_result.add_issue(ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.SECURITY,
            message="Medium severity 3",
            line_number=50
        ))
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Fix security issues"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generator.generate(review_result, language="python")
        
        security_prompt = result.get_prompt_by_category(IssueCategory.SECURITY)
        assert security_prompt is not None
        # Should contain both counts
        summary = security_prompt.severity_summary.lower()
        assert "2 high" in summary
        assert "3 medium" in summary


class TestPromptGeneratorErrorHandling:
    """Test error handling in prompt generation."""
    
    def test_handles_openai_api_error_gracefully(self):
        """Should handle OpenAI API errors without crashing."""
        from src.services.prompt_generator import PromptGenerator
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="Security issue",
            line_number=10
        ))
        
        # Mock API error - just use Exception since APIError requires request object
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        result = generator.generate(review_result, language="python")
        
        # Should return empty result rather than crash
        assert isinstance(result, PromptGenerationResult)
        assert not result.has_prompts()
        assert not result.has_prompts()
    
    def test_handles_timeout_gracefully(self):
        """Should handle request timeout without crashing."""
        from src.services.prompt_generator import PromptGenerator
        from openai import APITimeoutError
        
        mock_client = Mock()
        generator = PromptGenerator(client=mock_client)
        
        review_result = ReviewResult()
        review_result.add_issue(ReviewIssue(
            severity=Severity.MEDIUM,
            category=IssueCategory.COMPLEXITY,
            message="Complex function",
            line_number=50
        ))
        
        mock_client.chat.completions.create.side_effect = APITimeoutError("Timeout")
        
        result = generator.generate(review_result, language="python")
        
        assert isinstance(result, PromptGenerationResult)
        assert not result.has_prompts()
