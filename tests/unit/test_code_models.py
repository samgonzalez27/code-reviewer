"""
Unit tests for code models (ParsedCode, CodeMetadata).
"""
import pytest
from pydantic import ValidationError
from src.models.code_models import ParsedCode, CodeMetadata


class TestCodeMetadataValidation:
    """Test validation logic in CodeMetadata."""
    
    def test_comment_ratio_valid_values(self):
        """CodeMetadata should accept valid comment ratios (0.0 to 1.0)."""
        # Test boundary values
        metadata1 = CodeMetadata(comment_ratio=0.0)
        assert metadata1.comment_ratio == 0.0
        
        metadata2 = CodeMetadata(comment_ratio=1.0)
        assert metadata2.comment_ratio == 1.0
        
        metadata3 = CodeMetadata(comment_ratio=0.5)
        assert metadata3.comment_ratio == 0.5
    
    def test_comment_ratio_rejects_negative(self):
        """CodeMetadata should reject negative comment ratios."""
        with pytest.raises(ValidationError):
            CodeMetadata(comment_ratio=-0.1)
    
    def test_comment_ratio_rejects_above_one(self):
        """CodeMetadata should reject comment ratios above 1.0."""
        with pytest.raises(ValidationError):
            CodeMetadata(comment_ratio=1.5)


class TestParsedCodeMethods:
    """Test ParsedCode methods."""
    
    def test_is_valid_with_no_syntax_errors(self):
        """is_valid() should return True when has_syntax_errors is False."""
        parsed = ParsedCode(
            content="def foo(): pass",
            language="python",
            metadata=CodeMetadata(),
            has_syntax_errors=False
        )
        assert parsed.is_valid() is True
    
    def test_is_valid_with_syntax_errors(self):
        """is_valid() should return False when has_syntax_errors is True."""
        parsed = ParsedCode(
            content="def foo(",
            language="python",
            metadata=CodeMetadata(),
            has_syntax_errors=True
        )
        assert parsed.is_valid() is False
    
    def test_get_summary_structure(self):
        """get_summary() should return a dict with expected keys."""
        metadata = CodeMetadata(
            line_count=10,
            function_count=2,
            class_count=1,
            complexity=5.0,
            comment_ratio=0.2
        )
        parsed = ParsedCode(
            content="class Foo:\n    def bar(): pass",
            language="python",
            metadata=metadata,
            has_syntax_errors=False
        )
        
        summary = parsed.get_summary()
        
        # Check structure
        assert "language" in summary
        assert "lines" in summary
        assert "functions" in summary
        assert "classes" in summary
        assert "complexity" in summary
        assert "has_errors" in summary
        
        # Check values
        assert summary["language"] == "python"
        assert summary["lines"] == 10
        assert summary["functions"] == 2
        assert summary["classes"] == 1
        assert summary["complexity"] == 5.0
        assert summary["has_errors"] is False
