"""
Analyst Node - Code Interpreter Worker
Performs numerical calculations using Python code execution
CRITICAL: Never let LLM calculate directly - always generate and execute code
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_experimental.tools import PythonAstREPLTool
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM - Fast deterministic
llm = ChatOpenAI(
    api_key=os.getenv("MEGALLM_API_KEY"),
    base_url=os.getenv("MEGALLM_BASE_URL"),
    model=os.getenv("MEGALLM_MODEL"),
    temperature=0,  # Deterministic for code
    streaming=False,  # Disable for speed
    max_tokens=400  # Limit code output
)

# Initialize Python REPL tool
python_tool = PythonAstREPLTool()

# Helper function for parsing ratings
HELPER_CODE = """
import re
def parse_rating(text):
    '''Extract numeric rating from text like "Rated 5 out of 5 stars"'''
    if pd.isna(text):
        return None
    match = re.search(r'Rated (\\d+) out of', str(text))
    return int(match.group(1)) if match else None

# Apply to Rating column if it's text
if 'Rating' in df.columns and df['Rating'].dtype == 'object':
    df['numeric_rating'] = df['Rating'].apply(parse_rating)
    df['Rating'] = df['numeric_rating']  # Replace with numeric
"""

ANALYST_PROMPT = """
You are a professional Data Analyst with Python programming skills.

CRITICAL RULES:
1. NEVER calculate manually with LLM
2. ALWAYS write Python code for calculations
3. If user asks for CHART → return JSON data for frontend

AVAILABLE DATA:
- DataFrame 'df' is already loaded in memory
- Special column: 'ai_sentiment' (positive/negative/neutral)

CHART WORKFLOW:
1. Tính toán data cần thiết
2. Gán vào biến 'chart_data' dạng dict với format:
   {
     "type": "pie|bar|line|scatter|area|radar|treemap|composed",
     "data": [...],  # List of dicts
     "title": "Tên chart",
     "xKey": "name",  # Optional: tên cột X axis
     "yKey": "value", # Optional: tên cột Y axis
     "zKey": "size",  # Optional: cho scatter 3D
     "series": [{"type": "bar", "dataKey": "col1"}, ...]  # For composed chart
   }

VÍ DỤ VẼ CHART:

1. PIE CHART - Distribution:
User: "Draw sentiment distribution chart"
```python
sentiment_counts = df['ai_sentiment'].value_counts()
chart_data = {
    "type": "pie",
    "data": [{"name": name, "value": int(count)} for name, count in sentiment_counts.items()],
    "title": "Sentiment Distribution"
}
```

2. SCATTER CHART - Correlation analysis:
User: "Draw scatter chart rating vs review length"
```python
chart_data = {
    "type": "scatter",
    "data": [{"x": row['Rating'], "y": len(str(row['Review']))} for i, row in df.head(200).iterrows()],
    "title": "Rating vs Review Length",
    "xKey": "x",
    "yKey": "y"
}
```

3. AREA CHART - Time series:
User: "Draw monthly trend"
```python
import pandas as pd
df['date'] = pd.to_datetime(df['Time'], errors='coerce')
trend = df.groupby(df['date'].dt.to_period('M')).size()
chart_data = {
    "type": "area",
    "data": [{"name": str(period), "value": int(count)} for period, count in trend.items()],
    "title": "Xu hướng Review theo Tháng",
    "xKey": "name",
    "yKey": "value"
}
```

4. RADAR CHART - Multi-dimensional comparison:
User: "Draw radar chart for sentiment analysis"
```python
metrics = {
    'Positive': int(len(df[df['ai_sentiment']=='positive'])),
    'Negative': int(len(df[df['ai_sentiment']=='negative'])),
    'Neutral': int(len(df[df['ai_sentiment']=='neutral']))
}
chart_data = {
    "type": "radar",
    "data": [{"name": k, "value": v} for k, v in metrics.items()],
    "title": "Multi-dimensional Sentiment Analysis"
}
```

5. TREEMAP - Hierarchical:
User: "Draw treemap for sentiment"
```python
chart_data = {
    "type": "treemap",
    "data": [{"name": name, "value": int(count)} for name, count in df['ai_sentiment'].value_counts().items()],
    "title": "Sentiment Distribution Treemap"
}
```

6. BAR CHART - Rating distribution:
User: "Show rating distribution"
```python
rating_counts = df['Rating'].value_counts().sort_index()
chart_data = {
    "type": "bar",
    "data": [{"name": f"{rating} stars", "value": int(count)} for rating, count in rating_counts.items()],
    "title": "Rating Distribution"
}
```

7. LINE CHART - Trend over time:
User: "Show review trends over time"
```python
df['Review Date'] = pd.to_datetime(df['Review Date'], errors='coerce')
daily_counts = df.groupby(df['Review Date'].dt.date).size()
chart_data = {
    "type": "line",
    "data": [{"name": str(date), "value": int(count)} for date, count in daily_counts.tail(30).items()],
    "title": "Review Volume (Last 30 Days)",
    "xKey": "name",
    "yKey": "value"
}
```

8. COMPOSED CHART - Sentiment + Volume:
User: "Show sentiment breakdown by rating"
```python
rating_sentiment = df.groupby(['Rating', 'ai_sentiment']).size().unstack(fill_value=0)
chart_data = {
    "type": "composed",
    "data": [{"name": f"{r}★", "positive": int(rating_sentiment.loc[r, 'positive']), 
              "negative": int(rating_sentiment.loc[r, 'negative'])} 
             for r in sorted(rating_sentiment.index)],
    "title": "Sentiment by Rating",
    "series": [
        {"type": "bar", "dataKey": "positive"},
        {"type": "bar", "dataKey": "negative"}
    ]
}
```

9. SCATTER - Review length vs Rating:
User: "Analyze review length impact on rating"
```python
sample = df.sample(min(500, len(df)))
chart_data = {
    "type": "scatter",
    "data": [{"x": len(str(row.get('Review Text', ''))), "y": row.get('Rating', 3)} 
             for _, row in sample.iterrows()],
    "title": "Review Length vs Rating",
    "xKey": "x",
    "yKey": "y"
}
```

10. AREA CHART - Cumulative reviews:
User: "Show cumulative review growth"
```python
df['Review Date'] = pd.to_datetime(df['Review Date'], errors='coerce')
daily = df.groupby(df['Review Date'].dt.date).size().cumsum()
chart_data = {
    "type": "area",
    "data": [{"name": str(date), "value": int(count)} for date, count in daily.tail(60).items()],
    "title": "Cumulative Review Growth"
}
chart_data = {
    "type": "composed",
    "data": [{"name": f"{r} sao", "count": int(row['Review']), "positive_pct": round(row['ai_sentiment'], 1)} for r, row in rating_stats.iterrows()],
    "title": "Reviews & Positive % theo Rating",
    "xKey": "name",
    "series": [{"type": "bar", "dataKey": "count"}, {"type": "line", "dataKey": "positive_pct"}]
}
```

CALCULATION EXAMPLE (NO CHART):
User: "How many positive reviews?"
Code: ```python
result = int(df['ai_sentiment'].value_counts()['positive'])
```

IMPORTANT:
- For charts → MUST assign to 'chart_data' variable
- For calculations only → assign to 'result' variable
- Code must be concise and accurate
"""


def analyst_node(state):
    """
    Code-based analyst node
    Generates Python code and executes it for accurate calculations
    
    Args:
        state: Current agent state with messages
        
    Returns:
        Updated state with calculation results
    """
    from src.agents.tools import SESSION_DATA
    
    messages = state["messages"]
    last_user_message = next(
        (msg.content for msg in reversed(messages) if hasattr(msg, 'content')),
        ""
    )
    
    # Get DataFrame from session first to provide context
    df = SESSION_DATA.get('default')
    
    if df is None:
        return {
            "messages": [AIMessage(content="**No Data Available**\n\nPlease upload a CSV file first!")],
            "loop_step": 1,
            "current_node": "analyst"
        }
    
    # Build data context
    data_context = f"""
**DataFrame 'df' is available with:**
- Rows: {len(df):,}
- Columns: {', '.join(df.columns.tolist())}
- Sentiment column: 'ai_sentiment' (positive/negative/neutral)
"""
    
    # Step 1: Ask LLM to generate Python code
    code_gen_messages = [
        SystemMessage(content=ANALYST_PROMPT),
        HumanMessage(content=f"{data_context}\n\n**Question:** {last_user_message}\n\nWrite Python code to answer. Return code only, no explanation.")
    ]
    
    code_response = llm.invoke(code_gen_messages)
    generated_code = code_response.content
    
    # Extract code from markdown if present
    if "```python" in generated_code:
        generated_code = generated_code.split("```python")[1].split("```")[0].strip()
    elif "```" in generated_code:
        generated_code = generated_code.split("```")[1].split("```")[0].strip()
    
    # Step 2: Execute the code
    try:
        # Create execution environment
        exec_globals = {
            'df': df,
            'pd': __import__('pandas'),
            'np': __import__('numpy'),
            're': __import__('re'),
            'result': None,
            'chart_data': None
        }
        
        # Execute helper code first (parse ratings if needed)
        try:
            exec(HELPER_CODE, exec_globals)
        except:
            pass  # Ignore if helper fails
        
        # Execute user code
        exec(generated_code, exec_globals)
        
        # Check if chart data was created
        if exec_globals.get('chart_data') is not None:
            import json
            chart_json = json.dumps(exec_globals['chart_data'], ensure_ascii=False)
            # Show chart only, hide code
            final_response = f"```json\n{chart_json}\n```"
        elif exec_globals.get('result') is not None:
            # Show result only, hide code
            final_response = f"{exec_globals['result']}"
        else:
            # No explicit result/chart_data variable
            final_response = f"Analysis completed successfully!"
        
    except Exception as e:
        final_response = f"Error: {str(e)}"
    
    # Prepare analysis data for other nodes
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
        "analysis_data": analysis_data
    }
