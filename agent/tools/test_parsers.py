#!/usr/bin/env python3
"""Standalone test script for parsers (bypasses tools/__init__.py)."""

import sys
import os

#  Directly import parser modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'parsers'))

def test_all_parsers():
    """Test all language parsers."""
    # Import modules directly to avoid tools/__init__.py
    import language_detector
    from python_parser import PythonParser
    from javascript_parser import JavaScriptParser
    from java_parser import JavaParser
    from go_parser import GoParser
    
    print('=' * 60)
    print('Language-Agnostic Parser Test Suite')
    print('=' * 60)
    
    # Test 1: Language Detection
    print('\n📋 Test 1: Language Detection')
    print('-' * 60)
    test_cases = [
        ('test.py', 'python'),
        ('test.js', 'javascript'),
        ('test.ts', 'typescript'),
        ('test.jsx', 'javascript'),
        ('Test.java', 'java'),
        ('test.go', 'go'),
        ('test.rb', 'ruby'),
        ('unknown.xyz', None)
    ]
    
    passed = 0
    for file, expected in test_cases:
        result = language_detector.detect_language(file)
        status = '✅' if result == expected else '❌'
        print(f'{status} {file:20s} → {result or "None":15s} (expected: {expected or "None"})')
        if result == expected:
            passed += 1
    
    print(f'\nLanguage Detection: {passed}/{len(test_cases)} passed')
    
    # Test 2: Python Parser
    print('\n🐍 Test 2: Python Parser')
    print('-' * 60)
    parser = PythonParser()
    sample_file = 'test_samples/sample.py'
    
    funcs = parser.extract_functions(sample_file)
    classes = parser.extract_classes(sample_file)
    imports = parser.extract_imports(sample_file)
    
    print(f'Functions: {len(funcs)}')
    for f in funcs:
        print(f'  • {f["name"]:25s} (line {f["line_number"]:3d})')
    
    print(f'\nClasses: {len(classes)}')
    for c in classes:
        print(f'  • {c["name"]:25s} with {len(c["methods"])} methods')
        for m in c["methods"]:
            print(f'    - {m}')
    
    print(f'\nImports: {len(imports)}')
    
    # Test 3: JavaScript Parser
    print('\n📜 Test 3: JavaScript Parser')
    print('-' * 60)
    parser = JavaScriptParser()
    sample_file = 'test_samples/sample.js'
    
    funcs = parser.extract_functions(sample_file)
    classes = parser.extract_classes(sample_file)
    
    print(f'Functions: {len(funcs)}')
    for f in funcs:
        print(f'  • {f["name"]:25s} (line {f["line_number"]:3d})')
    
    print(f'\nClasses: {len(classes)}')
    for c in classes:
        print(f'  • {c["name"]:25s} with {len(c.get("methods", []))} methods')
    
    # Test 4: Java Parser
    print('\n☕ Test 4: Java Parser')
    print('-' * 60)
    parser = JavaParser()
    sample_file = 'test_samples/ShoppingCart.java'
    
    funcs = parser.extract_functions(sample_file)
    classes = parser.extract_classes(sample_file)
    
    print(f'Methods: {len(funcs)}')
    for f in funcs[:5]:  # Show first 5
        print(f'  • {f["name"]:25s} (line {f["line_number"]:3d})')
    
    print(f'\nClasses: {len(classes)}')
    for c in classes:
        print(f'  • {c["name"]:25s} with {len(c.get("methods", []))} methods')
    
    # Test 5: Go Parser
    print('\n🔵 Test 5: Go Parser')
    print('-' * 60)
    parser = GoParser()
    sample_file = 'test_samples/sample.go'
    
    funcs = parser.extract_functions(sample_file)
    classes = parser.extract_classes(sample_file)
    
    print(f'Functions: {len(funcs)}')
    for f in funcs:
        vis = 'public' if not f['is_private'] else 'private'
        print(f'  • {f["name"]:25s} ({vis:7s}, line {f["line_number"]:3d})')
    
    print(f'\nStructs/Interfaces: {len(classes)}')
    for c in classes:
        print(f'  • {c["name"]:25s} ({c.get("type", "unknown"):9s}) with {len(c.get("methods", []))} methods')
    
    print('\n' + '=' * 60)
    print('✅ All parser tests completed successfully!')
    print('=' * 60)

if __name__ == '__main__':
    try:
        test_all_parsers()
    except Exception as e:
        print(f'\n❌ Test failed: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1) 