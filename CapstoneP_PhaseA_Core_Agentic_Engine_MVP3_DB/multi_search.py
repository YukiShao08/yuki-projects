"""
Multi-Provider Web Search with Fallback
Supports multiple search APIs with automatic fallback when rate limited
"""

import requests
import json
import time
from typing import List, Dict, Optional
from threading import Lock

# Global throttling for all search providers
_last_search_time = 0
_search_lock = Lock()
_min_search_interval = 1  # Reduced to 1 second for faster responses


def search_duckduckgo(query: str, max_results: int = 5) -> Optional[Dict]:
    """
    Search using DuckDuckGo (Primary - Free, no API key needed)
    
    Returns:
        Dict with results or None if failed
    """
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                return None
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")[:300]
                })
            
            return {
                "provider": "DuckDuckGo",
                "results": formatted_results,
                "count": len(formatted_results)
            }
    except Exception as e:
        error_msg = str(e).lower()
        # Check for rate limiting
        if any(keyword in error_msg for keyword in ["rate limit", "429", "blocked", "throttle"]):
            return {"error": "rate_limited", "provider": "DuckDuckGo"}
        return {"error": str(e), "provider": "DuckDuckGo"}


def search_searxng(query: str, max_results: int = 5, instance_url: str = "https://searx.be") -> Optional[Dict]:
    """
    Search using SearXNG (Fallback - Free, open-source metasearch)
    
    Public instances: https://searx.be, https://searx.org, https://search.sapti.me
    
    Returns:
        Dict with results or None if failed
    """
    import os
    
    # Get proxy settings from environment
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    
    params = {
        "q": query,
        "format": "json",
        "engines": "google,bing,duckduckgo",  # Use multiple engines
        "safesearch": "0"
    }
    
    # Try with proxy first (if configured), then without proxy as fallback
    proxy_configs = []
    if http_proxy or https_proxy:
        proxy_configs.append({
            "http": http_proxy,
            "https": https_proxy or http_proxy
        })
    # Always try without proxy as fallback
    proxy_configs.append(None)
    
    for proxies in proxy_configs:
        try:
            response = requests.get(
                f"{instance_url}/search",
                params=params,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                proxies=proxies,
                verify=True
            )
        
            if response.status_code != 200:
                if proxies is None:  # If this was the no-proxy attempt, give up
                    return {"error": f"HTTP {response.status_code}", "provider": "SearXNG"}
                continue  # Try next proxy configuration
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                if proxies is None:  # If this was the no-proxy attempt, give up
                    return None
                continue  # Try next proxy configuration
            
            formatted_results = []
            for result in results[:max_results]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", "")[:300]
                })
            
            return {
                "provider": "SearXNG",
                "results": formatted_results,
                "count": len(formatted_results)
            }
        except Exception as e:
            # If this was the no-proxy attempt, return error
            if proxies is None:
                return {"error": str(e), "provider": "SearXNG"}
            # Otherwise, try next proxy configuration
            continue
    
    # All attempts failed
    return {"error": "All proxy configurations failed", "provider": "SearXNG"}


def search_tavily(query: str, max_results: int = 5, api_key: Optional[str] = None) -> Optional[Dict]:
    """
    Search using Tavily API (Fallback - Free tier: 1000 requests/month)
    Designed specifically for AI/RAG applications
    
    Get API key: https://tavily.com
    
    Returns:
        Dict with results or None if failed
    """
    if not api_key:
        return {"error": "API key required", "provider": "Tavily"}
    
    import os
    
    # Get proxy settings from environment
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    
    proxies = None
    if http_proxy or https_proxy:
        proxies = {
            "http": http_proxy,
            "https": https_proxy or http_proxy
        }
    
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic"
            },
            timeout=10,
            proxies=proxies
        )
        
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "provider": "Tavily"}
        
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            return None
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content", "")[:300]
            })
        
        return {
            "provider": "Tavily",
            "results": formatted_results,
            "count": len(formatted_results)
        }
    except Exception as e:
        return {"error": str(e), "provider": "Tavily"}


def multi_search(query: str, max_results: int = 5, tavily_api_key: str = "") -> str:
    """
    Multi-provider search with automatic fallback
    
    Tries providers in order:
    1. DuckDuckGo (primary - free, no API key)
    2. Tavily (fallback - free tier with API key)
    3. SearXNG (fallback - free, public instances)
    
    Args:
        query: Search query string
        max_results: Maximum number of results
        tavily_api_key: Optional Tavily API key (from environment or .env)
    
    Returns:
        JSON string with search results
    """
    global _last_search_time
    
    # Throttling across all providers
    with _search_lock:
        current_time = time.time()
        time_since_last = current_time - _last_search_time
        
        if time_since_last < _min_search_interval:
            wait_time = _min_search_interval - time_since_last
            time.sleep(wait_time)
        
        _last_search_time = time.time()
    
    # Try providers in order
    providers_tried = []
    """
    # 1. Try DuckDuckGo first
    result = search_duckduckgo(query, max_results)
    if result and "error" not in result:
        return json.dumps({
            "query": query,
            "provider": result["provider"],
            "results": result["results"],
            "count": result["count"],
            "fallback_used": False
        }, indent=2)
    elif result and result.get("error") == "rate_limited":
        providers_tried.append(f"DuckDuckGo (rate limited)")
    else:
        providers_tried.append(f"DuckDuckGo (failed)")
    """
    # 2. Fallback to Tavily (if API key provided)
    if tavily_api_key:
        result = search_tavily(query, max_results, tavily_api_key)
        if result and "error" not in result:
            return json.dumps({
                "query": query,
                "provider": result["provider"],
                "results": result["results"],
                "count": result["count"],
                "fallback_used": True,
                "providers_tried": providers_tried
            }, indent=2)
        elif result:
            providers_tried.append(f"Tavily ({result.get('error', 'failed')})")
    
    # 3. Fallback to SearXNG (last resort)
    result = search_searxng(query, max_results)
    if result and "error" not in result:
        return json.dumps({
            "query": query,
            "provider": result["provider"],
            "results": result["results"],
            "count": result["count"],
            "fallback_used": True,
            "providers_tried": providers_tried
        }, indent=2)
    elif result:
        providers_tried.append(f"SearXNG ({result.get('error', 'failed')})")
    
    # All providers failed
    return json.dumps({
        "query": query,
        "error": "All search providers failed",
        "results": [],
        "count": 0,
        "providers_tried": providers_tried,
        "message": "Unable to complete the search. All search providers (DuckDuckGo, Tavily, SearXNG) failed or were rate limited. Please wait a moment and try again."
    }, indent=2)

