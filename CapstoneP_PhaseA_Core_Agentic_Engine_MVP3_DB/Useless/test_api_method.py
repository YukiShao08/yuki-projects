"""
Test different HTTP methods for the embeddings API
"""

import requests
import os

# API configuration
api_key = "sk_f4e0b32d_6f6cf1db6bd8ccf6735fab4976aaa0accd32"
base_url = "https://space.ai-builders.com/backend/v1"
endpoint = f"{base_url}/embeddings"

# Proxy configuration
proxy_port = os.getenv("PROXY_PORT", "7890")
http_proxy = f"http://127.0.0.1:{proxy_port}"
proxies = {
    "http": http_proxy,
    "https": http_proxy
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

test_text = "test query"

print("="*70)
print("Testing Embeddings API with Different HTTP Methods")
print("="*70)
print(f"Endpoint: {endpoint}")
print(f"Proxy: {http_proxy}")
print()

# Test 1: POST with JSON body (current method)
print("[TEST 1] POST with JSON body")
print("-"*70)
try:
    response = requests.post(
        endpoint,
        headers=headers,
        json={
            "input": test_text,
            "model": "text-embedding-ada-002"
        },
        timeout=30,
        proxies=proxies
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response URL: {response.url}")
    if response.status_code == 200:
        print("[SUCCESS] POST method works!")
        data = response.json()
        print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'List response'}")
    else:
        print(f"[FAILED] Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"[ERROR] {e}")

print()

# Test 2: POST with form data
print("[TEST 2] POST with form data")
print("-"*70)
try:
    response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {api_key}"},
        data={
            "input": test_text,
            "model": "text-embedding-ada-002"
        },
        timeout=30,
        proxies=proxies
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response URL: {response.url}")
    if response.status_code == 200:
        print("[SUCCESS] POST with form data works!")
    else:
        print(f"[FAILED] Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"[ERROR] {e}")

print()

# Test 3: GET with query parameters
print("[TEST 3] GET with query parameters")
print("-"*70)
try:
    response = requests.get(
        endpoint,
        headers=headers,
        params={
            "input": test_text,
            "model": "text-embedding-ada-002"
        },
        timeout=30,
        proxies=proxies
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response URL: {response.url}")
    if response.status_code == 200:
        print("[SUCCESS] GET method works!")
    else:
        print(f"[FAILED] Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"[ERROR] {e}")

print()
print("="*70)
print("Test completed. Check which method works above.")
print("="*70)

