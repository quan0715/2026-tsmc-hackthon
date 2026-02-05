"""Test Gap Analysis Tool - Identify uncovered functions for test generation.

This tool identifies which functions lack test coverage across multiple languages
(Python, JavaScript/TypeScript, Java, Go). It does NOT generate test code - that 
is handled by the agent using SKILL.md patterns.
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class TestGapInput(BaseModel):
    """Input schema for test gap analysis."""
    source_file: str = Field(description="Path to source file to analyze (supports .py, .js, .ts, .java, .go)")
    test_file: Optional[str] = Field(default=None, description="Path to test file (optional, auto-detected if not provided)")


class TestGapAnalyzer:
    """Analyze test coverage gaps by comparing source and test files.
    
    Now supports multiple languages via language-agnostic parsers.
    """
    
    def __init__(self, root_dir: str = "/workspace"):
        self.root_dir = root_dir
    
    def extract_functions(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract all function definitions from a file (language-agnostic).
        
        Args:
            filepath: Path to source file
            
        Returns:
            List of function info dicts with name, line_number, is_private
        """
        if not os.path.exists(filepath):
            return []
        
        try:
            from agent.tools.parsers import get_parser
            parser = get_parser(filepath)
            return parser.extract_functions(filepath)
        except ValueError as e:
            # Unsupported language
            return []
        except Exception as e:
            # Other errors
            return []
    
    def extract_tested_functions(self, test_file: str) -> Set[str]:
        """Extract names of functions being tested (language-agnostic).
        
        Args:
            test_file: Path to test file
            
        Returns:
            Set of tested function names
        """
        if not os.path.exists(test_file):
            return set()
        
        try:
            from agent.tools.parsers import get_parser
            parser = get_parser(test_file)
            return parser.extract_tested_functions(test_file)
        except ValueError as e:
            # Unsupported language
            return set()
        except Exception as e:
            # Other errors
            return set()
    
    def find_test_file(self, source_file: str) -> Optional[str]:
        """Attempt to auto-locate test file for source file (multi-language).
        
        Looks for common test file patterns based on language:
        - Python: test_*.py, *_test.py
        - JavaScript/TypeScript: *.test.js, *.spec.js, *.test.ts, *.spec.ts
        - Java: *Test.java
        - Go: *_test.go
        """
        source_path = Path(source_file)
        base_name = source_path.stem
        ext = source_path.suffix
        
        # Language-specific test file patterns
        candidates = []
        
        if ext == '.py':
            candidates = [
                source_path.parent / f"test_{base_name}.py",
                source_path.parent / f"{base_name}_test.py",
                source_path.parent / "tests" / f"test_{base_name}.py",
                Path("tests") / f"test_{base_name}.py"
            ]
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            candidates = [
                source_path.parent / f"{base_name}.test{ext}",
                source_path.parent / f"{base_name}.spec{ext}",
                source_path.parent / "__tests__" / f"{base_name}.test{ext}",
                Path("__tests__") / f"{base_name}.test{ext}"
            ]
        elif ext == '.java':
            candidates = [
                source_path.parent / f"{base_name}Test.java",
                source_path.parent.parent / "test" / "java" / f"{base_name}Test.java",
            ]
        elif ext == '.go':
            candidates = [
                source_path.parent / f"{base_name}_test.go",
            ]
        
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        
        return None
    
    def analyze_gaps(self, source_file: str, test_file: Optional[str] = None) -> Dict[str, Any]:
        """Analyze test coverage gaps.
        
        Args:
            source_file: Path to source file
            test_file: Path to test file (optional, will auto-detect)
            
        Returns:
            Gap analysis with uncovered functions and recommendations
        """
        # Resolve paths
        if not os.path.isabs(source_file):
            source_file = os.path.join(self.root_dir, source_file)
        
        if not os.path.exists(source_file):
            return {
                "error": f"Source file not found: {source_file}",
                "source_file": source_file
            }
        
        # Extract source functions
        source_functions = self.extract_functions(source_file)
        
        # Filter out private functions and test functions
        public_functions = [
            f for f in source_functions 
            if not f['is_private'] and not f['is_test']
        ]
        
        # Auto-detect test file if not provided
        if test_file is None:
            test_file = self.find_test_file(source_file)
        
        # Extract tested functions
        if test_file and os.path.exists(test_file):
            tested_functions = self.extract_tested_functions(test_file)
            test_file_exists = True
        else:
            tested_functions = set()
            test_file_exists = False
        
        # Find gaps
        uncovered = [
            f for f in public_functions 
            if f['name'] not in tested_functions
        ]
        
        # Calculate coverage
        total_public = len(public_functions)
        covered = total_public - len(uncovered)
        coverage_pct = (covered / total_public * 100) if total_public > 0 else 100.0
        
        # Generate recommendations
        recommendations = []
        if not test_file_exists:
            # Suggest test file based on language
            ext = Path(source_file).suffix
            if ext == '.py':
                test_file = source_file.replace('.py', '_test.py')
            elif ext in ['.js', '.jsx']:
                test_file = source_file.replace(ext, f'.test{ext}')
            elif ext in ['.ts', '.tsx']:
                test_file = source_file.replace(ext, f'.test{ext}')
            elif ext == '.java':
                test_file = source_file.replace('.java', 'Test.java')
            elif ext == '.go':
                test_file = source_file.replace('.go', '_test.go')
            else:
                test_file = source_file + '_test'
            recommendations.append(f"Create test file: {test_file}")
        
        for func in uncovered:
            recommendations.append(
                f"Add test_{func['name']}() to cover {func['name']} (line {func['line_number']})"
            )
        
        return {
            "source_file": source_file,
            "test_file": test_file,
            "test_file_exists": test_file_exists,
            "total_functions": total_public,
            "tested_functions": covered,
            "uncovered_functions": len(uncovered),
            "coverage_percentage": round(coverage_pct, 2),
            "gaps": [
                {
                    "function": f['name'],
                    "line": f['line_number'],
                    "recommendation": f"test_{f['name']}"
                }
                for f in uncovered
            ],
            "recommendations": recommendations[:5],  # Limit to top 5
            "summary": self._generate_summary(total_public, covered, coverage_pct)
        }
    
    def _generate_summary(self, total: int, covered: int, coverage_pct: float) -> str:
        """Generate human-readable summary."""
        if coverage_pct == 100:
            return f"✅ Perfect! All {total} functions have tests (100% coverage)"
        elif coverage_pct >= 80:
            return f"⚠️  Good coverage: {covered}/{total} functions tested ({coverage_pct:.1f}%)"
        elif coverage_pct >= 50:
            return f"⚠️  Moderate coverage: {covered}/{total} functions tested ({coverage_pct:.1f}%)"
        else:
            return f"❌ Low coverage: {covered}/{total} functions tested ({coverage_pct:.1f}%)"


from agent.registry import register_tool


@register_tool(
    description=(
        "Identify functions lacking test coverage in Python, JavaScript/TypeScript, Java, or Go files. "
        "Returns list of uncovered functions with line numbers and test recommendations. "
        "Does NOT generate test code - use this to find gaps, then use SKILL.md patterns to write tests. "
        "Supports: .py, .js, .jsx, .ts, .tsx, .java, .go"
    )
)
def analyze_test_gaps(source_file: str, test_file: str = None) -> str:
    """Identify functions without test coverage.
    
    Args:
        source_file: Path to source file
        test_file: Path to test file (optional, auto-detected)
        
    Returns:
        JSON with uncovered functions and recommendations
    """
    import json
    analyzer = TestGapAnalyzer(root_dir="/workspace")
    result = analyzer.analyze_gaps(source_file, test_file)
    return json.dumps(result, indent=2)
