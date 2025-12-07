import { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import Dashboard from './components/Dashboard';
import FileUpload from './components/FileUpload';
import { healthAPI } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [dataLoaded, setDataLoaded] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  // Check data status on mount and periodically
  useEffect(() => {
    const checkDataStatus = async () => {
      try {
        const status = await healthAPI.checkDataStatus();
        setDataLoaded(status.loaded);
        console.log('Data status:', status);
      } catch (error) {
        console.error('Failed to check data status:', error);
      }
    };

    // Initial check
    checkDataStatus();

    // Check every 3 seconds
    const interval = setInterval(checkDataStatus, 3000);

    return () => clearInterval(interval);
  }, []);

  const handleUploadSuccess = (response) => {
    if (response === null) {
      // Reset case
      setDataLoaded(false);
      console.log('Data reset');
    } else {
      // Upload case
      setDataLoaded(true);
      console.log('Upload success:', response);
    }
  };

  return (
    <div className={`h-screen flex flex-col ${darkMode ? 'bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900' : 'bg-gradient-to-br from-slate-100 via-purple-100 to-slate-100'}`}>
      {/* Header with Gradient */}
      <header className="bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 text-white shadow-2xl">
        <div className="container mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-yellow-200 to-pink-200">
              Amazon Feedback AI Agent
            </h1>
            <p className="text-sm text-purple-100 mt-1">
              Multi-Agent System • Powered by LangGraph & React
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* Dark/Light Mode Toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg transition-all border border-white/30"
              title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {darkMode ? (
                <svg className="w-5 h-5 text-yellow-300" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" fillRule="evenodd" clipRule="evenodd"></path>
                </svg>
              ) : (
                <svg className="w-5 h-5 text-indigo-200" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path>
                </svg>
              )}
            </button>
            
            {/* About Button */}
            <button
              onClick={() => setShowAbout(true)}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg transition-all border border-white/30 text-sm font-medium"
            >
              About
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Modern Sidebar */}
        <aside className={`w-72 ${darkMode ? 'bg-gradient-to-b from-slate-800 to-slate-900 border-purple-500/30' : 'bg-gradient-to-b from-white to-gray-50 border-gray-300'} border-r p-6 space-y-3 shadow-2xl`}>
          <div className="mb-6">
            <h2 className={`text-xs font-semibold ${darkMode ? 'text-purple-300' : 'text-purple-700'} uppercase tracking-wider mb-3`}>
              Navigation
            </h2>
          </div>

          <button
            onClick={() => setActiveTab('upload')}
            className={`w-full flex items-center gap-4 px-5 py-4 rounded-xl transition-all duration-300 ${
              activeTab === 'upload'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/50 scale-105'
                : darkMode 
                  ? 'text-gray-300 hover:bg-slate-700/50 hover:text-white'
                  : 'text-gray-700 hover:bg-purple-100 hover:text-purple-700'
            }`}
          >
            <span className="font-medium">Upload Data</span>
          </button>

          <button
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center gap-4 px-5 py-4 rounded-xl transition-all duration-300 ${
              activeTab === 'chat'
                ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/50 scale-105'
                : darkMode
                  ? 'text-gray-300 hover:bg-slate-700/50 hover:text-white'
                  : 'text-gray-700 hover:bg-blue-100 hover:text-blue-700'
            }`}
          >
            <span className="font-medium">AI Chat</span>
          </button>

          <button
            onClick={() => setActiveTab('dashboard')}
            className={`w-full flex items-center gap-4 px-5 py-4 rounded-xl transition-all duration-300 ${
              activeTab === 'dashboard'
                ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg shadow-green-500/50 scale-105'
                : darkMode
                  ? 'text-gray-300 hover:bg-slate-700/50 hover:text-white'
                  : 'text-gray-700 hover:bg-green-100 hover:text-green-700'
            }`}
          >
            <span className="font-medium">Analytics</span>
          </button>

          {/* Status Card */}
          <div className={`pt-6 mt-6 border-t ${darkMode ? 'border-slate-700' : 'border-gray-300'}`}>
            <div className={`text-xs ${darkMode ? 'text-purple-300' : 'text-purple-700'} uppercase tracking-wider mb-3`}>
              System Status
            </div>
            <div className={`flex items-center gap-3 p-4 rounded-lg ${
              dataLoaded 
                ? darkMode
                  ? 'bg-gradient-to-r from-green-900/50 to-emerald-900/50 border border-green-500/30'
                  : 'bg-gradient-to-r from-green-50 to-emerald-50 border border-green-300'
                : darkMode
                  ? 'bg-slate-800/50 border border-slate-700'
                  : 'bg-gray-100 border border-gray-300'
            }`}>
              <div className={`w-3 h-3 rounded-full ${
                dataLoaded 
                  ? 'bg-green-400 animate-pulse shadow-lg shadow-green-400/50' 
                  : darkMode ? 'bg-gray-500' : 'bg-gray-400'
              }`} />
              <div>
                <div className={`text-sm font-medium ${
                  dataLoaded 
                    ? darkMode ? 'text-green-400' : 'text-green-600'
                    : darkMode ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  {dataLoaded ? 'Data Loaded' : 'No Data'}
                </div>
                {dataLoaded && (
                  <div className={`text-xs ${darkMode ? 'text-green-300/70' : 'text-green-600/70'}`}>
                    Ready to analyze
                  </div>
                )}
              </div>
            </div>
          </div>
        </aside>

        {/* Content Area with Glass Effect */}
        <main className={`flex-1 overflow-hidden ${darkMode ? 'bg-slate-900/30' : 'bg-white/30'} backdrop-blur-sm`}>
          <div className={`p-8 h-full overflow-auto ${activeTab === 'upload' ? 'block' : 'hidden'}`}>
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </div>
          
          <div className={activeTab === 'chat' ? 'block h-full' : 'hidden'}>
            <ChatInterface dataLoaded={dataLoaded} />
          </div>
          
          <div className={activeTab === 'dashboard' ? 'block h-full overflow-auto' : 'hidden'}>
            <Dashboard dataLoaded={dataLoaded} />
          </div>
        </main>
      </div>

      {/* About Modal */}
      {showAbout && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 text-white px-6 py-5 flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold">About This Project</h2>
                <p className="text-sm text-purple-100 mt-1">Amazon Feedback AI Agent</p>
              </div>
              <button
                onClick={() => setShowAbout(false)}
                className="p-2 hover:bg-white/20 rounded-lg transition-all flex-shrink-0"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Project Description */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Project Overview</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  A multi-agent AI system for analyzing Amazon customer feedback using LangGraph, React, and advanced NLP techniques. 
                  Features include sentiment analysis (90% accuracy), RAG-based search, data visualization, and strategic insights generation.
                </p>
              </div>

              {/* Authors */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">Authors</h3>
                <div className="space-y-4">
                  {/* Author 1 */}
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200">
                    <div className="flex items-start gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                        HQ
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800">Ho Minh Quan</h4>
                        <p className="text-sm text-purple-600 font-medium">DS/AIE • Final Year Student</p>
                        <p className="text-xs text-gray-500 mt-1">Ho Chi Minh University of Science (HCMUS)</p>
                        <div className="flex gap-3 mt-2">
                          <a
                            href="https://github.com/[quan-github]"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:text-blue-700 hover:underline"
                          >
                            GitHub
                          </a>
                          <a
                            href="mailto:[quan-email]@example.com"
                            className="text-xs text-blue-600 hover:text-blue-700 hover:underline"
                          >
                            Email
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Author 2 */}
                  <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-4 border border-blue-200">
                    <div className="flex items-start gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-cyan-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                        TP
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800">Tran Nguyen Thanh Phong</h4>
                        <p className="text-sm text-blue-600 font-medium">DA/DS • Final Year Student</p>
                        <p className="text-xs text-gray-500 mt-1">Ho Chi Minh University of Science (HCMUS)</p>
                        <div className="flex gap-3 mt-2">
                          <a
                            href="https://github.com/[phong-github]"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:text-blue-700 hover:underline"
                          >
                            GitHub
                          </a>
                          <a
                            href="mailto:[phong-email]@example.com"
                            className="text-xs text-blue-600 hover:text-blue-700 hover:underline"
                          >
                            Email
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Thank You Message */}
              <div className="bg-gradient-to-r from-purple-100 to-pink-100 rounded-lg p-4 border border-purple-300">
                <p className="text-sm text-gray-700 text-center">
                  <span className="font-semibold">Thank you for using our application!</span>
                  <br />
                  If you have any questions or feedback, please feel free to contact us via email.
                </p>
              </div>

              {/* Tech Stack */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Tech Stack</h3>
                <div className="flex flex-wrap gap-2">
                  {['Python', 'FastAPI', 'LangGraph', 'React', 'Tailwind CSS', 'Recharts', 'SVM', 'RAG'].map((tech) => (
                    <span
                      key={tech}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setShowAbout(false)}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all font-medium shadow-md hover:shadow-lg"
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

export default App;
