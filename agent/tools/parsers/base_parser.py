"""Abstract base class for language parsers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Set


class BaseParser(ABC):
    """Abstract base class defining the parser interface for code analysis."""
    
    @abstractmethod
    def extract_functions(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all function definitions from a file.
        
        Args:
            filepath: Path to source file
            
        Returns:
            List of function info dicts with keys:
                - name: Function name
                - line_number: Line number where function is defined
                - is_private: Boolean indicating if function is private
                - is_test: Boolean indicating if this is a test function
                - args: List of argument names (optional)
        """
        pass
    
    @abstractmethod
    def extract_classes(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all class definitions from a file.
        
        Args:
            filepath: Path to source file
            
        Returns:
            List of class info dicts with keys:
                - name: Class name
                - line_number: Line number where class is defined
                - methods: List of method names
                - bases: List of base class names (optional)
        """
        pass
    
    @abstractmethod
    def extract_imports(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all import statements from a file.
        
        Args:
            filepath: Path to source file
            
        Returns:
            List of import info dicts with keys:
                - type: Import type (e.g., 'import', 'from_import')
                - name: Imported name
                - module: Module name (for from imports)
                - alias: Import alias if any
        """
        pass
    
    def extract_tested_functions(self, test_file: str) -> Set[str]:
        """Extract names of functions being tested.
        
        This looks for patterns specific to each language's testing conventions.
        
        Args:
            test_file: Path to test file
            
        Returns:
            Set of tested function names
        """
        # Default implementation - can be overridden
        test_functions = self.extract_functions(test_file)
        tested = set()
        
        for test_func in test_functions:
            if test_func.get('is_test'):
                # Try to extract tested function name from test name
                name = self._extract_tested_name(test_func['name'])
                if name:
                    tested.add(name)
        
        return tested
    
    def calculate_complexity(self, filepath: str) -> Dict[str, Any]:
        """Calculate code complexity metrics.
        
        This is optional and may not be supported by all parsers.
        
        Args:
            filepath: Path to source file
            
        Returns:
            Dictionary containing complexity metrics, or empty dict if not supported
        """
        # Default implementation returns empty metrics
        return {
            "cyclomatic_complexity": [],
            "complexity_hotspots": [],
            "maintainability_index": None,
            "summary": {}
        }
    
    def _extract_tested_name(self, test_name: str) -> str:
        """Extract the tested function name from a test function name.
        
        This is a helper method that can be overridden by language-specific parsers.
        
        Args:
            test_name: Name of test function
            
        Returns:
            Name of tested function, or empty string if not extractable
        """
        # Common pattern: test_function_name -> function_name
        if test_name.startswith('test_'):
            return test_name[5:]  # Remove 'test_' prefix
        elif test_name.startswith('Test'):
            # TestFunctionName -> functionName
            name = test_name[4:]
            if name:
                return name[0].lower() + name[1:]
        return ""
