# LangChain Integration Flow Diagram

## Overview
This document visualizes the LangChain integration architecture in `langchain_agents.py`, showing how tools, agents, and fallback mechanisms work together.

---

## Architecture Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LANGCHAIN INTEGRATION FLOW                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│  LangChain Tools │
│  (langchain_tools.py)
├─────────────────┤
│ • multi_search   │
│ • query_my_notes │
└────────┬─────────┘
         │
         │ get_langchain_tools()
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 1: AGENT CREATION                                │
│                    create_agent_executor()                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐          │
│  │   ChatOpenAI │      │  System      │      │  LangChain   │          │
│  │   (get_llm())│ ────▶│  Prompt      │ ────▶│  Tools       │          │
│  │              │      │  (from       │      │  (from       │          │
│  │ • base_url   │      │   prompts)   │      │   tools)     │          │
│  │ • api_key    │      │              │      │              │          │
│  │ • model      │      │              │      │              │          │
│  └──────────────┘      └──────────────┘      └──────────────┘          │
│         │                      │                      │                  │
│         └──────────────────────┼──────────────────────┘                  │
│                                │                                         │
│                                ▼                                         │
│                    ┌───────────────────────┐                           │
│                    │   create_agent()       │                           │
│                    │   (LangChain 1.2.0)    │                           │
│                    │                        │                           │
│                    │  Input:                │                           │
│                    │  • model: ChatOpenAI   │                           │
│                    │  • system_prompt       │                           │
│                    │  • tools: [tools]      │                           │
│                    │                        │                           │
│                    │  Output:              │                           │
│                    │  • CompiledStateGraph │                           │
│                    └───────────┬───────────┘                           │
│                                │                                         │
│                                ▼                                         │
│                    ┌───────────────────────┐                           │
│                    │   Banking Agent       │                           │
│                    │   (Agent Executor)    │                           │
│                    └───────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
         │
         │ get_banking_agent()
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 2: AGENT INVOCATION                              │
│                    invoke_banking_agent()                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  User Input                                                               │
│  ┌─────────────────┐                                                     │
│  │ "What's the     │                                                     │
│  │  interest rate?"│                                                     │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           │ Convert to LangChain Messages                                │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │ [HumanMessage]  │                                                     │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           │ agent.invoke({"messages": messages}, config)                 │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────┐             │
│  │         PRIMARY PATH: LangChain Agent                 │             │
│  │                                                         │             │
│  │  ┌──────────────────────────────────────────────┐     │             │
│  │  │  Agent Processing                             │     │             │
│  │  │                                               │     │             │
│  │  │  1. LLM decides if tool needed               │     │             │
│  │  │  2. If yes → Call LangChain Tool             │     │             │
│  │  │  3. Tool executes (multi_search/query_notes)│     │             │
│  │  │  4. Results returned to LLM                  │     │             │
│  │  │  5. LLM generates final response             │     │             │
│  │  └──────────────────────────────────────────────┘     │             │
│  │                                                         │             │
│  │  ┌──────────────────────────────────────────────┐     │             │
│  │  │  Tool Execution Flow                        │     │             │
│  │  │                                               │     │             │
│  │  │  query_my_notes → banking_notes_tool.py     │     │             │
│  │  │  multi_search → multi_search.py             │     │             │
│  │  └──────────────────────────────────────────────┘     │             │
│  │                                                         │             │
│  │  Response: {messages: [...], state: {...}}           │             │
│  └──────────────────────────────────────────────────────┘             │
│           │                                                              │
│           │ ✅ Success?                                                  │
│           │                                                              │
│           ├───────────── YES ──────────────┐                            │
│           │                                 │                            │
│           ▼                                 ▼                            │
│  ┌─────────────────┐            ┌──────────────────────┐             │
│  │ Extract Response│            │   ERROR HANDLING      │             │
│  │                 │            │                       │             │
│  │ • Find AI msg   │            │  Check error type:    │             │
│  │ • Extract text  │            │  • Internal Server   │             │
│  │ • Return result │            │    Error?             │             │
│  └────────┬────────┘            │  • Other errors?      │             │
│           │                      └──────────┬───────────┘             │
│           │                                 │                            │
│           │                                 │ "Internal Server Error"    │
│           │                                 ▼                            │
│           │                      ┌──────────────────────┐             │
│           │                      │   FALLBACK PATH      │             │
│           │                      │   Direct OpenAI      │             │
│           │                      │   Client            │             │
│           │                      └──────────┬─────────┘             │
│           │                                   │                        │
│           │                                   ▼                        │
│           │                      ┌──────────────────────┐             │
│           │                      │  openai.OpenAI()       │             │
│           │                      │                       │             │
│           │                      │  • Same setup as     │             │
│           │                      │    main.py            │             │
│           │                      │  • base_url:          │             │
│           │                      │    space.ai-builders  │             │
│           │                      │  • api_key:           │             │
│           │                      │    SECOND_MIND_API_KEY │             │
│           │                      │  • proxy settings     │             │
│           │                      └──────────┬─────────┘             │
│           │                                   │                        │
│           │                                   ▼                        │
│           │                      ┌──────────────────────┐             │
│           │                      │  Convert Messages    │             │
│           │                      │                       │             │
│           │                      │  LangChain → OpenAI  │             │
│           │                      │  format              │             │
│           │                      └──────────┬─────────┘             │
│           │                                   │                        │
│           │                                   ▼                        │
│           │                      ┌──────────────────────┐             │
│           │                      │  chat.completions    │             │
│           │                      │  .create()           │             │
│           │                      │                       │             │
│           │                      │  • model: "gpt-5"    │             │
│           │                      │  • messages: [...]  │             │
│           │                      │  • max_tokens: 4000  │             │
│           │                      └──────────┬─────────┘             │
│           │                                   │                        │
│           │                                   ▼                        │
│           │                      ┌──────────────────────┐             │
│           │                      │  Extract Response     │             │
│           │                      │                       │             │
│           │                      │  response.choices[0]  │             │
│           │                      │  .message.content     │             │
│           │                      └──────────┬─────────┘             │
│           │                                   │                        │
│           └───────────────────────────────────┼────────────────────┘
│                                                 │
│                                                 │
│                                                 ▼
│                                    ┌──────────────────────┐
│                                    │  Final Response      │
│                                    │                      │
│                                    │  {                    │
│                                    │    "output": "...",   │
│                                    │    "messages": [...], │
│                                    │    "state": {...},    │
│                                    │    "success": true    │
│                                    │  }                    │
│                                    └───────────────────────┘
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. **LangChain Tools** (`langchain_tools.py`)
- **multi_search**: Web search using multiple providers (SearXNG, Tavily)
- **query_my_notes**: Banking knowledge base search (FAISS-based)
- Both wrapped as `StructuredTool` with Pydantic input schemas

### 2. **Agent Creation** (`create_agent_executor()`)
- **Inputs**:
  - `ChatOpenAI` LLM instance (configured with API endpoint)
  - System prompt (from `langchain_prompts.py`)
  - LangChain tools (from `get_langchain_tools()`)
- **Process**: Uses `create_agent()` from LangChain 1.2.0
- **Output**: `CompiledStateGraph` (the agent executor)

### 3. **Agent Invocation** (`invoke_banking_agent()`)
- **Primary Path**: 
  - Invokes agent with `{"messages": messages}`
  - Agent processes request, may call tools, returns response
- **Fallback Path**:
  - Triggered on "Internal Server Error"
  - Uses direct `openai.OpenAI` client (same as `main.py`)
  - Bypasses LangChain wrapper to avoid format incompatibility

### 4. **Error Handling & Fallback**
- **Condition**: "Internal Server Error" from LangChain agent
- **Reason**: LangChain's `create_agent()` formats tool-calling requests in a way the API endpoint doesn't support
- **Solution**: Direct OpenAI client call with identical setup to `main.py`

---

## Key Design Decisions

1. **Tool Integration**: Tools are wrapped as `StructuredTool` for type safety and LLM schema generation
2. **Fallback Mechanism**: Ensures reliability when LangChain agent fails due to API compatibility
3. **Message Format**: Converts between LangChain message objects and OpenAI dict format
4. **Error Resilience**: Graceful degradation to direct API calls when agent wrapper fails

---

## Data Flow Summary

```
User Input
    ↓
LangChain Messages (HumanMessage)
    ↓
Agent Invocation
    ↓
[SUCCESS] → Extract Response → Return Result
    ↓
[FAILURE - Internal Server Error]
    ↓
Fallback: Direct OpenAI Client
    ↓
Convert Messages to OpenAI Format
    ↓
API Call (chat.completions.create)
    ↓
Extract Response → Return Result
```

---

## File Dependencies

```
langchain_agents.py
    ├── langchain_tools.py (tools)
    ├── langchain_prompts.py (system prompt)
    ├── banking_notes_tool.py (query_my_notes implementation)
    ├── multi_search.py (multi_search implementation)
    └── main.py (fallback reference implementation)
```

---

## API Endpoint Configuration

- **Base URL**: `https://space.ai-builders.com/backend/v1`
- **API Key**: `SECOND_MIND_API_KEY` (environment variable)
- **Model**: `gpt-5`
- **Proxy**: Configured via `get_proxy()` function

---

*Generated for presentation of LangChain integration architecture*

