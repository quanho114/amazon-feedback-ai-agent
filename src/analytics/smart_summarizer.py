"""
Smart Summarizer with Gatekeeper
Only calls LLM 120B for reviews that actually need analysis
Saves API cost and improves efficiency
"""
import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()


class ReviewCategory(Enum):
    """Categories for review routing"""
    SKIP_TOO_SHORT = "skip_short"      # < 10 words, already a summary
    SKIP_NEUTRAL = "skip_neutral"       # Neutral/Positive, no issues
    ANALYZE_NEGATIVE = "negative"       # Negative - extract root cause
    ANALYZE_MIXED = "mixed"             # Long mixed review - separate pros/cons


class TopicClassifier:
    """
    Keyword-based topic classification for Amazon Platform reviews
    No LLM needed - fast and accurate for common topics
    """
    
    TOPIC_KEYWORDS = {
        "Delivery": [
            'delivery', 'deliver', 'shipping', 'shipped', 'package', 'parcel',
            'arrived', 'late', 'driver', 'courier', 'tracking', 'lost',
            'damaged', 'box', 'days', 'week', 'address', 'door', 'porch'
        ],
        "Customer Service": [
            'customer service', 'support', 'representative', 'rep', 'agent',
            'call', 'phone', 'chat', 'help', 'contact', 'response', 'wait',
            'hold', 'escalate', 'manager', 'resolve', 'unhelpful', 'rude'
        ],
        "Account/Prime": [
            'prime', 'membership', 'subscription', 'account', 'login',
            'password', 'locked', 'suspended', 'cancelled', 'cancel',
            'charged', 'billing', 'payment', 'credit card', 'unauthorized'
        ],
        "Refund/Return": [
            'refund', 'return', 'money back', 'reimburse', 'credit',
            'exchange', 'replacement', 'policy', 'denied', 'rejected'
        ],
        "Website/App": [
            'website', 'app', 'site', 'page', 'checkout', 'cart', 'order',
            'search', 'filter', 'bug', 'error', 'crash', 'slow', 'glitch'
        ],
        "Seller/Product": [
            'seller', 'vendor', 'third party', 'product', 'item', 'quality',
            'fake', 'counterfeit', 'authentic', 'description', 'picture',
            'review', 'rating', 'stars'
        ]
    }
    
    @classmethod
    def classify(cls, text: str) -> Tuple[str, float]:
        """
        Classify review topic based on keywords
        
        Returns:
            Tuple of (topic, confidence)
        """
        text_lower = text.lower()
        scores = {}
        
        for topic, keywords in cls.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[topic] = score
        
        if not scores:
            return ("General", 0.0)
        
        # Get top topic
        top_topic = max(scores, key=scores.get)
        total_matches = sum(scores.values())
        confidence = scores[top_topic] / total_matches if total_matches > 0 else 0
        
        return (top_topic, round(confidence, 2))
    
    @classmethod
    def get_all_topics(cls, text: str) -> List[Tuple[str, int]]:
        """Get all matching topics with scores"""
        text_lower = text.lower()
        results = []
        
        for topic, keywords in cls.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                results.append((topic, score))
        
        return sorted(results, key=lambda x: x[1], reverse=True)


@dataclass
class GatekeeperResult:
    """Result from gatekeeper check"""
    category: ReviewCategory
    should_call_llm: bool
    reason: str
    word_count: int
    sentiment: str


@dataclass 
class AnalysisResult:
    """Structured result from LLM analysis"""
    original_text: str
    category: str
    summary: Optional[str] = None
    
    # Topic classification (keyword-based, no LLM)
    topic: Optional[str] = None  # Delivery/Customer Service/Account/etc
    topic_confidence: Optional[float] = None
    
    # For negative reviews (LLM extracted)
    main_issue: Optional[str] = None
    issue_detail: Optional[str] = None
    severity: Optional[str] = None  # High/Medium/Low
    
    # For mixed reviews
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None
    
    # Tags for dashboard
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class SmartSummarizer:
    """
    Smart summarization pipeline with Gatekeeper
    Only calls expensive LLM for reviews that need deep analysis
    """
    
    # Keywords indicating issues (even in positive reviews)
    # Updated for Amazon PLATFORM reviews (not product reviews)
    ISSUE_KEYWORDS = [
        'but', 'however', 'although', 'except', 'issue', 'problem',
        'late', 'delay', 'never arrived', 'wrong address', 'lost package',
        'refund', 'return', 'cancelled', 'charged', 'unauthorized',
        'customer service', 'support', 'no help', 'rude', 'unhelpful',
        'prime', 'subscription', 'account', 'locked', 'suspended',
        'disappointed', 'frustrat', 'angry', 'worst', 'terrible',
        'never again', 'waste', 'scam', 'fake', 'misleading'
    ]
    
    # Prompts for LLM - Updated for Amazon Platform Reviews
    NEGATIVE_PROMPT = """You are an Amazon Platform Review Analyst. Analyze this negative review about Amazon's service/platform.

REVIEW:
{review}

TASK: Extract root cause and categorize the issue.

RESPOND IN JSON FORMAT ONLY:
{{
    "main_issue": "Delivery|Customer Service|Account/Prime|Refund/Return|Website/App|Seller Issue|Other",
    "issue_detail": "Brief description of the specific problem (max 20 words)",
    "severity": "High|Medium|Low",
    "tags": ["tag1", "tag2"],
    "summary": "One sentence summary of the complaint"
}}

ISSUE CATEGORIES:
- Delivery: Late, lost, damaged, wrong address, driver issues
- Customer Service: Unhelpful, rude, long wait, no resolution
- Account/Prime: Unauthorized charges, cancellation issues, locked account
- Refund/Return: Refund denied, slow refund, return problems
- Website/App: Technical issues, misleading info, checkout problems
- Seller Issue: Third-party seller problems, fake products
- Other: Job application, general complaints

SEVERITY GUIDE:
- High: Unauthorized charges, account locked, legal threat, safety issue
- Medium: Significant delay, poor service, partial refund
- Low: Minor inconvenience, slow response

TAGS: Use short actionable tags. Return plain text only, do NOT include square brackets [] or special characters.
Examples: Late Delivery, Lost Package, Rude Support, Refund Denied, Prime Cancelled, Account Locked, Wrong Item, Unauthorized Charge"""

    MIXED_PROMPT = """You are an Amazon Platform Review Analyst. This review has mixed opinions about Amazon's service. Separate them clearly.

REVIEW:
{review}

TASK: Extract pros and cons about Amazon's platform/service.

RESPOND IN JSON FORMAT ONLY:
{{
    "pros": ["positive point 1", "positive point 2"],
    "cons": ["negative point 1", "negative point 2"],
    "tags": ["tag1", "tag2"],
    "summary": "One balanced sentence summarizing the review"
}}

IMPORTANT: Tags should be plain text only, do NOT include square brackets [] or special characters.

FOCUS ON:
- Delivery experience (speed, accuracy, driver behavior)
- Customer service quality
- Prime membership value
- Website/App usability
- Refund/Return process
- Overall shopping experience

Keep each point concise (max 10 words each)."""

    def __init__(self):
        """Initialize with LLM for complex analysis"""
        self.llm = ChatOpenAI(
            api_key=os.getenv("MEGALLM_API_KEY"),
            base_url=os.getenv("MEGALLM_BASE_URL"),
            model=os.getenv("MEGALLM_MODEL"),
            temperature=0,  # Deterministic for structured output
            max_tokens=300
        )
        
        self.stats = {
            "total": 0,
            "skipped_short": 0,
            "skipped_neutral": 0,
            "analyzed_negative": 0,
            "analyzed_mixed": 0,
            "llm_calls": 0
        }
    
    def _count_words(self, text: str) -> int:
        """Count words in text"""
        return len(text.split())
    
    def _has_issue_keywords(self, text: str) -> bool:
        """Check if text contains issue-related keywords"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.ISSUE_KEYWORDS)
    
    def _is_mixed_review(self, text: str, sentiment: str) -> bool:
        """Detect if review is mixed (has both positive and negative aspects)"""
        text_lower = text.lower()
        
        # Check for contrast words
        has_contrast = any(w in text_lower for w in ['but', 'however', 'although', 'except', 'though'])
        
        # Check word count (mixed reviews tend to be longer)
        is_long = self._count_words(text) > 50
        
        # Neutral sentiment often indicates mixed feelings
        is_neutral = sentiment == 'neutral'
        
        return (has_contrast and is_long) or (is_neutral and is_long and self._has_issue_keywords(text))
    
    def gatekeeper(self, text: str, sentiment: str) -> GatekeeperResult:
        """
        Gatekeeper: Decide if review needs LLM analysis
        
        Args:
            text: Review text
            sentiment: Sentiment label (positive/negative/neutral)
            
        Returns:
            GatekeeperResult with routing decision
        """
        word_count = self._count_words(text)
        
        # Rule 1: Too short - skip
        if word_count < 10:
            return GatekeeperResult(
                category=ReviewCategory.SKIP_TOO_SHORT,
                should_call_llm=False,
                reason="Review too short, already a summary",
                word_count=word_count,
                sentiment=sentiment
            )
        
        # Rule 2: Negative review - always analyze
        if sentiment == 'negative':
            return GatekeeperResult(
                category=ReviewCategory.ANALYZE_NEGATIVE,
                should_call_llm=True,
                reason="Negative review - extract root cause",
                word_count=word_count,
                sentiment=sentiment
            )
        
        # Rule 3: Mixed review (long with contrast)
        if self._is_mixed_review(text, sentiment):
            return GatekeeperResult(
                category=ReviewCategory.ANALYZE_MIXED,
                should_call_llm=True,
                reason="Mixed review - separate pros/cons",
                word_count=word_count,
                sentiment=sentiment
            )
        
        # Rule 4: Positive/Neutral with issue keywords - analyze
        if self._has_issue_keywords(text) and word_count > 30:
            return GatekeeperResult(
                category=ReviewCategory.ANALYZE_MIXED,
                should_call_llm=True,
                reason="Contains issue keywords despite positive sentiment",
                word_count=word_count,
                sentiment=sentiment
            )
        
        # Rule 5: Default - skip neutral/positive without issues
        return GatekeeperResult(
            category=ReviewCategory.SKIP_NEUTRAL,
            should_call_llm=False,
            reason="Positive/Neutral review without issues",
            word_count=word_count,
            sentiment=sentiment
        )
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse JSON from LLM response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        return {"error": "Failed to parse response", "raw": response}
    
    def analyze_review(self, text: str, sentiment: str) -> AnalysisResult:
        """
        Main entry point: Analyze a single review
        
        Args:
            text: Review text
            sentiment: Sentiment label
            
        Returns:
            AnalysisResult with structured data
        """
        self.stats["total"] += 1
        
        # Step 1: Gatekeeper check
        gate_result = self.gatekeeper(text, sentiment)
        
        # Step 2: Always classify topic (keyword-based, no LLM cost)
        topic, topic_conf = TopicClassifier.classify(text)
        
        # Step 3: Route based on category
        if not gate_result.should_call_llm:
            # Skip LLM - but still return topic classification
            if gate_result.category == ReviewCategory.SKIP_TOO_SHORT:
                self.stats["skipped_short"] += 1
            else:
                self.stats["skipped_neutral"] += 1
                
            return AnalysisResult(
                original_text=text,
                category=gate_result.category.value,
                topic=topic,
                topic_confidence=topic_conf,
                summary=text if gate_result.category == ReviewCategory.SKIP_TOO_SHORT else None,
                tags=[f"Good {topic}"] if sentiment == 'positive' and topic != "General" else None
            )
        
        # Step 4: Call LLM for complex analysis
        self.stats["llm_calls"] += 1
        
        if gate_result.category == ReviewCategory.ANALYZE_NEGATIVE:
            self.stats["analyzed_negative"] += 1
            result = self._analyze_negative(text)
        else:
            self.stats["analyzed_mixed"] += 1
            result = self._analyze_mixed(text)
        
        # Add topic classification to LLM result
        result.topic = topic
        result.topic_confidence = topic_conf
        
        return result
    
    def _analyze_negative(self, text: str) -> AnalysisResult:
        """Analyze negative review - extract root cause"""
        prompt = self.NEGATIVE_PROMPT.format(review=text)
        
        response = self.llm.invoke([
            SystemMessage(content="You are a JSON-only response bot. Only output valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        data = self._parse_llm_response(response.content)
        
        return AnalysisResult(
            original_text=text,
            category="negative",
            main_issue=data.get("main_issue"),
            issue_detail=data.get("issue_detail"),
            severity=data.get("severity"),
            tags=data.get("tags", []),
            summary=data.get("summary")
        )
    
    def _analyze_mixed(self, text: str) -> AnalysisResult:
        """Analyze mixed review - separate pros/cons"""
        prompt = self.MIXED_PROMPT.format(review=text)
        
        response = self.llm.invoke([
            SystemMessage(content="You are a JSON-only response bot. Only output valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        data = self._parse_llm_response(response.content)
        
        return AnalysisResult(
            original_text=text,
            category="mixed",
            pros=data.get("pros", []),
            cons=data.get("cons", []),
            tags=data.get("tags", []),
            summary=data.get("summary")
        )
    
    def analyze_batch(self, reviews: List[Dict]) -> List[AnalysisResult]:
        """
        Analyze multiple reviews
        
        Args:
            reviews: List of {"text": str, "sentiment": str}
            
        Returns:
            List of AnalysisResult
        """
        results = []
        for review in reviews:
            result = self.analyze_review(review["text"], review["sentiment"])
            results.append(result)
        
        return results
    
    def get_stats(self) -> Dict:
        """Get processing statistics"""
        total = self.stats["total"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "skip_rate": f"{(self.stats['skipped_short'] + self.stats['skipped_neutral']) / total * 100:.1f}%",
            "llm_call_rate": f"{self.stats['llm_calls'] / total * 100:.1f}%"
        }


# Singleton instance
_summarizer = None

def get_summarizer() -> SmartSummarizer:
    """Get singleton summarizer instance"""
    global _summarizer
    if _summarizer is None:
        _summarizer = SmartSummarizer()
    return _summarizer


# Convenience functions
def smart_summarize(text: str, sentiment: str) -> Dict:
    """Quick function to summarize a single review"""
    summarizer = get_summarizer()
    result = summarizer.analyze_review(text, sentiment)
    return result.to_dict()


def smart_summarize_batch(reviews: List[Dict]) -> List[Dict]:
    """Quick function to summarize multiple reviews"""
    summarizer = get_summarizer()
    results = summarizer.analyze_batch(reviews)
    return [r.to_dict() for r in results]
