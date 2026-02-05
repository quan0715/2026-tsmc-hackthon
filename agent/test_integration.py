"""Test tool and skill integration"""
# Import tools to trigger registration
from agent.tools import bash, analyze_code_context, analyze_test_gaps
from agent.registry import list_registered_tools, get_tool

print("=== Registered Tools ===")
for tool_name in list_registered_tools():
    print(f"  ✓ {tool_name}")

# Test context analyzer
print("\n=== Testing Context Analyzer ===")
analyze_fn = get_tool("analyze_code_context")
if analyze_fn:
    result = analyze_fn("./agent/tools/bash.py")
    print(f"✓ Works! Output length: {len(result)} chars")
else:
    print("✗ Not found")

# Test gap analyzer
print("\n=== Testing Gap Analyzer ===")
gap_fn = get_tool("analyze_test_gaps")
if gap_fn:
    result = gap_fn("./agent/tools/bash.py")
    print(f"✓ Works! Output length: {len(result)} chars")
else:
    print("✗ Not found")

print("\n✅ Integration test complete!")
