# Auto-Fix Generation Design Document

## Overview
This document describes the test-driven design for extending the AI Code Reviewer system to support automatic fix generation. The design follows object-oriented principles and uses the Strategy pattern to maintain consistency with the existing architecture.

## Design Principles

### 1. Object-Oriented Design Patterns
- **Strategy Pattern**: Both `AIReviewer` and `CodeFixer` follow the strategy pattern, making them interchangeable and testable
- **Single Responsibility**: Each class has a clear, focused purpose
- **Dependency Injection**: Services accept dependencies via constructor for testability
- **Separation of Concerns**: Models, services, and business logic are clearly separated

### 2. Test-Driven Development (TDD)
All tests were written before implementation, following:
- Red-Green-Refactor cycle
- Comprehensive edge case coverage
- Mock-based unit testing for external dependencies

## Architecture Components

### 1. Data Models (`src/models/code_fix_models.py`)

#### FixStatus Enum
```python
class FixStatus(str, Enum):
    SUGGESTED = "suggested"  # Fix has been suggested but not applied
    APPLIED = "applied"      # Fix has been applied to the code
    REJECTED = "rejected"    # Fix was rejected by user
    PENDING = "pending"      # Fix is pending review
```

#### FixConfidence Enum
```python
class FixConfidence(str, Enum):
    LOW = "low"          # AI is uncertain about this fix
    MEDIUM = "medium"    # AI is moderately confident
    HIGH = "high"        # AI is confident this fix is correct
    VERIFIED = "verified" # Fix has been verified (e.g., by tests)
```

#### CodeFix Model
Represents a single code fix suggestion:
- **issue_description**: Description of the issue being fixed
- **original_code**: The original problematic code
- **fixed_code**: The corrected code
- **line_start/line_end**: Location in the file
- **explanation**: Human-readable explanation of the fix
- **confidence**: Confidence level (FixConfidence)
- **severity**: Severity of the issue (from review_models)
- **category**: Category of the issue (from review_models)
- **status**: Current status of the fix
- **diff**: Optional unified diff format

Methods:
- `is_high_confidence()`: Returns True if confidence is HIGH or VERIFIED
- `is_critical()`: Returns True if severity is CRITICAL

#### CodeFixResult Model
Aggregates all fixes for a code review:
- **fixes**: List of CodeFix objects
- **total_fixes**: Count of all fixes
- **high_confidence_count**: Count of high/verified confidence fixes
- **medium_confidence_count**: Count of medium confidence fixes
- **low_confidence_count**: Count of low confidence fixes
- **applied_count**: Count of fixes that have been applied
- **success**: Whether fix generation succeeded
- **error_message**: Optional error message if generation failed
- **fixer_name**: Name of the service that generated fixes

Methods:
- `add_fix(fix)`: Add a fix and update statistics
- `update_statistics()`: Recalculate all statistics
- `get_fixes_by_confidence(confidence)`: Filter fixes by confidence level
- `get_fixes_by_status(status)`: Filter fixes by status
- `get_high_confidence_fixes()`: Get only high/verified confidence fixes
- `has_fixes()`: Check if any fixes were generated
- `get_summary()`: Get summary statistics dict

### 2. CodeFixer Service (`src/services/code_fixer.py`)

A new service responsible for generating automated fixes using AI.

#### Responsibilities
1. Generate fixes for individual issues
2. Generate fixes for multiple issues in batch
3. Extract relevant code context around issues
4. Parse AI responses into CodeFix objects
5. Track token usage and costs

#### Key Methods

```python
def __init__(client: Optional[OpenAI] = None, config: Optional[Dict[str, Any]] = None)
```
- Accepts OpenAI client and configuration
- Creates client from environment if not provided
- Initializes with sensible defaults (model: gpt-4o-mini, temperature: 0.2)

```python
def generate_fix(parsed_code: ParsedCode, issue: ReviewIssue) -> CodeFixResult
```
- Generates a fix for a single issue
- Extracts relevant code context around the issue line number
- Calls OpenAI API with structured prompt
- Parses response into CodeFixResult
- Handles errors gracefully

```python
def generate_fixes(parsed_code: ParsedCode, issues: List[ReviewIssue]) -> CodeFixResult
```
- Generates fixes for multiple issues in one API call
- More efficient than calling generate_fix repeatedly
- Returns consolidated CodeFixResult

```python
def get_usage_stats() -> Dict[str, Any]
```
- Returns token usage and estimated cost
- Similar to AIReviewer's usage tracking

#### Context Window Management
- For large files, extracts relevant context around issue line numbers (e.g., ±10 lines)
- Handles issues without line numbers by including full code or reasonable default
- Prevents context window overflow with large files

### 3. AIReviewer Extensions (`src/services/ai_reviewer.py`)

Extended to integrate with CodeFixer for automatic fix generation.

#### New Configuration Options
```python
config = {
    "enable_auto_fix": bool,      # Enable/disable auto-fix generation
    "code_fixer": CodeFixer,      # Optional CodeFixer instance
    "auto_fix_min_severity": Severity,  # Minimum severity for auto-fix
}
```

#### New/Modified Methods

```python
def review(parsed_code: ParsedCode) -> ReviewResult
```
- Extended to optionally generate fixes when `enable_auto_fix=True`
- Attaches `fix_result: CodeFixResult` to ReviewResult
- Only generates fixes if issues are found
- Handles CodeFixer errors gracefully without failing the review

```python
def review_with_fixes(parsed_code: ParsedCode, auto_fix: bool = True) -> Tuple[ReviewResult, CodeFixResult]
```
- Dedicated method that explicitly returns both review and fix results
- Always attempts fix generation (unless auto_fix=False)
- Returns tuple of (ReviewResult, CodeFixResult)

```python
def get_fixable_issues(issues: List[ReviewIssue], min_severity: Severity = Severity.MEDIUM) -> List[ReviewIssue]
```
- Filters issues to determine which are auto-fixable
- Excludes issues without line numbers (can't fix without location)
- Respects minimum severity threshold
- May filter by category (e.g., COMPLEXITY issues are typically not auto-fixable)

```python
def apply_fixes(parsed_code: ParsedCode, fixes: CodeFixResult, min_confidence: FixConfidence = FixConfidence.HIGH) -> str
```
- Applies fixes to the code
- Only applies fixes meeting minimum confidence threshold
- Applies fixes in order (considering line number changes)
- Returns original code on error (safe fallback)
- Returns modified code string

## Integration Flow

### Standard Review Flow (auto-fix disabled)
1. User calls `reviewer.review(parsed_code)`
2. AIReviewer analyzes code and returns ReviewResult with issues
3. No fix generation occurs

### Review with Auto-Fix Flow (auto-fix enabled)
1. User calls `reviewer.review(parsed_code)` with `enable_auto_fix=True` config
2. AIReviewer analyzes code → generates ReviewResult with issues
3. If issues found:
   - Filters fixable issues using `get_fixable_issues()`
   - Calls `code_fixer.generate_fixes(parsed_code, fixable_issues)`
   - Attaches CodeFixResult to ReviewResult
4. Returns ReviewResult with embedded fix_result

### Explicit Fix Generation Flow
1. User calls `review_result, fix_result = reviewer.review_with_fixes(parsed_code)`
2. AIReviewer performs review
3. Generates fixes for all fixable issues
4. Returns separate ReviewResult and CodeFixResult objects

### Fix Application Flow
1. User has ReviewResult with fix_result
2. User calls `modified_code = reviewer.apply_fixes(parsed_code, fix_result, min_confidence=FixConfidence.HIGH)`
3. AIReviewer applies only high-confidence fixes
4. Returns modified code string
5. User can save modified code or preview changes

## Test Coverage

### Model Tests (`tests/unit/test_code_fix_models.py`) - 514 lines
- ✅ FixStatus and FixConfidence enum values
- ✅ CodeFix model creation with required/optional fields
- ✅ CodeFix validation (required fields, positive line numbers)
- ✅ CodeFix helper methods (is_high_confidence, is_critical)
- ✅ CodeFixResult creation and defaults
- ✅ CodeFixResult.add_fix() updates statistics
- ✅ CodeFixResult filtering by confidence and status
- ✅ CodeFixResult.get_high_confidence_fixes()
- ✅ CodeFixResult.get_summary()
- ✅ Error handling with success flag

### CodeFixer Tests (`tests/unit/test_code_fixer.py`) - 543 lines
- ✅ Initialization with client and configuration
- ✅ Client creation from environment
- ✅ Error when no API key
- ✅ generate_fix() returns CodeFixResult
- ✅ generate_fix() calls OpenAI API correctly
- ✅ Issue details included in prompt
- ✅ Code context included in prompt
- ✅ Parsing single fix from AI response
- ✅ Parsing multiple fixes (batch generation)
- ✅ Parsing different confidence levels
- ✅ Parsing diff information
- ✅ Handling malformed JSON gracefully
- ✅ Extracting JSON from markdown blocks
- ✅ Empty issues list handling
- ✅ Token usage tracking
- ✅ Cost estimation
- ✅ Context window management for large files
- ✅ Issues without line numbers
- ✅ API error handling

### AIReviewer Integration Tests (`tests/unit/test_ai_reviewer_autofix.py`) - 563 lines
- ✅ Auto-fix configuration options
- ✅ Auto-fix disabled by default
- ✅ CodeFixer instance injection
- ✅ Automatic CodeFixer creation
- ✅ review() with auto-fix returns extended result
- ✅ review() calls CodeFixer when enabled
- ✅ review() skips fixes when disabled
- ✅ review() doesn't call fixer when no issues
- ✅ review() handles CodeFixer errors
- ✅ review_with_fixes() exists and returns tuple
- ✅ review_with_fixes() accepts auto_fix parameter
- ✅ get_fixable_issues() filtering by category
- ✅ get_fixable_issues() respects min_severity
- ✅ get_fixable_issues() excludes issues without line numbers
- ✅ apply_fixes() modifies code correctly
- ✅ apply_fixes() respects confidence threshold
- ✅ apply_fixes() handles multiple fixes
- ✅ apply_fixes() returns original on error

## Design Benefits

### 1. Testability
- All components are unit testable with mocked dependencies
- No coupling to external APIs in tests
- Clear interfaces between components

### 2. Flexibility
- CodeFixer can be used standalone or integrated with AIReviewer
- Configuration-driven behavior (enable/disable auto-fix)
- Pluggable confidence thresholds for fix application

### 3. Safety
- Multi-level confidence system prevents dangerous auto-fixes
- Original code preserved on errors
- Fixes are suggestions by default, not automatically applied
- High confidence threshold for actual application

### 4. Maintainability
- Clear separation of concerns
- Follows existing code patterns (Strategy pattern)
- Comprehensive test coverage
- Self-documenting code through Pydantic models

### 5. Extensibility
- Easy to add new fix types
- Can add verification step (e.g., syntax check after fix)
- Can integrate with other review strategies
- Could add user feedback loop to improve confidence scoring

## Future Enhancements (Out of Scope)

1. **Fix Verification**: Run fixes through linters/tests to increase confidence
2. **Interactive Mode**: Present fixes to user for approval before applying
3. **Batch Application**: Apply multiple fixes atomically with rollback
4. **Fix History**: Track which fixes were accepted/rejected for learning
5. **Custom Fix Templates**: Allow users to define fix patterns
6. **Diff Preview**: Show unified diffs before applying fixes
7. **Multi-file Fixes**: Handle fixes that span multiple files
8. **Incremental Fixes**: Apply fixes one at a time with validation

## Implementation Checklist

- [x] Write tests for CodeFix and CodeFixResult models
- [x] Write tests for CodeFixer service
- [x] Write tests for AIReviewer auto-fix integration
- [x] Atomic commits for each test suite
- [ ] Implement CodeFix and CodeFixResult models
- [ ] Implement CodeFixer service
- [ ] Extend AIReviewer with auto-fix capabilities
- [ ] Verify all tests pass
- [ ] Update documentation
- [ ] Add integration tests
- [ ] Performance testing with large files

## Atomic Commits Made

1. `8035d7c` - test: add comprehensive tests for CodeFix and CodeFixResult models
2. `be98bdf` - test: add comprehensive tests for CodeFixer service
3. `e06d770` - test: add tests for AIReviewer auto-fix integration

Total: 3 atomic commits, 1,620 lines of test code
