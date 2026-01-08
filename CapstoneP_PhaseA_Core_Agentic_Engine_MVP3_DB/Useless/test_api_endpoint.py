"""
Simple script to test the API endpoint
Tests the OpenAI-compatible API at https://space.ai-builders.com/backend/v1
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
import sys

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

def test_api_endpoint():
    """Test the API endpoint with a simple request"""
    
    print("=" * 60)
    print("API Endpoint Test Script")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("SECOND_MIND_API_KEY")
    if not api_key:
        print("❌ ERROR: SECOND_MIND_API_KEY not found in .env file")
        print(f"   Looking for .env at: {env_path}")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Configure proxy (if needed)
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    proxy_port = os.getenv("PROXY_PORT", "7890")
    
    if not http_proxy:
        http_proxy = f"http://127.0.0.1:{proxy_port}"
    if not https_proxy:
        https_proxy = http_proxy
    
    os.environ["HTTP_PROXY"] = http_proxy
    os.environ["HTTPS_PROXY"] = https_proxy
    print(f"✅ Proxy configured: {http_proxy}")
    
    # Initialize client
    base_url = "https://space.ai-builders.com/backend/v1"
    model = "gpt-5"
    
    print(f"\n📡 Connecting to API endpoint...")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=30.0,
        )
        
        # Test 1: Simple chat completion
        print("\n" + "-" * 60)
        print("Test 1: Simple Chat Completion")
        print("-" * 60)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, API test successful!' in one sentence."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("✅ Request successful!")
        print(f"   Response: {response.choices[0].message.content}")
        print(f"   Model used: {response.model}")
        print(f"   Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        # Test 2: Check available models (if endpoint supports it)
        print("\n" + "-" * 60)
        print("Test 2: Check API Health")
        print("-" * 60)
        
        try:
            # Try to get models list (some APIs support this)
            models_response = client.models.list()
            print("✅ Models endpoint accessible")
            if hasattr(models_response, 'data') and models_response.data:
                print(f"   Available models: {len(models_response.data)}")
                for model_info in models_response.data[:5]:  # Show first 5
                    print(f"     - {model_info.id}")
        except Exception as e:
            print(f"⚠️  Models endpoint not available (this is OK): {type(e).__name__}")
        
        # Test 3: Test with longer conversation
        print("\n" + "-" * 60)
        print("Test 3: Multi-turn Conversation")
        print("-" * 60)
        
        messages = [
            {"role": "system", "content": "You are a helpful banking assistant."},
            {"role": "user", "content": "What is a term deposit?"}
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        print("✅ Multi-turn test successful!")
        print(f"   Response: {response.choices[0].message.content[:200]}...")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! API endpoint is working correctly.")
        print("=" * 60)
        return True
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        print("\n" + "=" * 60)
        print("❌ API Test Failed")
        print("=" * 60)
        print(f"Error Type: {error_type}")
        print(f"Error Message: {error_msg}")
        
        # Provide troubleshooting tips
        print("\n" + "-" * 60)
        print("Troubleshooting Tips:")
        print("-" * 60)
        
        if "Internal Server Error" in error_msg:
            print("1. The API server may be down or experiencing issues")
            print("2. Check if the API endpoint is accessible:")
            print(f"   curl -X GET {base_url}/models")
            print("3. Verify your API key is valid")
            print("4. Check network/proxy connectivity")
        elif "Unauthorized" in error_msg or "401" in error_msg:
            print("1. Invalid API key - check your SECOND_MIND_API_KEY")
            print("2. API key may have expired")
            print("3. Verify API key has proper permissions")
        elif "Not Found" in error_msg or "404" in error_msg:
            print("1. API endpoint URL may be incorrect")
            print(f"2. Verify base_url: {base_url}")
            print("3. Check if the model name 'gpt-5' is correct")
        elif "timeout" in error_msg.lower():
            print("1. Network connection is slow or proxy is blocking")
            print("2. Check proxy settings")
            print("3. Try increasing timeout value")
        elif "Connection" in error_msg or "network" in error_msg.lower():
            print("1. Check internet connection")
            print("2. Verify proxy settings are correct")
            print(f"3. Test proxy: {http_proxy}")
        else:
            print("1. Check API documentation for error details")
            print("2. Verify all configuration parameters")
            print("3. Check server logs if you have access")
        
        return False

if __name__ == "__main__":
    success = test_api_endpoint()
    sys.exit(0 if success else 1)

