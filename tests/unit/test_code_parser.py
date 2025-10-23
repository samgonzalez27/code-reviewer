"""
Unit tests for CodeParser service.

This module tests the code parsing functionality that extracts
metadata and prepares code for review analysis.

Following TDD: Write tests first (RED), then implement (GREEN), then refactor.
"""
import pytest
from pathlib import Path
from src.services.code_parser import CodeParser
from src.models.code_models import ParsedCode, CodeMetadata


class TestCodeParserInitialization:
    """Test CodeParser initialization and configuration."""
    
    def test_code_parser_can_be_instantiated(self):
        """Test that CodeParser can be created."""
        parser = CodeParser()
        assert parser is not None
    
    def test_code_parser_accepts_configuration(self):
        """Test that CodeParser can be configured with options."""
        config = {"max_file_size": 1024, "encoding": "utf-8"}
        parser = CodeParser(config=config)
        assert parser is not None


class TestCodeParserBasicParsing:
    """Test basic code parsing functionality."""
    
    def test_parse_simple_python_function(self):
        """Test parsing a simple Python function."""
        parser = CodeParser()
        code = """def hello():
    return "Hello, World!"
"""
        
        result = parser.parse(code, language="python")
        
        assert isinstance(result, ParsedCode)
        assert result.content == code
        assert result.language == "python"
        assert result.metadata is not None
    
    def test_parse_python_class(self):
        """Test parsing a Python class."""
        parser = CodeParser()
        code = """class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
"""
        
        result = parser.parse(code, language="python")
        
        assert isinstance(result, ParsedCode)
        assert result.content == code
        assert result.metadata is not None
    
    def test_parse_empty_code_returns_valid_result(self):
        """Test that empty code can be parsed without errors."""
        parser = CodeParser()
        code = ""
        
        result = parser.parse(code, language="python")
        
        assert isinstance(result, ParsedCode)
        assert result.content == ""
        assert result.metadata.line_count == 0


class TestCodeMetadataExtraction:
    """Test metadata extraction from code."""
    
    def test_extract_line_count(self):
        """Test that line count is correctly calculated."""
        parser = CodeParser()
        code = """def func():
    pass
    pass
"""
        
        result = parser.parse(code, language="python")
        
        assert result.metadata.line_count == 3
    
    def test_extract_function_count(self):
        """Test that function count is correctly identified."""
        parser = CodeParser()
        code = """def func1():
    pass

def func2():
    pass

def func3():
    pass
"""
        
        result = parser.parse(code, language="python")
        
        assert result.metadata.function_count == 3
    
    def test_extract_class_count(self):
        """Test that class count is correctly identified."""
        parser = CodeParser()
        code = """class ClassA:
    pass

class ClassB:
    pass
"""
        
        result = parser.parse(code, language="python")
        
        assert result.metadata.class_count == 2
    
    def test_extract_comment_count(self):
        """Test that comments are counted."""
        parser = CodeParser()
        code = """# This is a comment
def func():
    # Another comment
    pass  # Inline comment
"""
        
        result = parser.parse(code, language="python")
        
        assert result.metadata.comment_count >= 3
    
    def test_extract_import_count(self):
        """Test that imports are counted."""
        parser = CodeParser()
        code = """import os
import sys
from pathlib import Path
"""
        
        result = parser.parse(code, language="python")
        
        assert result.metadata.import_count == 3
    
    def test_calculate_code_complexity_metric(self):
        """Test that basic complexity metric is calculated."""
        parser = CodeParser()
        code = """def complex_func(x):
    if x > 0:
        if x > 10:
            return "high"
        else:
            return "medium"
    else:
        return "low"
"""
        
        result = parser.parse(code, language="python")
        
        # Complexity should be > 1 due to nested conditions
        assert result.metadata.complexity > 1


class TestCodeParserFromFile:
    """Test parsing code from files."""
    
    def test_parse_from_file_path(self, tmp_path):
        """Test parsing code from a file path."""
        parser = CodeParser()
        
        # Create a temporary Python file
        test_file = tmp_path / "test_code.py"
        test_file.write_text("""def test():
    return True
""")
        
        result = parser.parse_file(test_file)
        
        assert isinstance(result, ParsedCode)
        assert result.language == "python"
        assert "def test():" in result.content
    
    def test_parse_file_detects_language_from_extension(self, tmp_path):
        """Test that language is auto-detected from file extension."""
        parser = CodeParser()
        
        test_file = tmp_path / "script.py"
        test_file.write_text("print('hello')")
        
        result = parser.parse_file(test_file)
        
        assert result.language == "python"
    
    def test_parse_file_with_path_string(self, tmp_path):
        """Test parsing with string path instead of Path object."""
        parser = CodeParser()
        
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")
        
        result = parser.parse_file(str(test_file))
        
        assert isinstance(result, ParsedCode)
        assert result.content == "x = 1"


class TestCodeParserErrorHandling:
    """Test error handling in code parser."""
    
    def test_parse_with_syntax_error_still_returns_result(self):
        """Test that syntax errors don't crash the parser."""
        parser = CodeParser()
        code = """def broken(
    # Missing closing parenthesis
    pass
"""
        
        result = parser.parse(code, language="python")
        
        assert isinstance(result, ParsedCode)
        assert result.has_syntax_errors is True
        assert len(result.syntax_errors) > 0
    
    def test_parse_file_not_found_raises_error(self):
        """Test that missing files raise appropriate error."""
        parser = CodeParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/file.py")
    
    def test_parse_unsupported_language_raises_error(self):
        """Test that unsupported languages raise appropriate error."""
        parser = CodeParser()
        code = "some code"
        
        with pytest.raises(ValueError, match="Unsupported language"):
            parser.parse(code, language="brainfuck")
    
    def test_parse_with_invalid_encoding_handles_gracefully(self, tmp_path):
        """Test that encoding issues are handled gracefully."""
        parser = CodeParser()
        
        # Create file with specific encoding
        test_file = tmp_path / "encoded.py"
        test_file.write_bytes(b"# \xff\xfe Invalid UTF-8")
        
        # Should handle encoding issues gracefully
        result = parser.parse_file(test_file, encoding="utf-8", errors="replace")
        
        assert isinstance(result, ParsedCode)


class TestCodeParserAdvancedFeatures:
    """Test advanced parsing features."""
    
    def test_parse_extracts_function_names(self):
        """Test that function names are extracted."""
        parser = CodeParser()
        code = """def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b
"""
        
        result = parser.parse(code, language="python")
        
        assert "calculate_sum" in result.metadata.function_names
        assert "calculate_product" in result.metadata.function_names
    
    def test_parse_extracts_class_names(self):
        """Test that class names are extracted."""
        parser = CodeParser()
        code = """class Calculator:
    pass

class Logger:
    pass
"""
        
        result = parser.parse(code, language="python")
        
        assert "Calculator" in result.metadata.class_names
        assert "Logger" in result.metadata.class_names
    
    def test_parse_identifies_docstrings(self):
        """Test that docstrings are identified."""
        parser = CodeParser()
        code = '''def documented():
    """This function has a docstring."""
    pass
'''
        
        result = parser.parse(code, language="python")
        
        assert result.metadata.has_docstrings is True
        assert result.metadata.docstring_count > 0
    
    def test_parse_calculates_code_to_comment_ratio(self):
        """Test that code-to-comment ratio is calculated."""
        parser = CodeParser()
        code = """# Comment 1
# Comment 2
def func():
    pass
"""
        
        result = parser.parse(code, language="python")
        
        # Should have a ratio since we have comments and code
        assert result.metadata.comment_ratio > 0
        assert result.metadata.comment_ratio <= 1


class TestCodeParserMultiLanguageSupport:
    """Test support for multiple programming languages."""
    
    def test_parse_javascript_code(self):
        """Test parsing JavaScript code."""
        parser = CodeParser()
        code = """function hello() {
    console.log("Hello");
}
"""
        
        result = parser.parse(code, language="javascript")
        
        assert isinstance(result, ParsedCode)
        assert result.language == "javascript"
    
    def test_parse_typescript_code(self):
        """Test parsing TypeScript code."""
        parser = CodeParser()
        code = """interface User {
    name: string;
    age: number;
}
"""
        
        result = parser.parse(code, language="typescript")
        
        assert isinstance(result, ParsedCode)
        assert result.language == "typescript"
    
    def test_supported_languages_list(self):
        """Test that parser provides list of supported languages."""
        parser = CodeParser()
        
        supported = parser.supported_languages()
        
        assert isinstance(supported, list)
        assert "python" in supported
        assert len(supported) > 0


class TestCodeParserPerformance:
    """Test parser performance characteristics."""
    
    def test_parse_large_file_within_reasonable_time(self):
        """Test that large files are parsed efficiently."""
        parser = CodeParser()
        
        # Generate a large code sample
        code = "\n".join([f"def func_{i}():\n    pass\n" for i in range(1000)])
        
        import time
        start = time.time()
        result = parser.parse(code, language="python")
        duration = time.time() - start
        
        assert isinstance(result, ParsedCode)
        assert duration < 5.0  # Should parse in under 5 seconds
    
    def test_parse_caches_results_for_identical_code(self):
        """Test that identical code parsing can use caching."""
        parser = CodeParser(config={"enable_cache": True})
        code = "def test(): pass"
        
        # Parse once
        result1 = parser.parse(code, language="python")
        
        # Parse again (should be faster if cached)
        result2 = parser.parse(code, language="python")
        
        assert result1.content == result2.content
        assert result1.metadata.line_count == result2.metadata.line_count


class TestCodeModelsValidation:
    """Test validation in code models."""
    
    def test_comment_ratio_validation(self):
        """Test that comment ratio is validated."""
        from pydantic import ValidationError
        
        # Valid ratios
        metadata = CodeMetadata(comment_ratio=0.5)
        assert metadata.comment_ratio == 0.5
        
        # Invalid ratios should fail
        with pytest.raises(ValidationError):
            CodeMetadata(comment_ratio=1.5)
        
        with pytest.raises(ValidationError):
            CodeMetadata(comment_ratio=-0.1)
    
    def test_parsed_code_language_lowercase(self):
        """Test that language is converted to lowercase."""
        metadata = CodeMetadata()
        parsed = ParsedCode(
            content="test",
            language="PYTHON",
            metadata=metadata
        )
        
        assert parsed.language == "python"
    
    def test_parsed_code_is_valid_method(self):
        """Test is_valid method."""
        metadata = CodeMetadata()
        
        # Valid code
        valid_code = ParsedCode(
            content="test",
            language="python",
            metadata=metadata,
            has_syntax_errors=False
        )
        assert valid_code.is_valid() is True
        
        # Invalid code
        invalid_code = ParsedCode(
            content="test",
            language="python",
            metadata=metadata,
            has_syntax_errors=True
        )
        assert invalid_code.is_valid() is False
    
    def test_parsed_code_get_summary(self):
        """Test get_summary method."""
        metadata = CodeMetadata(
            line_count=10,
            function_count=2,
            class_count=1,
            complexity=5.0
        )
        parsed = ParsedCode(
            content="test",
            language="python",
            metadata=metadata,
            has_syntax_errors=False
        )
        
        summary = parsed.get_summary()
        
        assert summary["language"] == "python"
        assert summary["lines"] == 10
        assert summary["functions"] == 2
        assert summary["classes"] == 1
        assert summary["complexity"] == 5.0
        assert summary["has_errors"] is False


class TestCodeParserEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_parse_file_with_jsx_extension(self, tmp_path):
        """Test parsing JSX file."""
        parser = CodeParser()
        test_file = tmp_path / "component.jsx"
        test_file.write_text("const Component = () => <div>Hello</div>;")
        
        result = parser.parse_file(test_file)
        
        assert result.language == "javascript"
    
    def test_parse_file_with_tsx_extension(self, tmp_path):
        """Test parsing TSX file."""
        parser = CodeParser()
        test_file = tmp_path / "component.tsx"
        test_file.write_text("const Component: React.FC = () => <div>Hello</div>;")
        
        result = parser.parse_file(test_file)
        
        assert result.language == "typescript"
    
    def test_parse_file_with_unknown_extension_defaults_to_python(self, tmp_path):
        """Test that unknown extensions default to python."""
        parser = CodeParser()
        test_file = tmp_path / "file.unknown"
        test_file.write_text("def test(): pass")
        
        result = parser.parse_file(test_file)
        
        assert result.language == "python"


class TestCodeMetadataValidation:
    """Test CodeMetadata model validation."""
    
    def test_comment_ratio_validation_rejects_values_above_1(self):
        """Test that comment_ratio > 1.0 is rejected."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError, match="comment_ratio"):
            CodeMetadata(comment_ratio=1.5)
    
    def test_comment_ratio_validation_rejects_negative_values(self):
        """Test that negative comment_ratio is rejected."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError, match="comment_ratio"):
            CodeMetadata(comment_ratio=-0.1)
    
    def test_comment_ratio_accepts_valid_values(self):
        """Test that valid comment_ratio values are accepted."""
        metadata = CodeMetadata(comment_ratio=0.5)
        assert metadata.comment_ratio == 0.5
        
        metadata = CodeMetadata(comment_ratio=0.0)
        assert metadata.comment_ratio == 0.0
        
        metadata = CodeMetadata(comment_ratio=1.0)
        assert metadata.comment_ratio == 1.0
    
    def test_comment_ratio_validator_method_directly(self):
        """Test the validator method directly to cover the ValueError path."""
        # This tests the actual validator logic beyond Pydantic's field constraints
        with pytest.raises(ValueError, match="between 0 and 1"):
            CodeMetadata.validate_comment_ratio(1.5)


class TestCodeParserEdgeCases:
    """Test edge cases and error handling in CodeParser."""
    
    def test_parse_python_class_with_docstring(self):
        """Test parsing Python class with docstring."""
        parser = CodeParser()
        code = '''class MyClass:
    """This is a class docstring."""
    def method(self):
        """Method docstring."""
        pass
'''
        
        result = parser.parse(code, language="python")
        
        assert result.metadata.class_count == 1
        assert result.metadata.docstring_count == 2
        assert result.metadata.has_docstrings is True
    
    def test_parse_python_with_boolean_operators(self):
        """Test parsing Python code with boolean operators (and/or)."""
        parser = CodeParser()
        code = '''def complex_check(a, b, c, d):
    if a and b or c and d:
        return True
    return False
'''
        
        result = parser.parse(code, language="python")
        
        # Should detect increased complexity due to boolean operators
        assert result.metadata.complexity > 1
    
    def test_parse_javascript_with_syntax_errors(self):
        """Test parsing JavaScript with syntax errors."""
        parser = CodeParser()
        code = "function test() { console.log('missing brace';"
        
        result = parser.parse(code, language="javascript")
        
        assert result.has_syntax_errors is True
        assert len(result.syntax_errors) > 0
    
    def test_parse_javascript_with_unmatched_parentheses(self):
        """Test parsing JavaScript with unmatched parentheses."""
        parser = CodeParser()
        code = "function test() { console.log('test'; }"
        
        result = parser.parse(code, language="javascript")
        
        assert result.has_syntax_errors is True
        assert "parentheses" in result.syntax_errors[0].lower()
    
    def test_parse_file_with_encoding_error_strict_mode(self, tmp_path):
        """Test parsing file with encoding error in strict mode."""
        parser = CodeParser()
        test_file = tmp_path / "bad_encoding.py"
        
        # Write file with latin-1 encoding
        test_file.write_bytes(b"# \xe9\xe8\xe7\n def test(): pass")
        
        # Should raise exception in strict mode
        with pytest.raises(UnicodeDecodeError):
            parser.parse_file(test_file, encoding="ascii", errors="strict")
    
    def test_parse_file_with_encoding_error_replace_mode(self, tmp_path):
        """Test parsing file with encoding error in replace mode."""
        parser = CodeParser()
        test_file = tmp_path / "bad_encoding.py"
        
        # Write file with latin-1 encoding
        test_file.write_bytes(b"# \xe9\xe8\xe7\ndef test(): pass")
        
        # Should handle gracefully with replace mode
        result = parser.parse_file(test_file, encoding="ascii", errors="replace")
        
        assert result is not None
        assert result.language == "python"
    
    def test_parse_file_no_extension_defaults_to_python(self, tmp_path):
        """Test that files without extension default to Python."""
        parser = CodeParser()
        test_file = tmp_path / "noextension"
        test_file.write_text("def test(): pass")
        
        result = parser.parse_file(test_file)
        
        # Should default to python when no extension match
        assert result.language == "python"
        assert result.file_path == str(test_file)
    
    def test_parse_file_encoding_error_fallback(self, tmp_path, monkeypatch):
        """Test that parse_file falls back to replace mode when first read fails."""
        from pathlib import Path
        from unittest.mock import Mock, MagicMock
        
        parser = CodeParser()
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        # Mock Path.read_text to raise UnicodeDecodeError on first call, succeed on second
        original_read_text = Path.read_text
        call_count = [0]
        
        def mock_read_text(self, encoding="utf-8", errors="strict"):
            call_count[0] += 1
            if call_count[0] == 1 and errors != "strict":
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "fake error")
            return "def test(): pass"
        
        monkeypatch.setattr(Path, "read_text", mock_read_text)
        
        # Call with errors="ignore" to trigger fallback
        result = parser.parse_file(test_file, encoding="utf-8", errors="ignore")
        
        assert result is not None
        assert result.language == "python"
        # Should have called read_text twice (first fail, then fallback)
        assert call_count[0] == 2
