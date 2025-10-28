"""
Utility functions for Streamlit app.

This module contains all the business logic and helper functions
used by the Streamlit UI, separated for testability.
"""
import json
import csv
import os
from io import StringIO
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict

from src.models.review_models import ReviewResult, ReviewIssue, Severity, IssueCategory
from src.models.prompt_models import PromptSuggestion, PromptGenerationResult
from src.services.review_engine import ReviewEngine
from src.services.prompt_generator import PromptGenerator


# ============================================================================
# Severity Formatting
# ============================================================================

def format_severity_with_color(severity: Severity) -> str:
    """
    Format severity level with emoji and text.
    
    Args:
        severity: Severity enum value
        
    Returns:
        Formatted string with emoji and severity name
    """
    emoji_map = {
        Severity.CRITICAL: "🔴",
        Severity.HIGH: "🟠",
        Severity.MEDIUM: "🟡",
        Severity.LOW: "🔵",
        Severity.INFO: "⚪"
    }
    
    emoji = emoji_map.get(severity, "⚫")
    return f"{emoji} {severity.value.upper()}"


def get_severity_color_map() -> Dict[Severity, str]:
    """
    Get mapping of severity levels to color codes.
    
    Returns:
        Dictionary mapping Severity to color string
    """
    return {
        Severity.CRITICAL: "red",
        Severity.HIGH: "orange",
        Severity.MEDIUM: "yellow",
        Severity.LOW: "blue",
        Severity.INFO: "gray"
    }


# ============================================================================
# Issue Formatting
# ============================================================================

def format_issue_for_display(issue: ReviewIssue) -> Dict[str, Any]:
    """
    Format a ReviewIssue for display in UI.
    
    Args:
        issue: ReviewIssue object
        
    Returns:
        Dictionary with formatted issue data
    """
    return {
        "severity": issue.severity.value,
        "category": issue.category.value,
        "message": issue.message,
        "line": issue.line_number if issue.line_number else "N/A",
        "suggestion": issue.suggestion,
        "rule_id": issue.rule_id
    }


def group_issues_by_severity(issues: List[ReviewIssue]) -> Dict[Severity, List[ReviewIssue]]:
    """
    Group issues by severity level.
    
    Args:
        issues: List of ReviewIssue objects
        
    Returns:
        Dictionary mapping Severity to list of issues
    """
    grouped = defaultdict(list)
    for issue in issues:
        grouped[issue.severity].append(issue)
    return dict(grouped)


def group_issues_by_category(issues: List[ReviewIssue]) -> Dict[IssueCategory, List[ReviewIssue]]:
    """
    Group issues by category.
    
    Args:
        issues: List of ReviewIssue objects
        
    Returns:
        Dictionary mapping IssueCategory to list of issues
    """
    grouped = defaultdict(list)
    for issue in issues:
        grouped[issue.category].append(issue)
    return dict(grouped)


# ============================================================================
# Review Summary
# ============================================================================

def generate_summary_dict(result: ReviewResult) -> Dict[str, Any]:
    """
    Generate summary dictionary from ReviewResult.
    
    Args:
        result: ReviewResult object
        
    Returns:
        Dictionary with summary metrics
    """
    return {
        "total_issues": result.total_issues,
        "quality_score": result.quality_score,
        "passed": result.passed,
        "critical_count": result.critical_count,
        "high_count": result.high_count,
        "medium_count": result.medium_count,
        "low_count": result.low_count,
        "info_count": result.info_count
    }


def get_quality_score_color(score: float) -> str:
    """
    Get color code based on quality score.
    
    Args:
        score: Quality score (0-100)
        
    Returns:
        Color string for display
    """
    if score >= 90:
        return "green"
    if score >= 70:
        return "yellow"
    return "red"


# ============================================================================
# Code Validation
# ============================================================================

def validate_code_input(code: str, max_lines: int = 10000) -> Tuple[bool, str]:
    """
    Validate code input from user.
    
    Args:
        code: Code string to validate
        max_lines: Maximum allowed lines
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not code or not code.strip():
        return False, "Code input is empty. Please provide code to review."
    
    line_count = len(code.split('\n'))
    if line_count > max_lines:
        return False, f"Code is too large ({line_count} lines). Maximum is {max_lines} lines."
    
    return True, ""


def validate_language_selection(language: str) -> bool:
    """
    Validate language selection.
    
    Args:
        language: Language identifier
        
    Returns:
        True if language is supported
    """
    # Support common languages - no longer using CodeParser
    supported = ["python", "javascript", "typescript", "java", "cpp", "c", "go", "rust"]
    return language.lower() in supported


# ============================================================================
# Review Execution
# ============================================================================

def run_review(code: str, language: str, config: Dict[str, Any]) -> Optional[ReviewResult]:
    """
    Execute code review with given configuration.
    
    Args:
        code: Source code to review
        language: Programming language
        config: Review configuration dictionary
        
    Returns:
        ReviewResult or None if error
    """
    try:
        # Create a simple ParsedCode object without using CodeParser
        from src.models.code_models import ParsedCode, CodeMetadata
        
        # Create basic metadata
        lines = code.split('\n')
        metadata = CodeMetadata(
            line_count=len(lines),
            blank_line_count=sum(1 for line in lines if not line.strip()),
            comment_count=0  # Will be calculated by AI if needed
        )
        
        # Create parsed code object
        parsed_code = ParsedCode(
            content=code,
            language=language,
            metadata=metadata
        )
        
        # Run review
        engine = ReviewEngine(config=config)
        result = engine.review(parsed_code)
        
        return result
    except Exception:
        # Return None or error result
        return None


# ============================================================================
# Export Functionality
# ============================================================================

def export_to_json(result: ReviewResult) -> str:
    """
    Export review result to JSON string.
    
    Args:
        result: ReviewResult object
        
    Returns:
        JSON string
    """
    data = {
        "issues": [
            {
                "severity": issue.severity.value,
                "category": issue.category.value,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
                "rule_id": issue.rule_id
            }
            for issue in result.issues
        ],
        "quality_score": result.quality_score,
        "total_issues": result.total_issues,
        "passed": result.passed,
        "reviewer_name": result.reviewer_name
    }
    
    return json.dumps(data, indent=2)


def export_to_markdown(result: ReviewResult) -> str:
    """
    Export review result to Markdown format.
    
    Args:
        result: ReviewResult object
        
    Returns:
        Markdown string
    """
    md = f"""# Code Review Report

## Summary
- **Quality Score**: {result.quality_score}/100
- **Total Issues**: {result.total_issues}
- **Status**: {'✅ PASSED' if result.passed else '❌ FAILED'}

## Issues by Severity
- 🔴 Critical: {result.critical_count}
- 🟠 High: {result.high_count}
- 🟡 Medium: {result.medium_count}
- 🔵 Low: {result.low_count}
- ⚪ Info: {result.info_count}

## Detailed Issues

"""
    
    for i, issue in enumerate(result.issues, 1):
        severity_color = format_severity_with_color(issue.severity)
        md += f"### {i}. {severity_color} - {issue.category.value.title()}\n"
        md += f"**Line**: {issue.line_number or 'N/A'}\n\n"
        md += f"**Message**: {issue.message}\n\n"
        if issue.suggestion:
            md += f"**Suggestion**: {issue.suggestion}\n\n"
        md += "---\n\n"
    
    return md


def export_to_csv(result: ReviewResult) -> str:
    """
    Export review result to CSV format.
    
    Args:
        result: ReviewResult object
        
    Returns:
        CSV string
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Severity", "Category", "Line", "Message", "Suggestion", "Rule ID"])
    
    # Data rows
    for issue in result.issues:
        writer.writerow([
            issue.severity.value,
            issue.category.value,
            issue.line_number or "N/A",
            issue.message,
            issue.suggestion or "",
            issue.rule_id or ""
        ])
    
    return output.getvalue()


# ============================================================================
# Configuration Helpers
# ============================================================================

def get_default_config() -> Dict[str, Any]:
    """
    Get default review configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        "enable_style": True,
        "enable_complexity": True,
        "enable_security": True,
        "enable_ai": False,
        "max_complexity": 10
    }


def build_config_from_ui_inputs(ui_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build review configuration from UI inputs.
    
    Args:
        ui_inputs: Dictionary of UI input values
        
    Returns:
        Configuration dictionary for ReviewEngine
    """
    config = {}
    
    # Copy all inputs to config
    for key, value in ui_inputs.items():
        config[key] = value
    
    return config


def get_review_mode_config(mode: str) -> Dict[str, Any]:
    """
    Get configuration for predefined review modes.
    
    Args:
        mode: Review mode ('quick', 'standard', 'deep')
        
    Returns:
        Configuration dictionary
    """
    if mode == "quick":
        return {
            "enable_style": True,
            "enable_complexity": True,
            "enable_security": True,
            "enable_ai": False
        }
    if mode == "standard":
        return {
            "enable_style": True,
            "enable_complexity": True,
            "enable_security": True,
            "enable_ai": True,
            "ai_model": "gpt-4o-mini"
        }
    if mode == "deep":
        return {
            "enable_style": False,
            "enable_complexity": False,
            "enable_security": False,
            "enable_ai": True,
            "ai_model": "gpt-4o"
        }
    
    return get_default_config()


# ============================================================================
# Prompt Generation Integration
# ============================================================================

def generate_copilot_prompts(
    review_result: ReviewResult,
    language: str = "python",
    api_key: Optional[str] = None
) -> Optional[PromptGenerationResult]:
    """
    Generate GitHub Copilot prompts from review results.
    
    Args:
        review_result: ReviewResult containing code issues
        language: Programming language for context
        api_key: Optional API key (uses environment variable if not provided)
        
    Returns:
        PromptGenerationResult with generated prompts, or None if API key missing
    """
    # Check for API key
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return None
    
    # Check if there are any issues
    if not review_result.issues:
        return PromptGenerationResult(language=language)
    
    try:
        # Create generator and generate prompts
        generator = PromptGenerator(api_key=api_key)
        result = generator.generate(review_result, language=language)
        return result
    except Exception:
        # Return empty result on error
        return PromptGenerationResult(language=language)


# ============================================================================
# Prompt Formatting for UI
# ============================================================================

def format_prompt_for_display(prompt: PromptSuggestion) -> Dict[str, Any]:
    """
    Format a single prompt suggestion for UI display.
    
    Args:
        prompt: PromptSuggestion to format
        
    Returns:
        Dictionary with formatted prompt data for display
    """
    # Get category emoji
    category_emoji = get_category_emoji(prompt.category)
    category_display = f"{category_emoji} {prompt.category.value.replace('_', ' ').title()}"
    
    # Format line references
    if prompt.line_references:
        lines_display = ", ".join(str(line) for line in prompt.line_references)
    else:
        lines_display = "N/A"
    
    return {
        "category": category_display,
        "prompt": prompt.prompt_text,
        "issue_count": prompt.issue_count,
        "severity": prompt.severity_summary,
        "lines": lines_display
    }


def format_prompts_for_display(result: PromptGenerationResult) -> List[Dict[str, Any]]:
    """
    Format all prompts in result for UI display.
    
    Args:
        result: PromptGenerationResult with prompts
        
    Returns:
        List of formatted prompt dictionaries
    """
    return [format_prompt_for_display(prompt) for prompt in result.prompts]


# ============================================================================
# Prompt Export
# ============================================================================

def export_prompts_to_text(result: PromptGenerationResult) -> str:
    """
    Export prompts as plain text format.
    
    Args:
        result: PromptGenerationResult to export
        
    Returns:
        Formatted text string
    """
    if not result.has_prompts():
        return "No prompts generated."
    
    lines = ["=" * 80]
    lines.append("GITHUB COPILOT PROMPTS")
    lines.append(f"Language: {result.language}")
    lines.append("=" * 80)
    lines.append("")
    
    for i, prompt in enumerate(result.prompts, 1):
        lines.append(f"{i}. {prompt.category.value.replace('_', ' ').upper()}")
        lines.append(f"   Issues: {prompt.issue_count} ({prompt.severity_summary})")
        if prompt.line_references:
            lines.append(f"   Lines: {', '.join(str(line) for line in prompt.line_references)}")
        lines.append("")
        lines.append(f"   Prompt:")
        lines.append(f"   {prompt.prompt_text}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("")
    
    return "\n".join(lines)


def export_prompts_to_json(result: PromptGenerationResult) -> str:
    """
    Export prompts as JSON format.
    
    Args:
        result: PromptGenerationResult to export
        
    Returns:
        JSON string
    """
    data = {
        "language": result.language,
        "prompt_count": len(result.prompts),
        "prompts": [
            {
                "category": prompt.category.value,
                "prompt_text": prompt.prompt_text,
                "issue_count": prompt.issue_count,
                "severity_summary": prompt.severity_summary,
                "line_references": prompt.line_references
            }
            for prompt in result.prompts
        ]
    }
    
    return json.dumps(data, indent=2)


def export_prompts_to_markdown(result: PromptGenerationResult) -> str:
    """
    Export prompts as Markdown format.
    
    Args:
        result: PromptGenerationResult to export
        
    Returns:
        Markdown string
    """
    if not result.has_prompts():
        return "# GitHub Copilot Prompts\n\nNo prompts generated."
    
    md = "# GitHub Copilot Prompts\n\n"
    md += f"**Language**: {result.language}\n\n"
    md += f"**Total Prompts**: {len(result.prompts)}\n\n"
    md += "---\n\n"
    
    for i, prompt in enumerate(result.prompts, 1):
        category_emoji = get_category_emoji(prompt.category)
        md += f"## {i}. {category_emoji} {prompt.category.value.replace('_', ' ').title()}\n\n"
        md += f"**Issues Addressed**: {prompt.issue_count}\n\n"
        md += f"**Severity**: {prompt.severity_summary}\n\n"
        
        if prompt.line_references:
            md += f"**Lines**: {', '.join(str(line) for line in prompt.line_references)}\n\n"
        
        md += "### Prompt\n\n"
        md += f"```\n{prompt.prompt_text}\n```\n\n"
        md += "---\n\n"
    
    return md


# ============================================================================
# Prompt Copy Helper
# ============================================================================

def prepare_prompt_for_copy(
    prompt: PromptSuggestion,
    include_context: bool = False
) -> str:
    """
    Prepare prompt text for copying to clipboard (GitHub Copilot ready).
    
    Args:
        prompt: PromptSuggestion to prepare
        include_context: Whether to include context information
        
    Returns:
        Clean prompt text ready for Copilot
    """
    if not include_context:
        # Just the prompt text, clean and ready
        return prompt.prompt_text
    
    # Include context for better results
    context_parts = []
    context_parts.append(f"Category: {prompt.category.value.replace('_', ' ').title()}")
    context_parts.append(f"Issues: {prompt.issue_count} ({prompt.severity_summary})")
    
    if prompt.line_references:
        lines_str = ", ".join(str(line) for line in prompt.line_references)
        context_parts.append(f"Lines: {lines_str}")
    
    context_parts.append("")
    context_parts.append(prompt.prompt_text)
    
    return "\n".join(context_parts)


# ============================================================================
# UI Helper Functions
# ============================================================================

def get_category_emoji(category: IssueCategory) -> str:
    """
    Get emoji representation for issue category.
    
    Args:
        category: IssueCategory enum value
        
    Returns:
        Emoji string
    """
    emoji_map = {
        IssueCategory.SECURITY: "🔒",
        IssueCategory.COMPLEXITY: "🔄",
        IssueCategory.STYLE: "✨",
        IssueCategory.PERFORMANCE: "⚡",
        IssueCategory.BUG_RISK: "🐛",
        IssueCategory.BEST_PRACTICES: "👍",
        IssueCategory.DOCUMENTATION: "📝"
    }
    
    return emoji_map.get(category, "📌")


def get_category_color(category: IssueCategory) -> str:
    """
    Get color code for issue category.
    
    Args:
        category: IssueCategory enum value
        
    Returns:
        Color string for UI styling
    """
    color_map = {
        IssueCategory.SECURITY: "red",
        IssueCategory.BUG_RISK: "orange",
        IssueCategory.COMPLEXITY: "blue",
        IssueCategory.PERFORMANCE: "blue",
        IssueCategory.STYLE: "gray",
        IssueCategory.BEST_PRACTICES: "blue",
        IssueCategory.DOCUMENTATION: "gray"
    }
    
    return color_map.get(category, "gray")


def should_generate_prompts(has_api_key: bool, has_issues: bool) -> bool:
    """
    Determine if prompts should be generated based on configuration.
    
    Args:
        has_api_key: Whether OpenAI API key is available
        has_issues: Whether review found any issues
        
    Returns:
        True if prompts should be generated
    """
    return has_api_key and has_issues
