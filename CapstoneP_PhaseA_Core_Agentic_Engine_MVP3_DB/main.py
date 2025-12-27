from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
from pathlib import Path
from groq import Groq
from openai import OpenAI
from openai import APIConnectionError, APIError
import httpx
from dotenv import load_dotenv
from duckduckgo_search import DDGS
import json
import time
from threading import Lock
from banking_notes_tool import query_my_notes
from multi_search import multi_search
from Database import create_chat, get_all_chats_db, save_message, chat_exists, get_messages   

# Fix encoding issues on Windows
if sys.platform == 'win32':
    try:
        # Set stdout encoding to UTF-8 to handle Unicode characters
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7 fallback
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Request throttling for DuckDuckGo searches
_last_search_time = 0
_search_lock = Lock()
_min_search_interval = 10  # Minimum seconds between search requests (increased to reduce rate limiting)

# Load environment variables from .env file (explicit path to avoid CWD issues)
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# Simple debug print to confirm env loading (does NOT print the key itself)
if os.getenv("SECOND_MIND_API_KEY"):
    print("SECOND_MIND_API_KEY is set from .env")
else:
    print("SECOND_MIND_API_KEY is NOT set – check .env location and contents")

app = FastAPI(title="Hello World API with AI", version="1.0.0")

# Mount static files directory
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# The groq_client is used in the /hello endpoint to optionally enhance responses with AI, which is simple and free,called Llama3-70b-8192 model.
# Initialize Groq client with proxy support (for Clash/China network)
# Get API key from https://console.groq.com/
# Set GROQ_API_KEY environment variable or it will use None
# Proxy settings: HTTP_PROXY or PROXY_PORT (defaults to 7890 for Clash)

groq_client = None
try:
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        # Get proxy settings - support both HTTP_PROXY env var and PROXY_PORT
        http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        proxy_port = os.getenv("PROXY_PORT", "7890")  # Default to Clash port 7890
        
        # Configure proxy - Clash typically uses http://127.0.0.1:7890
        if not http_proxy:
            http_proxy = f"http://127.0.0.1:{proxy_port}"
        if not https_proxy:
            https_proxy = http_proxy
        
        # Set environment variables for httpx to use (Groq uses httpx internally)
        os.environ["HTTP_PROXY"] = http_proxy
        os.environ["HTTPS_PROXY"] = https_proxy
        
        # Create httpx client with proxy for explicit control
        proxy_client = httpx.Client(
            proxies={
                "http://": http_proxy,
                "https://": https_proxy
            },
            timeout=30.0
        )
        
        # Initialize Groq with custom httpx client
        # Note: Groq client may accept http_client parameter, if not, env vars will be used
        try:
            groq_client = Groq(
                api_key=api_key,
                http_client=proxy_client
            )
        except TypeError:
            # If http_client parameter not supported, use default (env vars will work)
            groq_client = Groq(api_key=api_key)
        
        print(f"Groq client initialized with proxy: {http_proxy}")
except Exception as e:
    print(f"Warning: Groq client not initialized: {e}")

#openai_client with more features, called gpt-5, which is more powerful and expensive.
# Initialize OpenAI-compatible client for Second Mind API
# Custom base URL: https://space.ai-builders.com/backend/v1
openai_client = None


def get_openai_client() -> Optional[OpenAI]:
    """
    Lazily initialize and return the OpenAI-compatible client.
    This reads SECOND_MIND_API_KEY from the environment each time it's needed,
    so changes to .env are picked up after a reload.
    """
    global openai_client

    # If already created, just reuse it
    if openai_client is not None:
        return openai_client

    # Debug info about .env and environment
    print(f"DEBUG: Looking for .env at: {env_path} (exists={env_path.exists()})")

    second_mind_api_key = os.getenv("SECOND_MIND_API_KEY")
    if not second_mind_api_key:
        print("DEBUG: SECOND_MIND_API_KEY is NOT set in environment.")
        return None

    # Optional: configure proxy for OpenAI client via environment variables
    # Only use proxy if explicitly set in environment variables
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    
    # Only set proxy if it's explicitly configured (don't force proxy usage)
    if http_proxy or https_proxy:
        if http_proxy:
            os.environ["HTTP_PROXY"] = http_proxy
            print(f"DEBUG: Using HTTP_PROXY: {http_proxy}")
        if https_proxy:
            os.environ["HTTPS_PROXY"] = https_proxy
            print(f"DEBUG: Using HTTPS_PROXY: {https_proxy}")
    else:
        # Explicitly remove proxy settings if not needed
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        print("DEBUG: No proxy configured, using direct connection")

    try:
        # Create httpx client with better SSL and timeout settings
        http_client = httpx.Client(
            timeout=60.0,  # 60 second timeout
            verify=True,  # Verify SSL certificates
            follow_redirects=True
        )
        
        client = OpenAI(
            api_key=second_mind_api_key,
            base_url="https://space.ai-builders.com/backend/v1",
            http_client=http_client
        )
        openai_client = client
        print("DEBUG: OpenAI-compatible client initialized successfully.")
        return client
    except Exception as e:
        print(f"DEBUG: Failed to initialize OpenAI-compatible client: {e}")
        import traceback
        print(traceback.format_exc())
        return None


class InputRequest(BaseModel):
    input: str


class ChatRequest(BaseModel):
    user_message: str
    chat_id: Optional[str] = None


# DuckDuckGo Search Tool Function
def duckduckgo_search(query: str, max_results: int = 3) -> str:
    """
    Perform a web search using DuckDuckGo with retry logic for rate limiting.
    Includes request throttling to reduce rate limit issues.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5, max: 10)
    
    Returns:
        JSON string containing search results with title, URL, and snippet
    """
    global _last_search_time
    
    # Request throttling: ensure minimum time between searches
    with _search_lock:
        current_time = time.time()
        time_since_last = current_time - _last_search_time
        
        if time_since_last < _min_search_interval:
            wait_time = _min_search_interval - time_since_last
            print(f"Throttling: waiting {wait_time:.2f} seconds before search...")
            time.sleep(wait_time)
        
        _last_search_time = time.time()
    
    # Limit max_results to reasonable number
    max_results = min(max(1, max_results), 10)
    
    # Retry logic for rate limiting
    max_retries = 3
    retry_delay = 5  # seconds (increased to handle rate limits better)
    initial_delay = 2  # Small delay before first request to avoid immediate rate limits
    
    # Add initial delay to space out requests
    if max_retries > 0:
        time.sleep(initial_delay)
    
    for attempt in range(max_retries):
        try:
            # Add exponential backoff delay (except on first attempt)
            if attempt > 0:
                delay = retry_delay * (2 ** (attempt - 1))  # Exponential backoff: 5s, 10s, 20s, 40s 80s, each retry raised longer.
                print(f"Retrying search after {delay} seconds (attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                
                # Check if we got results
                # Empty results might indicate rate limiting, s
                # 
                # o retry with delay
                if not results:
                    if attempt < max_retries - 1:
                        delay = retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"No results returned, may be rate limited. Waiting {delay} seconds before retry (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(delay)
                        continue  # Retry if no results
                    return json.dumps({
                        "query": query,
                        "results": [],
                        "count": 0,
                        "error": "No results found",
                        "message": "No search results found after multiple attempts. This may be due to rate limiting or the query not matching any content. Please wait a moment and try again."
                    }, indent=2)
                
                # Format results for the AI
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", "")[:300]  # Limit snippet length
                    })
                
                return json.dumps({
                    "query": query,
                    "results": formatted_results,
                    "count": len(formatted_results)
                }, indent=2)
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for rate limiting indicators (expanded list)
            rate_limit_keywords = [
                "rate limit", "too many requests", "429", "blocked", 
                "temporarily unavailable", "try again", "wait", "throttle",
                "quota", "limit exceeded", "slow down"
            ]
            
            if any(keyword in error_msg for keyword in rate_limit_keywords):
                if attempt < max_retries - 1:
                    # Will retry with backoff - add extra delay for rate limits
                    delay = retry_delay * (2 ** attempt) + 5  # Extra 5 seconds for rate limits
                    print(f"Rate limit detected, waiting {delay} seconds before retry (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                    continue
                else:
                    return json.dumps({
                        "error": "Rate limit exceeded",
                        "query": query,
                        "message": "DuckDuckGo has rate-limited this request after multiple attempts. Please wait 1-2 minutes before trying again. For weather information, consider using dedicated weather APIs or services like weather.com, accuweather.com, or bbc.com/weather."
                    }, indent=2)
            else:
                # Other errors - return immediately
                return json.dumps({
                    "error": f"Search failed: {str(e)}",
                    "query": query,
                    "message": f"An error occurred during the search: {str(e)}"
                }, indent=2)
    
    # If all retries failed
    return json.dumps({
        "error": "Search failed after multiple attempts",
        "query": query,
        "message": "Unable to complete the search after several attempts. This may be due to rate limiting or network issues."
    }, indent=2)


# Define the tool schema for OpenAI function calling
DUCKDUCKGO_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "duckduckgo_search",
        "description": "Search the web using multiple search providers (DuckDuckGo, SearXNG, Tavily) with automatic fallback to get current information, facts, news, or any web content. This tool automatically tries different providers if one is rate-limited, making it more reliable than single-provider search. Use this tool when you need to find recent information, verify facts, or search for content that may not be in your training data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string. Be specific and clear about what you're searching for."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return. Default is 5, maximum is 10.",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    }
}

#This defines a tool the AI mobel can call during a conversation. e.g. pass to the "tools" parameter in the OpenAI API call.
QUERY_MY_NOTES_TOOL = {
    "type": "function",
    "function": {
        "name": "query_my_notes",
        "description": "Search your personal banking knowledge base containing banking documents about interest rates, loan terms, deposit information, and banking policies for Hong Kong and China. Use this tool when the user asks questions about banking products, interest rates, loans, deposits, mortgages, or banking policies. This tool searches through local banking documents and can provide specific, accurate information from your knowledge base. Always use this tool FIRST for banking-related questions before using web search.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string. Be specific about what banking information you're looking for. Examples: 'term deposit interest rate Hong Kong', 'loan rates China', 'minimum deposit amount', 'mortgage rates first-time buyers'. You can formulate multiple targeted queries if needed to find comprehensive information."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of top results to return from the knowledge base. Default is 3, maximum is 10. Use higher values (5-10) when you need more comprehensive information or when initial results don't fully answer the question.",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    }
}


@app.get("/")
async def root():
    """Serve the chat web application"""
    index_path = BASE_DIR / "static" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Hello, World! API is running. Use /hello endpoint with POST request."}


@app.post("/hello")
async def hello_world(request: InputRequest):
    """
    Endpoint that returns a JSON object with a message including the input.
    If Groq API is configured, it will enhance the message using AI.
    """
    user_input = request.input
    
    # Basic response
    message = f"Hello, World {user_input}"
    
    # If Groq is available, enhance with AI (optional)
    if groq_client:
        try:
            # Use a free coding model similar to gpt-5-codex
            # Using llama3-70b-8192 or mixtral-8x7b-32768 (both free on Groq)
            completion = groq_client.chat.completions.create(
                model="llama3-70b-8192",  # Free, fast coding model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Keep responses concise."
                    },
                    {
                        "role": "user",
                        "content": f"Say hello world with this input: {user_input}"
                    }
                ],
                temperature=0.7, #temperature is a parameter that controls the randomness of the model's output.Good balance: consistent enough for most tasks, with some variety
                max_tokens=100 #max_tokens is a parameter that controls the maximum number of tokens in the model's output.
            )
            ai_response = completion.choices[0].message.content
            message = f"Hello, World {user_input} (AI: {ai_response})"
        except Exception as e:
            # If AI fails, fall back to basic message
            print(f"AI enhancement failed: {e}")
            pass
    
    return {"message": message}


@app.get("/hello/{input_text}")
async def hello_world_get(input_text: str):
    """
    GET endpoint that returns a JSON object with a message including the input.
    """
    return {"message": f"Hello, World {input_text}"}


@app.post("/chat") #register a founcation as a rount handler.
async def chat(request: ChatRequest):
    """
    Chat endpoint that calls OpenAI-compatible API (Second Mind) with web search capability.
    Accepts a user_message and returns the assistant's response.
    The agent can automatically use DuckDuckGo search when it needs current information.
    """
    client = get_openai_client()
    if not client:
        raise HTTPException(
            status_code=500,
            detail=(
                "OpenAI-compatible client not initialized. "
                "Ensure .env is in the same folder as main.py, "
                "contains SECOND_MIND_API_KEY, and the server has been restarted."
            ),
        )
    
    try:
        # Store initial user message for logging
        initial_user_message = request.user_message

        chat_id = request.chat_id
        if not chat_id:
            chat_id = str(int(time.time() * 1000))
        
        if not chat_exists(chat_id):
            title = initial_user_message[:50] if len(initial_user_message) > 50 else initial_user_message
            create_chat(chat_id, title)
            print(f"✅ Created new chat: {chat_id} with title: {title}")
        
        # Initialize conversation messages with system prompt
        messages = [
            {
                "role": "system",
                "content": """You are a helpful banking assistant with access to a personal banking knowledge base and web search. 

RESPONSE STYLE:
- Be concise and direct. Provide the essential information without unnecessary elaboration.
- For factual questions, give the answer first, then cite sources.
- Avoid lengthy explanations unless the user asks for details.

BANKING QUESTIONS HANDLING:
1. When users ask questions about banking products, interest rates, loans, deposits, mortgages, or banking policies for Hong Kong or China, ALWAYS use the query_my_notes tool FIRST to search your local banking documents.

2. After receiving results from query_my_notes:
   - If the results contain relevant information that answers the question: Provide a concise, direct answer using that information. Include the specific data (e.g., interest rates, terms) clearly. You can make additional query_my_notes calls with different search terms if you need more specific details.
   - If the results are empty, irrelevant, or don't contain the answer: Briefly state that the information is not available in your local knowledge base, then use duckduckgo_search to find current information from the web. This handles cases where:
     * The question is about banking topics not covered in your documents
     * The question asks for very recent/current information that may have changed
     * The question is about banking topics outside Hong Kong/China
     * The question requires real-time data or news

3. For non-banking questions: Use duckduckgo_search directly. Provide concise answers - give the key information first, then cite sources if needed.

4. Always be transparent: If you're using web search because local knowledge didn't have the answer, mention this briefly to the user.

5. Always cite your sources and provide specific information from the knowledge base when available."""
            }
        ]
        
        # Load conversation history from database if this is a continuing conversation
        # Load BEFORE saving current message to avoid duplicates
        previous_messages = get_messages(chat_id)
        if previous_messages:
            print(f"📜 Loading {len(previous_messages)} previous messages for chat {chat_id}")
            # Add previous messages to conversation
            # Filter out messages with role "tool calls" as those are internal logging
            for msg in previous_messages:
                if msg["role"] in ["user", "assistant"]:  # Only include user and assistant messages
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Add the current user message
        messages.append({
            "role": "user",
            "content": request.user_message
        })
        
        # Save the current user message to database (after loading history to avoid duplicates)
        save_message(chat_id, initial_user_message, "user")
        print(f"Saved user message to chat {chat_id}")
        
        # Store tool calls and results for logging
        all_tool_calls = []
        all_tool_results = []
        
        # Maximum number of tool call iterations to prevent infinite loops
        max_iterations = 3
        iteration = 0
        
        while iteration < max_iterations:
            # Prepare tools list (include banking notes tool if available)
            tools = [DUCKDUCKGO_SEARCH_TOOL]
            # Add banking notes tool if index is available (lightweight check - no initialization)
            try:
                from banking_notes_tool import banking_notes_tool_available
                if banking_notes_tool_available():
                    tools.append(QUERY_MY_NOTES_TOOL)
            except Exception as e:
                print(f"Warning: Could not check banking notes tool availability: {e}")
            
            # Call the chat completion API with tools
            completion = client.chat.completions.create(
                model="gpt-5",
                messages=messages,
                tools=tools,
                tool_choice="auto",  # Let the model decide when to use tools
                max_tokens=4000  # Allow longer responses
            )
            
            message = completion.choices[0].message
            
            # If no tool calls, we're done - print history and return the response
            if not message.tool_calls:
                final_response = message.content or "I apologize, but I couldn't generate a response."
                
                # Print message history before returning (with encoding safety)
                try:
                    print("\n" + "=" * 80)
                    print("MESSAGE HISTORY")
                    print("=" * 80)
                    print(f"\n1. INITIAL USER MESSAGE:")
                    print(f"   {initial_user_message}")
                    print(f"\n2. ASSISTANT TOOL CALLS:")
                    if all_tool_calls:
                        for i, tool_call in enumerate(all_tool_calls, 1):
                            print(f"   Tool Call {i}:")
                            print(f"     Function: {tool_call.get('function', {}).get('name', 'N/A')}")
                            try:
                                args_str = json.dumps(tool_call.get('function', {}).get('arguments', {}), indent=6, ensure_ascii=False)
                                print(f"     Arguments: {args_str}")
                            except Exception as e:
                                print(f"     Arguments: [Error encoding: {str(e)}]")
                    else:
                        print("   No tool calls were made.")
                    print(f"\n3. TOOL RESULTS:")
                    if all_tool_results:
                        for i, tool_result in enumerate(all_tool_results, 1):
                            print(f"   Tool Result {i}:")
                            try:
                                result_data = json.loads(tool_result.get('content', '{}'))
                                result_str = json.dumps(result_data, indent=6, ensure_ascii=False)
                                print(f"     {result_str}")
                            except Exception as e:
                                content = tool_result.get('content', 'N/A')
                                # Safely encode content for printing
                                try:
                                    safe_content = content[:200] if len(content) > 200 else content
                                    print(f"     {safe_content}")
                                except:
                                    print(f"     [Content encoding error: {str(e)}]")
                    else:
                        print("   No tool results.")
                    print(f"\n4. FINAL ASSISTANT MESSAGE:")
                    # Safely print final response
                    try:
                        print(f"   {final_response}")
                    except UnicodeEncodeError:
                        # Fallback: encode to ASCII with error handling
                        safe_response = final_response.encode('ascii', 'ignore').decode('ascii')
                        print(f"   {safe_response}")
                    print("=" * 80 + "\n")
                except Exception as e:
                    # If printing fails, log error but don't break the response
                    print(f"\n[Warning: Could not print message history due to encoding error: {str(e)}]\n")
                
                # Build message history for API response
                # Parse tool results from JSON strings to objects for better readability
                formatted_tool_results = []
                for tool_result in all_tool_results:
                    formatted_result = {
                        "tool_call_id": tool_result.get("tool_call_id"),
                        "name": tool_result.get("name"),
                        "content": tool_result.get("content")
                    }
                    # Try to parse JSON content for better formatting
                    try:
                        formatted_result["parsed_content"] = json.loads(tool_result.get("content", "{}"))
                    except:
                        formatted_result["parsed_content"] = None
                    formatted_tool_results.append(formatted_result)
                
                message_history = {
                    "initial_user_message": initial_user_message,
                    "tool_calls": all_tool_calls,
                    "tool_results": formatted_tool_results,
                    "final_assistant_message": final_response
                }
                
                # Save assistant's response to database
                save_message(chat_id, final_response, "assistant")
                print(f"Saved assistant response to chat {chat_id}")
                
                return {
                    "response": final_response,
                    "chat_id": chat_id,  # Return chat_id for frontend to track conversation
                    "message_history": message_history
                }
            
            # Add assistant's message to conversation with tool calls
            assistant_message = {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in message.tool_calls
                ]
            }
            messages.append(assistant_message)
            
            # Store tool calls for logging
            for tc in message.tool_calls:
                all_tool_calls.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
            
            # Execute tool calls
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "duckduckgo_search":
                    # Execute the search (now uses multi-provider with fallback)
                    search_query = function_args.get("query", "")
                    max_results = function_args.get("max_results", 5)
                    # Get Tavily API key from environment if available
                    tavily_key = os.getenv("TAVILY_API_KEY")
                    search_results = multi_search(search_query, max_results, tavily_key)
                    
                    # Store tool result for logging
                    tool_result = {
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": search_results
                    }
                    all_tool_results.append(tool_result)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": search_results
                    })
                
                elif function_name == "query_my_notes":
                    # Execute banking notes query
                    notes_query = function_args.get("query", "")
                    top_k = function_args.get("top_k", 3)
                    notes_results = query_my_notes(notes_query, top_k=top_k)
                    
                    # Store tool result for logging
                    tool_result = {
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": notes_results
                    }
                    all_tool_results.append(tool_result)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": notes_results
                    })
                
                else:
                    # Unknown tool
                    error_result = json.dumps({"error": f"Unknown tool: {function_name}"})
                    tool_result = {
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": error_result
                    }
                    all_tool_results.append(tool_result)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": error_result
                    })
            
            iteration += 1
        
        # If we've reached max iterations, get a final response
        final_completion = client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            max_tokens=4000  # Allow longer responses
        )
        
        final_response = final_completion.choices[0].message.content or "I apologize, but I couldn't complete the request."
        
        # Print message history before returning (with encoding safety)
        try:
            print("\n" + "=" * 80)
            print("MESSAGE HISTORY")
            print("=" * 80)
            print(f"\n1. INITIAL USER MESSAGE:")
            print(f"   {initial_user_message}")
            print(f"\n2. ASSISTANT TOOL CALLS:")
            if all_tool_calls:
                for i, tool_call in enumerate(all_tool_calls, 1):
                    print(f"   Tool Call {i}:")
                    print(f"     Function: {tool_call.get('function', {}).get('name', 'N/A')}")
                    try:
                        args = json.loads(tool_call.get('function', {}).get('arguments', '{}'))
                        args_str = json.dumps(args, indent=6, ensure_ascii=False)
                        print(f"     Arguments: {args_str}")
                    except Exception as e:
                        print(f"     Arguments: [Error encoding: {str(e)}]")
            else:
                print("   No tool calls were made.")
            print(f"\n3. TOOL RESULTS:")
            if all_tool_results:
                for i, tool_result in enumerate(all_tool_results, 1):
                    print(f"   Tool Result {i}:")
                    try:
                        result_data = json.loads(tool_result.get('content', '{}'))
                        result_str = json.dumps(result_data, indent=6, ensure_ascii=False)
                        print(f"     {result_str}")
                    except Exception as e:
                        content = tool_result.get('content', 'N/A')
                        try:
                            if len(content) > 500:
                                safe_content = content[:500]
                                print(f"     {safe_content}...")
                            else:
                                print(f"     {content}")
                        except UnicodeEncodeError:
                            safe_content = content.encode('ascii', 'ignore').decode('ascii')
                            print(f"     {safe_content}")
            else:
                print("   No tool results.")
            print(f"\n4. FINAL ASSISTANT MESSAGE:")
            # Safely print final response
            try:
                print(f"   {final_response}")
            except UnicodeEncodeError:
                # Fallback: encode to ASCII with error handling
                safe_response = final_response.encode('ascii', 'ignore').decode('ascii')
                print(f"   {safe_response}")
            print("=" * 80 + "\n")
        except Exception as e:
            # If printing fails, log error but don't break the response
            print(f"\n[Warning: Could not print message history due to encoding error: {str(e)}]\n")
        
        # Build message history for API response
        # Parse tool results from JSON strings to objects for better readability
        formatted_tool_results = []
        for tool_result in all_tool_results:
            formatted_result = {
                "tool_call_id": tool_result.get("tool_call_id"),
                "name": tool_result.get("name"),
                "content": tool_result.get("content")
            }
            # Try to parse JSON content for better formatting
            try:
                formatted_result["parsed_content"] = json.loads(tool_result.get("content", "{}"))
            except:
                formatted_result["parsed_content"] = None
            formatted_tool_results.append(formatted_result)
        
        message_history = {
            "initial_user_message": initial_user_message,
            "tool_calls": all_tool_calls,
            "tool_results": formatted_tool_results,
            "final_assistant_message": final_response
        }

        # Save assistant's response to database
        save_message(chat_id, final_response, "assistant")
        print(f"Saved assistant response to chat {chat_id}")
        
        return {
            "response": final_response,
            "chat_id": chat_id,  # Return chat_id for frontend to track conversation
            "message_history": message_history
        }
    
    except APIConnectionError as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Connection Error in /chat endpoint:")
        print(error_traceback)
        error_detail = (
            f"Failed to connect to AI API. This is usually a network or proxy issue.\n"
            f"Error: {str(e)}\n\n"
            f"Possible solutions:\n"
            f"1. Check your internet connection\n"
            f"2. If using a proxy, verify it's running and configured correctly\n"
            f"3. Check firewall/antivirus settings\n"
            f"4. Try disabling proxy by removing HTTP_PROXY/HTTPS_PROXY environment variables"
        )
        raise HTTPException(
            status_code=503,  # Service Unavailable - more appropriate for connection errors
            detail=error_detail
        )
    except APIError as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ API Error in /chat endpoint:")
        print(error_traceback)
        raise HTTPException(
            status_code=500,
            detail=f"AI API error: {str(e)}"
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Unexpected Error in /chat endpoint:")
        print(error_traceback)
        raise HTTPException(
            status_code=500,
            detail=f"Error calling chat API: {str(e)}"
        )

@app.get("/messages/{chat_id}")
async def get_chat_messages(chat_id: str):
    try:
            messages=get_messages(chat_id)
            return {"messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting chat messages: {str(e)}"
        )

@app.get("/all_chats")
async def get_all_chats():
    try:
        chats=get_all_chats_db()
        return {"chats": chats}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting all chats: {str(e)}"
        )



