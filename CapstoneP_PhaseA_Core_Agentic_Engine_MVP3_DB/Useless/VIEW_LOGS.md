# How to View Server Console Logs

## Method 1: Run Server in Foreground (Recommended)

Run the server in foreground mode to see all logs in real-time:

```bash
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseA_Core_Agentic_Engine
python launch_server_foreground.py
```

This will:
- Show all server output in the terminal
- Display debug messages from `banking_notes_tool.py`
- Show request/response logs
- Allow you to see errors immediately

## Method 2: Check if Server is Running in Background

If the server is running in the background, you can:

1. **Check running processes:**
   ```bash
   tasklist | findstr python
   tasklist | findstr uvicorn
   ```

2. **View process output** (if running in a separate window):
   - Look for the terminal/console window where you started the server
   - The logs should be visible there

## Method 3: Check Logs via API

You can also check if the server is responding:

```bash
# Test if server is running
curl http://127.0.0.1:8000/docs

# Or open in browser
# http://127.0.0.1:8000/docs
```

## What to Look For in Logs

When you make a request to `/chat`, you should see:

```
DEBUG: BankingNotesQueryTool initialized with embeddings_url: https://space.ai-builders.com/backend/v1
DEBUG: Embeddings endpoint configured as: https://space.ai-builders.com/backend/v1/embeddings
Embeddings API initialized with proxy: http://127.0.0.1:7890
DEBUG: Making request to embeddings endpoint: https://space.ai-builders.com/backend/v1/embeddings
DEBUG: Using proxies: {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
DEBUG: Base URL: https://space.ai-builders.com/backend/v1
DEBUG: Response status: 200
```

If you see the old URL (`https://space.ai-builders.com/embeddings` without `/backend/v1`), the server is using cached code.

## Method 4: Stop and Restart in Foreground

1. Stop the server:
   ```bash
   python stop_server.py
   ```

2. Start in foreground to see logs:
   ```bash
   python launch_server_foreground.py
   ```

Now you'll see all output directly in your terminal!

