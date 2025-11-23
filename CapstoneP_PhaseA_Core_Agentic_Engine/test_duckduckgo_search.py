"""
Standalone test script for DuckDuckGo Search API integration.
This script verifies that the duckduckgo-search library works correctly.

Best Practices:
1. Always use DDGS as a context manager (with statement) to ensure proper cleanup
2. Handle exceptions gracefully - DuckDuckGo may rate limit or block requests
3. Limit max_results to reasonable numbers (5-10) to avoid timeouts
4. Add delays between searches if making multiple requests
5. Cache results when possible to reduce API calls

Common Errors:
1. Rate limiting: Too many requests may result in temporary blocks
2. Network timeouts: Add timeout handling for slow connections
3. Empty results: Some queries may return no results
4. Invalid queries: Empty or very long queries may cause issues
"""

from duckduckgo_search import DDGS
import json
import time


def duckduckgo_search(query: str, max_results: int = 5) -> list:
    """
    Perform a DuckDuckGo web search.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        List of search results, each containing 'title', 'href', and 'body'
    
    Raises:
        Exception: If search fails
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except Exception as e:
        raise Exception(f"DuckDuckGo search failed: {str(e)}")


def test_duckduckgo_search(query: str = "Python FastAPI", max_results: int = 5):
    """
    Test function to verify DuckDuckGo search functionality.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
    
    Returns:
        List of search results
    """
    try:
        print(f"Testing DuckDuckGo search with query: '{query}'")
        print(f"Max results: {max_results}\n")
        
        results = duckduckgo_search(query, max_results)
        
        print(f"✓ Search completed successfully!")
        print(f"✓ Found {len(results)} results\n")
        
        # Display results
        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  URL: {result.get('href', 'N/A')}")
            snippet = result.get('body', 'N/A')
            if len(snippet) > 100:
                snippet = snippet[:100] + "..."
            print(f"  Snippet: {snippet}")
            print()
        
        return results
            
    except Exception as e:
        print(f"✗ Error during search: {type(e).__name__}: {e}")
        raise


def test_error_handling():
    """Test error handling scenarios."""
    print("=" * 60)
    print("Testing error handling...")
    print("=" * 60)
    
    # Test with empty query
    try:
        results = duckduckgo_search("", max_results=1)
        print(f"Empty query handled: {len(results)} results")
    except Exception as e:
        print(f"Empty query error (expected): {type(e).__name__}: {e}")
    
    # Test with very long query
    try:
        long_query = "a" * 1000
        results = duckduckgo_search(long_query, max_results=1)
        print(f"Long query handled: {len(results)} results")
    except Exception as e:
        print(f"Long query error: {type(e).__name__}: {e}")
    
    # Test with special characters
    try:
        results = duckduckgo_search("Python & FastAPI", max_results=1)
        print(f"Special characters handled: {len(results)} results")
    except Exception as e:
        print(f"Special characters error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("DuckDuckGo Search API Test Script")
    print("=" * 60)
    print()
    
    # Test 1: Basic search
    try:
        results = test_duckduckgo_search("Python FastAPI", max_results=3)
        print("=" * 60)
        print("✓ Basic search test PASSED")
        print("=" * 60)
    except Exception as e:
        print("=" * 60)
        print(f"✗ Basic search test FAILED: {e}")
        print("=" * 60)
    
    print()
    
    # Test 2: Error handling
    test_error_handling()
    
    print()
    print("=" * 60)
    print("Test script completed!")
    print("=" * 60)

