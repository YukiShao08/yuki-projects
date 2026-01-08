"""
Test script for multi-provider search functionality
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configure proxy for Clash for Windows (port 7890)
# This must be set BEFORE importing modules that use requests
proxy_port = os.getenv("PROXY_PORT", "7890")
proxy_url = f"http://127.0.0.1:{proxy_port}"

# Set proxy environment variables
os.environ["HTTP_PROXY"] = proxy_url
os.environ["HTTPS_PROXY"] = proxy_url
os.environ["http_proxy"] = proxy_url
os.environ["https_proxy"] = proxy_url

print(f"[INFO] Proxy configured: {proxy_url}")

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from multi_search import multi_search

def test_multi_search():
    """Test the multi-provider search"""
    
    print("="*70)
    print("Testing Multi-Provider Search")
    print("="*70)
    print()
    
    # Test queries
    test_queries = [
        "Python FastAPI",
        "HSBC UK personal loan rates 2024"
    ]
    
    # Get Tavily API key if available
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        print("[OK] Tavily API key found - will use as fallback")
    else:
        print("[INFO] Tavily API key not found - using DuckDuckGo + SearXNG only")
    
    # Show proxy status
    proxy_configured = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    if proxy_configured:
        print(f"[OK] Proxy configured: {proxy_configured}")
    else:
        print("[WARNING] No proxy configured")
    print()
    
    for query in test_queries:
        print(f"Testing query: '{query}'")
        print("-" * 70)
        
        try:
            result = multi_search(query, max_results=3, tavily_api_key=tavily_key)
            # Parse JSON string to dict
            import json
            result_dict = json.loads(result) if isinstance(result, str) else result
            
            if "error" in result_dict:
                print(f"[ERROR] Error: {result_dict.get('error', 'Unknown error')}")
                if "providers_tried" in result_dict:
                    print(f"   Providers tried: {', '.join(result_dict['providers_tried'])}")
            else:
                provider = result_dict.get("provider", "Unknown")
                count = result_dict.get("count", 0)
                fallback = result_dict.get("fallback_used", False)
                
                print(f"[OK] Success! Provider: {provider}")
                print(f"  Results: {count}")
                if fallback:
                    print(f"  [WARNING] Fallback was used (primary provider failed)")
                    if "providers_tried" in result_dict:
                        print(f"  Providers tried: {', '.join(result_dict['providers_tried'])}")
                
                # Show first result
                results = result_dict.get("results", [])
                if results:
                    print(f"\n  First result:")
                    print(f"    Title: {results[0].get('title', 'N/A')[:60]}...")
                    print(f"    URL: {results[0].get('url', 'N/A')[:60]}...")
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
        
        print()
        print("="*70)
        print()
    
    print("Test completed!")

if __name__ == "__main__":
    test_multi_search()

