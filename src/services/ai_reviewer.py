"""
AI-Powered Code Reviewer Service.

This service uses OpenAI's Chat Completion API to provide intelligent,
context-aware code reviews that complement rule-based reviewers.
"""
import os
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from openai import OpenAI
from openai.types.chat import ChatCompletion
from src.services.review_engine import ReviewStrategy
from src.models.code_models import ParsedCode
from src.models.review_models import ReviewResult, ReviewIssue, Severity, IssueCategory
from src.models.code_fix_models import CodeFixResult, FixConfidence


# pylint: disable=too-many-instance-attributes
class AIReviewer(ReviewStrategy):
    """AI-powered code reviewer using OpenAI's GPT models."""
    
    DEFAULT_SYSTEM_PROMPT = """You are an expert code reviewer. Analyze code for bugs, \
security issues, performance problems, and best practices violations.

IMPORTANT: You must respond with ONLY valid JSON in this exact format:
{
  "issues": [
    {
      "severity": "critical|high|medium|low|info",
      "category": "security|bug_risk|performance|best_practices|style|complexity|documentation",
      "message": "Clear description of the issue",
      "line_number": 5,
      "suggestion": "How to fix it"
    }
  ]
}

If no issues are found, return: {"issues": []}
Do not include any text before or after the JSON."""
    
    def __init__(
        self,
        client: Optional[OpenAI] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize AIReviewer."""
        self.config = config or {}
        
        # Initialize OpenAI client
        if client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not found in environment. "
                    "Set it in .env file or pass client explicitly."
                )
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = client
        
        # Extract configuration with defaults
        self.model = self.config.get("model", "gpt-4o-mini")
        self.temperature = self.config.get("temperature", 0.3)
        self.max_tokens = self.config.get("max_tokens", 2000)
        self.timeout = self.config.get("timeout", 30)
        self.system_prompt = self.config.get("system_prompt", self.DEFAULT_SYSTEM_PROMPT)
        
        # Auto-fix configuration
        self.enable_auto_fix = self.config.get("enable_auto_fix", False)
        self.code_fixer = None
        
        if self.enable_auto_fix:
            # Use provided fixer or create one
            if "code_fixer" in self.config:
                self.code_fixer = self.config["code_fixer"]
            else:
                from src.services.code_fixer import CodeFixer
                self.code_fixer = CodeFixer(client=self.client, config=self.config)
        
        # Usage tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0
    
    def review(self, parsed_code: ParsedCode) -> ReviewResult:
        """Review code using OpenAI's AI models."""
        result = ReviewResult(
            reviewer_name="AIReviewer",
            review_timestamp=datetime.now().isoformat()
        )
        
        # Skip if code has syntax errors
        if parsed_code.has_syntax_errors:
            result.add_issue(ReviewIssue(
                severity=Severity.INFO,
                category=IssueCategory.BUG_RISK,
                message="Skipping AI review due to syntax errors. Fix syntax first.",
                rule_id="AI000"
            ))
            result.update_statistics()
            return result
        
        try:
            # Build prompt with code and metadata
            user_prompt = self._build_user_prompt(parsed_code)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            # Track usage
            self._track_usage(response)
            
            # Parse AI response into issues
            issues = self._parse_ai_response(response)
            for issue in issues:
                result.add_issue(issue)
        
        except Exception as e:
            # Handle API errors gracefully
            result.add_issue(ReviewIssue(
                severity=Severity.INFO,
                category=IssueCategory.BUG_RISK,
                message=f"AI review failed: {str(e)}",
                suggestion="Check API key, network connection, or try again later",
                rule_id="AI999"
            ))
        
        result.update_statistics()
        
        # Generate fixes if auto-fix is enabled and issues were found
        if self.enable_auto_fix and result.total_issues > 0 and self.code_fixer:
            try:
                fixable_issues = self.get_fixable_issues(result.issues)
                if fixable_issues:
                    fix_result = self.code_fixer.generate_fixes(parsed_code, fixable_issues)
                    result.fix_result = fix_result
            except Exception:
                # Don't fail review if fix generation fails
                result.fix_result = CodeFixResult(success=False)
        
        return result
    
    def _build_user_prompt(self, parsed_code: ParsedCode) -> str:
        """Build the user prompt with code and context."""
        metadata = parsed_code.metadata
        
        prompt = f"""Review this {parsed_code.language.upper()} code for issues:

Code Metadata:
- Lines: {metadata.line_count}
- Functions: {metadata.function_count}
- Classes: {metadata.class_count}
- Complexity: {metadata.complexity}
- Has Docstrings: {metadata.has_docstrings}

Code to review:
```{parsed_code.language}
{parsed_code.content}
```

Identify all issues including:
- Security vulnerabilities (SQL injection, hardcoded secrets, unsafe operations)
- Potential bugs (logic errors, edge cases, error handling)
- Performance problems (inefficient algorithms, unnecessary operations)
- Code quality (naming, structure, readability, maintainability)
- Best practices violations

Return your findings as JSON only."""
        return prompt
    
    def _parse_ai_response(self, response: ChatCompletion) -> List[ReviewIssue]:
        """Parse OpenAI API response into ReviewIssue objects."""
        issues = []
        
        try:
            content = response.choices[0].message.content
            if not content:
                return issues
            
            # Try parsing as JSON
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "issues" in data:
                    issues_data = data["issues"]
                elif isinstance(data, list):
                    issues_data = data
                else:
                    return issues
            except json.JSONDecodeError:
                # Try extracting from markdown code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    if json_end > json_start:
                        content = content[json_start:json_end].strip()
                        data = json.loads(content)
                        issues_data = data if isinstance(data, list) else data.get("issues", [])
                    else:
                        return issues
                else:
                    return issues
            
            # Convert to ReviewIssue objects
            for issue_data in issues_data:
                try:
                    severity = Severity(issue_data.get("severity", "info").lower())
                    category = IssueCategory(issue_data.get("category", "best_practices").lower())
                    
                    issue = ReviewIssue(
                        severity=severity,
                        category=category,
                        message=issue_data.get("message", ""),
                        line_number=issue_data.get("line_number"),
                        suggestion=issue_data.get("suggestion"),
                        rule_id=f"AI{issue_data.get('line_number', 0):03d}"
                    )
                    issues.append(issue)
                except (KeyError, ValueError):
                    continue
        
        except Exception:
            pass
        
        return issues
    
    def _track_usage(self, response: ChatCompletion) -> None:
        """Track token usage and estimated cost."""
        if not response.usage:
            return
        
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        self.total_tokens_used += total_tokens
        
        # Estimate cost based on model
        if "gpt-4o" in self.model:
            cost = (prompt_tokens * 2.50 / 1_000_000) + (completion_tokens * 10 / 1_000_000)
        elif "gpt-4" in self.model:
            cost = (prompt_tokens * 30 / 1_000_000) + (completion_tokens * 60 / 1_000_000)
        else:
            cost = (prompt_tokens * 0.50 / 1_000_000) + (completion_tokens * 1.50 / 1_000_000)
        
        self.total_cost += cost
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this reviewer."""
        return {
            "total_tokens": self.total_tokens_used,
            "estimated_cost_usd": round(self.total_cost, 4),
            "model": self.model
        }
    
    def review_with_fixes(
        self,
        parsed_code: ParsedCode,
        auto_fix: bool = True
    ) -> Tuple[ReviewResult, Optional[CodeFixResult]]:
        """
        Review code and generate fixes.
        
        Args:
            parsed_code: The code to review
            auto_fix: Whether to generate fixes (default: True)
            
        Returns:
            Tuple of (ReviewResult, CodeFixResult or None)
        """
        # Perform review
        review_result = self.review(parsed_code)
        
        # Generate fixes if requested and not already done
        fix_result = None
        if auto_fix:
            # Check if fixes were already generated during review
            if hasattr(review_result, 'fix_result') and review_result.fix_result is not None:
                fix_result = review_result.fix_result
            elif review_result.total_issues > 0:
                # Generate fixes now
                try:
                    # Create fixer if needed
                    if not self.code_fixer:
                        from src.services.code_fixer import CodeFixer
                        fixer = CodeFixer(client=self.client, config=self.config)
                    else:
                        fixer = self.code_fixer
                    
                    fixable_issues = self.get_fixable_issues(review_result.issues)
                    if fixable_issues:
                        fix_result = fixer.generate_fixes(parsed_code, fixable_issues)
                    else:
                        fix_result = CodeFixResult()
                except Exception:
                    fix_result = CodeFixResult(success=False)
            else:
                fix_result = CodeFixResult()
        
        return review_result, fix_result
    
    def get_fixable_issues(
        self,
        issues: List[ReviewIssue],
        min_severity: Optional[Severity] = None
    ) -> List[ReviewIssue]:
        """
        Filter issues to determine which are auto-fixable.
        
        Args:
            issues: List of issues to filter
            min_severity: Minimum severity to include (optional)
            
        Returns:
            List of fixable issues
        """
        fixable = []
        
        # Severity hierarchy for comparison
        severity_order = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        
        min_severity_value = severity_order.get(min_severity, 0) if min_severity else 0
        
        for issue in issues:
            # Skip issues without line numbers (can't fix without location)
            if issue.line_number is None:
                continue
            
            # Check severity threshold
            if severity_order.get(issue.severity, 0) < min_severity_value:
                continue
            
            # Some categories are typically not auto-fixable
            if issue.category == IssueCategory.COMPLEXITY:
                # Complexity issues usually require manual refactoring
                continue
            
            fixable.append(issue)
        
        return fixable
    
    def apply_fixes(
        self,
        parsed_code: ParsedCode,
        fixes: CodeFixResult,
        min_confidence: FixConfidence = FixConfidence.HIGH
    ) -> str:
        """
        Apply fixes to code.
        
        Args:
            parsed_code: The original parsed code
            fixes: The fixes to apply
            min_confidence: Minimum confidence level to apply (default: HIGH)
            
        Returns:
            Modified code with fixes applied
        """
        try:
            # Start with original code
            modified_code = parsed_code.content
            
            # Filter fixes by confidence
            confidence_order = {
                FixConfidence.LOW: 0,
                FixConfidence.MEDIUM: 1,
                FixConfidence.HIGH: 2,
                FixConfidence.VERIFIED: 3,
            }
            
            min_confidence_value = confidence_order.get(min_confidence, 2)
            
            applicable_fixes = [
                fix for fix in fixes.fixes
                if confidence_order.get(fix.confidence, 0) >= min_confidence_value
            ]
            
            # Sort fixes by line number (reverse order to avoid line number shifts)
            applicable_fixes.sort(key=lambda f: f.line_start, reverse=True)
            
            # Apply fixes
            for fix in applicable_fixes:
                # Simple string replacement (in production, use more robust line-based replacement)
                if fix.original_code in modified_code:
                    modified_code = modified_code.replace(
                        fix.original_code,
                        fix.fixed_code,
                        1  # Replace only first occurrence
                    )
            
            return modified_code
        
        except Exception:
            # On any error, return original code
            return parsed_code.content
