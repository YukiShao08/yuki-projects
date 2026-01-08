"""
Script to verify the embeddings endpoint fix is in place
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from banking_notes_tool import get_banking_notes_tool, reset_banking_notes_tool

print("="*70)
print("Verifying Banking Notes Tool Configuration")
print("="*70)
print()

# Reset to force fresh initialization
reset_banking_notes_tool()

# Get the tool (will create new instance)
tool = get_banking_notes_tool()

if tool is None:
    print("ERROR: Could not initialize banking notes tool")
    print("Check if my_notes.index exists in Phase B project")
    sys.exit(1)

# Check the endpoint
endpoint = tool.embeddings_api.embeddings_endpoint
expected = "https://space.ai-builders.com/backend/v1/embeddings"

print(f"Current endpoint: {endpoint}")
print(f"Expected endpoint: {expected}")
print()

if endpoint == expected:
    print("[SUCCESS] Endpoint is correct!")
    print()
    print("If you're still getting errors, make sure:")
    print("1. The FastAPI server has been restarted")
    print("2. All Python cache files have been cleared")
    print("3. The server is using the updated banking_notes_tool.py")
else:
    print("[ERROR] Endpoint is incorrect!")
    print(f"   Difference: {endpoint} vs {expected}")
    sys.exit(1)

print("="*70)

