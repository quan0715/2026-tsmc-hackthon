"""Context Analysis Tool - Static code analysis for multiple languages.

This tool extracts code structure and complexity metrics to provide context
for refactoring suggestions across Python, JavaScript/TypeScript, Java, and Go.
It does NOT perform refactoring itself.
"""
import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# Optional dependencies with graceful fallbacks
try:
    from pygments.lexers import get_lexer_for_filename
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

# tree-sitter often fails in Docker/restricted environments
try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except (ImportError, OSError):
    TREE_SITTER_AVAILABLE = False


class FileAnalysis(BaseModel):
    """Input schema for context analysis tool."""
    filepath: str = Field(description="Path to source file to analyze (supports .py, .js, .ts, .java, .go) (relative or absolute)")


class ContextAnalysisTool:
    """Static code analysis tool supporting multiple languages (Python, JavaScript/TypeScript, Java, Go)."""
    
    def __init__(self, root_dir: str = "/workspace", skills_dir: Optional[str] = None):
        """Initialize the context analysis tool.
        
        Args:
            root_dir: Root directory for resolving relative paths
            skills_dir: Directory containing skill files (for few-shot examples)
        """
        self.root_dir = root_dir
        self.skills_dir = skills_dir or f"{root_dir}/skills/refactoring"
    
    def parse_file_structure(self, filepath: str) -> Dict[str, Any]:
        """Parse file structure using language-appropriate parser.
        
        Args:
            filepath: Path to source file
            
        Returns:
            Dictionary containing imports, classes, functions, and global variables
        """
        if not os.path.exists(filepath):
            return {
                "error": f"File not found: {filepath}",
                "imports": [],
                "classes": [],
                "functions": [],
                "globals": []
            }
        
        try:
            from agent.tools.parsers import get_parser
            parser = get_parser(filepath)
            
            structure = {
                "imports": parser.extract_imports(filepath),
                "classes": parser.extract_classes(filepath),
                "functions": parser.extract_functions(filepath),
                "globals": []  # Not all languages have global variables
            }
            
            return structure
            
        except ValueError as e:
            # Unsupported language
            return {
                "error": str(e),
                "imports": [],
                "classes": [],
                "functions": [],
                "globals": []
            }
        except Exception as e:
            return {
                "error": f"Error parsing file: {e}",
                "imports": [],
                "classes": [],
                "functions": [],
                "globals": []
            }
    
    def calculate_complexity(self, filepath: str) -> Dict[str, Any]:
        """Calculate code complexity metrics using language-appropriate parser.
        
        Args:
            filepath: Path to source file
            
        Returns:
            Dictionary containing complexity metrics (when supported)
        """
        if not os.path.exists(filepath):
            return {
                "cyclomatic_complexity": [],
                "complexity_hotspots": [],
                "maintainability_index": None,
                "summary": {}
            }
        
        try:
            from agent.tools.parsers import get_parser
            parser = get_parser(filepath)
            return parser.calculate_complexity(filepath)
        except ValueError as e:
            # Unsupported language
            return {
                "error": str(e),
                "cyclomatic_complexity": [],
                "complexity_hotspots": [],
                "maintainability_index": None,
                "summary": {}
            }
        except Exception as e:
            return {
                "error": f"Error calculating complexity: {e}",
                "cyclomatic_complexity": [],
                "complexity_hotspots": [],
                "maintainability_index": None,
                "summary": {}
            }
    
    def match_few_shot_examples(self, code_structure: Dict[str, Any], 
                                complexity_data: Dict[str, Any]) -> List[str]:
        """Select relevant refactoring patterns based on code smells.
        
        Args:
            code_structure: Parsed code structure
            complexity_data: Complexity metrics
            
        Returns:
            List of applicable refactoring pattern names
        """
        applicable_patterns = []
        
        # Check for complexity hotspots → suggest Guard Clauses or Extract Method
        if complexity_data.get("complexity_hotspots"):
            applicable_patterns.append("Nested Ifs → Guard Clauses")
            applicable_patterns.append("Long Function → Extract Method")
        
        # Check for high average complexity
        summary = complexity_data.get("summary", {})
        if summary.get("average_complexity", 0) > 5:
            applicable_patterns.append("Complex Conditionals → Polymorphism")
        
        # Check for long functions (heuristic: > 20 LOC would be in complexity)
        if summary.get("total_functions", 0) > 0:
            avg_complexity = summary.get("average_complexity", 0)
            if avg_complexity > 7:
                applicable_patterns.append("Long Function → Extract Method")
        
        # Check for potential duplication (heuristic based on similar function names)
        functions = code_structure.get("functions", [])
        function_names = [f["name"] for f in functions]
        
        # Look for similar prefixes (e.g., calculate_x, calculate_y)
        prefixes = {}
        for name in function_names:
            parts = name.split('_')
            if len(parts) > 1:
                prefix = '_'.join(parts[:-1])
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
        
        if any(count >= 2 for count in prefixes.values()):
            applicable_patterns.append("Duplicated Code → DRY Principle")
        
        # Check for potential magic numbers (suggest Named Constants)
        # This is a simple heuristic - in reality would need deeper AST analysis
        if len(functions) > 0 or len(code_structure.get("classes", [])) > 0:
            applicable_patterns.append("Magic Numbers → Named Constants")
        
        return list(set(applicable_patterns))  # Remove duplicates
    
    def extract_context(self, filepath: str) -> Dict[str, Any]:
        """Extract complete context including structure, complexity, and relevant examples.
        
        Args:
            filepath: Path to Python file
            
        Returns:
            Complete context object for refactoring
        """
        # Resolve relative paths
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.root_dir, filepath)
        
        if not os.path.exists(filepath):
            return {
                "error": f"File not found: {filepath}",
                "filepath": filepath
            }
        
        # Parse structure
        structure = self.parse_file_structure(filepath)
        
        # Calculate complexity
        complexity = self.calculate_complexity(filepath)
        
        # Match relevant patterns
        patterns = self.match_few_shot_examples(structure, complexity)
        
        # Build context object
        context = {
            "filepath": filepath,
            "structure": structure,
            "complexity": complexity,
            "applicable_patterns": patterns,
            "recommendations": self._generate_recommendations(structure, complexity, patterns)
        }
        
        return context
    
    def _generate_recommendations(self, structure: Dict, complexity: Dict, 
                                  patterns: List[str]) -> List[str]:
        """Generate high-level recommendations based on analysis.
        
        Args:
            structure: Code structure
            complexity: Complexity metrics
            patterns: Applicable patterns
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Complexity-based recommendations
        hotspots = complexity.get("complexity_hotspots", [])
        if hotspots:
            for hotspot in hotspots:
                recommendations.append(
                    f"Function '{hotspot['name']}' has high complexity ({hotspot['complexity']}). "
                    f"Consider breaking it down into smaller functions."
                )
        
        # Maintainability recommendations
        mi_rank = complexity.get("maintainability_rank", "A")
        if mi_rank in ["C", "D", "F"]:
            recommendations.append(
                f"Maintainability index is {mi_rank}. Consider refactoring to improve code quality."
            )
        
        # Pattern-based recommendations
        if "Nested Ifs → Guard Clauses" in patterns:
            recommendations.append(
                "Nested conditionals detected. Use guard clauses to reduce nesting."
            )
        
        if "Duplicated Code → DRY Principle" in patterns:
            recommendations.append(
                "Similar function names detected. Check for code duplication."
            )
        
        return recommendations
    
    # Helper methods
    
    def _get_name(self, node):
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def _get_return_annotation(self, node):
        """Get return type annotation from function."""
        if node.returns:
            return self._get_name(node.returns)
        return None
    
    def _is_top_level_function(self, tree, func_node):
        """Check if function is defined at module level (not inside a class)."""
        for node in tree.body:
            if node is func_node:
                return True
        return False
    
    def _is_top_level_assign(self, tree, assign_node):
        """Check if assignment is at module level."""
        for node in tree.body:
            if node is assign_node:
                return True
        return False


from agent.registry import register_tool


@register_tool(
    description=(
        "Analyze source files (Python, JavaScript/TypeScript, Java, Go) to extract code structure "
        "(imports, classes, functions), complexity metrics (when available), and applicable refactoring patterns. "
        "Returns detailed context for refactoring decisions. Supports: .py, .js, .jsx, .ts, .tsx, .java, .go"
    )
)
def analyze_code_context(filepath: str) -> str:
    """Analyze a source file and extract refactoring context.
    
    Args:
        filepath: Path to source file to analyze
        
    Returns:
        JSON string containing code structure, complexity metrics, and recommendations
    """
    import json
    analyzer = ContextAnalysisTool(root_dir="/workspace")
    context = analyzer.extract_context(filepath)
    return json.dumps(context, indent=2)
