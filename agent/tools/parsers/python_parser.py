"""Python parser using AST for accurate code analysis."""

import ast
import os
from typing import Dict, List, Any, Set

try:
    from .base_parser import BaseParser
except ImportError:
    from base_parser import BaseParser

# Optional: radon for complexity metrics
try:
    from radon.complexity import cc_visit, cc_rank
    from radon.metrics import mi_visit, mi_rank
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False


class PythonParser(BaseParser):
    """Parser for Python source files using the ast module."""
    
    def extract_functions(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all function definitions from a Python file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=filepath)
            except SyntaxError:
                return []
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line_number': node.lineno,
                    'is_private': node.name.startswith('_'),
                    'is_test': node.name.startswith('test_'),
                    'args': [arg.arg for arg in node.args.args]
                })
        
        return functions
    
    def extract_classes(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all class definitions from a Python file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=filepath)
            except SyntaxError:
                return []
        
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                
                classes.append({
                    'name': node.name,
                    'line_number': node.lineno,
                    'methods': methods,
                    'bases': [self._get_name(base) for base in node.bases]
                })
        
        return classes
    
    def extract_imports(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all import statements from a Python file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=filepath)
            except SyntaxError:
                return []
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'name': alias.name,
                        'module': None,
                        'alias': alias.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        'type': 'from_import',
                        'module': module,
                        'name': alias.name,
                        'alias': alias.asname
                    })
        
        return imports
    
    def extract_tested_functions(self, test_file: str) -> Set[str]:
        """Extract names of functions being tested from a Python test file."""
        test_functions = self.extract_functions(test_file)
        tested = set()
        
        for test_func in test_functions:
            if test_func['is_test']:
                # test_calculate_discount -> calculate_discount
                name = test_func['name'][5:]  # Remove 'test_' prefix
                tested.add(name)
        
        return tested
    
    def calculate_complexity(self, filepath: str) -> Dict[str, Any]:
        """Calculate code complexity metrics using radon."""
        if not RADON_AVAILABLE:
            return super().calculate_complexity(filepath)
        
        if not os.path.exists(filepath):
            return super().calculate_complexity(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        try:
            # Cyclomatic complexity
            cc_results = cc_visit(source_code)
            
            # Maintainability index
            mi_score = mi_visit(source_code, multi=True)
            
            complexity_data = {
                "cyclomatic_complexity": [],
                "complexity_hotspots": [],
                "maintainability_index": mi_score,
                "maintainability_rank": mi_rank(mi_score),
                "summary": {}
            }
            
            total_complexity = 0
            for result in cc_results:
                cc_info = {
                    "name": result.name,
                    "complexity": result.complexity,
                    "rank": cc_rank(result.complexity),
                    "lineno": result.lineno,
                    "classname": result.classname if hasattr(result, 'classname') else None
                }
                complexity_data["cyclomatic_complexity"].append(cc_info)
                total_complexity += result.complexity
                
                # Mark as hotspot if complexity > 10
                if result.complexity > 10:
                    complexity_data["complexity_hotspots"].append({
                        "name": result.name,
                        "complexity": result.complexity,
                        "lineno": result.lineno,
                        "severity": "high" if result.complexity > 15 else "medium"
                    })
            
            complexity_data["summary"] = {
                "total_functions": len(cc_results),
                "total_complexity": total_complexity,
                "average_complexity": total_complexity / len(cc_results) if cc_results else 0,
                "hotspot_count": len(complexity_data["complexity_hotspots"])
            }
            
            return complexity_data
            
        except Exception as e:
            return {
                "error": f"Error calculating complexity: {e}",
                "cyclomatic_complexity": [],
                "complexity_hotspots": [],
                "maintainability_index": 0,
                "summary": {}
            }
    
    def _get_name(self, node):
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
