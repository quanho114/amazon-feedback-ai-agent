"""
Insight Node - Strategic Analysis Worker
Provides business insights using Chain-of-Thought reasoning
Model: DeepSeek V3 (Optimized for stability & cost)
"""
import os
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM - DeepSeek V3 for strategic analysis
llm = ChatOpenAI(
    api_key=os.getenv("MEGALLM_API_KEY"),
    base_url=os.getenv("MEGALLM_BASE_URL"),
    model=os.getenv("MEGALLM_MODEL"),  # Use config model
    temperature=0.3,  # Slightly higher for creative solutions
    streaming=False,
    max_tokens=1200  # Increased for detailed insights
)

INSIGHT_PROMPT = """You are a Strategic Business Analyst specializing in Amazon e-commerce feedback analysis.

MISSION:
Extract actionable business insights from customer reviews and feedback data.

ANALYSIS FRAMEWORK:
1. Pattern Recognition: Identify recurring themes in the provided NEGATIVE SAMPLES
2. Root Cause Analysis: Find underlying issues behind complaints
3. Impact Assessment: Prioritize issues by frequency and severity
4. Action Planning: Recommend specific, measurable improvements

FOCUS AREAS (Amazon Platform):
- Delivery & Logistics
- Customer Service Quality
- Account & Prime Membership
- Refund & Return Process
- Website/App Usability
- Seller Issues

OUTPUT STRUCTURE (Markdown):
## [ANALYSIS] Key Findings
- Finding 1: [Observation based on specific reviews]
- Finding 2: [Observation based on statistics]
- Finding 3: [Pattern identified from samples]

## [INSIGHTS] Strategic Implications
1. **[Insight Title]**: [Explanation with business impact]
2. **[Insight Title]**: [Explanation with business impact]
3. **[Insight Title]**: [Explanation with business impact]

## [ACTIONS] Recommended Next Steps
- **Priority 1**: [Specific action with expected outcome]
- **Priority 2**: [Specific action with expected outcome]
- **Priority 3**: [Specific action with expected outcome]

## [RISKS] Potential Concerns
- [Risk description and mitigation strategy]
- [Risk description and mitigation strategy]

RULES:
- Be concise and data-driven
- **Reference specific complaints** found in the sample reviews
- Focus on actionable insights, not generic observations
- Prioritize by business impact
- Use plain text (no emoji icons)
- Cite specific patterns from the data
"""


def insight_node(state):
    """
    Strategic insight generation node with retry logic
    
    Flow:
    1. Check if data exists in SESSION_DATA
    2. Get analysis_data from state (shared by sentiment_node/analyst_node)
    3. Generate strategic insights using LLM
    4. Retry on failure with exponential backoff
    
    Args:
        state: Current agent state with messages and analysis data
        
    Returns:
        Updated state with strategic insights
    """
    from src.agents.tools import SESSION_DATA
    
    messages = state["messages"]
    last_user_message = next(
        (msg.content for msg in reversed(messages) if hasattr(msg, 'content')),
        ""
    )
    
    # STEP 1: Check if data exists
    df = SESSION_DATA.get('default')
    
    if df is None:
        return {
            "messages": [AIMessage(content="**No Data Available**\n\nPlease upload a CSV file first so I can generate strategic insights!")],
            "loop_step": 1,
            "current_node": "insight"
        }
    
    # STEP 2: Get analysis data from state (shared by other nodes)
    analysis_data = state.get("analysis_data", {})
    
    # STEP 3: Build comprehensive data context (Stats + Sample Reviews)
    stats_text = ""
    sample_reviews_text = ""
    
    # A. Get statistics (from analysis_data or calculate)
    if analysis_data and analysis_data.get("total_reviews", 0) > 0:
        # Use shared analysis data (from sentiment_node)
        total = analysis_data.get("total_reviews", 0)
        sentiment_counts = analysis_data.get("sentiment_counts", {})
        sentiment_dist = analysis_data.get("sentiment_distribution", {})
        
        stats_text = f"""- Total Reviews: {total:,}
- Positive: {sentiment_counts.get('positive', 0):,} ({sentiment_dist.get('positive', 'N/A')})
- Negative: {sentiment_counts.get('negative', 0):,} ({sentiment_dist.get('negative', 'N/A')})
- Neutral: {sentiment_counts.get('neutral', 0):,} ({sentiment_dist.get('neutral', 'N/A')})"""
    else:
        # Fallback: Calculate from DataFrame directly
        if 'ai_sentiment' in df.columns:
            sentiment_counts = df['ai_sentiment'].value_counts()
            total = len(df)
            
            stats_text = f"""- Total Reviews: {total:,}
- Positive: {int(sentiment_counts.get('positive', 0)):,} ({sentiment_counts.get('positive', 0) / total * 100:.1f}%)
- Negative: {int(sentiment_counts.get('negative', 0)):,} ({sentiment_counts.get('negative', 0) / total * 100:.1f}%)
- Neutral: {int(sentiment_counts.get('neutral', 0)):,} ({sentiment_counts.get('neutral', 0) / total * 100:.1f}%)"""
        else:
            stats_text = f"- Total Reviews: {len(df):,}\n- Sentiment data not available"
    
    # B. Get sample negative reviews for deeper analysis
    text_col = None
    for col in df.columns:
        if 'review' in col.lower() or 'text' in col.lower() or 'content' in col.lower():
            text_col = col
            break
    
    if text_col and 'ai_sentiment' in df.columns:
        # Get 5 negative samples for root cause analysis
        negative_samples = df[df['ai_sentiment'] == 'negative'].head(5)
        if len(negative_samples) > 0:
            sample_reviews_text = "\n### SAMPLE NEGATIVE REVIEWS (for root cause analysis):\n"
            for idx, row in negative_samples.iterrows():
                review_text = str(row[text_col])[:200]  # Limit to 200 chars
                sample_reviews_text += f"- {review_text}...\n"
    
    # STEP 4: Combine context
    data_context = f"""
DATA STATISTICS:
{stats_text}
{sample_reviews_text if sample_reviews_text else "\nNo negative review samples available."}
"""
    
    # STEP 5: Construct prompt with data context
    user_query = f"{data_context}\nUSER QUERY: {last_user_message}"
    
    full_messages = [
        SystemMessage(content=INSIGHT_PROMPT),
        HumanMessage(content=user_query)
    ]
    
    # STEP 6: Call LLM with retry logic for stability
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"[INFO] Insight Node analyzing... (Attempt {attempt+1}/{max_retries})")
            response = llm.invoke(full_messages)
            
            return {
                "messages": [response],
                "loop_step": 1,
                "current_node": "insight"
            }
        except Exception as e:
            error_msg = str(e)
            print(f"[WARNING] Insight LLM Error (Attempt {attempt+1}/{max_retries}): {error_msg}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                print(f"[INFO] Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Fallback response with basic insights
                fallback_msg = f"""## [SYSTEM] Automated Strategic Analysis Unavailable

Unable to generate detailed insights due to: {error_msg}

### Manual Quick Insight Approach:

Based on the data statistics:
{stats_text}

**Recommended Actions:**
1. Review the sentiment distribution above
2. Identify the most frequent complaint categories in negative reviews
3. Look for patterns in the sample negative reviews
4. Prioritize issues by frequency and severity
5. Create action items for the top 3 issues

**Please try again in a moment for automated insights.**"""
                
                return {
                    "messages": [AIMessage(content=fallback_msg)],
                    "loop_step": 1,
                    "current_node": "insight"
                }
