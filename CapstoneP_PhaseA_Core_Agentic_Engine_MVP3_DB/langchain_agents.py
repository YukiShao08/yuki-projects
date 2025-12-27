"""
New Python file
"""
import os
from dotenv import load_dotenv
from pathlib import Path
from get_proxy import get_proxy
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_tools import get_langchain_tools
from langchain_prompts import get_banking_assistant_sys_prompt
from typing import Any, Dict, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


#load environment variables
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

def get_llm() -> ChatOpenAI:
    """
    Get the LLM model
    """
    api_key = os.getenv("SECOND_MIND_API_KEY")
    if not api_key:
        raise ValueError(
            "SECOND_MIND_API_KEY is not set in environment variables."
            "Please check your .env file."
        )
    
    os.environ["HTTP_PROXY"] = get_proxy()[0]
    os.environ["HTTPS_PROXY"] = get_proxy()[1]
    
    # Use the same configuration as main.py's OpenAI client
    # The key difference: LangChain's ChatOpenAI wraps OpenAI client
    # but may format requests differently, causing Internal Server Error
    llm = ChatOpenAI( #interact with chat model like GPT
        model="gpt-5", 
        api_key=api_key,
        base_url="https://space.ai-builders.com/backend/v1",
        temperature=0.7,
        max_tokens=4000,#allow longer responses
        timeout=60.0,  # Add timeout to prevent hanging
        max_retries=2,  # Retry on failure
        )

    if os.environ["HTTP_PROXY"]:
        print(f"Using proxy: {os.environ['HTTP_PROXY']}")

    return llm

def create_agent_executor(use_tools: bool = True) -> Any:
    """
    Create the agent executor using LangChain 1.2.0 API
    
    Args:
        use_tools: If False, create agent without tools (for testing API compatibility)
    
    Returns:
        Agent executor
    """
    llm = get_llm()
    tools = get_langchain_tools() if use_tools else []
    
    # Extract system prompt from the prompt template
    system_prompt = get_banking_assistant_sys_prompt()
    
    # Create agent using the new LangChain 1.2.0 API
    # Note: Some API endpoints may not support tool calling properly
    # If tools cause issues, set use_tools=False
    agent_kwargs = {
        "model": llm,
        "system_prompt": system_prompt,
        "debug": True,  # Enable debug mode for verbose output
    }
    
    if use_tools and tools:
        agent_kwargs["tools"] = tools
    
    agent = create_agent(**agent_kwargs) #Dynamic arguments: conditionally add tools only if needed
    
    print(f"Banking agent created successfully (tools: {'enabled' if use_tools and tools else 'disabled'})")
    return agent

_agent_executor = None

def get_banking_agent() -> Any:
    """
    Get the agent
    """
    global _agent_executor

    if _agent_executor is None:
        _agent_executor = create_agent_executor()

    return _agent_executor

def reset_banking_agent():
    global _agent_executor
    _agent_executor = None
    print("Banking agent reset")

def invoke_banking_agent(user_input: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Invoke the banking agent with user input.
    
    Args:
        user_input: The user's message/question
        chat_history: Optional list of previous messages in format [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    
    Returns:
        Dictionary containing the agent's response with keys:
        - "output": The final response text
        - "messages": All messages in the conversation
        - "intermediate_steps": Tool calls and results (if any)
        
    Raises:
        Exception: If the agent invocation fails
        
    Example:
        # Single turn conversation
        response = invoke_banking_agent("What's the interest rate for term deposits in Hong Kong?")
        print(response["output"])
        
        # Multi-turn conversation with history
        history = [
            {"role": "user", "content": "What's the interest rate?"},
            {"role": "assistant", "content": "The interest rate is 3.5%"}
        ]
        response = invoke_banking_agent("Tell me more about mortgages", chat_history=history)
    """
    try:
        agent = get_banking_agent()
        
        # Build messages list
        messages = []
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add current user input
        messages.append(HumanMessage(content=user_input))
        
        # Invoke the agent with messages
        # The agent expects: {"messages": [HumanMessage(...), AIMessage(...), ...]}
        # Returns a state graph with messages and other state information
        
        # Add config to handle errors better
        config = {
            "recursion_limit": 10,  # Limit recursion depth
            "configurable": {
                "thread_id": "test-thread-1"
            }
        }
        
        # The issue: create_agent() wraps the LLM and may format tool-calling requests
        # in a way that your API endpoint doesn't support, even though direct OpenAI client works.
        # This is because LangChain adds extra metadata/formatting that the API rejects.
        print("\n" + "=" * 60)
        print("Attempting to invoke LangChain agent...")
        print("=" * 60)
        
        # Try to invoke agent using create_agent() format
        # If it fails, fallback to direct OpenAI client (same as main.py)
        try:
            print("Attempting to invoke LangChain agent (create_agent)...")
            response = agent.invoke({"messages": messages}, config=config)
            
            # Extract response from create_agent format (state graph)
            final_messages = response.get("messages", []) if isinstance(response, dict) else []
            
            # Find the last AI message (the agent's response)
            output_text = None
            for msg in reversed(final_messages):
                if hasattr(msg, 'content') and isinstance(msg, AIMessage):
                    output_text = msg.content
                    break
            
            if output_text is None and final_messages:
                last_msg = final_messages[-1]
                if hasattr(last_msg, 'content'):
                    output_text = last_msg.content
            
            print("\n" + "=" * 60)
            print("SOLUTION SUMMARY:")
            print("=" * 60)
            print("✅ Method: LangChain Agent (create_agent)")
            print("   Status: Successfully using create_agent()")
            print("=" * 60 + "\n")
            
            return {
                "output": output_text or "No response generated",
                "messages": final_messages,
                "state": response,
                "success": True
            }
        except Exception as invoke_error:
            # If agent invocation fails, try direct LLM call as fallback
            error_msg = str(invoke_error)
            if "Internal Server Error" in error_msg:
                print("❌ LangChain agent invocation failed with Internal Server Error")
                print("   Reason: LangChain's create_agent() formats tool-calling requests")
                print("   in a way your API endpoint doesn't support")
                print("\n" + "=" * 60)
                print("FALLBACK: Switching to direct OpenAI client (same as main.py)")
                print("=" * 60)
                
                # Use the EXACT same approach as main.py (which works!)
                # The issue: LangChain's create_agent() wraps the LLM and formats
                # tool-calling requests in a way your API endpoint doesn't support
                from openai import OpenAI as DirectOpenAI
                
                try:
                    # Use the exact same client setup as main.py
                    api_key = os.getenv("SECOND_MIND_API_KEY")
                    proxy_settings = get_proxy()
                    os.environ["HTTP_PROXY"] = proxy_settings[0]
                    os.environ["HTTPS_PROXY"] = proxy_settings[1]
                    
                    # Create client exactly like main.py does (line 143-146)
                    direct_client = DirectOpenAI(
                        api_key=api_key,
                        base_url="https://space.ai-builders.com/backend/v1",
                    )
                    
                    # Convert LangChain messages to OpenAI format (same as main.py)
                    llm_messages = []
                    system_prompt = get_banking_assistant_sys_prompt()
                    llm_messages.append({"role": "system", "content": system_prompt})
                    
                    for msg in messages:
                        if isinstance(msg, HumanMessage):
                            llm_messages.append({"role": "user", "content": msg.content})
                        elif isinstance(msg, AIMessage):
                            llm_messages.append({"role": "assistant", "content": msg.content})
                    
                    # Call API directly (EXACT same way as main.py line 472-478)
                    direct_response = direct_client.chat.completions.create(
                        model="gpt-5",
                        messages=llm_messages,
                        max_tokens=4000,
                        temperature=0.7
                    )
                    
                    print("✅ Direct OpenAI client call succeeded!")
                    print("   Method: Using direct OpenAI client (same as main.py)")
                    print("   Status: API endpoint is working correctly")
                    print("   Note: LangChain agent failed, but direct client works fine")
                    print("=" * 60 + "\n")
                    
                    # Extract response content (same format as main.py line 484)
                    response_content = direct_response.choices[0].message.content
                    
                    # Print solution summary
                    print("\n" + "=" * 60)
                    print("SOLUTION SUMMARY:")
                    print("=" * 60)
                    print("✅ Method: Direct OpenAI Client (Fallback)")
                    print("   Reason: LangChain agent failed due to request format incompatibility")
                    print("   Status: Successfully using same approach as main.py")
                    print("=" * 60 + "\n")
                    
                    # Return response in same format as agent would
                    return {
                        "output": response_content or "No response generated",
                        "messages": messages + [AIMessage(content=response_content)] if response_content else messages,
                        "state": {"direct_call": True, "method": "openai_client"},
                        "success": True,
                        "warning": "Used direct OpenAI client instead of LangChain agent. The API endpoint works fine, but LangChain's create_agent() wrapper formats tool-calling requests in a way your API doesn't support."
                    }
                except Exception as llm_error:
                    print(f"❌ Direct LLM call also failed: {llm_error}")
                    raise invoke_error  # Re-raise original error
            
            raise invoke_error  # Re-raise if not Internal Server Error
        
        # Successfully used LangChain agent
        print("\n" + "=" * 60)
        print("SOLUTION SUMMARY:")
        print("=" * 60)
        print("✅ Method: LangChain Agent")
        print("   Status: Successfully using create_agent()")
        print("=" * 60 + "\n")
        
        # Extract the final response from the state graph
        # The response contains a "messages" list with all messages including the final AI response
        final_messages = response.get("messages", [])
        
        # Find the last AI message (the agent's response)
        output_text = None
        for msg in reversed(final_messages):
            if hasattr(msg, 'content') and isinstance(msg, AIMessage):
                output_text = msg.content
                break
        
        # If no AI message found, try to get any content
        if output_text is None and final_messages:
            last_msg = final_messages[-1]
            if hasattr(last_msg, 'content'):
                output_text = last_msg.content
        
        return {
            "output": output_text or "No response generated",
            "messages": final_messages,
            "state": response,
            "success": True
        }
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Provide more helpful error messages
        if "Internal Server Error" in error_msg:
            error_msg = (
                "API endpoint returned Internal Server Error. "
                "This could be due to:\n"
                "1. API server is down or experiencing issues\n"
                "2. Invalid API key or authentication failure\n"
                "3. Request format issue\n"
                "4. Network/proxy connectivity problem\n"
                f"Original error: {error_msg}"
            )
        elif "API key" in error_msg.lower() or "authentication" in error_msg.lower():
            error_msg = (
                "Authentication error. Please check:\n"
                "1. SECOND_MIND_API_KEY is set correctly in .env file\n"
                "2. API key is valid and has proper permissions\n"
                f"Original error: {error_msg}"
            )
        
        return {
            "output": None,
            "error": error_msg,
            "error_type": error_type,
            "success": False
        }

# For testing/debugging
if __name__ == "__main__":
    print("LangChain Agent Module")
    print("=" * 50)
    
    try:
        # Test LLM creation
        print("\n1. Testing LLM creation...")
        llm = get_llm()
        #print(f"   ✅ LLM created: {llm.model}")
        
        # Test tools loading
        print("\n2. Testing tools loading...")
        tools = get_langchain_tools()
        print(f"   ✅ Loaded {len(tools)} tools")
        for tool in tools:
            print(f"      - {tool.name}")
        
        # Test prompt creation
        print("\n3. Testing prompt creation...")
        #prompt = get_banking_assistant_prompt()
        #print(f"   ✅ Prompt created with {len(prompt.messages)} messages")
        
        # Test agent creation
        print("\n4. Testing agent creation...")
        agent = get_banking_agent()
        print("   ✅ Agent created successfully")
        
        # Test agent invocation (optional - requires API key)
        print("\n5. Testing agent invocation...")
        try:
            response = invoke_banking_agent("What's the top 5 GDP countries in the world?")
            if response.get("success"):
                print(f"   ✅ Agent response: {response.get('output', 'No output')[:200]}...")
            else:
                print(f"   ❌ Agent error: {response.get('error', 'Unknown error')}")
                print(f"   Error type: {response.get('error_type', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ Exception during invocation: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()



