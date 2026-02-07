import React from 'react';
import { Bot, Sparkles, Brain, ArrowRight, AlertCircle, CheckCircle, Zap } from 'lucide-react';
import '../styles/Landing.css';

const Landing = ({ onEnter, healthStatus }) => {
  return (
    <div className="landing-page">
      <div className="landing-container">
        <div className="hero-section">
          {/* Profile Section */}
          <div className="profile-section">
            <div className="profile-image-container">
              <img 
                src="/profile.jpg" 
                alt="Arvind Yogesh Suresh Babu" 
                className="profile-image"
                onError={(e) => {
                  // Fallback to placeholder if image not found
                  e.target.src = 'https://ui-avatars.com/api/?name=Arvind&size=200&background=7c3aed&color=fff&bold=true';
                }}
              />
              <div className="profile-ring"></div>
            </div>
            <div className="profile-intro">
              <h2 className="profile-name">Arvind Yogesh Suresh Babu</h2>
              <p className="profile-tagline">Computer Vision Engineer | AI Enthusiast</p>
              <p className="profile-description">
                Welcome! I'm Arvind Yogesh Suresh Babu, passionate about building intelligent systems that see and understand the world. 
                Through Pasupathy, you can explore my journey in computer vision, machine learning, robotics, and more. 
                Ask me anything about my projects, skills, experience, or research!
              </p>
            </div>
          </div>

          <div className="hero-icon">
            <Sparkles size={80} className="sparkles-icon" />
          </div>
          <h1>Pasupathy</h1>
          <p className="hero-subtitle">
            Arvind's AI Assistant – Your Personal Knowledge Companion
          </p>
          
          <div className="features-grid">
            <div className="feature">
              <Brain className="feature-icon" />
              <h3>Intelligent Insights</h3>
              <p>Get smart answers about Arvind from curated personal data</p>
            </div>
            <div className="feature">
              <Zap className="feature-icon" />
              <h3>Instant Responses</h3>
              <p>Lightning-fast retrieval using advanced RAG technology</p>
            </div>
            <div className="feature">
              <Bot className="feature-icon" />
              <h3>AI-Powered</h3>
              <p>Powered by Google Gemini for intelligent conversations</p>
            </div>
          </div>

          {/* Show system status only if there's an issue */}
          {healthStatus && (
            healthStatus.status !== 'ready' || 
            healthStatus.database !== 'connected' || 
            healthStatus.model_status !== 'ready' ||
            healthStatus.dataset_count === 0 ||
            healthStatus.error
          ) && (
            <div className="system-status">
              <h3>System Status</h3>
              <div className="status-items">
                <div className={`status-item ${healthStatus?.status === 'ready' ? 'ready' : healthStatus?.status === 'initializing' ? 'initializing' : 'error'}`}>
                  {healthStatus?.status === 'ready' ? (
                    <CheckCircle size={20} className="ready" />
                  ) : (
                    <AlertCircle size={20} className={healthStatus?.status === 'initializing' ? 'initializing' : 'error'} />
                  )}
                  <span>API: {healthStatus?.status || 'Checking...'}</span>
                </div>
                <div className={`status-item ${healthStatus?.database === 'connected' ? 'ready' : 'error'}`}>
                  {healthStatus?.database === 'connected' ? (
                    <CheckCircle size={20} className="ready" />
                  ) : (
                    <AlertCircle size={20} className="error" />
                  )}
                  <span>Database: {healthStatus?.database || 'Unknown'}</span>
                </div>
                <div className={`status-item ${healthStatus?.model_status === 'ready' ? 'ready' : healthStatus?.model_status === 'initializing' ? 'initializing' : 'error'}`}>
                  {healthStatus?.model_status === 'ready' ? (
                    <CheckCircle size={20} className="ready" />
                  ) : (
                    <AlertCircle size={20} className={healthStatus?.model_status === 'initializing' ? 'initializing' : 'error'} />
                  )}
                  <span>Model: {healthStatus?.model_status === 'ready' ? 'Ready' : healthStatus?.model_message || 'Initializing'}</span>
                </div>
                {healthStatus?.dataset_count !== undefined && (
                  <div className={`status-item ${healthStatus.dataset_count > 0 ? 'ready' : 'error'}`}>
                    {healthStatus.dataset_count > 0 ? (
                      <CheckCircle size={20} className="ready" />
                    ) : (
                      <AlertCircle size={20} className="error" />
                    )}
                    <span>Knowledge Base: {healthStatus.dataset_count.toLocaleString()} documents</span>
                  </div>
                )}
              </div>
            </div>
          )}

          <button 
            onClick={onEnter} 
            className="enter-btn"
            disabled={healthStatus?.model_status !== 'ready'}
          >
            Start Conversation
            <ArrowRight size={20} />
          </button>

          {healthStatus?.error && (
            <div className="error-message">
              <AlertCircle size={16} />
              <span>Initialization Error: {healthStatus.error}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Landing;