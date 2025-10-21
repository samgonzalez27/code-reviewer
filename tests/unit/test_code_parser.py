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
