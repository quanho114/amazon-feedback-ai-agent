"""
Sentiment Analysis Node - Emotion Analysis Worker
Extracts sentiment and specific pain points from reviews
Uses ML model (SVM 90% accuracy) for sentiment classification
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM - Fast config
llm = ChatOpenAI(
    api_key=os.getenv("MEGALLM_API_KEY"),
    base_url=os.getenv("MEGALLM_BASE_URL"),
    model=os.getenv("MEGALLM_MODEL"),
    temperature=0.1,  # Lower = faster
    streaming=False,  # Disable for speed
    max_tokens=500  # Limit output
)

SENTIMENT_PROMPT = """You are a Customer Sentiment Analysis Expert specializing in Amazon reviews.

MISSION:
1. Analyze overall sentiment distribution from the provided data
2. Identify key patterns and pain points
3. Provide actionable business insights

OUTPUT FORMAT - Clean text, NO JSON:

## CUSTOMER SENTIMENT ANALYSIS

### Overview
- Dominant sentiment: [Positive/Negative/Neutral]
- Positive: X% (X,XXX reviews)
- Negative: Y% (YYY reviews)  
- Neutral: Z% (ZZZ reviews)

### Assessment
[Brief 2-3 line analysis of overall customer satisfaction]

### Key Strengths
- [What customers love - specific point 1]
- [What customers love - specific point 2]

### Areas for Improvement
- [Main pain point 1 with impact]
- [Main pain point 2 with impact]

### Recommendations
1. [Specific, actionable recommendation 1]
2. [Specific, actionable recommendation 2]
3. [Specific, actionable recommendation 3]

IMPORTANT:
- Be data-driven and specific
- Focus on actionable insights
- Use plain text (no emoji icons)
- Keep it concise but comprehensive
"""


def sentiment_node(state):
    """
    Sentiment analysis node with ML model integration
    
    Flow:
    1. Check if data exists
    2. Calculate sentiment distribution (from ML model results)
    3. Generate insights using LLM
    4. Share analysis_data with other nodes
    
    Args:
        state: Current agent state with messages
        
    Returns:
        Updated state with sentiment analysis results and shared data
    """
    from src.agents.tools import SESSION_DATA
    
    messages = state["messages"]
    last_user_message = next(
        (msg.content for msg in reversed(messages) if hasattr(msg, 'content')),
        ""
    )
    
    # STEP 1: Check data availability
    df = SESSION_DATA.get('default')
    
    if df is None:
        return {
            "messages": [AIMessage(content="**No Data Available**\n\nPlease upload a CSV file first to analyze sentiment!")],
            "loop_step": 1,
            "current_node": "sentiment",
            "analysis_data": {}
        }
    
    # STEP 2: Verify sentiment column exists (from ML model)
    if 'ai_sentiment' not in df.columns:
        return {
            "messages": [AIMessage(content="**Data Error**\n\nSentiment column not found. Please re-upload CSV file!")],
            "loop_step": 1,
            "current_node": "sentiment",
            "analysis_data": {}
        }
    
    # STEP 3: Calculate sentiment distribution
    sentiment_counts = df['ai_sentiment'].value_counts()
    total = len(df)
    
    # Calculate percentages
    positive_count = int(sentiment_counts.get('positive', 0))
    negative_count = int(sentiment_counts.get('negative', 0))
    neutral_count = int(sentiment_counts.get('neutral', 0))
    
    sentiment_dist = {
        "positive": f"{positive_count / total * 100:.1f}%",
        "negative": f"{negative_count / total * 100:.1f}%",
        "neutral": f"{neutral_count / total * 100:.1f}%"
    }
    
    # STEP 4: Get sample reviews for deeper analysis
    text_col = None
    for col in df.columns:
        if 'review' in col.lower() or 'text' in col.lower() or 'content' in col.lower():
            text_col = col
            break
    
    sample_reviews = ""
    if text_col:
        # Get 3 negative samples (most important for analysis)
        negative_samples = df[df['ai_sentiment'] == 'negative'].head(3)
        if len(negative_samples) > 0:
            sample_reviews += "\n### SAMPLE NEGATIVE REVIEWS (for pain point analysis):\n"
            for idx, row in negative_samples.iterrows():
                review_text = str(row[text_col])[:150]  # Limit to 150 chars
                sample_reviews += f"- {review_text}...\n"
        
        # Get 2 positive samples (to identify strengths)
        positive_samples = df[df['ai_sentiment'] == 'positive'].head(2)
        if len(positive_samples) > 0:
            sample_reviews += "\n### SAMPLE POSITIVE REVIEWS (for strength identification):\n"
            for idx, row in positive_samples.iterrows():
                review_text = str(row[text_col])[:150]
                sample_reviews += f"- {review_text}...\n"
    
    # STEP 5: Build comprehensive data context for LLM
    data_summary = f"""
DATA CONTEXT:
- Total Reviews: {total:,}
- Positive: {positive_count:,} ({sentiment_dist['positive']})
- Negative: {negative_count:,} ({sentiment_dist['negative']})
- Neutral: {neutral_count:,} ({sentiment_dist['neutral']})
{sample_reviews}

USER QUERY: {last_user_message}

Analyze this sentiment distribution and provide actionable insights based on the data and sample reviews.
"""
    
    # STEP 6: Construct prompt
    full_messages = [
        SystemMessage(content=SENTIMENT_PROMPT),
        HumanMessage(content=data_summary)
    ]
    
    # STEP 7: Invoke LLM for insights
    try:
        response = llm.invoke(full_messages)
    except Exception as e:
        # Fallback if LLM fails
        fallback_response = f"""## CUSTOMER SENTIMENT ANALYSIS

### Overview
- Total Reviews: {total:,}
- Positive: {positive_count:,} ({sentiment_dist['positive']})
- Negative: {negative_count:,} ({sentiment_dist['negative']})
- Neutral: {neutral_count:,} ({sentiment_dist['neutral']})

Unable to generate detailed insights due to: {str(e)}

Please try again or use the Analyst node for detailed statistics.
"""
        response = AIMessage(content=fallback_response)
    
    # STEP 8: Prepare analysis data for sharing with other nodes
    analysis_data = {
        "total_reviews": total,
        "sentiment_counts": {
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count
        },
        "sentiment_distribution": sentiment_dist
    }
    
    return {
        "messages": [response],
        "loop_step": 1,
        "current_node": "sentiment",
        "analysis_data": analysis_data  # Share with insight_node, analyst_node
    }
