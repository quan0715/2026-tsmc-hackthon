"""JavaScript/TypeScript parser using regex patterns."""

import os
import re
from typing import Dict, List, Any, Set

try:
    from .base_parser import BaseParser
except ImportError:
    from base_parser import BaseParser


class JavaScriptParser(BaseParser):
    """Parser for JavaScript and TypeScript files using regex patterns."""
    
    # Regex patterns for JS/TS parsing
    FUNCTION_PATTERN = re.compile(
        r'(?:^|\s)(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(',
        re.MULTILINE
    )
    ARROW_FUNCTION_PATTERN = re.compile(
        r'(?:^|\s)(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
        re.MULTILINE
    )
    METHOD_PATTERN = re.compile(
        r'^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{',
        re.MULTILINE
    )
    CLASS_PATTERN = re.compile(
        r'(?:^|\s)(?:export\s+)?class\s+(\w+)',
        re.MULTILINE
    )
    IMPORT_PATTERN = re.compile(
        r'import\s+(?:{([^}]+)}|(\*\s+as\s+\w+)|(\w+))\s+from\s+[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )
    TEST_PATTERNS = [
        re.compile(r'(?:test|it)\s*\(\s*[\'"](.+?)[\'"]'),
        re.compile(r'describe\s*\(\s*[\'"](.+?)[\'"]'),
    ]
    
    def extract_functions(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract function definitions from JavaScript/TypeScript file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        functions = []
        lines = content.split('\n')
        
        # Extract regular functions
        for match in self.FUNCTION_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            functions.append({
                'name': name,
                'line_number': line_num,
                'is_private': name.startswith('_'),
                'is_test': self._is_test_function(name),
                'args': []  # Could extract args from match if needed
            })
        
        # Extract arrow functions
        for match in self.ARROW_FUNCTION_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            functions.append({
                'name': name,
                'line_number': line_num,
                'is_private': name.startswith('_'),
                'is_test': self._is_test_function(name),
                'args': []
            })
        
        return functions
    
    def extract_classes(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract class definitions from JavaScript/TypeScript file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        classes = []
        
        for match in self.CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # Find class body to extract methods
            # Simple heuristic: find matching braces
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
                # Filter out keywords
                if method_name not in ['if', 'for', 'while', 'switch', 'catch']:
                    methods.append(method_name)
            
            classes.append({
                'name': class_name,
                'line_number': line_num,
                'methods': methods,
                'bases': []  # JS doesn't have explicit multiple inheritance
            })
        
        return classes
    
    def extract_imports(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract import statements from JavaScript/TypeScript file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        imports = []
        
        for match in self.IMPORT_PATTERN.finditer(content):
            named = match.group(1)
            star = match.group(2)
            default = match.group(3)
            module = match.group(4)
            
            if named:
                # Named imports: import { foo, bar } from 'module'
                names = [n.strip() for n in named.split(',')]
                for name in names:
                    imports.append({
                        'type': 'named_import',
                        'name': name,
                        'module': module,
                        'alias': None
                    })
            elif star:
                # Namespace import: import * as foo from 'module'
                imports.append({
                    'type': 'namespace_import',
                    'name': star.strip(),
                    'module': module,
                    'alias': None
                })
            elif default:
                # Default import: import foo from 'module'
                imports.append({
                    'type': 'default_import',
                    'name': default,
                    'module': module,
                    'alias': None
                })
        
        return imports
    
    def extract_tested_functions(self, test_file: str) -> Set[str]:
        """Extract names of functions being tested from a JS/TS test file."""
        if not os.path.exists(test_file):
            return set()
        
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tested = set()
        
        # Look for test('should test functionName', ...) patterns
        for pattern in self.TEST_PATTERNS:
            for match in pattern.finditer(content):
                test_description = match.group(1)
                # Try to extract function name from description
                # Common patterns: "should test foo", "tests bar", "foo works"
                words = test_description.lower().split()
                for i, word in enumerate(words):
                    if word in ['test', 'tests', 'should'] and i + 1 < len(words):
                        potential_name = words[i + 1]
                        # Convert to camelCase if needed
                        tested.add(potential_name)
        
        return tested
    
    def _is_test_function(self, name: str) -> bool:
        """Check if a function name indicates it's a test."""
        return name.startswith('test') or name.endswith('Test')
    
    def calculate_complexity(self, filepath: str) -> Dict[str, Any]:
        """Calculate basic cyclomatic complexity for JavaScript/TypeScript.
        
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
            # Find function body (simplified - get next 50 lines or until next function)
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
