"""
Data models for code parsing and analysis.

These Pydantic models provide type-safe representations of
parsed code and its metadata for the code review system.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CodeMetadata(BaseModel):
    """
    Metadata extracted from parsed code.
    
    Contains various metrics and information about the code structure,
    complexity, and characteristics.
    """
    line_count: int = Field(default=0, ge=0, description="Total number of lines")
    function_count: int = Field(default=0, ge=0, description="Number of functions")
    class_count: int = Field(default=0, ge=0, description="Number of classes")
    comment_count: int = Field(default=0, ge=0, description="Number of comments")
    import_count: int = Field(default=0, ge=0, description="Number of import statements")
    complexity: float = Field(default=1.0, ge=1.0, description="Cyclomatic complexity")
    
    # Advanced metadata
    function_names: List[str] = Field(
        default_factory=list, description="List of function names"
    )
    class_names: List[str] = Field(
        default_factory=list, description="List of class names"
    )
    has_docstrings: bool = Field(
        default=False, description="Whether code contains docstrings"
    )
    docstring_count: int = Field(default=0, ge=0, description="Number of docstrings")
    comment_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Ratio of comments to total lines"
    )
    
    # Additional metrics
    blank_line_count: int = Field(default=0, ge=0, description="Number of blank lines")
    code_line_count: int = Field(
        default=0, ge=0,
        description="Number of actual code lines (excluding comments/blanks)"
    )
    
    @field_validator('comment_ratio')
    @classmethod
    def validate_comment_ratio(cls, v: float) -> float:
        """Ensure comment ratio is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Comment ratio must be between 0 and 1")
        return v


class ParsedCode(BaseModel):
    """
    Represents parsed code with its content and metadata.
    
    This is the primary model returned by the CodeParser service.
    """
    content: str = Field(description="The raw code content")
    language: str = Field(description="Programming language of the code")
    metadata: CodeMetadata = Field(description="Extracted metadata about the code")
    
    # Error tracking
    has_syntax_errors: bool = Field(
        default=False, description="Whether syntax errors were detected"
    )
    syntax_errors: List[str] = Field(
        default_factory=list, description="List of syntax error messages"
    )
    
    # Optional file information
    file_path: Optional[str] = Field(
        default=None, description="Path to source file if parsed from file"
    )
    encoding: str = Field(default="utf-8", description="Character encoding of the source")
    
    # Parsing metadata
    parse_timestamp: Optional[str] = Field(
        default=None, description="ISO timestamp of when parsing occurred"
    )
    parser_version: str = Field(
        default="1.0.0", description="Version of the parser used"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Ensure language is lowercase."""
        return v.lower()
    
    def is_valid(self) -> bool:
        """
        Check if the parsed code is valid (no syntax errors).
        
        Returns:
            bool: True if code has no syntax errors, False otherwise
        """
        return not self.has_syntax_errors
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the parsed code.
        
        Returns:
            dict: Summary containing key metrics
        """
        return {
            "language": self.language,
            "lines": self.metadata.line_count,
            "functions": self.metadata.function_count,
            "classes": self.metadata.class_count,
            "complexity": self.metadata.complexity,
            "has_errors": self.has_syntax_errors,
        }
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "def hello():\n    return 'Hello, World!'\n",
                "language": "python",
                "metadata": {
                    "line_count": 2,
                    "function_count": 1,
                    "class_count": 0,
                    "comment_count": 0,
                    "import_count": 0,
                    "complexity": 1.0,
                    "function_names": ["hello"],
                    "class_names": [],
                    "has_docstrings": False,
                    "docstring_count": 0,
                    "comment_ratio": 0.0,
                    "blank_line_count": 0,
                    "code_line_count": 2,
                },
                "has_syntax_errors": False,
                "syntax_errors": [],
            }
        }
    )
