import React, { useState, useEffect, useRef } from 'react';
import { Send, Download, RotateCw, Copy, Check } from 'lucide-react';
import { sendMessage, sendMessageStream, regenerateResponse, exportSession } from '../services/api';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import '../styles/ChatInterface.css';

const ChatInterface = ({ session, onSessionUpdate }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [copiedMessageId, setCopiedMessageId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (session && session.messages) {
      setMessages(session.messages);
    } else {
      // Clear messages when starting a new chat
      setMessages([]);
    }
  }, [session]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);
    setStreamingMessage('');

    // Add user message immediately
    const tempUserMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      let fullResponse = '';
      let sessionId = session?.session_id;
      const currentMessages = [...messages, tempUserMsg]; // Capture current state

      await sendMessageStream(userMessage, sessionId, (data) => {
        if (data.content) {
          fullResponse += data.content;
          setStreamingMessage(fullResponse);
        }
        if (data.done) {
          sessionId = data.session_id;
          const assistantMsg = {
            id: Date.now().toString() + '_assistant',
            role: 'assistant',
            content: fullResponse,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, assistantMsg]);
          setStreamingMessage('');
          
          // Update the session with the new session_id and messages
          if (onSessionUpdate) {
            const updatedSession = {
              session_id: sessionId,
              messages: [...currentMessages, assistantMsg],
              title: session?.title || userMessage.substring(0, 50)
            };
            onSessionUpdate(updatedSession);
          }
        }
        if (data.error) {
          throw new Error(data.error);
        }
      });
    } catch (error) {
      console.error('Error:', error);
      const errorMsg = {
        id: Date.now().toString() + '_error',
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
      setStreamingMessage('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!session?.session_id || isLoading) return;

    setIsLoading(true);
    // Remove last assistant message
    setMessages(prev => prev.slice(0, -1));

    try {
      const result = await regenerateResponse(session.session_id);
      if (result.status === 'success' && result.session) {
        setMessages(result.session.messages);
        if (onSessionUpdate) {
          onSessionUpdate(result.session);
        }
      }
    } catch (error) {
      console.error('Regenerate error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (content, messageId) => {
    navigator.clipboard.writeText(content);
    setCopiedMessageId(messageId);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  const handleExport = async (format) => {
    if (!session?.session_id) return;
    try {
      await exportSession(session.session_id, format);
    } catch (error) {
      console.error('Export error:', error);
    }
  };

  const renderMessage = (message) => {
    const isUser = message.role === 'user';

    return (
      <div key={message.id} className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
        <div style={{ maxWidth: '800px', width: '100%', margin: '0 auto' }}>
          <div className="message-header">
            <span className="message-role">{isUser ? 'You' : 'Pasupathy'}</span>
            <div className="message-actions">
              {!isUser && (
                <button onClick={() => handleCopy(message.content, message.id)} className="action-btn" title="Copy">
                  {copiedMessageId === message.id ? <Check size={16} /> : <Copy size={16} />}
                </button>
              )}
            </div>
          </div>
          <div className="message-content">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>{session?.title || 'New Chat'}</h2>
        <div className="chat-header-actions">
          <button onClick={() => handleExport('json')} className="header-btn" title="Export JSON">
            <Download size={18} />
          </button>
          <button onClick={() => handleExport('markdown')} className="header-btn" title="Export Markdown">
            <Download size={18} /> MD
          </button>
        </div>
      </div>

      <div className="messages-container">
        {messages.map(renderMessage)}
        
        {streamingMessage && (
          <div className="message assistant-message streaming">
            <div style={{ maxWidth: '800px', width: '100%', margin: '0 auto' }}>
              <div className="message-header">
                <span className="message-role">Pasupathy</span>
              </div>
              <div className="message-content">
                <ReactMarkdown>{streamingMessage}</ReactMarkdown>
                <span className="cursor-blink">▊</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        {messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && (
          <button onClick={handleRegenerate} className="regenerate-btn" disabled={isLoading}>
            <RotateCw size={16} /> Regenerate
          </button>
        )}
        
        <div className="input-wrapper">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask Pasupathy anything about Arvind..."
            disabled={isLoading}
            rows={1}
          />
          <button onClick={handleSend} disabled={isLoading || !input.trim()} className="send-btn">
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;