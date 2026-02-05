"""Java parser using regex patterns."""

import os
import re
from typing import Dict, List, Any, Set

try:
    from .base_parser import BaseParser
except ImportError:
    from base_parser import BaseParser


class JavaParser(BaseParser):
    """Parser for Java files using regex patterns."""
    
    # Regex patterns for Java parsing
    METHOD_PATTERN = re.compile(
        r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?'
        r'(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\s*\{',
        re.MULTILINE
    )
    CLASS_PATTERN = re.compile(
        r'(?:public\s+)?(?:abstract\s+)?(?:final\s+)?class\s+(\w+)',
        re.MULTILINE
    )
    INTERFACE_PATTERN = re.compile(
        r'(?:public\s+)?interface\s+(\w+)',
        re.MULTILINE
    )
    IMPORT_PATTERN = re.compile(
        r'import\s+(?:static\s+)?([^;]+);',
        re.MULTILINE
    )
    TEST_ANNOTATION_PATTERN = re.compile(
        r'@Test\s+(?:public\s+)?(?:void\s+)?(\w+)\s*\(',
        re.MULTILINE
    )
    
    def extract_functions(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract method definitions from Java file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        functions = []
        
        # Extract methods
        for match in self.METHOD_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # Skip constructors (methods with same name as class)
            # This is a simplification; proper detection would need class context
            
            functions.append({
                'name': name,
                'line_number': line_num,
                'is_private': 'private' in match.group(0),
                'is_test': self._is_test_method(match.start(), content),
                'args': []
            })
        
        return functions
    
    def extract_classes(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract class and interface definitions from Java file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        classes = []
        
        # Extract classes
        for match in self.CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # Find class body to extract methods
            start = match.end()
            brace_count = 0
            class_end = start
            
            for i in range(start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_end = i
                        break
            
            class_body = content[start:class_end]
            methods = []
            
            for method_match in self.METHOD_PATTERN.finditer(class_body):
                method_name = method_match.group(1)
                methods.append(method_name)
            
            classes.append({
                'name': class_name,
                'line_number': line_num,
                'methods': methods,
                'bases': []  # Would need to parse extends/implements
            })
        
        # Extract interfaces
        for match in self.INTERFACE_PATTERN.finditer(content):
            interface_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            classes.append({
                'name': interface_name,
                'line_number': line_num,
                'methods': [],
                'bases': [],
                'is_interface': True
            })
        
        return classes
    
    def extract_imports(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract import statements from Java file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        imports = []
        
        for match in self.IMPORT_PATTERN.finditer(content):
            import_path = match.group(1).strip()
            is_static = 'static' in match.group(0)
            
            # Extract class name (last part of import)
            parts = import_path.split('.')
            name = parts[-1]
            module = '.'.join(parts[:-1]) if len(parts) > 1 else ''
            
            imports.append({
                'type': 'static_import' if is_static else 'import',
                'name': name,
                'module': module,
                'alias': None
            })
        
        return imports
    
    def extract_tested_functions(self, test_file: str) -> Set[str]:
        """Extract names of functions being tested from a Java test file."""
        if not os.path.exists(test_file):
            return set()
        
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tested = set()
        
        # Look for @Test annotated methods
        for match in self.TEST_ANNOTATION_PATTERN.finditer(content):
            test_method_name = match.group(1)
            # Common Java test naming: testFunctionName or shouldTestFunctionName
            if test_method_name.startswith('test'):
                # testCalculate -> calculate
                name = test_method_name[4:]
                if name:
                    tested.add(name[0].lower() + name[1:])
            elif test_method_name.startswith('should'):
                # shouldCalculate -> calculate
                name = test_method_name[6:]
                if name:
                    tested.add(name[0].lower() + name[1:])
        
        return tested
    
    def _is_test_method(self, position: int, content: str) -> bool:
        """Check if a method at given position has @Test annotation."""
        # Look backwards from position for @Test
        before = content[:position]
        lines_before = before.split('\n')
        
        # Check last few lines for @Test
        for line in reversed(lines_before[-5:]):
            if '@Test' in line:
                return True
        
        return False
    
    def calculate_complexity(self, filepath: str) -> Dict[str, Any]:
        """Calculate basic cyclomatic complexity for Java.
        
        Uses pattern matching to count decision points (if, for, while, case, catch, etc.)
        Cyclomatic complexity = 1 + number of decision points
        """
        if not os.path.exists(filepath):
            return {
                "cyclomatic_complexity": [],
                "complexity_hotspots": [],
                "maintainability_index": None,
                "summary": {}
            }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract functions with their content
        functions = self.extract_functions(filepath)
        complexity_data = {
            "cyclomatic_complexity": [],
            "complexity_hotspots": [],
            "maintainability_index": None,
            "summary": {}
        }
        
        lines = content.split('\n')
        total_complexity = 0
        
        for func in functions:
            # Find method body (simplified - get next 50 lines or until next method)
            start_line = func['line_number'] - 1
            end_line = min(start_line + 50, len(lines))
            
            # Look for next function to determine end
            for other_func in functions:
                if other_func['line_number'] > func['line_number']:
                    end_line = min(end_line, other_func['line_number'] - 1)
                    break
            
            func_body = '\n'.join(lines[start_line:end_line])
            
            # Count decision points
            complexity = 1  # Base complexity
            
            # Count control flow keywords
            decision_patterns = [
                r'\bif\s*\(',           # if statements
                r'\belse\s+if\b',       # else if
                r'\bfor\s*\(',          # for loops
                r'\bwhile\s*\(',        # while loops
                r'\bdo\s*\{',           # do-while
                r'\bcase\s+',           # switch cases
                r'\bcatch\s*\(',        # try-catch
                r'\&\&',                # logical AND
                r'\|\|',                # logical OR
                r'\?',                  # ternary operator
            ]
            
            for pattern in decision_patterns:
                complexity += len(re.findall(pattern, func_body))
            
            # Calculate rank (A-F based on complexity)
            rank = self._complexity_rank(complexity)
            
            cc_info = {
                "name": func['name'],
                "complexity": complexity,
                "rank": rank,
                "lineno": func['line_number'],
                "classname": None
            }
            
            complexity_data["cyclomatic_complexity"].append(cc_info)
            total_complexity += complexity
            
            # Mark as hotspot if complexity > 10
            if complexity > 10:
                complexity_data["complexity_hotspots"].append({
                    "name": func['name'],
                    "complexity": complexity,
                    "lineno": func['line_number'],
                    "severity": "high" if complexity > 15 else "medium"
                })
        
        complexity_data["summary"] = {
            "total_functions": len(functions),
            "total_complexity": total_complexity,
            "average_complexity": total_complexity / len(functions) if functions else 0,
            "hotspot_count": len(complexity_data["complexity_hotspots"])
        }
        
        return complexity_data
    
    def _complexity_rank(self, complexity: int) -> str:
        """Calculate complexity rank (A-F) based on complexity score."""
        if complexity <= 5:
            return 'A'
        elif complexity <= 10:
            return 'B'
        elif complexity <= 20:
            return 'C'
        elif complexity <= 30:
            return 'D'
        elif complexity <= 40:
            return 'E'
        else:
            return 'F'
