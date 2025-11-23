# FastAPI Hello World Application

A minimal FastAPI web application with an endpoint that returns a JSON object with a message.

## Features

- FastAPI endpoint that returns `{"message": "Hello, World <input>"}`
- Optional AI enhancement using Groq (free tier) with models similar to gpt-5-codex
- Two endpoints:
  - `POST /hello` - Accepts JSON with `{"input": "your text"}`
  - `GET /hello/{input_text}` - Accepts input as path parameter

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Set up Groq API key for AI features:
   - Get a free API key from https://console.groq.com/
   - Create a `.env` file and add: `GROQ_API_KEY=your_key_here`
   - Or set environment variable: `export GROQ_API_KEY=your_key_here` (Windows: `set GROQ_API_KEY=your_key_here`)

3. (Optional) Configure proxy for China network (Clash for Windows):
   - The application automatically uses proxy port 7890 (Clash default) if available
   - To customize, set environment variables:
     - `PROXY_PORT=7890` (default, can be changed)
     - Or set `HTTP_PROXY=http://127.0.0.1:7890` and `HTTPS_PROXY=http://127.0.0.1:7890`
   - Windows PowerShell: `$env:HTTP_PROXY="http://127.0.0.1:7890"` and `$env:HTTPS_PROXY="http://127.0.0.1:7890"`
   - Windows CMD: `set HTTP_PROXY=http://127.0.0.1:7890` and `set HTTPS_PROXY=http://127.0.0.1:7890`

## Running the Server

### Development Mode (with auto-reload):
```bash
uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage Examples

### POST Request:
```bash
curl -X POST "http://localhost:8000/hello" -H "Content-Type: application/json" -d '{"input": "from FastAPI"}'
```

### GET Request:
```bash
curl "http://localhost:8000/hello/from%20FastAPI"
```

## Response Format

```json
{
  "message": "Hello, World <your_input>"
}
```

