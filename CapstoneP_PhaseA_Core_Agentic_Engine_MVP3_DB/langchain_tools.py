"""
New Python file
"""

import os
from typing import List
from langchain_core.tools import StructuredTool
from langchain_core.utils.pydantic import BaseModel, Field
from multi_search import multi_search
from banking_notes_tool import query_my_notes, get_banking_notes_tool, banking_notes_tool_available

# Pydantic input models for type safety and validation

class MultiSearchInput(BaseModel):
    """Input schema for Multi search tool"""
    query: str = Field(description="The search query string. Be specific and clear about what you're searching for.")
    max_results: int = Field(
        description="Maximum number of search results to return. Default is 5, maximum is 10.",
        default=5,
        ge=1,#greater than or equal to 1
        le=10#
    )

class BankingNotesQueryInput(BaseModel):
    """Input schema for Banking notes query tool"""
    query: str = Field(description="The search query string. Be specific about what banking information you're looking for. Examples: 'term deposit interest rate Hong Kong', 'loan rates China', 'minimum deposit amount', 'mortgage rates first-time buyers'. You can formulate multiple targeted queries if needed to find comprehensive information.")
    #split complex queries into several single query.
    top_k: int = Field(
        description="Number of top results to return from the knowledge base. Default is 3, maximum is 10. Use higher values (5-10) when you need more comprehensive information or when initial results don't fully answer the question.",
        default=3,#multiple result let the LLM cross-check and verify consistency,and the LLM also can combine inform from multiple sources.
        ge=1,
        le=10
    )

# Wrapper functions that match LangChain tool interface
def multi_search_wrapper(query: str, max_results: int = 5) -> str:
    """Wrapper function for the multi_search tool"""
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    return multi_search(query, max_results, tavily_api_key)

def query_my_notes_wrapper(query: str, top_k: int = 3) -> str:
    """Wrapper function for the query_my_notes tool"""
    return query_my_notes(query, top_k)

# LangChain tool definitions

multi_search_tool = StructuredTool.from_function(   
    func=multi_search_wrapper,
    name="multi_search",
    description=(
        "Search the web using multiple search providers (SearXNG, Tavily)"
        "with automatic fallback to get current information, facts, news, or any web content. "
        "This tool automatically tries different providers"
        "more reliable than single-provider search. Use this tool when you need to find recent "
        "information, verify facts, or search for content that may not be in your training data."
        ),
    args_schema=MultiSearchInput,
    return_direct=False#return the results directly to the LLM, rather than a JSON string.
)

query_my_notes_tool = StructuredTool.from_function(
    func=query_my_notes_wrapper,
    name="query_my_notes",
    description=(
        "Search your personal banking knowledge base containing banking documents about interest rates, loan terms, deposit information, and banking policies for Hong Kong and China. "
        "Use this tool when the user asks questions about banking products, interest rates, loans, deposits, mortgages, or banking policies. "
        "This tool searches through local banking documents and can provide specific, accurate information from your knowledge base. "
        "Always use this tool FIRST for banking-related questions before using web search."
    ),
    args_schema=BankingNotesQueryInput,
    return_direct=False
)

def get_langchain_tools() -> List[StructuredTool]:
    """Get all the LangChain tools"""

    tools= [multi_search_tool]

    try:
        if banking_notes_tool_available():
            tools.append(query_my_notes_tool)
            print("banking notes tool available")
        else:
            print("banking notes tool not available (index not found)")
    except Exception as e:
        print(f"Warning: Could not check banking notes tool availability: {e}")
        return tools

    return tools

if __name__ == "__main__":
    print("LangChain Tools Module")
    print("=" * 50)
    
    tools = get_langchain_tools()
    print(f"\nAvailable tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")
    
    print("\n✅ Tools module loaded successfully")  