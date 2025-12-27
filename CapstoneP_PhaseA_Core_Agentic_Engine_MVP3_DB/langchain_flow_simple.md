# LangChain Integration Flow - Simplified

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGCHAIN INTEGRATION                        │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │ LangChain    │
                    │ Tools        │
                    │              │
                    │ • multi_search│
                    │ • query_notes│
                    └──────┬───────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │      Agent Creation                  │
        │  create_agent_executor()            │
        │                                      │
        │  ChatOpenAI + Tools + Prompt ────▶  │
        │  create_agent()                      │
        │                                      │
        │  Output: Banking Agent               │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │      Agent Invocation                │
        │  invoke_banking_agent()              │
        │                                      │
        │  User Input ──────────────────────▶  │
        │  agent.invoke()                      │
        └──────────────┬───────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
    ┌───────────────┐    ┌──────────────────┐
    │   SUCCESS     │    │   FAILURE         │
    │               │    │   (Internal       │
    │ Extract       │    │    Server Error)  │
    │ Response      │    │                   │
    │               │    │   ──────────────▶ │
    │ Return Result │    │   FALLBACK        │
    └───────────────┘    │   Direct OpenAI   │
                         │   Client          │
                         │   (same as main.py)│
                         │                   │
                         │   Return Result   │
                         └───────────────────┘
```

## Detailed Flow

### 1. Initialization Phase
```
Tools (langchain_tools.py)
    │
    ├─► multi_search_tool
    │   └─► Searches web (SearXNG, Tavily)
    │
    └─► query_my_notes_tool
        └─► Searches banking knowledge base (FAISS)
```

### 2. Agent Creation Phase
```
get_llm()
    │
    ├─► ChatOpenAI configured
    │   ├─► base_url: space.ai-builders.com
    │   ├─► model: gpt-5
    │   └─► proxy settings
    │
    ├─► get_langchain_tools()
    │   └─► Returns [multi_search_tool, query_my_notes_tool]
    │
    ├─► get_banking_assistant_sys_prompt()
    │   └─► Returns system prompt
    │
    └─► create_agent()
        └─► Returns CompiledStateGraph (Banking Agent)
```

### 3. Invocation Phase
```
User Input: "What's the interest rate?"
    │
    ├─► Convert to HumanMessage
    │
    ├─► agent.invoke({"messages": [HumanMessage(...)]})
    │
    ├─► [SUCCESS PATH]
    │   │
    │   ├─► Agent processes request
    │   ├─► May call tools (query_my_notes, multi_search)
    │   ├─► Tools execute and return results
    │   ├─► Agent generates final response
    │   └─► Return: {output, messages, state, success}
    │
    └─► [FAILURE PATH - Internal Server Error]
        │
        ├─► Catch exception
        ├─► Create direct OpenAI client (same as main.py)
        ├─► Convert messages to OpenAI format
        ├─► Call chat.completions.create()
        └─► Return: {output, messages, state, success, warning}
```

## Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **LangChain Tools** | Tool definitions (multi_search, query_my_notes) | `langchain_tools.py` |
| **ChatOpenAI** | LLM wrapper for LangChain | `get_llm()` in `langchain_agents.py` |
| **create_agent()** | Creates agent with tools and prompt | LangChain 1.2.0 API |
| **Banking Agent** | Compiled state graph that orchestrates tools | `get_banking_agent()` |
| **Fallback Client** | Direct OpenAI client when agent fails | `invoke_banking_agent()` |

## Error Handling Strategy

```
Primary: LangChain Agent
    │
    ├─► Success → Return response
    │
    └─► Failure (Internal Server Error)
        │
        └─► Fallback: Direct OpenAI Client
            │
            ├─► Same configuration as main.py
            ├─► Same API endpoint
            ├─► Same message format
            └─► Return response with warning
```

## Data Flow

```
Input: User Question
    ↓
LangChain Messages (HumanMessage)
    ↓
Agent Invocation
    ↓
[Decision Point]
    ├─► Tool Needed? → Execute Tool → Return to LLM
    └─► No Tool? → Generate Response
    ↓
Response Extraction
    ↓
Output: {output, messages, state, success}
```

## Fallback Mechanism

```
LangChain Agent Fails
    ↓
Error: "Internal Server Error"
    ↓
Reason: Request format incompatibility
    ↓
Solution: Direct OpenAI Client
    │
    ├─► Bypass LangChain wrapper
    ├─► Use native OpenAI format
    ├─► Same endpoint & configuration
    └─► Return response with warning flag
```

---

*This simplified diagram is designed for presentation purposes*

