import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, Download, RotateCw, Copy, Check, X, Edit2, Trash2, 
  Pin, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, Search,
  FileText, Bookmark, MoreVertical, Share2, Printer
} from 'lucide-react';
import { sendMessage, sendMessageStream, regenerateResponse, exportSession, generateFollowUpQuestions } from '../services/api';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import '../styles/ChatInterface.css';

const ChatInterface = ({ session, onSessionUpdate, onRenameSession }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [copiedMessageId, setCopiedMessageId] = useState(null);
  const [editingMessageId, setEditingMessageId] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [pinnedMessages, setPinnedMessages] = useState(new Set());
  const [foldedMessages, setFoldedMessages] = useState(new Set());
  const [messageReactions, setMessageReactions] = useState({});
  const [followUpQuestions, setFollowUpQuestions] = useState([]);
  const [abortController, setAbortController] = useState(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [showTokens, setShowTokens] = useState(false);
  const [tokenCount, setTokenCount] = useState({ input: 0, output: 0 });
  const [draft, setDraft] = useState('');
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load settings from localStorage
  const settings = {
    showTimestamps: localStorage.getItem('showTimestamps') !== 'false',
    temperature: parseFloat(localStorage.getItem('temperature')) || 0.7,
    maxTokens: parseInt(localStorage.getItem('maxTokens')) || 2048,
    responseStyle: localStorage.getItem('responseStyle') || 'balanced',
    responseLength: localStorage.getItem('responseLength') || 'medium',
    searchK: parseInt(localStorage.getItem('searchK')) || 25,
    customInstructions: localStorage.getItem('customInstructions') || '',
    enableLearning: localStorage.getItem('enableLearning') !== 'false',
  };

  useEffect(() => {
    if (session && session.messages) {
      setMessages(session.messages);
      // Load pinned messages from localStorage
      const savedPinned = localStorage.getItem(`pinned_${session.session_id}`);
      if (savedPinned) {
        setPinnedMessages(new Set(JSON.parse(savedPinned)));
      }
      // Load reactions
      const savedReactions = localStorage.getItem(`reactions_${session.session_id}`);
      if (savedReactions) {
        setMessageReactions(JSON.parse(savedReactions));
      }
    } else {
      setMessages([]);
      setPinnedMessages(new Set());
      setMessageReactions({});
    }
  }, [session]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Auto-save draft
  useEffect(() => {
    if (input && session?.session_id) {
      localStorage.setItem(`draft_${session.session_id}`, input);
    }
  }, [input, session?.session_id]);

  // Load draft on session change
  useEffect(() => {
    if (session?.session_id) {
      const savedDraft = localStorage.getItem(`draft_${session.session_id}`);
      if (savedDraft) {
        setInput(savedDraft);
      }
    }
  }, [session?.session_id]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Cmd+Enter or Ctrl+Enter to send
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        handleSend();
      }
      // Escape to clear input
      if (e.key === 'Escape') {
        setInput('');
        inputRef.current?.blur();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [input, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    const finalMessage = settings.customInstructions 
      ? `${settings.customInstructions}\n\n${userMessage}`
      : userMessage;
    
    setInput('');
    setIsLoading(true);
    setStreamingMessage('');
    setFollowUpQuestions([]);

    // Clear draft
    if (session?.session_id) {
      localStorage.removeItem(`draft_${session.session_id}`);
    }

    // Add user message immediately
    const tempUserMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    // Create abort controller
    const controller = new AbortController();
    setAbortController(controller);

    try {
      let fullResponse = '';
      let sessionId = session?.session_id;
      const currentMessages = [...messages, tempUserMsg];

      await sendMessageStream(
        finalMessage, 
        sessionId, 
        (data) => {
          if (controller.signal.aborted) return;
          
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
            
            // Update token count
            if (data.tokens) {
              setTokenCount(prev => ({
                input: prev.input + (data.tokens.input || 0),
                output: prev.output + (data.tokens.output || 0)
              }));
            }

            // Generate context-aware follow-up questions
            const queryContext = data.query_context || null;
            generateFollowUps(userMessage, fullResponse, queryContext);
            
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
        },
        {
          temperature: settings.temperature,
          max_tokens: settings.maxTokens,
          response_style: settings.responseStyle,
          response_length: settings.responseLength,
          search_k: settings.searchK,
          enable_learning: settings.enableLearning,
          signal: controller.signal
        }
      );
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request aborted');
        setStreamingMessage('');
      } else {
        console.error('Error:', error);
        const errorMsg = {
          id: Date.now().toString() + '_error',
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMsg]);
        setStreamingMessage('');
      }
    } finally {
      setIsLoading(false);
      setAbortController(null);
    }
  };

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
      setIsLoading(false);
      setStreamingMessage('');
    }
  };

  const handleRegenerate = async () => {
    if (!session?.session_id || isLoading) return;

    setIsLoading(true);
    setMessages(prev => prev.slice(0, -1));

    try {
      const result = await regenerateResponse(session.session_id, {
        temperature: settings.temperature,
        max_tokens: settings.maxTokens,
      });
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

  const handleCopyAll = () => {
    const allText = messages.map(m => `${m.role === 'user' ? 'You' : 'Pasupathy'}: ${m.content}`).join('\n\n');
    navigator.clipboard.writeText(allText);
  };

  const handleEditMessage = (messageId, content) => {
    setEditingMessageId(messageId);
    setEditContent(content);
  };

  const handleSaveEdit = async () => {
    // Find the message index
    const msgIndex = messages.findIndex(m => m.id === editingMessageId);
    if (msgIndex === -1) return;

    // Update the message
    const updatedMessages = [...messages];
    updatedMessages[msgIndex].content = editContent;
    
    // Remove all messages after this one (branching)
    const newMessages = updatedMessages.slice(0, msgIndex + 1);
    setMessages(newMessages);
    setEditingMessageId(null);
    setEditContent('');

    // If it's a user message, regenerate response
    if (messages[msgIndex].role === 'user') {
      // Trigger new response
      setInput(editContent);
      setTimeout(() => handleSend(), 100);
    }
  };

  const handleDeleteMessage = (messageId) => {
    setMessages(prev => prev.filter(m => m.id !== messageId));
  };

  const handlePinMessage = (messageId) => {
    setPinnedMessages(prev => {
      const newPinned = new Set(prev);
      if (newPinned.has(messageId)) {
        newPinned.delete(messageId);
      } else {
        newPinned.add(messageId);
      }
      // Save to localStorage
      if (session?.session_id) {
        localStorage.setItem(`pinned_${session.session_id}`, JSON.stringify([...newPinned]));
      }
      return newPinned;
    });
  };

  const handleToggleFold = (messageId) => {
    setFoldedMessages(prev => {
      const newFolded = new Set(prev);
      if (newFolded.has(messageId)) {
        newFolded.delete(messageId);
      } else {
        newFolded.add(messageId);
      }
      return newFolded;
    });
  };

  const handleReaction = (messageId, reaction) => {
    setMessageReactions(prev => {
      const newReactions = { ...prev, [messageId]: reaction };
      // Save to localStorage
      if (session?.session_id) {
        localStorage.setItem(`reactions_${session.session_id}`, JSON.stringify(newReactions));
      }
      return newReactions;
    });
  };

  const handleExport = async (format) => {
    if (!session?.session_id) return;
    try {
      await exportSession(session.session_id, format);
    } catch (error) {
      console.error('Export error:', error);
    }
  };

  const handleShare = async () => {
    // Generate shareable link (to be implemented on backend)
    const shareUrl = `${window.location.origin}/shared/${session?.session_id}`;
    await navigator.clipboard.writeText(shareUrl);
    alert('Share link copied to clipboard!');
  };

  const handlePrint = () => {
    window.print();
  };

  const generateFollowUps = async (userMsg, botResponse, queryContext = null) => {
    try {
      const result = await generateFollowUpQuestions(userMsg, botResponse, queryContext);
      if (result.status === 'success' && result.questions) {
        setFollowUpQuestions(result.questions);
      }
    } catch (error) {
      console.error('Error generating follow-ups:', error);
      // Fallback to generic questions
      setFollowUpQuestions([
        "Tell me more about that",
        "What else should I know?",
        "Can you elaborate?"
      ]);
    }
  };

  const handleRename = async () => {
    if (newTitle.trim() && session?.session_id && onRenameSession) {
      await onRenameSession(session.session_id, newTitle.trim());
      setIsRenaming(false);
      setNewTitle('');
    }
  };

  const renderMessage = (message) => {
    const isUser = message.role === 'user';
    const isPinned = pinnedMessages.has(message.id);
    const isFolded = foldedMessages.has(message.id);
    const reaction = messageReactions[message.id];
    const isLongMessage = message.content.length > 500;

    return (
      <div key={message.id} className={`message ${isUser ? 'user-message' : 'assistant-message'} ${isPinned ? 'pinned' : ''}`}>
        <div style={{ maxWidth: '800px', width: '100%', margin: '0 auto' }}>
          <div className="message-header">
            <div className="message-header-left">
              <span className="message-role">{isUser ? 'You' : 'Pasupathy'}</span>
              {settings.showTimestamps && (
                <span className="message-timestamp">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              )}
              {isPinned && <Pin size={14} className="pinned-icon" />}
            </div>
            <div className="message-actions">
              {!isUser && (
                <>
                  <button 
                    onClick={() => handleReaction(message.id, reaction === 'up' ? null : 'up')} 
                    className={`action-btn ${reaction === 'up' ? 'active' : ''}`}
                    title="Thumbs up"
                  >
                    <ThumbsUp size={16} />
                  </button>
                  <button 
                    onClick={() => handleReaction(message.id, reaction === 'down' ? null : 'down')} 
                    className={`action-btn ${reaction === 'down' ? 'active' : ''}`}
                    title="Thumbs down"
                  >
                    <ThumbsDown size={16} />
                  </button>
                </>
              )}
              {editingMessageId !== message.id && (
                <>
                  <button onClick={() => handleCopy(message.content, message.id)} className="action-btn" title="Copy">
                    {copiedMessageId === message.id ? <Check size={16} /> : <Copy size={16} />}
                  </button>
                  <button onClick={() => handleEditMessage(message.id, message.content)} className="action-btn" title="Edit">
                    <Edit2 size={16} />
                  </button>
                  <button onClick={() => handlePinMessage(message.id)} className="action-btn" title={isPinned ? "Unpin" : "Pin"}>
                    <Pin size={16} />
                  </button>
                  {isLongMessage && (
                    <button onClick={() => handleToggleFold(message.id)} className="action-btn" title={isFolded ? "Expand" : "Collapse"}>
                      {isFolded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
                    </button>
                  )}
                  <button onClick={() => handleDeleteMessage(message.id)} className="action-btn danger" title="Delete">
                    <Trash2 size={16} />
                  </button>
                </>
              )}
            </div>
          </div>
          
          {editingMessageId === message.id ? (
            <div className="message-edit">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="edit-textarea"
                rows={4}
              />
              <div className="edit-actions">
                <button onClick={() => setEditingMessageId(null)} className="cancel-btn">Cancel</button>
                <button onClick={handleSaveEdit} className="save-btn">Save & Regenerate</button>
              </div>
            </div>
          ) : (
            <div className={`message-content ${isFolded ? 'folded' : ''}`}>
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
                {isFolded ? message.content.substring(0, 200) + '...' : message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        {isRenaming ? (
          <div className="rename-input-wrapper">
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder={session?.title || 'New Chat'}
              className="rename-input"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRename();
                if (e.key === 'Escape') setIsRenaming(false);
              }}
            />
            <button onClick={handleRename} className="rename-save-btn">
              <Check size={16} />
            </button>
            <button onClick={() => setIsRenaming(false)} className="rename-cancel-btn">
              <X size={16} />
            </button>
          </div>
        ) : (
          <h2 onClick={() => {
            setIsRenaming(true);
            setNewTitle(session?.title || '');
          }} className="chat-title-editable">
            {session?.title || 'New Chat'}
            <Edit2 size={14} className="edit-icon" />
          </h2>
        )}
        
        <div className="chat-header-actions">
          {showTokens && (
            <div className="token-display">
              <span>Tokens: {tokenCount.input + tokenCount.output}</span>
              <span className="token-detail">↑{tokenCount.input} ↓{tokenCount.output}</span>
            </div>
          )}
          <button onClick={() => setShowTokens(!showTokens)} className="header-btn" title="Token Counter">
            <FileText size={18} />
          </button>
          <button onClick={handleCopyAll} className="header-btn" title="Copy All">
            <Copy size={18} />
          </button>
          <button onClick={handleShare} className="header-btn" title="Share">
            <Share2 size={18} />
          </button>
          <button onClick={handlePrint} className="header-btn" title="Print">
            <Printer size={18} />
          </button>
          <button onClick={() => handleExport('json')} className="header-btn" title="Export JSON">
            <Download size={18} />
          </button>
          <button onClick={() => handleExport('markdown')} className="header-btn" title="Export Markdown">
            <Download size={18} /> MD
          </button>
          <button onClick={() => handleExport('pdf')} className="header-btn" title="Export PDF">
            <Download size={18} /> PDF
          </button>
        </div>
      </div>

      <div className="messages-container">
        {/* Pinned messages section */}
        {[...pinnedMessages].length > 0 && (
          <div className="pinned-section">
            <h4><Pin size={16} /> Pinned Messages</h4>
            {messages.filter(m => pinnedMessages.has(m.id)).map(renderMessage)}
          </div>
        )}

        {messages.map(renderMessage)}
        
        {streamingMessage && (
          <div className="message assistant-message streaming">
            <div style={{ maxWidth: '800px', width: '100%', margin: '0 auto' }}>
              <div className="message-header">
                <span className="message-role">Pasupathy</span>
                <span className="typing-indicator">Thinking...</span>
              </div>
              <div className="message-content">
                <ReactMarkdown>{streamingMessage}</ReactMarkdown>
                <span className="cursor-blink">▊</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Follow-up questions */}
        {followUpQuestions.length > 0 && !isLoading && (
          <div className="followup-questions">
            <p className="followup-label">Related questions:</p>
            {followUpQuestions.map((q, idx) => (
              <button 
                key={idx} 
                onClick={() => {
                  // Set input and trigger send
                  setInput(q);
                  // Use setTimeout to ensure state is updated before sending
                  setTimeout(() => handleSend(), 50);
                }}
                className="followup-btn"
              >
                {q}
              </button>
            ))}
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        {messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && !isLoading && (
          <button onClick={handleRegenerate} className="regenerate-btn">
            <RotateCw size={16} /> Regenerate
          </button>
        )}
        
        {isLoading && (
          <button onClick={handleStop} className="stop-btn">
            <X size={16} /> Stop Generating
          </button>
        )}
        
        <div className="input-wrapper">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !(e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask Pasupathy anything about Arvind... (⌘+Enter to send)"
            disabled={isLoading}
            rows={1}
          />
          <button onClick={handleSend} disabled={isLoading || !input.trim()} className="send-btn">
            <Send size={20} />
          </button>
        </div>
        
        <div className="input-hints">
          <span>⌘+Enter to send • Shift+Enter for new line • Esc to clear</span>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
