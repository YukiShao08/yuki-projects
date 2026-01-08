# Multi-Provider Search Setup Guide

## Overview

The search system now uses **multiple providers with automatic fallback** to reduce rate limiting issues:

1. **DuckDuckGo** (Primary) - Free, no API key needed
2. **SearXNG** (Fallback) - Free, open-source metasearch
3. **Tavily** (Optional Fallback) - Free tier: 1000 requests/month

## How It Works

When a search is requested:
1. Tries **DuckDuckGo** first
2. If rate-limited or fails → automatically tries **SearXNG**
3. If still fails and Tavily API key is configured → tries **Tavily**
4. Returns results from the first successful provider

## Benefits

✅ **Reduced Rate Limiting**: If one provider is rate-limited, automatically uses another  
✅ **Higher Reliability**: Multiple fallbacks ensure searches succeed more often  
✅ **No Breaking Changes**: Still uses the same `duckduckgo_search` tool name  
✅ **Backward Compatible**: Works without any API keys (DuckDuckGo + SearXNG are free)

## Optional: Tavily API Key Setup

Tavily provides an additional fallback option with 1000 free requests/month.

### Get Tavily API Key:
1. Visit: https://tavily.com
2. Sign up for free account
3. Get your API key from dashboard

### Configure:
Add to your `.env` file:
```
TAVILY_API_KEY=your_tavily_api_key_here
```

**Note**: Tavily is optional. The system works fine with just DuckDuckGo + SearXNG (both free, no API keys needed).

## SearXNG Public Instances

The system uses public SearXNG instances. If one is down, you can modify `multi_search.py` to use a different instance:

- `https://searx.be`
- `https://searx.org`
- `https://search.sapti.me`
- `https://searx.tiekoetter.com`

## Testing

Test the multi-provider search:
```python
from multi_search import multi_search

# Test without Tavily API key
result = multi_search("Python FastAPI", max_results=5)
print(result)

# Test with Tavily API key (if configured)
import os
tavily_key = os.getenv("TAVILY_API_KEY")
result = multi_search("Python FastAPI", max_results=5, tavily_api_key=tavily_key)
print(result)
```

## Rate Limiting Notes

**Important**: The rate limiting protection in the code is **necessary** and should **NOT** be removed. It:
- Prevents hitting provider rate limits too quickly
- Reduces the chance of getting blocked
- Works across all providers

The multi-provider approach **reduces** rate limiting issues by:
- Spreading requests across multiple providers
- Automatically switching when one provider is rate-limited
- Using different rate limits from different providers

## Troubleshooting

### All providers failing?
- Check internet connection
- Wait 1-2 minutes and retry (rate limits are usually temporary)
- Verify SearXNG public instances are accessible

### Want to use a different SearXNG instance?
Edit `multi_search.py`, line ~60:
```python
def search_searxng(query: str, max_results: int = 5, instance_url: str = "https://searx.be"):
```
Change `instance_url` to your preferred instance.

### Want to add more providers?
You can extend `multi_search.py` to add:
- Bing Search API (Microsoft - free tier)
- Google Custom Search API (free tier with limits)
- SerpAPI (100 free requests/month)

