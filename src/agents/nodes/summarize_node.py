"""
Summarize Node - Smart Summarization Worker
Uses Gatekeeper + LLM 120B for efficient review analysis
Only calls LLM for reviews that actually need deep analysis
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

# Import smart summarizer
try:
    from src.analytics.smart_summarizer import get_summarizer, smart_summarize
    SMART_SUMMARIZER_AVAILABLE = True
except ImportError:
    SMART_SUMMARIZER_AVAILABLE = False

# Fallback LLM for general summarization
llm = ChatOpenAI(
    api_key=os.getenv("MEGALLM_API_KEY"),
    base_url=os.getenv("MEGALLM_BASE_URL"),
    model=os.getenv("MEGALLM_MODEL"),
    temperature=0.2,
    streaming=False,
    max_tokens=800
)

BATCH_SUMMARIZE_PROMPT = """You are a Review Analyst. Summarize the key insights from these customer reviews.

DATA SUMMARY:
{data_summary}

SAMPLE REVIEWS (showing {sample_count} of {total_count}):
{sample_reviews}

TASK: Provide a structured summary with:

1. OVERVIEW
- Total reviews analyzed
- Sentiment breakdown (positive/negative/neutral %)
- Overall customer satisfaction level

2. KEY THEMES
- Top 3 positive themes (what customers love)
- Top 3 negative themes (main complaints)

3. CRITICAL ISSUES (if any)
- Issues requiring immediate attention
- Severity level

4. ACTIONABLE INSIGHTS
- 2-3 specific recommendations

Keep response concise and actionable. Use bullet points."""


def summarize_node(state):
    """
    Smart summarization node with Gatekeeper
    
    Flow:
    1. Check if data exists
    2. Detect user intent (negative analysis / sample / overview)
    3. Route to appropriate summarization method:
       - Smart Summarizer (Gatekeeper) for negative reviews
       - Batch LLM for overview
    
    Smart Summarizer Benefits:
    - Saves 70% LLM calls (skips short/neutral reviews)
    - Only analyzes reviews that need deep analysis
    - Uses keyword-based topic classification (no LLM cost)
    
    Args:
        state: Current agent state with messages
        
    Returns:
        Updated state with summary
    """
    from src.agents.tools import SESSION_DATA
    
    messages = state["messages"]
    last_user_message = next(
        (msg.content for msg in reversed(messages) if hasattr(msg, 'content')),
        ""
    ).lower()
    
    # STEP 1: Check data availability
    df = SESSION_DATA.get('default')
    
    if df is None:
        return {
            "messages": [AIMessage(content="**No Data Available**\n\nPlease upload a CSV file first so I can summarize reviews!")],
            "loop_step": 1,
            "current_node": "summarize"
        }
    
    # STEP 2: Verify sentiment column exists
    if 'ai_sentiment' not in df.columns:
        return {
            "messages": [AIMessage(content="**Data Error**\n\nSentiment column not found. Please re-upload the CSV file!")],
            "loop_step": 1,
            "current_node": "summarize"
        }
    
    # STEP 3: Detect text column
    text_col = None
    for col in df.columns:
        if 'review' in col.lower() or 'text' in col.lower() or 'content' in col.lower():
            text_col = col
            break
    
    if text_col is None:
        # Fallback: try first object column
        object_cols = df.select_dtypes(include=['object']).columns
        if len(object_cols) > 0:
            text_col = object_cols[0]
        else:
            return {
                "messages": [AIMessage(content="**Text Column Not Found**\n\nUnable to find a column containing review text in the data.")],
                "loop_step": 1,
                "current_node": "summarize"
            }
    
    # STEP 4: Detect user intent
    wants_negative = any(w in last_user_message for w in [
        'negative', 'xau', 'te', 'complaint', 'van de', 'issue', 
        'problem', 'khieu nai', 'phan nan'
    ])
    wants_sample = any(w in last_user_message for w in [
        'sample', 'vi du', 'example', 'chi tiet', 'detail'
    ])
    
    # STEP 5: Route to appropriate summarization method
    try:
        if wants_negative and SMART_SUMMARIZER_AVAILABLE:
            # Smart analyze negative reviews (uses Gatekeeper)
            response_text = _analyze_negative_reviews(df, text_col)
        elif wants_sample and SMART_SUMMARIZER_AVAILABLE:
            # Smart analyze sample reviews
            response_text = _analyze_sample_reviews(df, text_col)
        else:
            # General overview summarization (batch LLM)
            response_text = _generate_overview(df, text_col)
    except Exception as e:
        # Fallback on error
        response_text = f"""**Summarization Error**

An error occurred: {str(e)}

Please try again or use the Analyst node to view detailed statistics."""
    
    return {
        "messages": [AIMessage(content=response_text)],
        "loop_step": 1,
        "current_node": "summarize"
    }


def _analyze_negative_reviews(df, text_col: str, limit: int = 10) -> str:
    """Analyze negative reviews with smart summarizer"""
    summarizer = get_summarizer()
    
    # Filter negative reviews
    negative_df = df[df['ai_sentiment'] == 'negative'].head(limit)
    
    if len(negative_df) == 0:
        return "No negative reviews found in the data."
    
    results = []
    for _, row in negative_df.iterrows():
        text = str(row[text_col])
        result = summarizer.analyze_review(text, 'negative')
        results.append(result.to_dict())
    
    # Format output
    output_lines = [
        f"## ANALYSIS OF {len(results)} NEGATIVE REVIEWS",
        f"(LLM called only for {summarizer.stats['llm_calls']} reviews requiring deep analysis)",
        ""
    ]
    
    for i, r in enumerate(results, 1):
        output_lines.append(f"### Review {i}")
        if r.get('main_issue'):
            output_lines.append(f"- Main Issue: {r['main_issue']}")
        if r.get('issue_detail'):
            output_lines.append(f"- Details: {r['issue_detail']}")
        if r.get('severity'):
            output_lines.append(f"- Severity: {r['severity']}")
        if r.get('tags'):
            output_lines.append(f"- Tags: {', '.join(r['tags'])}")
        if r.get('summary'):
            output_lines.append(f"- Summary: {r['summary']}")
        output_lines.append("")
    
    # Stats
    stats = summarizer.get_stats()
    output_lines.append(f"---\nStats: {stats['llm_calls']} LLM calls, Skip rate: {stats.get('skip_rate', 'N/A')}")
    
    return "\n".join(output_lines)


def _analyze_sample_reviews(df, text_col: str, limit: int = 5) -> str:
    """Analyze sample reviews from each sentiment category"""
    summarizer = get_summarizer()
    
    results_by_sentiment = {}
    
    for sentiment in ['negative', 'neutral', 'positive']:
        sentiment_df = df[df['ai_sentiment'] == sentiment].head(limit)
        results = []
        
        for _, row in sentiment_df.iterrows():
            text = str(row[text_col])
            result = summarizer.analyze_review(text, sentiment)
            results.append(result.to_dict())
        
        results_by_sentiment[sentiment] = results
    
    # Format output
    output_lines = ["## SAMPLE REVIEW ANALYSIS", ""]
    
    for sentiment, results in results_by_sentiment.items():
        output_lines.append(f"### {sentiment.upper()} ({len(results)} reviews)")
        
        for r in results:
            if r.get('category') == 'skip_short':
                output_lines.append(f"  - [SKIP] Too short")
            elif r.get('category') == 'skip_neutral':
                output_lines.append(f"  - [SKIP] No issues found")
            else:
                tags = ', '.join(r.get('tags', [])) if r.get('tags') else 'N/A'
                output_lines.append(f"  - Tags: [{tags}]")
                if r.get('summary'):
                    output_lines.append(f"    {r['summary'][:100]}...")
        
        output_lines.append("")
    
    stats = summarizer.get_stats()
    output_lines.append(f"---\nTotal: {stats['total']} reviews, LLM calls: {stats['llm_calls']}, Skip: {stats.get('skip_rate', 'N/A')}")
    
    return "\n".join(output_lines)


def _generate_overview(df, text_col: str) -> str:
    """Generate overview summary using LLM"""
    total = len(df)
    
    # Sentiment distribution
    sentiment_counts = df['ai_sentiment'].value_counts()
    sentiment_dist = {
        'positive': sentiment_counts.get('positive', 0),
        'negative': sentiment_counts.get('negative', 0),
        'neutral': sentiment_counts.get('neutral', 0)
    }
    
    # Sample reviews for context
    samples = []
    for sentiment in ['negative', 'positive', 'neutral']:
        sample_df = df[df['ai_sentiment'] == sentiment].head(3)
        for _, row in sample_df.iterrows():
            text = str(row[text_col])[:200]
            samples.append(f"[{sentiment.upper()}] {text}...")
    
    data_summary = f"""
- Total reviews: {total:,}
- Positive: {sentiment_dist['positive']:,} ({sentiment_dist['positive']/total*100:.1f}%)
- Negative: {sentiment_dist['negative']:,} ({sentiment_dist['negative']/total*100:.1f}%)
- Neutral: {sentiment_dist['neutral']:,} ({sentiment_dist['neutral']/total*100:.1f}%)
"""
    
    prompt = BATCH_SUMMARIZE_PROMPT.format(
        data_summary=data_summary,
        sample_count=len(samples),
        total_count=total,
        sample_reviews="\n".join(samples)
    )
    
    response = llm.invoke([
        SystemMessage(content="You are a data analyst. Provide concise, actionable insights."),
        HumanMessage(content=prompt)
    ])
    
    return response.content
