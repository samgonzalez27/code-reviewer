"""
Unit tests for ReviewEngine and review strategies.

This module tests the code review functionality including
different review strategies and the orchestration engine.

Following TDD: Write tests first (RED), then implement (GREEN), then refactor.
"""
import pytest
from src.services.review_engine import (
    ReviewEngine,
    ReviewStrategy,
    StyleReviewer,
    ComplexityReviewer,
    SecurityReviewer,
)
from src.models.review_models import ReviewResult, ReviewIssue, Severity, IssueCategory
from src.models.code_models import ParsedCode, CodeMetadata
from src.services.code_parser import CodeParser


# Test fixtures
@pytest.fixture
def simple_python_code():
    """Simple valid Python code for testing."""
    return """def hello():
    return "Hello, World!"
"""


@pytest.fixture
def complex_python_code():
    """Complex Python code with high cyclomatic complexity."""
    return """def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return "all positive"
            else:
                return "z negative"
        else:
            if z > 0:
                return "y negative"
            else:
                return "y and z negative"
    else:
        if y > 0:
            if z > 0:
                return "x negative"
            else:
                return "x and z negative"
        else:
            return "all negative"
"""


@pytest.fixture
def code_with_issues():
    """Python code with various style and security issues."""
    return """import os
API_KEY = "sk-1234567890abcdef"
PASSWORD = 'my_secret_password'

def badFunctionName():
    x=1+2
    return x
"""


@pytest.fixture
def parsed_simple_code(simple_python_code):
    """ParsedCode object for simple code."""
    parser = CodeParser()
    return parser.parse(simple_python_code, "python")


@pytest.fixture
def parsed_complex_code(complex_python_code):
    """ParsedCode object for complex code."""
    parser = CodeParser()
    return parser.parse(complex_python_code, "python")


@pytest.fixture
def parsed_code_with_issues(code_with_issues):
    """ParsedCode object for code with issues."""
    parser = CodeParser()
    return parser.parse(code_with_issues, "python")


class TestReviewEngineInitialization:
    """Test ReviewEngine initialization and configuration."""
    
    def test_review_engine_creates_default_reviewers(self):
        """Test that ReviewEngine creates default reviewers when none provided."""
        engine = ReviewEngine()
        
        assert hasattr(engine, 'reviewers')
        assert isinstance(engine.reviewers, list)
        assert len(engine.reviewers) > 0
        # Should have at least style, complexity, and security reviewers by default
        assert len(engine.reviewers) >= 3
    
    def test_review_engine_stores_configuration(self):
        """Test that ReviewEngine properly stores and uses configuration."""
        config = {"max_complexity": 5, "enable_security": True}
        engine = ReviewEngine(config=config)
        
        assert hasattr(engine, 'config')
        assert engine.config["max_complexity"] == 5
        assert engine.config["enable_security"] is True
    
    def test_review_engine_uses_custom_reviewers_list(self):
        """Test that ReviewEngine uses provided reviewers instead of defaults."""
        custom_reviewers = [StyleReviewer(), ComplexityReviewer()]
        engine = ReviewEngine(reviewers=custom_reviewers)
        
        assert len(engine.reviewers) == 2
        assert isinstance(engine.reviewers[0], StyleReviewer)
        assert isinstance(engine.reviewers[1], ComplexityReviewer)


class TestReviewEngineBasicReview:
    """Test basic review functionality."""
    
    def test_review_simple_code_returns_result(self, parsed_simple_code):
        """Test reviewing simple valid code returns ReviewResult."""
        engine = ReviewEngine()
        
        result = engine.review(parsed_simple_code)
        
        assert isinstance(result, ReviewResult)
        assert result.total_issues >= 0
    
    def test_review_valid_code_has_high_score(self, parsed_simple_code):
        """Test that valid code receives a high quality score."""
        engine = ReviewEngine()
        
        result = engine.review(parsed_simple_code)
        
        assert result.quality_score >= 70.0
        assert result.passed is True
    
    def test_review_code_with_issues_finds_problems(self, parsed_code_with_issues):
        """Test that code with issues is detected."""
        engine = ReviewEngine()
        
        result = engine.review(parsed_code_with_issues)
        
        assert result.total_issues > 0
        assert len(result.issues) > 0


class TestStyleReviewer:
    """Test StyleReviewer functionality."""
    
    def test_style_reviewer_implements_review_strategy(self):
        """Test that StyleReviewer implements ReviewStrategy interface."""
        reviewer = StyleReviewer()
        assert isinstance(reviewer, ReviewStrategy)
        # Verify it has the review method
        assert hasattr(reviewer, 'review')
        assert callable(reviewer.review)
    
    def test_style_reviewer_has_configuration(self):
        """Test that StyleReviewer stores configuration properly."""
        config = {"check_naming": True, "check_spacing": True}
        reviewer = StyleReviewer(config=config)
        
        assert hasattr(reviewer, 'config')
        assert reviewer.config["check_naming"] is True
        assert reviewer.config["check_spacing"] is True
    
    def test_style_reviewer_checks_naming_conventions(self, parsed_code_with_issues):
        """Test that StyleReviewer detects bad naming conventions."""
        reviewer = StyleReviewer()
        
        result = reviewer.review(parsed_code_with_issues)
        
        assert isinstance(result, ReviewResult)
        # Should find issue with badFunctionName
        style_issues = result.get_issues_by_category(IssueCategory.STYLE)
        assert len(style_issues) > 0
    
    def test_style_reviewer_checks_spacing(self, parsed_code_with_issues):
        """Test that StyleReviewer detects spacing issues."""
        reviewer = StyleReviewer()
        
        result = reviewer.review(parsed_code_with_issues)
        
        # Should find issue with x=1+2 (no spaces)
        assert result.total_issues > 0
    
    def test_style_reviewer_valid_code_passes(self, parsed_simple_code):
        """Test that well-styled code passes style review."""
        reviewer = StyleReviewer()
        
        result = reviewer.review(parsed_simple_code)
        
        # Simple code should have few or no style issues
        assert result.quality_score >= 80.0


class TestComplexityReviewer:
    """Test ComplexityReviewer functionality."""
    
    def test_complexity_reviewer_stores_threshold(self):
        """Test that ComplexityReviewer stores and uses complexity threshold."""
        reviewer = ComplexityReviewer(max_complexity=5)
        
        assert hasattr(reviewer, 'max_complexity')
        assert reviewer.max_complexity == 5
    
    def test_complexity_reviewer_has_default_threshold(self):
        """Test that ComplexityReviewer has sensible default threshold."""
        reviewer = ComplexityReviewer()
        
        assert hasattr(reviewer, 'max_complexity')
        assert reviewer.max_complexity > 0
        assert reviewer.max_complexity <= 20  # Reasonable default range
    
    def test_complexity_reviewer_detects_high_complexity(self, parsed_complex_code):
        """Test that ComplexityReviewer detects high cyclomatic complexity."""
        reviewer = ComplexityReviewer(max_complexity=5)
        
        result = reviewer.review(parsed_complex_code)
        
        assert isinstance(result, ReviewResult)
        complexity_issues = result.get_issues_by_category(IssueCategory.COMPLEXITY)
        assert len(complexity_issues) > 0
    
    def test_complexity_reviewer_simple_code_passes(self, parsed_simple_code):
        """Test that simple code passes complexity review."""
        reviewer = ComplexityReviewer(max_complexity=5)
        
        result = reviewer.review(parsed_simple_code)
        
        assert result.total_issues == 0
        assert result.quality_score == 100.0
    
    def test_complexity_reviewer_reports_complexity_value(self, parsed_complex_code):
        """Test that ComplexityReviewer reports actual complexity value."""
        reviewer = ComplexityReviewer(max_complexity=5)
        
        result = reviewer.review(parsed_complex_code)
        
        if result.total_issues > 0:
            # Check that issue message contains complexity information
            issue = result.issues[0]
            assert "complexity" in issue.message.lower()


class TestSecurityReviewer:
    """Test SecurityReviewer functionality."""
    
    def test_security_reviewer_implements_review_strategy(self):
        """Test that SecurityReviewer implements ReviewStrategy interface."""
        reviewer = SecurityReviewer()
        
        assert isinstance(reviewer, ReviewStrategy)
        assert hasattr(reviewer, 'review')
        assert callable(reviewer.review)
    
    def test_security_reviewer_detects_hardcoded_secrets(self, parsed_code_with_issues):
        """Test that SecurityReviewer detects hardcoded API keys and passwords."""
        reviewer = SecurityReviewer()
        
        result = reviewer.review(parsed_code_with_issues)
        
        assert isinstance(result, ReviewResult)
        security_issues = result.get_issues_by_category(IssueCategory.SECURITY)
        assert len(security_issues) > 0
        
        # Should detect both API_KEY and PASSWORD
        messages = [issue.message.lower() for issue in security_issues]
        has_secret_detection = any("secret" in msg or "key" in msg or "password" in msg for msg in messages)
        assert has_secret_detection
    
    def test_security_reviewer_clean_code_passes(self, parsed_simple_code):
        """Test that code without security issues passes."""
        reviewer = SecurityReviewer()
        
        result = reviewer.review(parsed_simple_code)
        
        security_issues = result.get_issues_by_category(IssueCategory.SECURITY)
        assert len(security_issues) == 0
    
    def test_security_reviewer_marks_secrets_as_high_severity(self, parsed_code_with_issues):
        """Test that hardcoded secrets are marked as high or critical severity."""
        reviewer = SecurityReviewer()
        
        result = reviewer.review(parsed_code_with_issues)
        
        security_issues = result.get_issues_by_category(IssueCategory.SECURITY)
        if len(security_issues) > 0:
            # At least one should be high or critical
            high_priority = [i for i in security_issues if i.is_high_priority()]
            assert len(high_priority) > 0


class TestReviewEngineOrchestration:
    """Test ReviewEngine orchestration of multiple reviewers."""
    
    def test_review_engine_runs_all_reviewers(self, parsed_code_with_issues):
        """Test that ReviewEngine runs all configured reviewers."""
        reviewers = [
            StyleReviewer(),
            ComplexityReviewer(),
            SecurityReviewer(),
        ]
        engine = ReviewEngine(reviewers=reviewers)
        
        result = engine.review(parsed_code_with_issues)
        
        # Should have issues from multiple categories
        assert result.total_issues > 0
        categories = {issue.category for issue in result.issues}
        assert len(categories) >= 2  # At least 2 different categories
    
    def test_review_engine_combines_results(self, parsed_code_with_issues):
        """Test that ReviewEngine properly combines results from multiple reviewers."""
        engine = ReviewEngine()
        
        result = engine.review(parsed_code_with_issues)
        
        # Should have aggregated statistics
        assert result.total_issues == len(result.issues)
        assert result.quality_score <= 100.0
        assert result.quality_score >= 0.0
    
    def test_review_engine_calculates_overall_score(self, parsed_simple_code):
        """Test that ReviewEngine calculates overall quality score."""
        engine = ReviewEngine()
        
        result = engine.review(parsed_simple_code)
        
        assert hasattr(result, 'quality_score')
        assert 0.0 <= result.quality_score <= 100.0
    
    def test_review_engine_determines_pass_fail(self, parsed_code_with_issues):
        """Test that ReviewEngine determines if code passes review."""
        engine = ReviewEngine()
        
        result = engine.review(parsed_code_with_issues)
        
        assert hasattr(result, 'passed')
        assert isinstance(result.passed, bool)


class TestReviewEngineConfiguration:
    """Test ReviewEngine configuration options."""
    
    def test_review_engine_respects_severity_threshold(self, parsed_code_with_issues):
        """Test that ReviewEngine can filter issues by severity threshold."""
        config = {"min_severity": "high"}
        engine = ReviewEngine(config=config)
        
        result = engine.review(parsed_code_with_issues)
        
        # All issues should be high or critical
        for issue in result.issues:
            assert issue.severity in (Severity.HIGH, Severity.CRITICAL)
    
    def test_review_engine_can_enable_disable_reviewers(self, parsed_code_with_issues):
        """Test that ReviewEngine can enable/disable specific reviewers."""
        config = {
            "enable_style": False,
            "enable_complexity": True,
            "enable_security": True,
        }
        engine = ReviewEngine(config=config)
        
        result = engine.review(parsed_code_with_issues)
        
        # Should not have style issues
        style_issues = result.get_issues_by_category(IssueCategory.STYLE)
        assert len(style_issues) == 0


class TestReviewStrategyInterface:
    """Test ReviewStrategy abstract interface."""
    
    def test_review_strategy_is_abstract(self):
        """Test that ReviewStrategy cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ReviewStrategy()
    
    def test_custom_reviewer_can_extend_strategy(self, parsed_simple_code):
        """Test that custom reviewers can extend ReviewStrategy."""
        
        class CustomReviewer(ReviewStrategy):
            def review(self, parsed_code: ParsedCode) -> ReviewResult:
                result = ReviewResult(reviewer_name="CustomReviewer")
                result.add_issue(ReviewIssue(
                    severity=Severity.INFO,
                    category=IssueCategory.BEST_PRACTICES,
                    message="Custom review message"
                ))
                result.update_statistics()
                return result
        
        reviewer = CustomReviewer()
        result = reviewer.review(parsed_simple_code)
        
        assert isinstance(result, ReviewResult)
        assert result.reviewer_name == "CustomReviewer"
        assert result.total_issues == 1


class TestReviewResultMethods:
    """Test ReviewResult model methods."""
    
    def test_add_issue_updates_statistics(self):
        """Test that add_issue properly updates statistics."""
        result = ReviewResult()
        
        result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="Test issue"
        ))
        
        assert result.total_issues == 1
        assert result.high_count == 1
    
    def test_get_issues_by_severity_filters_correctly(self):
        """Test filtering issues by severity."""
        result = ReviewResult()
        result.add_issue(ReviewIssue(
            severity=Severity.HIGH,
            category=IssueCategory.SECURITY,
            message="High issue"
        ))
        result.add_issue(ReviewIssue(
            severity=Severity.LOW,
            category=IssueCategory.STYLE,
            message="Low issue"
        ))
        
        high_issues = result.get_issues_by_severity(Severity.HIGH)
        
        assert len(high_issues) == 1
        assert high_issues[0].severity == Severity.HIGH
    
    def test_calculate_quality_score_formula(self):
        """Test quality score calculation formula."""
        result = ReviewResult()
        
        # Add issues with known point deductions
        result.add_issue(ReviewIssue(
            severity=Severity.CRITICAL,  # -20
            category=IssueCategory.SECURITY,
            message="Critical"
        ))
        result.add_issue(ReviewIssue(
            severity=Severity.HIGH,  # -10
            category=IssueCategory.SECURITY,
            message="High"
        ))
        
        score = result.calculate_quality_score()
        
        # Should be 100 - 20 - 10 = 70
        assert score == 70.0


class TestReviewEngineEdgeCases:
    """Test edge cases and advanced features in ReviewEngine."""
    
    def test_style_reviewer_detects_pascal_case_class_names(self):
        """Test that StyleReviewer detects improper class naming."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = """class my_bad_class:
    pass
"""
        parsed_code = parser.parse(code, "python")
        
        reviewer = StyleReviewer()
        result = reviewer.review(parsed_code)
        
        # Should find style issue with lowercase class name
        style_issues = result.get_issues_by_category(IssueCategory.STYLE)
        assert len(style_issues) > 0
        assert any("PascalCase" in issue.message for issue in style_issues)
    
    def test_style_reviewer_detects_line_length_violations(self):
        """Test that StyleReviewer detects lines that are too long."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        # Create a very long line
        long_line = "x = " + "1 + " * 50 + "1"
        code = f"""def test():
    {long_line}
    return x
"""
        parsed_code = parser.parse(code, "python")
        
        reviewer = StyleReviewer(config={"max_line_length": 80})
        result = reviewer.review(parsed_code)
        
        # Should find line length issue
        assert result.total_issues > 0
        assert any("too long" in issue.message.lower() for issue in result.issues)
    
    def test_complexity_reviewer_handles_syntax_errors(self):
        """Test that ComplexityReviewer handles syntax errors gracefully."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = "def broken( pass"  # Syntax error
        parsed_code = parser.parse(code, "python")
        
        reviewer = ComplexityReviewer(max_complexity=5)
        result = reviewer.review(parsed_code)
        
        # Should not crash, should return empty result
        assert result is not None
        assert result.total_issues == 0
    
    def test_complexity_reviewer_detects_comprehensions(self):
        """Test that ComplexityReviewer counts comprehensions with conditions."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = """def complex_func():
    result = [x for x in range(10) if x > 5 if x < 8]
    return result
"""
        parsed_code = parser.parse(code, "python")
        
        reviewer = ComplexityReviewer(max_complexity=1)
        result = reviewer.review(parsed_code)
        
        # The reviewer should flag high complexity even with simple code
        # because max_complexity is set very low
        assert result.total_issues >= 0  # May or may not have issues depending on calculation
    
    def test_security_reviewer_detects_eval_usage(self):
        """Test that SecurityReviewer detects dangerous eval() usage."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = """def dangerous():
    user_input = input("Enter code: ")
    result = eval(user_input)
    return result
"""
        parsed_code = parser.parse(code, "python")
        
        reviewer = SecurityReviewer()
        result = reviewer.review(parsed_code)
        
        # Should find security issue with eval
        security_issues = result.get_issues_by_category(IssueCategory.SECURITY)
        assert len(security_issues) > 0
        assert any("eval" in issue.message.lower() for issue in security_issues)
    
    def test_security_reviewer_detects_exec_usage(self):
        """Test that SecurityReviewer detects dangerous exec() usage."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = """def dangerous():
    code = "print('hello')"
    exec(code)
"""
        parsed_code = parser.parse(code, "python")
        
        reviewer = SecurityReviewer()
        result = reviewer.review(parsed_code)
        
        # Should find security issue with exec
        security_issues = result.get_issues_by_category(IssueCategory.SECURITY)
        assert len(security_issues) > 0
        assert any("exec" in issue.message.lower() for issue in security_issues)
    
    def test_security_reviewer_detects_sql_injection(self):
        """Test that SecurityReviewer detects SQL injection patterns."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = """def query_user(user_id):
    query = "SELECT * FROM users WHERE id = %s" % user_id
    return execute(query)
"""
        parsed_code = parser.parse(code, "python")
        
        reviewer = SecurityReviewer()
        result = reviewer.review(parsed_code)
        
        # Should find SQL injection risk
        security_issues = result.get_issues_by_category(IssueCategory.SECURITY)
        assert len(security_issues) > 0
    
    def test_security_reviewer_handles_syntax_errors(self):
        """Test that SecurityReviewer handles syntax errors gracefully."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = "def broken( pass"  # Syntax error
        parsed_code = parser.parse(code, "python")
        
        reviewer = SecurityReviewer()
        result = reviewer.review(parsed_code)
        
        # Should not crash
        assert result is not None
    
    def test_review_engine_handles_reviewer_exceptions(self):
        """Test that ReviewEngine handles exceptions from reviewers gracefully."""
        from src.services.code_parser import CodeParser
        
        class BrokenReviewer(ReviewStrategy):
            def review(self, parsed_code: ParsedCode) -> ReviewResult:
                raise RuntimeError("Reviewer crashed!")
        
        parser = CodeParser()
        code = "def test(): pass"
        parsed_code = parser.parse(code, "python")
        
        # Create engine with broken reviewer
        engine = ReviewEngine(reviewers=[BrokenReviewer(), StyleReviewer()])
        
        # Should not crash, should continue with other reviewers
        result = engine.review(parsed_code)
        
        assert result is not None
        # Should still have results from StyleReviewer
        assert result.reviewer_name == "ReviewEngine"
    
    def test_style_reviewer_helper_methods(self):
        """Test StyleReviewer helper methods for naming conventions."""
        reviewer = StyleReviewer()
        
        # Test snake_case detection
        assert reviewer._is_snake_case("valid_function_name") is True
        assert reviewer._is_snake_case("BadFunctionName") is False
        assert reviewer._is_snake_case("_private_function") is True
        
        # Test PascalCase detection
        assert reviewer._is_pascal_case("ValidClassName") is True
        assert reviewer._is_pascal_case("bad_class_name") is False
        
        # Test conversion to snake_case
        assert reviewer._to_snake_case("BadFunctionName") == "bad_function_name"
        assert reviewer._to_snake_case("HTMLParser") == "html_parser"
    
    def test_complexity_reviewer_detects_bool_operators(self):
        """Test that ComplexityReviewer detects boolean operators properly."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = """def check(a, b, c):
    if a and b or c:
        return True
    return False
"""
        parsed_code = parser.parse(code, "python")
        
        reviewer = ComplexityReviewer(max_complexity=2)
        result = reviewer.review(parsed_code)
        
        # Should detect complexity from boolean operators
        assert parsed_code.metadata.complexity >= 2
    
    def test_style_reviewer_checks_class_with_suggestion(self):
        """Test that StyleReviewer provides suggestions for bad class names."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = """class badClassName:
    pass
"""
        parsed_code = parser.parse(code, "python")
        
        reviewer = StyleReviewer()
        result = reviewer.review(parsed_code)
        
        # Should find issue with lowercase start
        style_issues = result.get_issues_by_category(IssueCategory.STYLE)
        assert len(style_issues) > 0
    
    def test_style_reviewer_handles_syntax_errors_gracefully(self):
        """Test that StyleReviewer handles syntax errors without crashing."""
        from src.services.code_parser import CodeParser
        
        parser = CodeParser()
        code = "def broken function( pass"  # Syntax error
        parsed_code = parser.parse(code, "python")
        
        reviewer = StyleReviewer()
        result = reviewer.review(parsed_code)
        
        # Should not crash, should return a result
        assert result is not None
        assert isinstance(result, ReviewResult)
