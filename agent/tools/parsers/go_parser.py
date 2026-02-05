"""Go parser using regex patterns."""

import os
import re
from typing import Dict, List, Any, Set

try:
    from .base_parser import BaseParser
except ImportError:
    from base_parser import BaseParser


class GoParser(BaseParser):
    """Parser for Go files using regex patterns."""
    
    # Regex patterns for Go parsing
    FUNCTION_PATTERN = re.compile(
        r'^\s*func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(',
        re.MULTILINE
    )
    STRUCT_PATTERN = re.compile(
        r'type\s+(\w+)\s+struct\s*\{',
        re.MULTILINE
    )
    INTERFACE_PATTERN = re.compile(
        r'type\s+(\w+)\s+interface\s*\{',
        re.MULTILINE
    )
    IMPORT_PATTERN = re.compile(
        r'import\s+(?:\(\s*([^)]+)\s*\)|"([^"]+)")',
        re.MULTILINE | re.DOTALL
    )
    
    def extract_functions(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract function definitions from Go file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        functions = []
        
        for match in self.FUNCTION_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # In Go, lowercase = private, uppercase = public
            is_private = name[0].islower() if name else False
            is_test = name.startswith('Test')
            
            functions.append({
                'name': name,
                'line_number': line_num,
                'is_private': is_private,
                'is_test': is_test,
                'args': []
            })
        
        return functions
    
    def extract_classes(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract struct and interface definitions from Go file.
        
        Note: Go doesn't have classes, but structs and interfaces serve similar purposes.
        """
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        classes = []
        
        # Extract structs
        for match in self.STRUCT_PATTERN.finditer(content):
            struct_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # Find methods for this struct
            # Pattern: func (receiver StructName) MethodName(
            method_pattern = re.compile(
                rf'func\s+\([^)]*{struct_name}[^)]*\)\s+(\w+)\s*\(',
                re.MULTILINE
            )
            methods = [m.group(1) for m in method_pattern.finditer(content)]
            
            classes.append({
                'name': struct_name,
                'line_number': line_num,
                'methods': methods,
                'bases': [],
                'type': 'struct'
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
                'type': 'interface'
            })
        
        return classes
    
    def extract_imports(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract import statements from Go file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        imports = []
        
        for match in self.IMPORT_PATTERN.finditer(content):
            multi_import = match.group(1)
            single_import = match.group(2)
            
            if single_import:
                # Single import: import "fmt"
                imports.append({
                    'type': 'import',
                    'name': single_import.split('/')[-1],
                    'module': single_import,
                    'alias': None
                })
            elif multi_import:
                # Multi-line import block
                for line in multi_import.split('\n'):
                    line = line.strip()
                    if line and '"' in line:
                        # Handle aliased imports: alias "package"
                        parts = line.split('"')
                        if len(parts) >= 2:
                            package = parts[1]
                            alias = parts[0].strip() if parts[0].strip() else None
                            imports.append({
                                'type': 'import',
                                'name': package.split('/')[-1],
                                'module': package,
                                'alias': alias
                            })
        
        return imports
    
    def extract_tested_functions(self, test_file: str) -> Set[str]:
        """Extract names of functions being tested from a Go test file.
        
        Go test convention: TestFunctionName tests FunctionName
        """
        if not os.path.exists(test_file):
            return set()
        
        test_functions = self.extract_functions(test_file)
        tested = set()
        
        for test_func in test_functions:
            if test_func['is_test']:
                # TestCalculate -> Calculate (Go convention)
                name = test_func['name'][4:]  # Remove 'Test' prefix
                if name:
                    tested.add(name)
                    # Also add lowercase version for private functions
                    tested.add(name[0].lower() + name[1:])
        
        return tested
    
    def calculate_complexity(self, filepath: str) -> Dict[str, Any]:
        """Calculate basic cyclomatic complexity for Go.
        
        Uses pattern matching to count decision points (if, for, switch, select, etc.)
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
            
            # Count control flow keywords (Go-specific)
            decision_patterns = [
                r'\bif\s+',             # if statements
                r'\belse\s+if\b',       # else if
                r'\bfor\s+',            # for loops (Go's only loop)
                r'\bcase\s+',           # switch/select cases
                r'\&\&',                # logical AND
                r'\|\|',                # logical OR
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
