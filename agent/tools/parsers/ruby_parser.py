"""Ruby parser using regex-based parsing for code analysis."""

import os
import re
from typing import Dict, List, Any, Set

try:
    from .base_parser import BaseParser
except ImportError:
    from base_parser import BaseParser


class RubyParser(BaseParser):
    """Parser for Ruby source files using regex-based parsing."""
    
    def extract_functions(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all function (method) definitions from a Ruby file.
        
        In Ruby, methods can be defined with 'def' keyword.
        """
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        functions = []
        lines = content.split('\n')
        
        # Pattern for method definitions: def method_name(args)
        # Supports: def name, def name(), def name(arg1, arg2), def self.name
        method_pattern = re.compile(r'^\s*def\s+(self\.)?(\w+[\?!]?)(\(.*?\))?')
        
        for i, line in enumerate(lines, 1):
            match = method_pattern.match(line)
            if match:
                is_class_method = match.group(1) is not None
                method_name = match.group(2)
                args_str = match.group(3) or "()"
                
                # Extract argument names
                args = []
                if args_str and args_str != "()":
                    # Remove parentheses and split by comma
                    args_content = args_str.strip('()')
                    if args_content:
                        # Handle various Ruby argument patterns
                        for arg in args_content.split(','):
                            arg = arg.strip()
                            # Remove default values, splat operators, keyword args, etc.
                            arg = re.sub(r'[=:].*$', '', arg)
                            arg = arg.replace('*', '').replace('&', '').strip()
                            if arg:
                                args.append(arg)
                
                functions.append({
                    'name': method_name,
                    'line_number': i,
                    'is_private': method_name.startswith('_'),
                    'is_test': self._is_test_method(method_name),
                    'is_class_method': is_class_method,
                    'args': args
                })
        
        return functions
    
    def extract_classes(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all class definitions from a Ruby file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        classes = []
        lines = content.split('\n')
        
        # Pattern for class definitions: class ClassName, class ClassName < ParentClass
        class_pattern = re.compile(r'^\s*class\s+(\w+)(?:\s*<\s*(\S+))?')
        # Pattern for module definitions
        module_pattern = re.compile(r'^\s*module\s+(\w+)')
        
        current_class = None
        current_methods = []
        indent_stack = []
        
        for i, line in enumerate(lines, 1):
            # Track indentation to know when we exit a class
            stripped = line.lstrip()
            if stripped:
                current_indent = len(line) - len(stripped)
            else:
                continue
            
            # Check for class definition
            class_match = class_pattern.match(line)
            if class_match:
                # Save previous class if any
                if current_class:
                    classes.append({
                        'name': current_class['name'],
                        'line_number': current_class['line_number'],
                        'methods': current_methods,
                        'bases': current_class['bases']
                    })
                
                # Start new class
                current_class = {
                    'name': class_match.group(1),
                    'line_number': i,
                    'bases': [class_match.group(2)] if class_match.group(2) else []
                }
                current_methods = []
                indent_stack = [current_indent]
                continue
            
            # Check for module definition (treat similarly to classes)
            module_match = module_pattern.match(line)
            if module_match:
                if current_class:
                    classes.append({
                        'name': current_class['name'],
                        'line_number': current_class['line_number'],
                        'methods': current_methods,
                        'bases': current_class['bases']
                    })
                
                current_class = {
                    'name': module_match.group(1),
                    'line_number': i,
                    'bases': []
                }
                current_methods = []
                indent_stack = [current_indent]
                continue
            
            # Check for method definitions within class
            if current_class:
                method_match = re.match(r'^\s*def\s+(self\.)?(\w+[\?!]?)', line)
                if method_match:
                    method_name = method_match.group(2)
                    current_methods.append(method_name)
                
                # Check for 'end' keyword to close class
                if re.match(r'^\s*end\s*$', line):
                    if indent_stack and current_indent <= indent_stack[0]:
                        # This 'end' closes the current class
                        classes.append({
                            'name': current_class['name'],
                            'line_number': current_class['line_number'],
                            'methods': current_methods,
                            'bases': current_class['bases']
                        })
                        current_class = None
                        current_methods = []
                        indent_stack = []
        
        # Don't forget the last class if file doesn't end with 'end'
        if current_class:
            classes.append({
                'name': current_class['name'],
                'line_number': current_class['line_number'],
                'methods': current_methods,
                'bases': current_class['bases']
            })
        
        return classes
    
    def extract_imports(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all require/load statements from a Ruby file."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        imports = []
        lines = content.split('\n')
        
        # Patterns for various Ruby import styles
        # require 'module_name'
        # require_relative 'file_name'
        # load 'file_name.rb'
        # include ModuleName
        # extend ModuleName
        
        require_pattern = re.compile(r"^\s*require\s+['\"]([^'\"]+)['\"]")
        require_relative_pattern = re.compile(r"^\s*require_relative\s+['\"]([^'\"]+)['\"]")
        load_pattern = re.compile(r"^\s*load\s+['\"]([^'\"]+)['\"]")
        include_pattern = re.compile(r"^\s*include\s+(\w+(?:::\w+)*)")
        extend_pattern = re.compile(r"^\s*extend\s+(\w+(?:::\w+)*)")
        
        for line in lines:
            # Check require
            match = require_pattern.match(line)
            if match:
                imports.append({
                    'type': 'require',
                    'name': match.group(1),
                    'module': None,
                    'alias': None
                })
                continue
            
            # Check require_relative
            match = require_relative_pattern.match(line)
            if match:
                imports.append({
                    'type': 'require_relative',
                    'name': match.group(1),
                    'module': None,
                    'alias': None
                })
                continue
            
            # Check load
            match = load_pattern.match(line)
            if match:
                imports.append({
                    'type': 'load',
                    'name': match.group(1),
                    'module': None,
                    'alias': None
                })
                continue
            
            # Check include
            match = include_pattern.match(line)
            if match:
                imports.append({
                    'type': 'include',
                    'name': match.group(1),
                    'module': None,
                    'alias': None
                })
                continue
            
            # Check extend
            match = extend_pattern.match(line)
            if match:
                imports.append({
                    'type': 'extend',
                    'name': match.group(1),
                    'module': None,
                    'alias': None
                })
                continue
        
        return imports
    
    def extract_tested_functions(self, test_file: str) -> Set[str]:
        """Extract names of functions being tested from a Ruby test file.
        
        Ruby test frameworks (RSpec, Minitest) use different patterns:
        - RSpec: describe 'ClassName' do ... it 'does something' do
        - Minitest: def test_method_name
        """
        test_functions = self.extract_functions(test_file)
        tested = set()
        
        # Read file content for RSpec-style tests
        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract from RSpec describe blocks
            describe_pattern = re.compile(r"describe\s+['\"]?(\w+)['\"]?")
            for match in describe_pattern.finditer(content):
                tested.add(match.group(1))
            
            # Extract from context/it blocks that mention method names
            it_pattern = re.compile(r"it\s+['\"].*?(\w+).*?['\"]")
            for match in it_pattern.finditer(content):
                # This is a heuristic - may need refinement
                method_name = match.group(1)
                if not method_name.lower() in ['should', 'can', 'will', 'does', 'is', 'has']:
                    tested.add(method_name)
        
        # Extract from Minitest-style test methods
        for test_func in test_functions:
            if test_func['is_test']:
                # test_calculate_discount -> calculate_discount
                name = self._extract_tested_name(test_func['name'])
                if name:
                    tested.add(name)
        
        return tested
    
    def _is_test_method(self, method_name: str) -> bool:
        """Check if a method name indicates it's a test method."""
        # Minitest convention
        if method_name.startswith('test_'):
            return True
        # RSpec convention (though these are usually blocks, not methods)
        if method_name in ['it', 'describe', 'context', 'before', 'after']:
            return True
        return False
    
    def _extract_tested_name(self, test_name: str) -> str:
        """Extract the tested function name from a test function name."""
        # Minitest: test_method_name -> method_name
        if test_name.startswith('test_'):
            return test_name[5:]
        return ""
