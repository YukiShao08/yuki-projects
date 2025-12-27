# Banking Notes Tool Integration Guide

## Overview

The `query_my_notes` tool has been added to your FastAPI application. This tool allows the agent to search through your banking documents knowledge base using vector search.

## What Was Added

1. **New Tool**: `query_my_notes` - Searches banking documents using FAISS vector index
2. **New Module**: `banking_notes_tool.py` - Contains the tool implementation
3. **Updated**: `main.py` - Integrated the tool into the agent workflow

## How It Works

### Tool Functionality

- **Loads FAISS Index**: Reads `my_notes.index` from Phase B project
- **Vector Search**: Uses embeddings API to convert queries to vectors
- **Retrieval**: Finds most relevant document chunks
- **Returns Results**: JSON with ranked results and source information

### Agent Behavior

The agent will:
1. **Automatically detect** banking-related questions
2. **Use `query_my_notes` FIRST** for banking queries
3. **Formulate targeted queries** based on the question
4. **Adjust queries** if initial results don't fully answer
5. **Use web search** only for non-banking information

## Setup

### 1. Install Dependencies

```bash
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseA_Core_Agentic_Engine
pip install -r requirements.txt
```

### 2. Ensure Index Exists

Make sure you've built the FAISS index in Phase B:
```bash
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseB_RAG
python rag_pipeline_custom_embeddings.py
```

This creates `my_notes.index` and `my_notes.index.metadata.pkl`

### 3. Verify Path

The tool looks for the index at:
```
C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseB_RAG\my_notes.index
```

If your index is in a different location, edit `banking_notes_tool.py`:
```python
# In get_banking_notes_tool() function
index_path = Path(r"YOUR_PATH_HERE\my_notes.index")
```

## Usage

### Example Queries

The agent will automatically use the tool for questions like:

- "What's the interest rate of term deposit in HK?"
- "What's the loan interest rate in China?"
- "What is the minimum deposit for a term deposit?"
- "What are the mortgage rates for first-time buyers?"
- "What is the deposit insurance coverage in China?"

### Testing

1. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

2. Open the web interface at `http://localhost:8000`

3. Ask a banking question:
   - "What's the interest rate of term deposit in HK?"
   - The agent should automatically use `query_my_notes`

4. Check the console output for tool calls and results

## Tool Schema

```python
QUERY_MY_NOTES_TOOL = {
    "type": "function",
    "function": {
        "name": "query_my_notes",
        "description": "Search your personal banking knowledge base...",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string..."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of top results...",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    }
}
```

## Response Format

The tool returns JSON in this format:

```json
{
  "query": "term deposit interest rate Hong Kong",
  "results": [
    {
      "rank": 1,
      "text": "HKD Term Deposits: 1 Month 3.25%, 12 Months 4.00%...",
      "score": 0.123,
      "source": "data/banking_documents/hk_term_deposit_rates.md"
    },
    ...
  ],
  "count": 3
}
```

## Agent Workflow

1. **User asks**: "What's the interest rate of term deposit in HK?"

2. **Agent decides**: This is a banking question → use `query_my_notes`

3. **Agent formulates query**: "term deposit interest rate Hong Kong"

4. **Tool executes**: Searches FAISS index, returns top 3 results

5. **Agent analyzes results**: Extracts relevant information

6. **Agent responds**: Provides answer based on retrieved documents

7. **If needed**: Agent can make follow-up queries with adjusted search terms

## Troubleshooting

### "Index not found" Error

- **Check**: Index exists at the expected path
- **Solution**: Run the RAG pipeline in Phase B to create the index
- **Verify**: Both `my_notes.index` and `my_notes.index.metadata.pkl` exist

### "API Error" When Querying

- **Check**: Internet connection and API key
- **Solution**: Verify embeddings API is accessible
- **Check**: API key is correct in `banking_notes_tool.py`

### Tool Not Being Used

- **Check**: System prompt mentions banking knowledge base
- **Check**: Tool is in the tools list (check console output)
- **Solution**: Ask more specific banking questions

### Slow Performance

- **First query**: Takes time to load index (one-time)
- **Subsequent queries**: Should be fast
- **If still slow**: Check embeddings API response time

## Customization

### Change Index Path

Edit `banking_notes_tool.py`:
```python
def get_banking_notes_tool():
    # Change this path
    index_path = Path(r"YOUR_CUSTOM_PATH\my_notes.index")
```

### Adjust Default top_k

Edit the tool schema in `main.py`:
```python
"top_k": {
    "default": 5,  # Change from 3 to 5
    ...
}
```

### Modify System Prompt

Edit the system message in `/chat` endpoint:
```python
"content": "You are a helpful banking assistant... [customize here]"
```

## Integration with Evaluation

You can test the tool with your evaluation datasets:

```python
# In Phase B project
from evaluate_rag_pipeline import RAGEvaluator
from banking_notes_tool import BankingNotesQueryTool

tool = BankingNotesQueryTool(index_path="my_notes.index")
# Use tool.query() for testing
```

## Next Steps

1. ✅ Install dependencies
2. ✅ Build index in Phase B
3. ✅ Start FastAPI server
4. ✅ Test with banking questions
5. ✅ Monitor tool usage in console
6. ✅ Adjust queries based on results

## Notes

- The tool is **lazy-loaded** - only initialized when first used
- The tool is **automatically added** to tools list if index exists
- The agent is **instructed to use it first** for banking questions
- Multiple queries can be made in one conversation if needed

