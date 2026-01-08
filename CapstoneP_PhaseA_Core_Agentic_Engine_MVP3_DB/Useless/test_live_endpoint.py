"""
Test the actual endpoint being used by the banking notes tool
This simulates what happens when the server calls query_my_notes
"""

import sys
from pathlib import Path

# Force reload the module
if 'banking_notes_tool' in sys.modules:
    del sys.modules['banking_notes_tool']

from banking_notes_tool import query_my_notes, get_banking_notes_tool, reset_banking_notes_tool

print("="*70)
print("Testing Live Banking Notes Tool")
print("="*70)
print()

# Reset to force fresh initialization
reset_banking_notes_tool()

# Get the tool
tool = get_banking_notes_tool()

if tool is None:
    print("ERROR: Could not get banking notes tool")
    sys.exit(1)

print(f"Tool endpoint: {tool.embeddings_api.embeddings_endpoint}")
print(f"Tool base URL: {tool.embeddings_api.base_url}")
print()

# Test a simple query
print("Testing query: 'test'")
print("-"*70)
try:
    result = query_my_notes("test", top_k=1)
    print("Query successful!")
    print(f"Result preview: {result[:200]}...")
except Exception as e:
    print(f"ERROR during query: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)

