import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import Landing from './components/Landing';
import ErrorBoundary from './components/ErrorBoundary';
import { HealthCheck } from './services/api';
import './styles/App.css';

function App() {
  const [currentSession, setCurrentSession] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [healthStatus, setHealthStatus] = useState(null);
  const [showLanding, setShowLanding] = useState(true);

  // Set page title to Pasupathy
  useEffect(() => {
    document.title = 'Pasupathy - Arvind\'s AI Assistant';
  }, []);

  const loadSessions = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/chat/sessions');
      const data = await response.json();
      setSessions(data.sessions);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
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
      await fetch(`http://localhost:5000/api/chat/sessions/${sessionId}`, {
        method: 'DELETE',
      });
      
      if (currentSession && currentSession.session_id === sessionId) {
        setCurrentSession(null);
      }
      loadSessions();
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const handleSessionUpdate = (updatedSession) => {
    // Update current session with the new session_id
    if (updatedSession && updatedSession.session_id) {
      setCurrentSession(updatedSession);
      // Reload sessions list to show the new/updated session
      // Add a small delay to ensure backend has saved the session
      setTimeout(() => loadSessions(), 500);
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
          healthStatus={healthStatus}
        />
        <div className="main-content">
          <ChatInterface
            session={currentSession}
            onSessionUpdate={handleSessionUpdate}
            healthStatus={healthStatus}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default App;