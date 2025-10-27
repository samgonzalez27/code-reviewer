"""
Review Engine Service.

This service orchestrates code review using multiple review strategies.
It follows the Strategy Pattern for pluggable reviewers and SOLID principles.

Design Patterns:
- Strategy Pattern: Pluggable review strategies
- Composite Pattern: Combine multiple reviewers
- Template Method: Common review workflow
"""
import ast
import re
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime
from src.models.code_models import ParsedCode
from src.models.review_models import ReviewResult, ReviewIssue, Severity, IssueCategory


class ReviewStrategy(ABC):
    """
    Abstract base class for review strategies (Strategy Pattern).
    
    Each concrete reviewer implements this interface to provide
    specific types of code review (style, security, complexity, etc.).
    """
    
    @abstractmethod
    def review(self, parsed_code: ParsedCode) -> ReviewResult:
        """
        Review the parsed code and return results.
        
        Args:
            parsed_code: The ParsedCode object to review
            
        Returns:
            ReviewResult with issues found
        """


class StyleReviewer(ReviewStrategy):
    """
    Reviews code style and formatting conventions.
    
    Checks for:
    - Naming conventions (snake_case for functions, PascalCase for classes)
    - Spacing around operators
    - Line length
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize StyleReviewer with optional configuration."""
        self.config = config or {
            "check_naming": True,
            "check_spacing": True,
            "max_line_length": 100,
        }
    
    def review(self, parsed_code: ParsedCode) -> ReviewResult:
        """
        Review code style and formatting.
        
        Args:
            parsed_code: The ParsedCode object to review
            
        Returns:
            ReviewResult containing style issues found
        """
        result = ReviewResult(
            reviewer_name="StyleReviewer",
            review_timestamp=datetime.now().isoformat()
        )
        
        code = parsed_code.content
        lines = code.split('\n')
        
        # Check naming conventions (for Python)
        if parsed_code.language == "python" and self.config.get("check_naming", True):
            try:
                tree = ast.parse(code)
                
                for node in ast.walk(tree):
                    # Check function naming (should be snake_case)
                    if isinstance(node, ast.FunctionDef):
                        if not self._is_snake_case(node.name) and not node.name.startswith('_'):
                            result.add_issue(ReviewIssue(
                                severity=Severity.LOW,
                                category=IssueCategory.STYLE,
                                message=f"Function '{node.name}' should use snake_case naming",
                                line_number=node.lineno,
                                suggestion=f"Rename to {self._to_snake_case(node.name)}",
                                rule_id="STYLE001"
                            ))
                    
                    # Check class naming (should be PascalCase)
                    elif isinstance(node, ast.ClassDef):
                        if not self._is_pascal_case(node.name):
                            result.add_issue(ReviewIssue(
                                severity=Severity.LOW,
                                category=IssueCategory.STYLE,
                                message=f"Class '{node.name}' should use PascalCase naming",
                                line_number=node.lineno,
                                rule_id="STYLE002"
                            ))
            
            except SyntaxError:
                # Can't check naming if syntax is invalid
                pass
        
        # Check spacing around operators
        if self.config.get("check_spacing", True):
            for i, line in enumerate(lines, 1):
                # Check for missing spaces around = in assignments (but not ==, !=, etc.)
                # Pattern: variable=value (no spaces)
                if re.search(r'\w=[^=]', line) and '==' not in line:
                    result.add_issue(ReviewIssue(
                        severity=Severity.INFO,
                        category=IssueCategory.STYLE,
                        message="Missing spaces around assignment operator",
                        line_number=i,
                        code_snippet=line.strip(),
                        suggestion="Add spaces around '=' operator",
                        rule_id="STYLE003"
                    ))
                
                # Check for missing spaces around + - * /
                if re.search(r'\w[+\-*/]\w', line):
                    result.add_issue(ReviewIssue(
                        severity=Severity.INFO,
                        category=IssueCategory.STYLE,
                        message="Missing spaces around operator",
                        line_number=i,
                        code_snippet=line.strip(),
                        suggestion="Add spaces around operators",
                        rule_id="STYLE004"
                    ))
        
        # Check line length
        max_length = self.config.get("max_line_length", 100)
        for i, line in enumerate(lines, 1):
            if len(line) > max_length:
                result.add_issue(ReviewIssue(
                    severity=Severity.INFO,
                    category=IssueCategory.STYLE,
                    message=f"Line too long ({len(line)} > {max_length} characters)",
                    line_number=i,
                    rule_id="STYLE005"
                ))
        
        result.update_statistics()
        return result
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name is in snake_case format."""
        return bool(re.match(r'^[a-z_][a-z0-9_]*$', name))
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name is in PascalCase format."""
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
    
    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class ComplexityReviewer(ReviewStrategy):
    """
    Reviews code complexity metrics.
    
    Checks cyclomatic complexity of functions and flags those
    that exceed the configured threshold (default: 10).
    """
    
    def __init__(self, max_complexity: int = 10, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ComplexityReviewer.
        
        Args:
            max_complexity: Maximum allowed cyclomatic complexity
            config: Optional additional configuration
        """
        self.max_complexity = max_complexity
        self.config = config or {}
    
    def review(self, parsed_code: ParsedCode) -> ReviewResult:
        """
        Review code complexity.
        
        Args:
            parsed_code: The ParsedCode object to review
            
        Returns:
            ReviewResult containing complexity issues found
        """
        result = ReviewResult(
            reviewer_name="ComplexityReviewer",
            review_timestamp=datetime.now().isoformat()
        )
        
        # For Python, analyze AST to calculate complexity per function
        if parsed_code.language == "python":
            try:
                tree = ast.parse(parsed_code.content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = self._calculate_function_complexity(node)
                        
                        if complexity > self.max_complexity:
                            severity = (
                                Severity.MEDIUM 
                                if complexity <= self.max_complexity * 1.5 
                                else Severity.HIGH
                            )
                            result.add_issue(ReviewIssue(
                                severity=severity,
                                category=IssueCategory.COMPLEXITY,
                                message=(
                                    f"Function '{node.name}' has high "
                                    f"cyclomatic complexity: {complexity}"
                                ),
                                line_number=node.lineno,
                                suggestion=(
                                    f"Consider refactoring to reduce complexity "
                                    f"(max: {self.max_complexity})"
                                ),
                                rule_id="COMPLEXITY001"
                            ))
            
            except SyntaxError:
                # Can't check complexity if syntax is invalid
                pass
        
        result.update_statistics()
        return result
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """
        Calculate cyclomatic complexity for a function.
        
        Complexity = 1 + number of decision points
        Decision points: if, while, for, except, and, or
        """
        complexity = 1
        
        for child in ast.walk(node):
            # Count decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # and/or operators add to complexity
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                # Comprehensions with conditions add complexity
                complexity += sum(1 for gen in child.generators for _ in gen.ifs)
        
        return complexity


class SecurityReviewer(ReviewStrategy):
    """
    Reviews code for security vulnerabilities.
    
    Checks for:
    - Hardcoded secrets (API keys, passwords, tokens)
    - SQL injection patterns
    - Unsafe eval/exec usage
    - Insecure imports
    """
    
    # Patterns for detecting hardcoded secrets
    SECRET_PATTERNS = [
        (
            r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            'API key'
        ),
        (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{3,})["\']', 'password'),
        (
            r'(?i)(secret|token)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            'secret/token'
        ),
        (
            r'(?i)(aws[_-]?access[_-]?key|access[_-]?key[_-]?id)\s*[=:]\s*["\']([A-Z0-9]{20})["\']',
            'AWS access key'
        ),
        (r'(?i)sk-[a-zA-Z0-9]{20,}', 'OpenAI API key'),
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize SecurityReviewer with optional configuration."""
        self.config = config or {}
    
    def review(self, parsed_code: ParsedCode) -> ReviewResult:
        """
        Review code for security issues.
        
        Args:
            parsed_code: The ParsedCode object to review
            
        Returns:
            ReviewResult containing security issues found
        """
        result = ReviewResult(
            reviewer_name="SecurityReviewer",
            review_timestamp=datetime.now().isoformat()
        )
        
        code = parsed_code.content
        lines = code.split('\n')
        
        # Check for hardcoded secrets
        for i, line in enumerate(lines, 1):
            for pattern, secret_type in self.SECRET_PATTERNS:
                matches = re.finditer(pattern, line)
                for _ in matches:
                    result.add_issue(ReviewIssue(
                        severity=Severity.CRITICAL,
                        category=IssueCategory.SECURITY,
                        message=f"Hardcoded {secret_type} detected",
                        line_number=i,
                        code_snippet=line.strip(),
                        suggestion=(
                            "Move sensitive data to environment variables "
                            "or secure configuration"
                        ),
                        rule_id="SEC001"
                    ))
        
        # Check for dangerous Python functions (if Python code)
        if parsed_code.language == "python":
            try:
                tree = ast.parse(code)
                
                for node in ast.walk(tree):
                    # Check for eval() or exec()
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if node.func.id in ('eval', 'exec'):
                                result.add_issue(ReviewIssue(
                                    severity=Severity.HIGH,
                                    category=IssueCategory.SECURITY,
                                    message=f"Dangerous use of {node.func.id}() function",
                                    line_number=node.lineno,
                                    suggestion=(
                                        f"Avoid using {node.func.id}() as it can "
                                        "execute arbitrary code"
                                    ),
                                    rule_id="SEC002"
                                ))
            
            except SyntaxError:
                # Can't check AST if syntax is invalid
                pass
        
        # Check for SQL injection patterns (basic)
        for i, line in enumerate(lines, 1):
            # Look for string formatting in SQL queries
            if re.search(r'(?i)(select|insert|update|delete).*%s|\.format\(', line):
                result.add_issue(ReviewIssue(
                    severity=Severity.HIGH,
                    category=IssueCategory.SECURITY,
                    message="Potential SQL injection vulnerability",
                    line_number=i,
                    code_snippet=line.strip(),
                    suggestion="Use parameterized queries instead of string formatting",
                    rule_id="SEC003"
                ))
        
        result.update_statistics()
        return result


class ReviewEngine:
    """
    Orchestrates code review using multiple ReviewStrategy implementations.
    
    This class follows the Composite Pattern to combine results from
    multiple reviewers into a single comprehensive review.
    
    Usage:
        engine = ReviewEngine()
        parsed_code = parser.parse(code, "python")
        result = engine.review(parsed_code)
        print(f"Quality Score: {result.quality_score}")
    """
    
    def __init__(
        self,
        reviewers: Optional[List[ReviewStrategy]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ReviewEngine.
        
        Args:
            reviewers: List of ReviewStrategy instances to use
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # If no reviewers provided, use default set
        if reviewers is None:
            self.reviewers = self._create_default_reviewers()
        else:
            self.reviewers = reviewers
    
    def _create_default_reviewers(self) -> List[ReviewStrategy]:
        """Create default set of reviewers based on configuration."""
        reviewers = []
        
        if self.config.get("enable_style", True):
            reviewers.append(StyleReviewer(config=self.config))
        
        if self.config.get("enable_complexity", True):
            max_complexity = self.config.get("max_complexity", 10)
            reviewers.append(ComplexityReviewer(max_complexity=max_complexity))
        
        if self.config.get("enable_security", True):
            reviewers.append(SecurityReviewer(config=self.config))
        
        # Add AI reviewer if enabled
        if self.config.get("enable_ai", False):
            reviewers.append(self._create_ai_reviewer())
        
        return reviewers
    
    def _create_ai_reviewer(self) -> ReviewStrategy:
        """Create AIReviewer with appropriate configuration."""
        from src.services.ai_reviewer import AIReviewer
        
        # Extract AI-specific config
        ai_config = {}
        if "ai_model" in self.config:
            ai_config["model"] = self.config["ai_model"]
        if "ai_temperature" in self.config:
            ai_config["temperature"] = self.config["ai_temperature"]
        if "ai_max_tokens" in self.config:
            ai_config["max_tokens"] = self.config["ai_max_tokens"]
        if "ai_timeout" in self.config:
            ai_config["timeout"] = self.config["ai_timeout"]
        if "ai_system_prompt" in self.config:
            ai_config["system_prompt"] = self.config["ai_system_prompt"]
        
        return AIReviewer(config=ai_config)
    
    def review(self, parsed_code: ParsedCode) -> ReviewResult:
        """
        Review the parsed code using all configured reviewers.
        
        This method orchestrates multiple reviewers following the Composite Pattern.
        It aggregates results from all reviewers into a single comprehensive review.
        
        Args:
            parsed_code: The ParsedCode object to review
            
        Returns:
            ReviewResult with aggregated results from all reviewers
        """
        # Create combined result
        combined_result = ReviewResult(
            reviewer_name="ReviewEngine",
            review_timestamp=datetime.now().isoformat()
        )
        
        # Run each reviewer and collect issues
        for reviewer in self.reviewers:
            try:
                reviewer_result = reviewer.review(parsed_code)
                
                # Add all issues from this reviewer to combined result
                for issue in reviewer_result.issues:
                    # Apply severity filtering if configured
                    min_severity = self.config.get("min_severity")
                    if min_severity:
                        severity_order = ["info", "low", "medium", "high", "critical"]
                        issue_idx = severity_order.index(issue.severity.value)
                        min_idx = severity_order.index(min_severity)
                        if issue_idx < min_idx:
                            continue
                    
                    combined_result.add_issue(issue)
                    
            except Exception:
                # Log error but continue with other reviewers (resilience)
                # In production, this would use proper logging
                continue
        
        # Final statistics update (in case of any manual modifications)
        combined_result.update_statistics()
        
        return combined_result
