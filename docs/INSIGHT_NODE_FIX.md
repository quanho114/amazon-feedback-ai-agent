# Insight Node Data Context Fix

## Problem
The Insight Node was not receiving statistical data context from previous nodes (Sentiment/Analyst), resulting in generic insights without data-backed observations.

## Root Cause
The `AgentState` did not have a shared field for passing analysis data between nodes. Each node operated in isolation without sharing computed statistics.

## Solution
Implemented a shared `analysis_data` field in the state that allows nodes to pass statistical context to downstream nodes.

## Changes Made

### 1. State Definition (`src/agents/state.py`)
Added `analysis_data` field to `AgentState`:
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    loop_step: Annotated[int, operator.add]
    data_info: dict
    current_node: str
    analysis_data: dict  # NEW: Shared analysis context
```

### 2. Sentiment Node (`src/agents/nodes/sentiment_node.py`)
Modified to populate `analysis_data` with sentiment statistics:
```python
analysis_data = {
    "total_reviews": total,
    "sentiment_counts": {
        "positive": int(sentiment_counts.get('positive', 0)),
        "negative": int(sentiment_counts.get('negative', 0)),
        "neutral": int(sentiment_counts.get('neutral', 0))
    },
    "sentiment_distribution": sentiment_dist
}

return {
    "messages": [response],
    "loop_step": 1,
    "current_node": "sentiment",
    "analysis_data": analysis_data  # NEW
}
```

### 3. Analyst Node (`src/agents/nodes/analyst_node.py`)
Modified to populate `analysis_data` with basic statistics:
```python
sentiment_counts = df['ai_sentiment'].value_counts()
analysis_data = {
    "total_reviews": len(df),
    "sentiment_counts": {
        "positive": int(sentiment_counts.get('positive', 0)),
        "negative": int(sentiment_counts.get('negative', 0)),
        "neutral": int(sentiment_counts.get('neutral', 0))
    }
}

return {
    "messages": [AIMessage(content=final_response)],
    "loop_step": 1,
    "current_node": "analyst",
    "analysis_data": analysis_data  # NEW
}
```

### 4. Insight Node (`src/agents/nodes/insight_node.py`)
Modified to read and use `analysis_data` from state:
```python
# Get analysis data from state
analysis_data = state.get("analysis_data", {})

# Build data context if available
data_context = ""
if analysis_data:
    total = analysis_data.get("total_reviews", 0)
    sentiment_counts = analysis_data.get("sentiment_counts", {})
    sentiment_dist = analysis_data.get("sentiment_distribution", {})
    
    data_context = f"""
DATA CONTEXT:
- Total Reviews: {total:,}
- Positive: {sentiment_counts.get('positive', 0):,} ({sentiment_dist.get('positive', 'N/A')})
- Negative: {sentiment_counts.get('negative', 0):,} ({sentiment_dist.get('negative', 'N/A')})
- Neutral: {sentiment_counts.get('neutral', 0):,} ({sentiment_dist.get('neutral', 'N/A')})

"""

# Construct prompt with data context
user_query = f"{data_context}USER QUERY: {last_user_message}"
```

### 5. API Initialization (`api.py`)
Updated initial state to include `analysis_data`:
```python
inputs = {
    "messages": messages,
    "loop_step": 0,
    "data_info": {},
    "current_node": "",
    "analysis_data": {}  # NEW
}
```

## Data Flow

```
User Query
    ↓
Supervisor (routes to worker)
    ↓
Sentiment/Analyst Node
    ↓
Computes statistics → Populates analysis_data in state
    ↓
Insight Node
    ↓
Reads analysis_data from state → Generates data-backed insights
    ↓
Response with statistical context
```

## Benefits

1. **Data-Driven Insights**: Insight Node now has access to actual statistics
2. **Consistent Context**: All nodes share the same data snapshot
3. **Extensible**: Easy to add more metrics to `analysis_data`
4. **No Breaking Changes**: Backward compatible with existing nodes

## Testing

Created test script: `scripts/test_insight_data_context.py`

Run test:
```bash
cd amazon-feedback-ai-agent
python scripts/test_insight_data_context.py
```

Expected output:
- Sentiment node populates analysis_data
- Insight node receives and uses the data
- Response includes numerical references to the data

## Future Enhancements

Potential additions to `analysis_data`:
- `rating_distribution`: Rating breakdown
- `top_keywords`: Most frequent terms
- `time_trends`: Temporal patterns
- `bad_reviews_sample`: Sample of negative reviews for context
- `kpi_metrics`: Custom KPIs (NPS, CSAT, etc.)

## Files Modified

1. `src/agents/state.py` - Added analysis_data field
2. `src/agents/nodes/sentiment_node.py` - Populates analysis_data
3. `src/agents/nodes/analyst_node.py` - Populates analysis_data
4. `src/agents/nodes/insight_node.py` - Reads analysis_data
5. `api.py` - Initializes analysis_data in state
6. `scripts/test_insight_data_context.py` - Test script (NEW)
7. `docs/INSIGHT_NODE_FIX.md` - This documentation (NEW)
