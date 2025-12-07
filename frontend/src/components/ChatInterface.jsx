import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, UserCircle, Sparkles, Plus, Trash2, MessageSquare, Menu, X, BookOpen, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { chatAPI } from '../services/api';
import ChartDisplay from './ChartDisplay';

// Sample prompts for tutorial
const SAMPLE_PROMPTS = [
  {
    category: 'Sentiment Analysis',
    icon: '😊',
    prompts: [
      'Analyze the sentiment distribution',
      'What percentage of reviews are positive?',
      'Show me sentiment breakdown',
      'What is the dominant sentiment?'
    ]
  },
  {
    category: 'Data Visualization',
    icon: '📊',
    prompts: [
      'Draw a pie chart for sentiment distribution',
      'Create a bar chart showing rating distribution',
      'Draw a line chart of reviews over time',
      'Show me a treemap for sentiment categories'
    ]
  },
  {
    category: 'Search Reviews',
    icon: '🔍',
    prompts: [
      'Find reviews about delivery problems',
      'Show me complaints about customer service',
      'Search for reviews mentioning Prime membership',
      'What do customers say about refunds?'
    ]
  },
  {
    category: 'Business Insights',
    icon: '💡',
    prompts: [
      'Give me business insights from the data',
      'What are the main customer complaints?',
      'Provide strategic recommendations',
      'What actions should we take to improve?'
    ]
  },
  {
    category: 'Summarization',
    icon: '📝',
    prompts: [
      'Summarize the negative reviews',
      'Give me an overview of customer feedback',
      'What are the key takeaways?',
      'Summarize the main themes in reviews'
    ]
  }
];

export default function ChatInterface({ dataLoaded }) {
  const [chatSessions, setChatSessions] = useState([
    { id: 1, title: 'New Chat', messages: [], createdAt: Date.now() }
  ]);
  const [currentSessionId, setCurrentSessionId] = useState(1);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [tutorialOpen, setTutorialOpen] = useState(false);
  const [copiedPrompt, setCopiedPrompt] = useState(null);
  const messagesEndRef = useRef(null);
  const [nextId, setNextId] = useState(2);

  const handleUsePrompt = (prompt) => {
    setInput(prompt);
    setTutorialOpen(false);
  };

  const handleCopyPrompt = (prompt) => {
    navigator.clipboard.writeText(prompt);
    setCopiedPrompt(prompt);
    setTimeout(() => setCopiedPrompt(null), 2000);
  };

  // Get current session
  const currentSession = chatSessions.find(s => s.id === currentSessionId);
  const messages = currentSession?.messages || [];

  const handleNewChat = () => {
    const newSession = {
      id: nextId,
      title: `Chat ${nextId}`,
      messages: [],
      createdAt: Date.now()
    };
    setChatSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(nextId);
    setNextId(nextId + 1);
    
    // Clear backend conversation
    chatAPI.clearConversation().catch(err => console.error('Failed to clear:', err));
  };

  const handleDeleteChat = (sessionId) => {
    if (chatSessions.length === 1) {
      alert('Cannot delete the last chat session');
      return;
    }
    
    const confirmed = window.confirm('Delete this chat?');
    if (!confirmed) return;
    
    setChatSessions(prev => prev.filter(s => s.id !== sessionId));
    
    // Switch to another chat if deleting current
    if (sessionId === currentSessionId) {
      const remaining = chatSessions.filter(s => s.id !== sessionId);
      setCurrentSessionId(remaining[0]?.id || 1);
    }
  };

  const handleSwitchChat = async (sessionId) => {
    if (sessionId === currentSessionId) return;
    
    setCurrentSessionId(sessionId);
    
    // Clear backend and reload session messages
    try {
      await chatAPI.clearConversation();
      // Note: In a real app, you'd sync backend with session messages
      console.log('Switched to session:', sessionId);
    } catch (error) {
      console.error('Failed to switch chat:', error);
    }
  };

  // Auto-update chat title based on first message
  useEffect(() => {
    if (messages.length === 1 && messages[0].role === 'user') {
      const firstMessage = messages[0].content;
      const title = firstMessage.length > 30 
        ? firstMessage.substring(0, 30) + '...'
        : firstMessage;
      
      setChatSessions(prev => prev.map(s => 
        s.id === currentSessionId 
          ? { ...s, title }
          : s
      ));
    }
  }, [messages, currentSessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    
    // Update current session messages
    setChatSessions(prev => prev.map(s => 
      s.id === currentSessionId 
        ? { ...s, messages: [...s.messages, userMessage] }
        : s
    ));
    
    setInput('');
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(input);
      
      // Extract chart data if present
      let chartData = null;
      let content = response.response;
      
      // Check if response contains chart JSON
      const chartMatch = content.match(/```json\n([\s\S]*?)\n```/);
      if (chartMatch) {
        try {
          chartData = JSON.parse(chartMatch[1]);
          // Remove JSON block from content to avoid showing it twice
          content = content.replace(/```json\n[\s\S]*?\n```/, '').trim();
        } catch (e) {
          console.error('Failed to parse chart data:', e);
        }
      }
      
      const aiMessage = {
        role: 'assistant',
        content: content,
        node: response.node,
        time: response.execution_time,
        chartData: chartData
      };
      
      // Update current session messages
      setChatSessions(prev => prev.map(s => 
        s.id === currentSessionId 
          ? { ...s, messages: [...s.messages, aiMessage] }
          : s
      ));
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.message}`,
      };
      
      // Update current session messages
      setChatSessions(prev => prev.map(s => 
        s.id === currentSessionId 
          ? { ...s, messages: [...s.messages, errorMessage] }
          : s
      ));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-full bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* Sidebar - Chat History */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} bg-white/80 backdrop-blur-md border-r border-purple-200 flex flex-col shadow-lg transition-all duration-300 overflow-hidden`}>
        {/* New Chat Button */}
        <div className="p-4 border-b border-purple-200">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-md hover:shadow-lg font-medium"
          >
            <Plus className="w-5 h-5" />
            New Chat
          </button>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {chatSessions.map((session) => (
            <div
              key={session.id}
              className={`group relative flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all ${
                session.id === currentSessionId
                  ? 'bg-gradient-to-r from-purple-100 to-pink-100 border border-purple-300 shadow-md'
                  : 'hover:bg-gray-100 border border-transparent'
              }`}
              onClick={() => handleSwitchChat(session.id)}
            >
              <MessageSquare className={`w-4 h-4 flex-shrink-0 ${
                session.id === currentSessionId ? 'text-purple-600' : 'text-gray-400'
              }`} />
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium truncate ${
                  session.id === currentSessionId ? 'text-purple-700' : 'text-gray-700'
                }`}>
                  {session.title}
                </p>
                <p className="text-xs text-gray-500">
                  {session.messages.length} messages
                </p>
              </div>
              {chatSessions.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteChat(session.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-all"
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header Bar */}
        <div className="bg-white/80 backdrop-blur-md border-b border-purple-200 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-purple-100 rounded-lg transition-all"
              title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
            >
              {sidebarOpen ? (
                <X className="w-5 h-5 text-gray-600" />
              ) : (
                <Menu className="w-5 h-5 text-gray-600" />
              )}
            </button>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium text-gray-700">
                {currentSession?.title || 'Chat'}
              </span>
            </div>
          </div>
          
          {/* Tutorial Button */}
          <button
            onClick={() => setTutorialOpen(true)}
            className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-600 hover:to-cyan-600 transition-all shadow-md hover:shadow-lg text-sm font-medium"
          >
            <BookOpen className="w-4 h-4" />
            Examples
          </button>
        </div>
        
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center mt-20">
            <div className="inline-block p-8 bg-white rounded-3xl shadow-2xl border border-purple-200">
              <h2 className="text-4xl font-bold mb-3 bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-pink-600">
                Hello!
              </h2>
              <p className="text-gray-700 text-lg mb-6">I'm an AI Agent for Amazon feedback analysis</p>
              
              {!dataLoaded ? (
                <p className="text-sm mt-4 text-orange-700 bg-orange-100 px-4 py-2 rounded-lg border border-orange-300">
                  Please upload CSV first
                </p>
              ) : (
                <div className="mt-6">
                  <p className="text-sm text-gray-600 mb-4">Try these quick actions:</p>
                  <div className="flex flex-wrap gap-3 justify-center">
                    <button
                      onClick={() => setInput('Analyze sentiment distribution')}
                      className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-md hover:shadow-lg text-sm"
                    >
                      📊 Analyze Sentiment
                    </button>
                    <button
                      onClick={() => setInput('Draw a pie chart for sentiment distribution')}
                      className="px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-600 hover:to-cyan-600 transition-all shadow-md hover:shadow-lg text-sm"
                    >
                      📈 Draw Chart
                    </button>
                    <button
                      onClick={() => setInput('Find reviews about delivery problems')}
                      className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:from-green-600 hover:to-emerald-600 transition-all shadow-md hover:shadow-lg text-sm"
                    >
                      🔍 Search Reviews
                    </button>
                    <button
                      onClick={() => setInput('Give me business insights')}
                      className="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-all shadow-md hover:shadow-lg text-sm"
                    >
                      💡 Get Insights
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            } message-fade-in`}
          >
            {/* AI Avatar */}
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-purple-600 flex items-center justify-center shadow-lg ring-2 ring-purple-300">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
            )}
            
            <div
              className={`${msg.chartData ? 'w-full max-w-6xl' : 'max-w-2xl'} rounded-2xl px-6 py-4 ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-300/50'
                  : 'bg-white text-gray-800 border border-purple-200 shadow-xl'
              }`}
            >
              {msg.role === 'assistant' ? (
                <>
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    {msg.node && (
                      <div className="text-xs text-purple-600 mt-2 flex items-center gap-2">
                        <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                        {msg.node} • {msg.time}s
                      </div>
                    )}
                  </div>
                  {msg.chartData && <ChartDisplay chartData={msg.chartData} />}
                </>
              ) : (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              )}
            </div>
            
            {/* User Avatar */}
            {msg.role === 'user' && (
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 flex items-center justify-center shadow-lg ring-2 ring-blue-300">
                <UserCircle className="w-6 h-6 text-white" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start message-fade-in">
            <div className="bg-white border border-purple-200 rounded-2xl px-6 py-4 shadow-lg">
              <Loader2 className="w-5 h-5 animate-spin text-purple-600" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

        {/* Input */}
        <div className="border-t border-purple-200 bg-white/80 backdrop-blur-md p-4 shadow-lg">
        <div className="max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              dataLoaded
                ? 'Type your question...'
                : 'Upload CSV first to chat'
            }
            disabled={!dataLoaded || loading}
            className="flex-1 px-5 py-4 bg-gray-50 border border-purple-300 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-400 transition-all"
          />
          <button
            onClick={handleSend}
            disabled={!dataLoaded || loading || !input.trim()}
            className="px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-purple-500/50 disabled:shadow-none"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        </div>
      </div>

      {/* Tutorial Modal */}
      {tutorialOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <BookOpen className="w-6 h-6" />
                <h2 className="text-xl font-bold">Prompt Examples</h2>
              </div>
              <button
                onClick={() => setTutorialOpen(false)}
                className="p-2 hover:bg-white/20 rounded-lg transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <p className="text-gray-600 text-sm">
                Click on any prompt to use it, or copy it to customize. These examples work best when you have data uploaded.
              </p>

              {SAMPLE_PROMPTS.map((category, idx) => (
                <div key={idx} className="space-y-3">
                  <h3 className="text-lg font-semibold flex items-center gap-2 text-gray-800">
                    <span className="text-2xl">{category.icon}</span>
                    {category.category}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {category.prompts.map((prompt, pIdx) => (
                      <div
                        key={pIdx}
                        className="group relative bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all cursor-pointer"
                        onClick={() => handleUsePrompt(prompt)}
                      >
                        <p className="text-sm text-gray-700 pr-8">{prompt}</p>
                        <div className="absolute top-2 right-2 flex gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCopyPrompt(prompt);
                            }}
                            className="p-1.5 bg-white rounded hover:bg-gray-100 transition-all opacity-0 group-hover:opacity-100"
                            title="Copy prompt"
                          >
                            {copiedPrompt === prompt ? (
                              <Check className="w-3.5 h-3.5 text-green-600" />
                            ) : (
                              <Copy className="w-3.5 h-3.5 text-gray-600" />
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Modal Footer */}
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-between items-center">
              <p className="text-xs text-gray-500">
                💡 Tip: You can modify these prompts to fit your specific needs
              </p>
              <button
                onClick={() => setTutorialOpen(false)}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-all font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
