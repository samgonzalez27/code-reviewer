"""
Utility functions for Streamlit app.

This module contains all the business logic and helper functions
used by the Streamlit UI, separated for testability.
"""
import json
import csv
from io import StringIO
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict

from src.models.review_models import ReviewResult, ReviewIssue, Severity, IssueCategory
from src.services.code_parser import CodeParser
from src.services.review_engine import ReviewEngine
from src.models.code_fix_models import CodeFixResult, FixConfidence, FixStatus


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
    parser = CodeParser()
    supported = parser.supported_languages()
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
        # Parse code
        parser = CodeParser()
        parsed_code = parser.parse(code, language)
        
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


def apply_fixes_to_code(
    code: str,
    fix_result: CodeFixResult,
    min_confidence: str = "high"
) -> str:
    """
    Apply generated fixes to source code.

    Strategy:
    - Filter fixes by confidence threshold.
    - Sort fixes by line_start in descending order to avoid shifting lines
      when applying multiple fixes.
    - Prefer line-number based replacement when possible (safer),
      otherwise fall back to a first-occurrence string replacement.

    Args:
        code: Original source code
        fix_result: CodeFixResult containing fixes
        min_confidence: Minimum confidence to apply (low/medium/high/verified/all)

    Returns:
        Modified source code with applicable fixes applied.
    """
    if not fix_result or not fix_result.fixes:
        return code

    # Normalize min_confidence
    min_conf = min_confidence.lower() if isinstance(min_confidence, str) else str(min_confidence)
    if min_conf == "all":
        min_conf_enum = None
    else:
        try:
            min_conf_enum = FixConfidence(min_conf)
        except Exception:
            # Default to high if unknown
            min_conf_enum = FixConfidence.HIGH

    # Map confidence to numeric order
    order = {
        FixConfidence.LOW: 0,
        FixConfidence.MEDIUM: 1,
        FixConfidence.HIGH: 2,
        FixConfidence.VERIFIED: 3,
    }

    min_value = 0 if min_conf_enum is None else order.get(min_conf_enum, 2)

    # Filter fixes
    applicable = [f for f in fix_result.fixes if order.get(f.confidence, 0) >= min_value]

    # Sort by line_start descending
    applicable.sort(key=lambda f: getattr(f, "line_start", 0) or 0, reverse=True)

    modified = code
    lines = modified.split('\n')

    for fix in applicable:
        try:
            ls = int(getattr(fix, "line_start", 1))
            le = int(getattr(fix, "line_end", ls))
        except Exception:
            ls, le = 1, 1

        # Use line-based replacement if line numbers are within range
        if 1 <= ls <= len(lines):
            # Adjust for 0-based index
            start_idx = max(0, ls - 1)
            end_idx = min(len(lines), le)
            fixed_lines = (fix.fixed_code or "").split('\n')
            # Replace the slice
            lines[start_idx:end_idx] = fixed_lines
            modified = "\n".join(lines)
            # Update lines reference for subsequent fixes
            lines = modified.split('\n')
            # Mark fix as applied
            try:
                fix.status = FixStatus.APPLIED
            except Exception:
                pass
            continue

        # Fallback: string replace first occurrence
        if fix.original_code and fix.original_code in modified:
            modified = modified.replace(fix.original_code, fix.fixed_code or "", 1)
            lines = modified.split('\n')
            try:
                fix.status = FixStatus.APPLIED
            except Exception:
                pass

    # Update statistics on the result
    try:
        fix_result.update_statistics()
    except Exception:
        pass

    return modified
