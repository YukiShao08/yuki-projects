# Understanding Python Tracebacks - Debugging Guide

## How to Read a Traceback

A traceback shows the **call stack** - the sequence of function calls that led to the error. Read it **from bottom to top**:

### Traceback Structure:
```
Traceback (most recent call last):  ← Start here (most recent)
  File "file.py", line X, in function_name
    code_that_failed
ErrorType: Error message  ← This is the ROOT CAUSE
```

### Reading Order:
1. **Bottom line** = The actual error (ROOT CAUSE)
2. **Work upward** = See how the error propagated through your code
3. **Top line** = Where the error was first caught/handled

---

## Your Specific Error Analysis

### The Error You Encountered:

```
httpcore.ConnectError: EOF occurred in violation of protocol (_ssl.c:997)
```

**Translation**: The SSL/TLS handshake failed when trying to connect to the API server.

### Call Stack (Bottom to Top):

1. **Root Cause** (Line 501):
   ```
   httpcore.ConnectError: EOF occurred in violation of protocol
   ```
   - SSL connection failed

2. **Wrapped by httpx** (Line 522):
   ```
   httpx.ConnectError: EOF occurred in violation of protocol
   ```
   - HTTP client library caught the connection error

3. **Wrapped by OpenAI SDK** (Line 534):
   ```
   openai.APIConnectionError: Connection error.
   ```
   - OpenAI SDK caught and re-raised it

4. **Your Code** (Line 527 in main.py):
   ```
   File "main.py", line 486, in chat
       completion = client.chat.completions.create(...)
   ```
   - This is where YOUR code called the API

5. **FastAPI Handler** (Line 771):
   - Your exception handler caught it and returned HTTP 500

---

## Root Cause Identified

The problem was in `main.py` lines 134-137:

```python
# OLD CODE (PROBLEM):
if not http_proxy:
    http_proxy = f"http://127.0.0.1:{proxy_port}"  # ← Forces proxy even if not needed!
```

**Issue**: The code was **automatically setting a proxy** (`127.0.0.1:7890`) even when:
- No proxy was configured
- The proxy server wasn't running
- The proxy doesn't support SSL properly

This caused SSL handshake failures when trying to connect through a non-existent or misconfigured proxy.

---

## Fixes Applied

### 1. **Made Proxy Optional** (Lines 129-146)
- ✅ Only uses proxy if explicitly set in environment variables
- ✅ Removes proxy settings if not needed
- ✅ Adds debug logging to show proxy status

### 2. **Better SSL Configuration** (Lines 148-157)
- ✅ Added explicit httpx client with proper timeout
- ✅ SSL verification enabled
- ✅ Better error logging during initialization

### 3. **Improved Error Handling** (Lines 787-820)
- ✅ Specific handling for `APIConnectionError`
- ✅ More helpful error messages with solutions
- ✅ Uses HTTP 503 (Service Unavailable) for connection errors (more appropriate than 500)

---

## How to Verify the Fix

1. **Check Debug Output**:
   - Look for: `"DEBUG: No proxy configured, using direct connection"`
   - If you see proxy messages, check your environment variables

2. **Test the API**:
   - Try the `/chat` endpoint again
   - If it still fails, check the new error message - it will be more helpful

3. **If You Need a Proxy**:
   - Set `HTTP_PROXY` and `HTTPS_PROXY` environment variables
   - Make sure your proxy server is running
   - Verify the proxy supports HTTPS/SSL

---

## Common Traceback Patterns

### Connection Errors:
```
ConnectError / ConnectionRefusedError
→ Network issue, server down, or firewall blocking
```

### SSL Errors:
```
SSL: EOF / SSL: CERTIFICATE_VERIFY_FAILED
→ SSL handshake failed or certificate issue
```

### Timeout Errors:
```
TimeoutError / ReadTimeout
→ Server took too long to respond
```

### Import Errors:
```
ModuleNotFoundError / ImportError
→ Missing package or wrong Python path
```

### Attribute Errors:
```
AttributeError: 'X' object has no attribute 'Y'
→ Trying to access non-existent method/property
```

---

## Tips for Debugging

1. **Always read from bottom to top** - the bottom line is the root cause
2. **Look for YOUR code** in the traceback - that's where you can fix it
3. **Check the error type** - different errors need different solutions
4. **Use print/logging** - add debug statements to trace execution
5. **Check environment** - many errors are due to missing config/env vars

---

## Next Steps

If you still encounter errors after these fixes:

1. **Check the new error message** - it should be more descriptive
2. **Look at debug output** - see what proxy/connection settings are being used
3. **Test network connectivity** - can you reach `https://space.ai-builders.com`?
4. **Check environment variables** - ensure no unwanted proxy settings

