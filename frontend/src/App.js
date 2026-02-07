import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import Settings from './components/Settings';
import Landing from './components/Landing';
import ErrorBoundary from './components/ErrorBoundary';
import { HealthCheck } from './services/api';
import './styles/App.css';

function App() {
  const [currentSession, setCurrentSession] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [healthStatus, setHealthStatus] = useState(null);
  const [showLanding, setShowLanding] = useState(true);
  const [showSettings, setShowSettings] = useState(false);

  // Set page title and apply theme
  useEffect(() => {
    document.title = 'Pasupathy - Arvind\'s AI Assistant';
    
    // Apply saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Cmd/Ctrl + N for new chat
      if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
        e.preventDefault();
        createNewChat();
      }
      
      // Cmd/Ctrl + K for search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        document.querySelector('.search-input')?.focus();
      }

      // Cmd/Ctrl + / for settings
      if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault();
        setShowSettings(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const loadSessions = () => {
    try {
      // Load sessions from localStorage only (private to this browser)
      const savedSessions = localStorage.getItem('chat_sessions');
      if (savedSessions) {
        setSessions(JSON.parse(savedSessions));
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const saveSessions = (newSessions) => {
    // Save to localStorage only (keeps chats private)
    localStorage.setItem('chat_sessions', JSON.stringify(newSessions));
    setSessions(newSessions);
  };

  const checkHealth = async () => {
    try {
      const status = await HealthCheck();
      setHealthStatus(status);
    } catch (error) {
      setHealthStatus({ status: 'error', error: error.message });
    }
  };

  // Run initial health check and load sessions on mount. Poll health periodically
  useEffect(() => {
    checkHealth();
    loadSessions();
    const healthInterval = setInterval(checkHealth, 5000);
    return () => clearInterval(healthInterval);
  }, []);

  const createNewChat = () => {
    setCurrentSession(null);
  };

  const selectSession = (session) => {
    setCurrentSession(session);
  };

  const deleteSession = async (sessionId) => {
    try {
      const updatedSessions = sessions.filter(s => s.session_id !== sessionId);
      saveSessions(updatedSessions);  // Save to localStorage only
      
      if (currentSession && currentSession.session_id === sessionId) {
        setCurrentSession(null);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const renameSession = async (sessionId, newTitle) => {
    try {
      const updatedSessions = sessions.map(session => 
        session.session_id === sessionId 
          ? { ...session, title: newTitle }
          : session
      );
      saveSessions(updatedSessions);  // Save to localStorage only
      
      // Update current session if it's the one being renamed
      if (currentSession && currentSession.session_id === sessionId) {
        setCurrentSession(prev => ({ ...prev, title: newTitle }));
      }
    } catch (error) {
      console.error('Error renaming session:', error);
    }
  };

  const handleSessionUpdate = (updatedSession) => {
    if (updatedSession && updatedSession.session_id) {
      setCurrentSession(updatedSession);
      
      // Update or add session in localStorage
      const existingIndex = sessions.findIndex(s => s.session_id === updatedSession.session_id);
      let updatedSessions;
      
      if (existingIndex >= 0) {
        updatedSessions = [...sessions];
        updatedSessions[existingIndex] = updatedSession;
      } else {
        updatedSessions = [updatedSession, ...sessions];
      }
      
      saveSessions(updatedSessions);
    }
  };

  if (showLanding) {
    return <Landing onEnter={() => setShowLanding(false)} healthStatus={healthStatus} />;
  }

  return (
    <ErrorBoundary>
      <div className="app">
        <Sidebar
          sessions={sessions}
          currentSession={currentSession}
          onSelectSession={selectSession}
          onCreateNewChat={createNewChat}
          onDeleteSession={deleteSession}
          onRenameSession={renameSession}
          onOpenSettings={() => setShowSettings(true)}
          healthStatus={healthStatus}
        />
        <div className="main-content">
          <ChatInterface
            session={currentSession}
            onSessionUpdate={handleSessionUpdate}
            onRenameSession={renameSession}
            healthStatus={healthStatus}
          />
        </div>
        <Settings 
          isOpen={showSettings} 
          onClose={() => setShowSettings(false)} 
        />
      </div>
    </ErrorBoundary>
  );
}

export default App;
