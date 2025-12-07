"""
Smart caching system for quick responses
"""
from functools import lru_cache
import hashlib
import json


class SmartCache:
    """In-memory cache for fast responses"""
    
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}
    
    def _hash_query(self, query: str) -> str:
        """Create hash key from query"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, query: str):
        """Get cached response"""
        key = self._hash_query(query)
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key]
        return None
    
    def set(self, query: str, response: str):
        """Cache response"""
        key = self._hash_query(query)
        
        # Evict least used if full
        if len(self.cache) >= self.max_size:
            least_used = min(self.access_count, key=self.access_count.get)
            del self.cache[least_used]
            del self.access_count[least_used]
        
        self.cache[key] = response
        self.access_count[key] = 0
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.access_count.clear()


# Global cache instance
RESPONSE_CACHE = SmartCache(max_size=200)


# Predefined smart responses
SMART_RESPONSES = {
    # Vietnamese
    'bạn là ai': '🤖 Tôi là **Amazon AI Assistant** - hệ thống phân tích review thông minh.\n\n**Được xây dựng bằng:**\n- 🧠 LangGraph (Multi-Agent)\n- ⚡ Gemini Pro (LLM)\n- 🔍 RAG + ChromaDB\n- 📊 Real-time Analytics\n\n**Tôi có 6 chuyên gia AI:**\n1. 😊 Sentiment Analyst\n2. 🔍 RAG Searcher\n3. 📝 Summarizer\n4. 💡 Insight Generator\n5. 🧮 Data Analyst\n6. 💬 Chat Assistant\n\nHoạt động 24/7, không cần nghỉ! 😎',
    
    'bạn làm được gì': '💪 **Khả năng của tôi:**\n\n🎯 **Top 5 tính năng hot nhất:**\n\n1️⃣ **Phân tích cảm xúc** 😊😐😢\n   → "Phân tích cảm xúc khách hàng"\n   → "Pain points là gì?"\n\n2️⃣ **Tìm kiếm thông minh** 🔍\n   → "Tìm review về pin"\n   → "Khách hàng nói gì về camera?"\n\n3️⃣ **Tóm tắt nhanh** 📝\n   → "Tóm tắt top 10 review tích cực"\n   → "Overview các than phiền"\n\n4️⃣ **Insights chiến lược** 💡\n   → "Đề xuất cải thiện sản phẩm"\n   → "Phân tích SWOT"\n\n5️⃣ **Thống kê số liệu** 🧮\n   → "Có bao nhiêu review 5 sao?"\n   → "Tỷ lệ negative bao nhiêu %?"\n\nThử ngay! 🚀',
    
    'xin chào': '👋 Xin chào! Tôi là **Amazon AI Assistant**!\n\n**Bạn muốn:**\n• 📊 Xem dashboard phân tích?\n• 💬 Chat để tìm hiểu insights?\n• 🔍 Tìm review cụ thể?\n\n**Gợi ý câu hỏi hot:**\n💡 "Có bao nhiêu review tích cực?"\n💡 "Tìm review nói về pin"\n💡 "Đề xuất cải thiện sản phẩm"\n\nBắt đầu thôi! 🎯',
    
    'hello': '👋 Hello! I\'m **Amazon AI Assistant**!\n\n**Quick Start:**\n• 📊 Check Analytics Dashboard\n• 💬 Chat for insights\n• 🔍 Search specific reviews\n\n**Try these:**\n💡 "How many positive reviews?"\n💡 "Find reviews about battery"\n💡 "Suggest product improvements"\n\nLet\'s go! 🚀',
    
    'cảm ơn': '😊 Không có gì! Rất vui được giúp bạn.\n\nCần gì cứ hỏi nhé! 💪',
    
    'thank you': '😊 You\'re very welcome!\n\nFeel free to ask anything else! 💪',
    
    # Help & guide
    'help': '🆘 **Quick Help Guide**\n\n**📊 Data Analysis:**\n• "How many reviews?" → Count total\n• "Average rating?" → Calculate stats\n• "Positive percentage?" → Get ratio\n\n**🔍 Search:**\n• "Find reviews about X" → RAG search\n• "What do customers say about Y?" → Retrieve info\n\n**😊 Sentiment:**\n• "Analyze emotions" → Sentiment breakdown\n• "What are pain points?" → Extract complaints\n\n**💡 Insights:**\n• "Suggest improvements" → Strategic advice\n• "SWOT analysis" → Business insights\n\nJust ask naturally! 🎯',
    
    'hướng dẫn': '🆘 **Hướng dẫn sử dụng**\n\n**📊 Phân tích số liệu:**\n• "Có bao nhiêu review?" → Đếm tổng\n• "Rating trung bình?" → Tính toán\n• "Tỷ lệ positive?" → Phần trăm\n\n**🔍 Tìm kiếm:**\n• "Tìm review về X" → RAG search\n• "Khách hàng nói gì về Y?" → Tra cứu\n\n**😊 Cảm xúc:**\n• "Phân tích cảm xúc" → Breakdown\n• "Pain points là gì?" → Vấn đề\n\n**💡 Insights:**\n• "Đề xuất cải thiện" → Chiến lược\n• "SWOT analysis" → Phân tích\n\nHỏi tự nhiên thôi! 🎯'
}


def get_smart_response(query: str) -> str:
    """
    Get instant smart response for common queries
    
    Args:
        query: User query
        
    Returns:
        Cached response or None
    """
    # Normalize query
    normalized = query.lower().strip()
    
    # Check exact match first
    for key, response in SMART_RESPONSES.items():
        if key in normalized:
            return response
    
    # Check cache
    return RESPONSE_CACHE.get(query)
