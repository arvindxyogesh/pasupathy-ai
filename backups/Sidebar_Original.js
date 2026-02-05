import React from 'react';
import { Plus, MessageCircle, Database, AlertCircle, CheckCircle, Sparkles } from 'lucide-react';
import '../styles/Sidebar.css';

const Sidebar = ({ sessions, currentSession, onSelectSession, onCreateNewChat, onDeleteSession, healthStatus }) => {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">
          <Sparkles size={24} className="pasupathy-icon" />
          <h2>Pasupathy</h2>
        </div>
        <button onClick={onCreateNewChat} className="new-chat-btn">
          <Plus size={20} />
          New Chat
        </button>
      </div>

      <div className="health-status">
        <div className={`status-item ${healthStatus?.status}`}>
          {healthStatus?.status === 'ready' ? (
            <CheckCircle size={16} className="ready" />
          ) : (
            <AlertCircle size={16} className="error" />
          )}
          <span>Model: {healthStatus?.initialized ? 'Ready' : 'Loading'}</span>
        </div>
        <div className={`status-item ${healthStatus?.database === 'connected' ? 'ready' : 'error'}`}>
          {healthStatus?.database === 'connected' ? (
            <CheckCircle size={16} className="ready" />
          ) : (
            <AlertCircle size={16} className="error" />
          )}
          <span>Database: {healthStatus?.database || 'Unknown'}</span>
        </div>
      </div>

      <div className="sessions-list">
        <h3>Conversations</h3>
        {sessions.length === 0 ? (
          <div className="no-sessions">No conversations yet</div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              className={`session-item ${currentSession?.session_id === session.session_id ? 'active' : ''}`}
              onClick={() => onSelectSession(session)}
            >
              <MessageCircle size={16} />
              <span className="session-title">{session.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.session_id);
                }}
                className="delete-session-btn"
                title="Delete chat"
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <div className="dataset-info">
          <Sparkles size={16} />
          <span>Arvind's AI Assistant</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;