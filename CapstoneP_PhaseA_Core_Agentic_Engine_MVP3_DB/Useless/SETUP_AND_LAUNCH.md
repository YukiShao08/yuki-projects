# Setup and Launch Guide for Banking Agent

Complete step-by-step guide to set up and launch your FastAPI banking agent with RAG capabilities.

## Prerequisites

Before starting, ensure you have:
- ✅ Python 3.10 or higher
- ✅ Internet connection (for API calls)
- ✅ API keys ready (see below)

## Step 1: Install Dependencies

### Navigate to Phase A Project

```bash
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseA_Core_Agentic_Engine
```

### Install Required Packages

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI and Uvicorn (web server)
- OpenAI client (for Second Mind API)
- FAISS (vector search)
- DuckDuckGo search
- Other dependencies

## Step 2: Set Up Banking Knowledge Base (Phase B)

The agent needs the FAISS index from Phase B project.

### Navigate to Phase B Project

```bash
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseB_RAG
```

### Build the FAISS Index

```bash
python rag_pipeline_custom_embeddings.py
```

**What this does:**
- Loads banking documents from `data/banking_documents/`
- Generates embeddings using your API
- Creates `my_notes.index` and `my_notes.index.metadata.pkl`
- Takes 5-15 minutes (first time only)

**Expected output:**
```
Loading documents from data/banking_documents...
Loaded 7 documents
Created 45 text chunks
Generating embeddings...
Processing batch 1/5...
...
Index built and saved to my_notes.index
```

### Verify Index Created

Check that these files exist:
- `my_notes.index`
- `my_notes.index.metadata.pkl`

## Step 3: Configure Environment Variables

### Create `.env` File

In the Phase A project directory, create a `.env` file:

```bash
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseA_Core_Agentic_Engine
```

Create `.env` with:

```env
# Second Mind API Key (for chat/LLM)
SECOND_MIND_API_KEY=your_second_mind_api_key_here

# Optional: Groq API Key (for alternative LLM)
GROQ_API_KEY=your_groq_api_key_here

# Optional: Proxy settings (if needed)
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
PROXY_PORT=7890
```

**Important:**
- Replace `your_second_mind_api_key_here` with your actual API key
- The embeddings API key is hardcoded in `banking_notes_tool.py` (can be changed if needed)

## Step 4: Verify File Structure

Your Phase A project should have:

```
CapstoneP_PhaseA_Core_Agentic_Engine/
├── main.py                    # Main FastAPI application
├── banking_notes_tool.py      # Banking knowledge base tool
├── requirements.txt           # Dependencies
├── .env                       # Environment variables (create this)
├── static/
│   ├── index.html            # Web interface
│   ├── script.js
│   └── style.css
└── __pycache__/
```

## Step 5: Launch the Agent

### Start the FastAPI Server

```bash
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseA_Core_Agentic_Engine
uvicorn main:app --reload
```

**Expected output:**
```
INFO:     Will watch for changes
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
Loaded FAISS index from C:\Users\HP\...\my_notes.index
Index contains 45 vectors
INFO:     Application startup complete.
```

### Access the Web Interface

Open your browser and go to:
```
http://localhost:8000
```

You should see the chat interface.

## Step 6: Test the Agent

### Test 1: Banking Question (Local KB)

**Question:** "What's the interest rate of term deposit in HK?"

**Expected behavior:**
- Agent uses `query_my_notes` tool
- Retrieves information from local knowledge base
- Provides answer with specific rates

### Test 2: Banking Question (Not in KB)

**Question:** "What are the mortgage rates in Singapore?"

**Expected behavior:**
- Agent tries `query_my_notes` first
- Detects information not available
- Falls back to `duckduckgo_search`
- Provides answer from web search

### Test 3: Non-Banking Question

**Question:** "What's the weather today?"

**Expected behavior:**
- Agent uses `duckduckgo_search` directly
- No local KB search needed

## Step 7: Monitor Tool Usage

Watch the console output to see:
- Which tools are called
- Search queries made
- Results retrieved
- Tool execution flow

Example console output:
```
Tool Call 1:
  Function: query_my_notes
  Arguments: {"query": "term deposit interest rate Hong Kong"}

Tool Result 1:
  {
    "query": "term deposit interest rate Hong Kong",
    "results": [...],
    "has_relevant_results": true
  }
```

## Troubleshooting

### Issue: "Index not found"

**Error:**
```
FileNotFoundError: FAISS index not found at...
```

**Solution:**
1. Make sure you built the index in Phase B
2. Check the path in `banking_notes_tool.py` is correct
3. Verify `my_notes.index` exists

### Issue: "SECOND_MIND_API_KEY not set"

**Error:**
```
OpenAI-compatible client not initialized
```

**Solution:**
1. Check `.env` file exists in Phase A directory
2. Verify `SECOND_MIND_API_KEY` is set
3. Restart the server after creating `.env`

### Issue: "Banking notes tool not available"

**Warning:**
```
Warning: Banking notes index not found...
```

**Solution:**
1. Build the index in Phase B first
2. Check file paths are correct
3. Tool will still work, just without local KB

### Issue: "Embeddings API Error"

**Error:**
```
Error getting embedding: ...
```

**Solution:**
1. Check internet connection
2. Verify embeddings API is accessible
3. Check API key in `banking_notes_tool.py`

### Issue: "Port already in use"

**Error:**
```
Address already in use
```

**Solution:**
```bash
# Use a different port
uvicorn main:app --reload --port 8001
```

## Quick Start Checklist

- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Banking index built in Phase B (`my_notes.index` exists)
- [ ] `.env` file created with `SECOND_MIND_API_KEY`
- [ ] Server started (`uvicorn main:app --reload`)
- [ ] Web interface accessible (`http://localhost:8000`)
- [ ] Test query works

## Production Deployment

For production use:

### Option 1: Run in Background (Windows)

```bash
# Using PowerShell
Start-Process python -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000" -WindowStyle Hidden
```

### Option 2: Use a Process Manager

Consider using:
- **PM2** (with pm2-windows)
- **Windows Service** (NSSM)
- **Docker** container

### Option 3: Deploy to Cloud

- **Heroku**: Add `Procfile` with `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
- **AWS EC2**: Use systemd service
- **Azure**: Use App Service
- **Google Cloud**: Use Cloud Run

## Configuration Options

### Change Port

```bash
uvicorn main:app --reload --port 8080
```

### Change Host (Allow External Access)

```bash
uvicorn main:app --reload --host 0.0.0.0
```

### Disable Auto-Reload (Production)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Chat Endpoint

**POST** `/chat`

**Request:**
```json
{
  "user_message": "What's the interest rate in HK?"
}
```

**Response:**
```json
{
  "response": "The term deposit interest rate in Hong Kong...",
  "message_history": {
    "initial_user_message": "...",
    "tool_calls": [...],
    "tool_results": [...],
    "final_assistant_message": "..."
  }
}
```

### Health Check

**GET** `/`

Returns the web interface or API status.

## Next Steps

1. ✅ **Test basic functionality** - Try different question types
2. ✅ **Monitor tool usage** - Check console for tool calls
3. ✅ **Customize system prompt** - Adjust agent behavior in `main.py`
4. ✅ **Add more documents** - Expand knowledge base in Phase B
5. ✅ **Deploy to production** - Use production deployment options

## Support

If you encounter issues:
1. Check console output for error messages
2. Verify all prerequisites are met
3. Check file paths and permissions
4. Review `FALLBACK_BEHAVIOR.md` for agent behavior details
5. Review `INTEGRATION_GUIDE.md` for integration details

## Quick Reference

```bash
# Start server
uvicorn main:app --reload

# Build index (Phase B)
cd ..\CapstoneP_PhaseB_RAG
python rag_pipeline_custom_embeddings.py

# Test API
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"user_message\": \"What's the interest rate in HK?\"}"
```

Happy banking! 🏦

