"""
AI-Powered Code Fixer Service.

This service uses OpenAI's Chat Completion API to generate automated
code fixes for issues detected during code review.
"""
import os
import json
from typing import Optional, Dict, Any, List
from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.models.code_models import ParsedCode
from src.models.review_models import ReviewIssue, Severity, IssueCategory
from src.models.code_fix_models import (
    CodeFix,
    CodeFixResult,
    FixConfidence,
    FixStatus,
)


class CodeFixer:
    """AI-powered code fixer using OpenAI's GPT models."""
    
    DEFAULT_SYSTEM_PROMPT = """You are an expert code fixing assistant. Generate precise, \
safe code fixes for identified issues.

IMPORTANT: You must respond with ONLY valid JSON in this exact format:
{
  "fixes": [
    {
      "issue_description": "Clear description of what is being fixed",
      "original_code": "The problematic code",
      "fixed_code": "The corrected code",
      "line_start": 1,
      "line_end": 1,
      "explanation": "Why this fix is needed and what it does",
      "confidence": "low|medium|high|verified",
      "diff": "Optional unified diff format"
    }
  ]
}

If no fixes can be generated, return: {"fixes": []}
Do not include any text before or after the JSON."""
    
    def __init__(
        self,
        client: Optional[OpenAI] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize CodeFixer."""
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
        self.temperature = self.config.get("temperature", 0.2)
        self.max_tokens = self.config.get("max_tokens", 2000)
        self.timeout = self.config.get("timeout", 30)
        self.system_prompt = self.config.get("system_prompt", self.DEFAULT_SYSTEM_PROMPT)
        
        # Usage tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0
    
    def generate_fix(
        self,
        parsed_code: ParsedCode,
        issue: ReviewIssue
    ) -> CodeFixResult:
        """
        Generate a fix for a single issue.
        
        Args:
            parsed_code: The parsed code containing the issue
            issue: The issue to fix
            
        Returns:
            CodeFixResult with the generated fix(es)
        """
        return self.generate_fixes(parsed_code, [issue])
    
    def generate_fixes(
        self,
        parsed_code: ParsedCode,
        issues: List[ReviewIssue]
    ) -> CodeFixResult:
        """
        Generate fixes for multiple issues.
        
        Args:
            parsed_code: The parsed code containing the issues
            issues: List of issues to fix
            
        Returns:
            CodeFixResult with all generated fixes
        """
        result = CodeFixResult()
        
        # Handle empty issues list
        if not issues:
            return result
        
        try:
            # Build prompt with code and issues
            user_prompt = self._build_user_prompt(parsed_code, issues)
            
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
            
            # Parse AI response into fixes
            fixes = self._parse_ai_response(response, issues)
            for fix in fixes:
                result.add_fix(fix)
        
        except Exception as e:
            # Handle API errors gracefully
            result.success = False
            result.error_message = str(e)
        
        return result
    
    def _build_user_prompt(
        self,
        parsed_code: ParsedCode,
        issues: List[ReviewIssue]
    ) -> str:
        """Build the user prompt with code and issues."""
        # Extract relevant code context
        code_context = self._extract_code_context(parsed_code, issues)
        
        # Build issues description
        issues_desc = []
        for i, issue in enumerate(issues, 1):
            line_info = f"line {issue.line_number}" if issue.line_number else "general"
            issues_desc.append(
                f"{i}. [{issue.severity.value.upper()}] {issue.message} ({line_info})"
            )
        
        prompt = f"""Generate fixes for the following issues in this {parsed_code.language.upper()} code:

Issues to fix:
{chr(10).join(issues_desc)}

Code context:
```{parsed_code.language}
{code_context}
```

For each issue, generate a precise fix with:
- The exact original code that needs to be changed
- The corrected code
- Line numbers where the fix should be applied
- Confidence level (high for safe/obvious fixes, medium for good fixes, low for uncertain)
- Brief explanation of the fix

Return your fixes as JSON only."""
        return prompt
    
    def _extract_code_context(
        self,
        parsed_code: ParsedCode,
        issues: List[ReviewIssue]
    ) -> str:
        """
        Extract relevant code context for the issues.
        
        For large files, extracts context around issue locations.
        For small files or issues without line numbers, returns full code.
        """
        # If file is small (< 100 lines), return full code
        if parsed_code.metadata.line_count < 100:
            return parsed_code.content
        
        # Check if all issues have line numbers
        issue_lines = [i.line_number for i in issues if i.line_number is not None]
        if not issue_lines:
            # No line numbers, return full code
            return parsed_code.content
        
        # Extract context around issues (±10 lines)
        lines = parsed_code.content.split('\n')
        context_lines = set()
        
        for line_num in issue_lines:
            start = max(0, line_num - 11)  # -1 for 0-indexing, -10 for context
            end = min(len(lines), line_num + 10)
            for i in range(start, end):
                context_lines.add(i)
        
        # Build context with line numbers
        sorted_lines = sorted(context_lines)
        context_parts = []
        
        for line_idx in sorted_lines:
            context_parts.append(f"{line_idx + 1}: {lines[line_idx]}")
        
        return '\n'.join(context_parts)
    
    def _parse_ai_response(
        self,
        response: ChatCompletion,
        issues: List[ReviewIssue]
    ) -> List[CodeFix]:
        """Parse OpenAI API response into CodeFix objects."""
        fixes = []
        
        try:
            content = response.choices[0].message.content
            if not content:
                return fixes
            
            # Try parsing as JSON
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "fixes" in data:
                    fixes_data = data["fixes"]
                elif isinstance(data, list):
                    fixes_data = data
                else:
                    return fixes
            except json.JSONDecodeError:
                # Try extracting from markdown code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    if json_end > json_start:
                        content = content[json_start:json_end].strip()
                        data = json.loads(content)
                        fixes_data = data if isinstance(data, list) else data.get("fixes", [])
                    else:
                        return fixes
                else:
                    return fixes
            
            # Convert to CodeFix objects
            for fix_data in fixes_data:
                try:
                    # Parse confidence
                    confidence_str = fix_data.get("confidence", "medium").lower()
                    try:
                        confidence = FixConfidence(confidence_str)
                    except ValueError:
                        confidence = FixConfidence.MEDIUM
                    
                    # Map issue to fix for severity/category
                    severity = Severity.INFO
                    category = IssueCategory.BEST_PRACTICES
                    
                    # Try to match issue by line number or description
                    line_start = fix_data.get("line_start")
                    if line_start:
                        for issue in issues:
                            if issue.line_number == line_start:
                                severity = issue.severity
                                category = issue.category
                                break
                    
                    fix = CodeFix(
                        issue_description=fix_data.get("issue_description", ""),
                        original_code=fix_data.get("original_code", ""),
                        fixed_code=fix_data.get("fixed_code", ""),
                        line_start=fix_data.get("line_start", 1),
                        line_end=fix_data.get("line_end", fix_data.get("line_start", 1)),
                        explanation=fix_data.get("explanation"),
                        confidence=confidence,
                        severity=severity,
                        category=category,
                        diff=fix_data.get("diff")
                    )
                    fixes.append(fix)
                except (KeyError, ValueError, TypeError):
                    # Skip invalid fixes
                    continue
        
        except Exception:
            pass
        
        return fixes
    
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
        """Get usage statistics for this fixer."""
        return {
            "total_tokens": self.total_tokens_used,
            "estimated_cost_usd": round(self.total_cost, 4),
            "model": self.model
        }
