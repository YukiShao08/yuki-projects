"""
Minimal API endpoint test script
Quick test to verify the API is working
"""

import os
import json
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

# Load .env file
load_dotenv(Path(__file__).parent / ".env")

# Get API key
api_key = os.getenv("SECOND_MIND_API_KEY")
if not api_key:
    print("❌ Error: SECOND_MIND_API_KEY not found in .env")
    exit(1)

# Configure proxy (optional)
proxy_port = os.getenv("PROXY_PORT", "7890")
os.environ["HTTP_PROXY"] = f"http://127.0.0.1:{proxy_port}"
os.environ["HTTPS_PROXY"] = f"http://127.0.0.1:{proxy_port}"

# Create client
client = OpenAI(
    api_key=api_key,
    base_url="https://space.ai-builders.com/backend/v1",
    timeout=30.0
)

# Test API
print("Testing API endpoint...")
try:
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": "what is the top 5 GDP countries in the world?"}
        ],
        max_tokens=40  # Increased to allow full response
    )
    print("✅ Success! API endpoint is reachable.")
    print("\n" + "=" * 60)
    print("Full Response Object (Debug):")
    print("=" * 60)
    print(f"Response type: {type(response)}")
    print(f"Response attributes: {dir(response)}")
    
    # Check if choices exist
    if not hasattr(response, 'choices') or not response.choices:
        print("⚠️  WARNING: No choices in response!")
        print(f"Full response object: {response}")
        print("\n❌ Cannot proceed without choices. API may have returned an error.")
        exit(1)
    
    print(f"Number of choices: {len(response.choices)}")
    
    # Convert response to dictionary and print as JSON
    print("\n" + "=" * 60)
    print("Response JSON:")
    print("=" * 60)
    
    response_dict = {
        "id": response.id if hasattr(response, 'id') else None,
        "model": response.model if hasattr(response, 'model') else None,
        "choices": [
            {
                "index": choice.index if hasattr(choice, 'index') else None,
                "message": {
                    "role": choice.message.role if hasattr(choice.message, 'role') else None,
                    "content": choice.message.content if hasattr(choice.message, 'content') else None,
                    "message_attrs": dir(choice.message) if hasattr(choice, 'message') else []
                },
                "finish_reason": choice.finish_reason if hasattr(choice, 'finish_reason') else None,
                "choice_attrs": dir(choice)
            }
            for choice in response.choices
        ],
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') and response.usage else None,
            "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else None,
            "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') and response.usage else None
        } if hasattr(response, 'usage') else None
    }
    
    print(json.dumps(response_dict, indent=2, ensure_ascii=False))
    
    # Extract and check content
    print("\n" + "=" * 60)
    print("Response Content Analysis:")
    print("=" * 60)
    
    first_choice = response.choices[0]
    message = first_choice.message
    
    # Try different ways to get content
    content = None
    if hasattr(message, 'content'):
        content = message.content
    elif hasattr(message, 'text'):
        content = message.text
    elif isinstance(message, dict):
        content = message.get('content') or message.get('text')
    
    if content:
        print(f"✅ Content found: {len(content)} characters")
        print(f"\nContent preview:\n{content[:500]}")
        if len(content) > 500:
            print(f"... (truncated, total length: {len(content)} chars)")
    else:
        print("⚠️  WARNING: Content is empty or None!")
        print(f"Message object type: {type(message)}")
        print(f"Message attributes: {dir(message)}")
        print(f"Message value: {message}")
        print("\n⚠️  This could indicate:")
        print("   1. API returned empty response")
        print("   2. Response format is different than expected")
        print("   3. Content is in a different attribute")
    
    # Check finish reason
    if hasattr(first_choice, 'finish_reason'):
        finish_reason = first_choice.finish_reason
        print(f"\nFinish reason: {finish_reason}")
        if finish_reason == "length":
            print("⚠️  Response was truncated due to max_tokens limit!")
    
    # Final verdict
    print("\n" + "=" * 60)
    if content and len(content.strip()) > 0:
        print("✅ API endpoint is WORKING - Response received successfully!")
    else:
        print("⚠️  API endpoint responded but content is empty")
        print("   - API connection: ✅ Working")
        print("   - Response content: ❌ Empty")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

