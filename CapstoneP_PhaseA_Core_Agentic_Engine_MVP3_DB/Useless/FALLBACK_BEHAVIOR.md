# Fallback Behavior for Banking Queries

## Overview

When a banking-related query cannot be answered from the local banking knowledge base, the agent has a clear fallback strategy to ensure users still get helpful answers.

## Fallback Strategy

### 1. Primary: Local Knowledge Base Search

**First Step**: Agent uses `query_my_notes` to search local banking documents.

**What happens**:
- Query is converted to embedding
- FAISS index is searched for similar chunks
- Top-k results are returned with relevance scores

### 2. Evaluation of Results

The agent evaluates the results from `query_my_notes`:

**Good Results** (High/Medium Relevance):
- Results contain relevant information
- Distance scores indicate good matches
- Agent uses this information to answer

**Poor Results** (Low Relevance or Empty):
- Results are empty or irrelevant
- Distance scores indicate poor matches
- Results don't answer the question

### 3. Fallback: Web Search

**When to Fallback**:
- ✅ Results are empty (`has_results: false`)
- ✅ Results have low relevance (`has_relevant_results: false`)
- ✅ Results don't contain the answer
- ✅ Question asks for very recent/current information
- ✅ Question is about topics not in local documents

**Fallback Action**:
- Agent clearly states: "This information is not available in my local banking knowledge base"
- Agent uses `duckduckgo_search` to find current information
- Agent provides answer from web search results
- Agent cites web sources

## Example Scenarios

### Scenario 1: Information Not in Local KB

**User**: "What are the current mortgage rates in Singapore?"

**Agent Behavior**:
1. Calls `query_my_notes("mortgage rates Singapore")`
2. Gets results with low relevance or empty results
3. Detects: Information not in local KB (only has HK/China data)
4. States: "I don't have Singapore mortgage rates in my local knowledge base, which focuses on Hong Kong and China. Let me search for current information..."
5. Calls `duckduckgo_search("current mortgage rates Singapore 2024")`
6. Provides answer from web search

### Scenario 2: Very Recent Information

**User**: "What was the interest rate change announced yesterday?"

**Agent Behavior**:
1. Calls `query_my_notes("interest rate change recent")`
2. Gets results but they're from static documents (dated)
3. Detects: Question asks for very recent information
4. States: "My local knowledge base contains historical rates, but you're asking about a very recent change. Let me search for the latest information..."
5. Calls `duckduckgo_search("Hong Kong interest rate change yesterday 2024")`
6. Provides current information

### Scenario 3: Topic Not Covered

**User**: "What are the cryptocurrency regulations for banks?"

**Agent Behavior**:
1. Calls `query_my_notes("cryptocurrency regulations banks")`
2. Gets empty or irrelevant results
3. Detects: Topic not covered in banking documents
4. States: "This topic is not covered in my local banking knowledge base. Let me search for current information..."
5. Calls `duckduckgo_search("cryptocurrency regulations banks Hong Kong China")`
6. Provides answer from web

### Scenario 4: Information Found Locally

**User**: "What's the interest rate of term deposit in HK?"

**Agent Behavior**:
1. Calls `query_my_notes("term deposit interest rate Hong Kong")`
2. Gets highly relevant results with specific rates
3. Detects: Good match, information available
4. Provides answer directly from local knowledge base
5. No web search needed

## Response Format Indicators

The `query_my_notes` tool returns helpful indicators:

```json
{
  "query": "mortgage rates Singapore",
  "results": [],
  "count": 0,
  "has_results": false,
  "has_relevant_results": false,
  "message": "Limited or no relevant information found in local knowledge base. Consider using web search for current information."
}
```

The agent uses these indicators to decide on fallback.

## System Prompt Instructions

The system prompt explicitly instructs the agent:

1. **Try local first**: Always use `query_my_notes` for banking questions
2. **Evaluate results**: Check if results answer the question
3. **Be transparent**: Tell user if local KB doesn't have the answer
4. **Fallback gracefully**: Use web search when local KB is insufficient
5. **Cite sources**: Always mention where information comes from

## Benefits

✅ **Comprehensive Coverage**: Users get answers even if not in local KB
✅ **Transparency**: Users know when using local vs. web information
✅ **Accuracy**: Local KB used when available (more accurate)
✅ **Current Information**: Web search provides latest updates
✅ **User Trust**: Clear communication about data sources

## Configuration

### Adjusting Relevance Thresholds

In `banking_notes_tool.py`, you can adjust relevance thresholds:

```python
"relevance": "high" if distance < 1.0 else "medium" if distance < 2.0 else "low"
```

Lower thresholds = stricter relevance (more fallbacks)
Higher thresholds = looser relevance (fewer fallbacks)

### Customizing Fallback Messages

Edit the system prompt in `main.py` to customize how the agent communicates fallback behavior.

## Testing Fallback Behavior

### Test Cases

1. **Not in KB**: Ask about banking in countries not covered (Singapore, Taiwan, etc.)
2. **Recent Info**: Ask about "today's rates" or "latest changes"
3. **New Topics**: Ask about topics not in documents (crypto, new regulations)
4. **In KB**: Ask standard questions (should use local KB)

### Expected Behavior

- ✅ Local KB questions → Use local KB, no fallback
- ✅ Not in KB questions → Use local KB first, then fallback to web
- ✅ Recent info questions → Use local KB first, then fallback to web
- ✅ Clear communication about data sources

## Monitoring

Check console output to see:
1. Which tool is called first
2. Results from `query_my_notes`
3. Decision to fallback (if any)
4. Web search queries made
5. Final answer sources

This helps verify fallback behavior is working correctly.

