"""
Code Parser Service.

This service is responsible for parsing source code files,
extracting metadata, and preparing code for review analysis.

This follows the Single Responsibility Principle (SOLID) - 
the parser only handles code parsing and metadata extraction.

Design Patterns Used:
- Strategy Pattern: Language-specific parsers
- Template Method: Common parsing workflow
"""
import ast
import re
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from src.models.code_models import ParsedCode, CodeMetadata


# Strategy Pattern: Abstract base for language-specific parsers
class LanguageParser(ABC):
    """Abstract base class for language-specific parsers (Strategy Pattern)."""
    
    @abstractmethod
    def parse(self, code: str) -> CodeMetadata:
        """Parse code and extract metadata."""
    
    @abstractmethod
    def check_syntax(self, code: str) -> tuple[bool, List[str]]:
        """Check for syntax errors. Returns (has_errors, error_list)."""


class PythonParser(LanguageParser):
    """Parser for Python code using AST."""
    
    def parse(self, code: str) -> CodeMetadata:
        """Parse Python code and extract metadata."""
        # Handle empty code
        if not code:
            return CodeMetadata(
                line_count=0,
                blank_line_count=0,
                code_line_count=0,
            )
        
        # Split lines, but handle trailing newline properly
        lines = code.split('\n')
        # Remove last empty line if code ends with newline
        if lines and lines[-1] == '':
            lines = lines[:-1]
        
        total_lines = len(lines)
        
        # Count different types of lines
        comment_count = 0
        blank_lines = 0
        code_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#'):
                comment_count += 1
            else:
                code_lines += 1
                # Count inline comments
                if '#' in line:
                    comment_count += 1
        
        # Parse AST for structural information
        function_names = []
        class_names = []
        import_count = 0
        docstring_count = 0
        complexity = 1.0
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Count functions
                if isinstance(node, ast.FunctionDef):
                    function_names.append(node.name)
                    # Calculate complexity (count decision points)
                    complexity += self._calculate_complexity(node)
                    # Check for docstring
                    if ast.get_docstring(node):
                        docstring_count += 1
                
                # Count classes
                elif isinstance(node, ast.ClassDef):
                    class_names.append(node.name)
                    if ast.get_docstring(node):
                        docstring_count += 1
                
                # Count imports
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_count += 1
        
        except SyntaxError:
            # If syntax error, we'll still return what we can count
            pass
        
        # Calculate comment ratio
        comment_ratio = comment_count / total_lines if total_lines > 0 else 0.0
        
        return CodeMetadata(
            line_count=total_lines,
            function_count=len(function_names),
            class_count=len(class_names),
            comment_count=comment_count,
            import_count=import_count,
            complexity=complexity,
            function_names=function_names,
            class_names=class_names,
            has_docstrings=docstring_count > 0,
            docstring_count=docstring_count,
            comment_ratio=comment_ratio,
            blank_line_count=blank_lines,
            code_line_count=code_lines,
        )
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> float:
        """Calculate cyclomatic complexity for a function."""
        complexity = 0
        for child in ast.walk(node):
            # Count decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def check_syntax(self, code: str) -> tuple[bool, List[str]]:
        """Check Python code for syntax errors."""
        try:
            ast.parse(code)
            return (False, [])
        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            return (True, [error_msg])


class JavaScriptParser(LanguageParser):
    """Basic parser for JavaScript code (regex-based)."""
    
    def parse(self, code: str) -> CodeMetadata:
        """Parse JavaScript code using regex patterns."""
        lines = code.split('\n')
        total_lines = len(lines)
        
        # Count comments
        single_line_comments = len(re.findall(r'//.*', code))
        multi_line_comments = len(re.findall(r'/\*.*?\*/', code, re.DOTALL))
        comment_count = single_line_comments + multi_line_comments
        
        # Count functions (basic regex)
        function_pattern = r'function\s+(\w+)\s*\('
        arrow_function_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>'
        function_matches = re.findall(function_pattern, code)
        arrow_matches = re.findall(arrow_function_pattern, code)
        function_names = function_matches + arrow_matches
        
        # Count classes
        class_pattern = r'class\s+(\w+)'
        class_names = re.findall(class_pattern, code)
        
        # Count imports
        import_pattern = r'(?:import|require)\s'
        import_count = len(re.findall(import_pattern, code))
        
        # Calculate lines
        blank_lines = sum(1 for line in lines if not line.strip())
        code_lines = total_lines - blank_lines
        
        comment_ratio = comment_count / total_lines if total_lines > 0 else 0.0
        
        return CodeMetadata(
            line_count=total_lines,
            function_count=len(function_names),
            class_count=len(class_names),
            comment_count=comment_count,
            import_count=import_count,
            complexity=1.0,  # Basic complexity for now
            function_names=function_names,
            class_names=class_names,
            has_docstrings=False,
            docstring_count=0,
            comment_ratio=comment_ratio,
            blank_line_count=blank_lines,
            code_line_count=code_lines,
        )
    
    def check_syntax(self, code: str) -> tuple[bool, List[str]]:
        """Basic syntax check for JavaScript (no native parser)."""
        # Simple checks for common syntax errors
        errors = []
        
        # Check for unmatched braces
        if code.count('{') != code.count('}'):
            errors.append("Unmatched braces")
        
        if code.count('(') != code.count(')'):
            errors.append("Unmatched parentheses")
        
        return (len(errors) > 0, errors)


class TypeScriptParser(JavaScriptParser):
    """Parser for TypeScript (extends JavaScript parser)."""
    
    def parse(self, code: str) -> CodeMetadata:
        """Parse TypeScript code (similar to JavaScript)."""
        metadata = super().parse(code)
        
        # Add TypeScript-specific parsing
        interface_pattern = r'interface\s+(\w+)'
        type_pattern = r'type\s+(\w+)'
        interfaces = re.findall(interface_pattern, code)
        types = re.findall(type_pattern, code)
        
        # Add interfaces and types to class count
        metadata.class_count += len(interfaces) + len(types)
        metadata.class_names.extend(interfaces + types)
        
        return metadata


class CodeParser:
    """
    Parses source code and extracts metadata for analysis.
    
    This class uses the Strategy Pattern to delegate parsing to
    language-specific parsers, following the Open/Closed Principle.
    
    Usage:
        parser = CodeParser()
        result = parser.parse(code_string, language="python")
        print(result.metadata.function_count)
    """
    
    # Language parsers registry (Open/Closed Principle)
    _PARSERS: Dict[str, LanguageParser] = {
        'python': PythonParser(),
        'javascript': JavaScriptParser(),
        'typescript': TypeScriptParser(),
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CodeParser.
        
        Args:
            config: Optional configuration dictionary with parser settings
        """
        self.config = config or {}
        self._cache = {} if self.config.get("enable_cache", False) else None
    
    def parse(self, code: str, language: str) -> ParsedCode:
        """
        Parse source code and extract metadata.
        
        Args:
            code: The source code as a string
            language: The programming language (e.g., 'python', 'javascript')
        
        Returns:
            ParsedCode: Parsed code with metadata
        
        Raises:
            ValueError: If the language is not supported
        """
        # Validate language
        language = language.lower()
        if language not in self._PARSERS:
            raise ValueError(f"Unsupported language: {language}")
        
        # Check cache
        if self._cache is not None:
            cache_key = f"{language}:{hash(code)}"
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        # Get language-specific parser (Strategy Pattern)
        parser = self._PARSERS[language]
        
        # Check syntax
        has_syntax_errors, syntax_errors = parser.check_syntax(code)
        
        # Extract metadata
        metadata = parser.parse(code)
        
        # Create ParsedCode object
        result = ParsedCode(
            content=code,
            language=language,
            metadata=metadata,
            has_syntax_errors=has_syntax_errors,
            syntax_errors=syntax_errors,
            parse_timestamp=datetime.now().isoformat(),
        )
        
        # Cache result
        if self._cache is not None:
            self._cache[cache_key] = result
        
        return result
    
    def parse_file(
        self, 
        file_path: Union[str, Path],
        encoding: str = "utf-8",
        errors: str = "strict"
    ) -> ParsedCode:
        """
        Parse source code from a file.
        
        Args:
            file_path: Path to the source code file
            encoding: Character encoding of the file
            errors: How to handle encoding errors ('strict', 'replace', 'ignore')
        
        Returns:
            ParsedCode: Parsed code with metadata
        
        Raises:
            FileNotFoundError: If the file does not exist
        """
        # Convert to Path object
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect language from extension
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
        }
        
        language = extension_map.get(path.suffix.lower())
        if not language:
            # Default to python if unknown
            language = 'python'
        
        # Read file content
        try:
            content = path.read_text(encoding=encoding, errors=errors)
        except UnicodeDecodeError:
            # Handle encoding errors based on errors parameter
            if errors == "strict":
                raise
            content = path.read_text(encoding=encoding, errors="replace")
        
        # Parse the code
        result = self.parse(content, language)
        
        # Add file path to result
        result.file_path = str(path)
        result.encoding = encoding
        
        return result
    
    def supported_languages(self) -> List[str]:
        """
        Get list of supported programming languages.
        
        Returns:
            list: List of supported language identifiers
        """
        return list(self._PARSERS.keys())
