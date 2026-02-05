"""Language detection utility for code analysis tools."""

from pathlib import Path
from typing import Optional


# Map file extensions to language identifiers
EXTENSION_LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.go': 'go',
    '.c': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.rb': 'ruby',
    '.php': 'php',
    '.rs': 'rust',
    '.kt': 'kotlin',
    '.swift': 'swift',
}


def detect_language(filepath: str) -> Optional[str]:
    """Detect programming language from file extension.
    
    Args:
        filepath: Path to source file
        
    Returns:
        Language identifier (e.g., 'python', 'javascript') or None if unknown
    """
    ext = Path(filepath).suffix.lower()
    return EXTENSION_LANGUAGE_MAP.get(ext)


def get_parser(filepath: str):
    """Get appropriate parser for a file based on its language.
    
    Args:
        filepath: Path to source file
        
    Returns:
        Parser instance for the detected language
        
    Raises:
        ValueError: If language is not supported
    """
    language = detect_language(filepath)
    
    if language == 'python':
        try:
            from .python_parser import PythonParser
        except ImportError:
            from python_parser import PythonParser
        return PythonParser()
    elif language in ['javascript', 'typescript']:
        try:
            from .javascript_parser import JavaScriptParser
        except ImportError:
            from javascript_parser import JavaScriptParser
        return JavaScriptParser()
    elif language == 'java':
        try:
            from .java_parser import JavaParser
        except ImportError:
            from java_parser import JavaParser
        return JavaParser()
    elif language == 'go':
        try:
            from .go_parser import GoParser
        except ImportError:
            from go_parser import GoParser
        return GoParser()
    else:
        raise ValueError(
            f"Unsupported language: {language or 'unknown'} (file: {filepath}). "
            f"Supported languages: python, javascript, typescript, java, go"
        )
