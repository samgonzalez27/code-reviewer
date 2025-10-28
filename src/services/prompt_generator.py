"""
AI-powered prompt generator for code issue remediation.

Uses OpenAI to generate GitHub Copilot-ready prompts that help developers
fix code issues following professional Python SWE standards.
"""
import os
from typing import Dict, List, Optional
from collections import defaultdict
from openai import OpenAI, APIError, APITimeoutError

from src.models.review_models import ReviewResult, ReviewIssue, IssueCategory, Severity
from src.models.prompt_models import PromptGenerationResult, PromptSuggestion


class PromptGenerator:
    """
    Generates AI-powered prompts for fixing code issues.
    
    Creates up to 5 category-based prompts prioritized by severity,
    tailored for GitHub Copilot with Python SWE best practices.
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are an expert Python software engineer helping developers fix code issues.
Generate clear, actionable prompts that can be used with GitHub Copilot to address specific code quality issues.
Your prompts should:
- Follow professional Python SWE standards and best practices
- Be specific and actionable
- Reference the exact issues and line numbers when relevant
- Provide context about why the fix is important
- Be formatted as clear instructions for GitHub Copilot
Keep prompts concise but comprehensive (2-4 sentences)."""
    
    def __init__(self, client: Optional[OpenAI] = None, config: Optional[Dict] = None):
        """
        Initialize the prompt generator.
        
        Args:
            client: Optional OpenAI client instance. If not provided, creates one from API key.
            config: Optional configuration dict with keys:
                - model: AI model to use (default: "gpt-4o-mini")
                - temperature: Response randomness 0-1 (default: 0.3)
                - max_prompts: Maximum number of prompts to generate (default: 5)
                - timeout: Request timeout in seconds (default: 30)
        
        Raises:
            ValueError: If no API key available and no client provided
        """
        self.config = config or {}
        
        # Set up OpenAI client
        if client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found. "
                    "Set it in .env file or pass client explicitly."
                )
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = client
        
        # Extract configuration with defaults
        self.model = self.config.get("model", "gpt-4o-mini")
        self.temperature = self.config.get("temperature", 0.3)
        self.max_prompts = self.config.get("max_prompts", 5)
        self.timeout = self.config.get("timeout", 30)
    
    def generate(self, review_result: ReviewResult, language: str = "python") -> PromptGenerationResult:
        """
        Generate prompts for fixing code issues.
        
        Args:
            review_result: Review result containing issues to address
            language: Programming language (default: "python")
        
        Returns:
            PromptGenerationResult with generated prompts
        """
        result = PromptGenerationResult(language=language)
        
        # Return empty result if no issues
        if review_result.total_issues == 0:
            return result
        
        # Group issues by category
        issues_by_category = self._group_issues_by_category(review_result.issues)
        
        # Prioritize categories by severity
        prioritized_categories = self._prioritize_categories(issues_by_category)
        
        # Generate prompts for top categories (up to max_prompts)
        for category in prioritized_categories[:self.max_prompts]:
            issues = issues_by_category[category]
            
            try:
                prompt_suggestion = self._generate_prompt_for_category(
                    category, issues, language
                )
                result.add_prompt(prompt_suggestion)
            except (APIError, APITimeoutError):
                # Skip this category on API error, continue with others
                continue
            except Exception:
                # Skip on any other error
                continue
        
        return result
    
    def _group_issues_by_category(self, issues: List[ReviewIssue]) -> Dict[IssueCategory, List[ReviewIssue]]:
        """Group issues by their category."""
        grouped = defaultdict(list)
        for issue in issues:
            grouped[issue.category].append(issue)
        return dict(grouped)
    
    def _prioritize_categories(self, issues_by_category: Dict[IssueCategory, List[ReviewIssue]]) -> List[IssueCategory]:
        """
        Prioritize categories based on severity and issue count.
        
        Returns categories sorted by:
        1. Highest severity in category (critical > high > medium > low > info)
        2. Count of issues in category (more issues = higher priority)
        """
        severity_order = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFO: 1
        }
        
        def category_priority(category: IssueCategory) -> tuple:
            issues = issues_by_category[category]
            max_severity = max(severity_order[issue.severity] for issue in issues)
            issue_count = len(issues)
            return (-max_severity, -issue_count)  # Negative for descending sort
        
        return sorted(issues_by_category.keys(), key=category_priority)
    
    def _generate_severity_summary(self, issues: List[ReviewIssue]) -> str:
        """Generate a severity summary string like '2 high, 3 medium'."""
        severity_counts = defaultdict(int)
        for issue in issues:
            severity_counts[issue.severity] += 1
        
        # Build summary in severity order
        parts = []
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
            if severity in severity_counts:
                count = severity_counts[severity]
                parts.append(f"{count} {severity.value}")
        
        return ", ".join(parts)
    
    def _generate_prompt_for_category(
        self, category: IssueCategory, issues: List[ReviewIssue], language: str
    ) -> PromptSuggestion:
        """
        Generate a prompt for a specific category of issues.
        
        Args:
            category: The issue category
            issues: List of issues in this category
            language: Programming language
        
        Returns:
            PromptSuggestion with generated prompt text
        """
        # Build context about the issues
        issue_details = []
        line_references = []
        
        for issue in issues:
            detail = f"- {issue.severity.value.upper()}: {issue.message}"
            if issue.line_number:
                detail += f" (line {issue.line_number})"
                line_references.append(issue.line_number)
            if issue.suggestion:
                detail += f"\n  Suggestion: {issue.suggestion}"
            issue_details.append(detail)
        
        issues_text = "\n".join(issue_details)
        
        # Build user prompt
        user_prompt = f"""Generate a GitHub Copilot prompt to fix the following {category.value} issues in {language} code:

{issues_text}

The prompt should:
- Be actionable and specific for GitHub Copilot
- Follow professional {language.upper()} SWE standards and best practices
- Address all {len(issues)} issue(s) in this category
- Be 2-4 sentences long
- Include context about why these fixes are important

Generate ONLY the prompt text that a developer would paste into GitHub Copilot."""
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            timeout=self.timeout
        )
        
        # Extract prompt text
        prompt_text = response.choices[0].message.content.strip()
        
        # Generate severity summary
        severity_summary = self._generate_severity_summary(issues)
        
        # Create and return PromptSuggestion
        return PromptSuggestion(
            category=category,
            prompt_text=prompt_text,
            issue_count=len(issues),
            severity_summary=severity_summary,
            line_references=sorted(set(line_references))
        )
