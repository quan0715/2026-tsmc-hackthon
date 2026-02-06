"""C parser using regex-based parsing for code analysis."""

import os
import re
from typing import Dict, List, Any, Set

try:
    from .base_parser import BaseParser
except ImportError:
    from base_parser import BaseParser


class CParser(BaseParser):
    """Parser for C source files using regex-based parsing."""
    
    def extract_functions(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all function definitions from a C file.
        
        Matches patterns like:
        - int main(int argc, char **argv)
        - void calculate_discount(float price, float *result)
        - static int helper_function(void)
        """
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove comments to avoid false matches
        content = self._remove_comments(content)
        
        functions = []
        
        # Pattern for C function definitions
        # Matches: [static] [inline] return_type function_name(params) {
        # This is a simplified pattern and may not catch all edge cases
        function_pattern = re.compile(
            r'^\s*(?:static\s+)?(?:inline\s+)?'  # Optional static/inline
            r'(?:const\s+)?'  # Optional const
            r'(\w+(?:\s*\*+)?)\s+'  # Return type (with optional pointers)
            r'(\w+)\s*'  # Function name
            r'\(([^)]*)\)\s*'  # Parameters
            r'(?:\{|;)',  # Opening brace or semicolon (for declarations)
            re.MULTILINE
        )
        
        lines = content.split('\n')
        line_positions = {}
        current_pos = 0
        for i, line in enumerate(lines, 1):
            line_positions[current_pos] = i
            current_pos += len(line) + 1  # +1 for newline
        
        for match in function_pattern.finditer(content):
            return_type = match.group(1).strip()
            function_name = match.group(2)
            params_str = match.group(3).strip()
            
            # Skip common false positives
            if function_name in ['if', 'while', 'for', 'switch', 'return']:
                continue
            
            # Find line number
            match_pos = match.start()
            line_number = 1
            for pos, line_num in sorted(line_positions.items()):
                if pos <= match_pos:
                    line_number = line_num
                else:
                    break
            
            # Extract parameter names
            args = []
            if params_str and params_str != 'void':
                # Split by comma, but be careful with function pointers
                params = self._split_params(params_str)
                for param in params:
                    param = param.strip()
                    if param and param != 'void':
                        # Extract parameter name (last word, ignoring pointers)
                        # e.g., "int *count" -> "count", "char **argv" -> "argv"
                        param_name = re.sub(r'.*\s+(\**)(\w+)$', r'\2', param)
                        if param_name:
                            args.append(param_name)
            
            # Determine if function is private (static in C)
            is_private = 'static' in match.group(0)
            
            # Check if it's a test function (common naming conventions)
            is_test = self._is_test_function(function_name)
            
            functions.append({
                'name': function_name,
                'line_number': line_number,
                'is_private': is_private,
                'is_test': is_test,
                'return_type': return_type,
                'args': args
            })
        
        return functions
    
    def extract_classes(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract struct definitions from a C file.
        
        C doesn't have classes, but structs are the closest equivalent.
        """
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove comments
        content = self._remove_comments(content)
        
        structs = []
        
        # Pattern for struct definitions
        # Matches: struct StructName { ... };
        # Also: typedef struct { ... } StructName;
        struct_pattern = re.compile(
            r'(?:typedef\s+)?struct\s+(\w+)?\s*\{([^}]*)\}(?:\s*(\w+))?\s*;',
            re.MULTILINE | re.DOTALL
        )
        
        lines = content.split('\n')
        line_positions = {}
        current_pos = 0
        for i, line in enumerate(lines, 1):
            line_positions[current_pos] = i
            current_pos += len(line) + 1
        
        for match in struct_pattern.finditer(content):
            struct_name = match.group(1) or match.group(3)
            if not struct_name:
                continue
            
            struct_body = match.group(2)
            
            # Find line number
            match_pos = match.start()
            line_number = 1
            for pos, line_num in sorted(line_positions.items()):
                if pos <= match_pos:
                    line_number = line_num
                else:
                    break
            
            # Extract member variables (fields)
            members = []
            for line in struct_body.split(';'):
                line = line.strip()
                if line:
                    # Extract member name (last word)
                    member_match = re.search(r'\b(\w+)\s*$', line)
                    if member_match:
                        members.append(member_match.group(1))
            
            structs.append({
                'name': struct_name,
                'line_number': line_number,
                'methods': [],  # C structs don't have methods
                'members': members,
                'bases': []  # C structs don't have inheritance
            })
        
        return structs
    
    def extract_imports(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract #include directives from a C file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        imports = []
        
        # Pattern for #include directives
        # Matches: #include <stdio.h> or #include "myheader.h"
        include_pattern = re.compile(r'^\s*#\s*include\s+[<"]([^>"]+)[>"]', re.MULTILINE)
        
        for match in include_pattern.finditer(content):
            header_name = match.group(1)
            
            # Determine if it's a system header (<>) or local header ("")
            is_system = '<' in match.group(0)
            
            imports.append({
                'type': 'include_system' if is_system else 'include_local',
                'name': header_name,
                'module': None,
                'alias': None
            })
        
        return imports
    
    def extract_tested_functions(self, test_file: str) -> Set[str]:
        """Extract names of functions being tested from a C test file.
        
        Common C test frameworks: Unity, CUnit, Check, etc.
        Test functions often follow patterns like:
        - test_function_name()
        - TEST(suite, test_name)
        """
        test_functions = self.extract_functions(test_file)
        tested = set()
        
        # Read file content for framework-specific patterns
        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Unity framework: TEST_CASE or TEST
            test_macro_pattern = re.compile(r'TEST(?:_CASE)?\s*\(\s*\w+\s*,\s*(\w+)\s*\)')
            for match in test_macro_pattern.finditer(content):
                test_name = match.group(1)
                # Extract tested function name
                name = self._extract_tested_name(test_name)
                if name:
                    tested.add(name)
        
        # Extract from test function names
        for test_func in test_functions:
            if test_func['is_test']:
                name = self._extract_tested_name(test_func['name'])
                if name:
                    tested.add(name)
        
        return tested
    
    def _is_test_function(self, function_name: str) -> bool:
        """Check if a function name indicates it's a test function."""
        test_prefixes = ['test_', 'Test', 'TEST_']
        test_suffixes = ['_test', '_Test', '_TEST']
        
        for prefix in test_prefixes:
            if function_name.startswith(prefix):
                return True
        
        for suffix in test_suffixes:
            if function_name.endswith(suffix):
                return True
        
        return False
    
    def _extract_tested_name(self, test_name: str) -> str:
        """Extract the tested function name from a test function name."""
        # test_calculate_discount -> calculate_discount
        if test_name.startswith('test_'):
            return test_name[5:]
        elif test_name.startswith('Test'):
            name = test_name[4:]
            if name:
                return name[0].lower() + name[1:]
        elif test_name.endswith('_test'):
            return test_name[:-5]
        elif test_name.endswith('Test'):
            return test_name[:-4]
        return ""
    
    def _remove_comments(self, content: str) -> str:
        """Remove C-style comments from source code."""
        # Remove multi-line comments /* ... */
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Remove single-line comments // ...
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        return content
    
    def _split_params(self, params_str: str) -> List[str]:
        """Split parameter string by comma, handling function pointers.
        
        This is a simplified version that handles basic cases.
        """
        params = []
        current_param = ""
        paren_depth = 0
        
        for char in params_str:
            if char == '(':
                paren_depth += 1
                current_param += char
            elif char == ')':
                paren_depth -= 1
                current_param += char
            elif char == ',' and paren_depth == 0:
                params.append(current_param.strip())
                current_param = ""
            else:
                current_param += char
        
        if current_param.strip():
            params.append(current_param.strip())
        
        return params
