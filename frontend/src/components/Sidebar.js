import React, { useState, useEffect } from 'react';
import { 
  Plus, MessageCircle, Database, AlertCircle, CheckCircle, Sparkles,
  Search, Folder, Archive, Star, Settings as SettingsIcon, Trash2,
  Tag, MoreVertical, Edit2, Check, X, Filter
} from 'lucide-react';
import '../styles/Sidebar.css';

const Sidebar = ({ sessions, currentSession, onSelectSession, onCreateNewChat, onDeleteSession, healthStatus, onOpenSettings, onRenameSession }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFolder, setSelectedFolder] = useState('all');
  const [favorites, setFavorites] = useState(new Set());
  const [archived, setArchived] = useState(new Set());
  const [folders, setFolders] = useState({});
  const [tags, setTags] = useState({});
  const [showArchived, setShowArchived] = useState(false);
  const [filterBy, setFilterBy] = useState('all'); // all, favorites, archived
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [contextMenuId, setContextMenuId] = useState(null);

  useEffect(() => {
    // Load favorites from localStorage
    const savedFavorites = localStorage.getItem('favorites');
    if (savedFavorites) {
      setFavorites(new Set(JSON.parse(savedFavorites)));
    }
    // Load archived
    const savedArchived = localStorage.getItem('archived');
    if (savedArchived) {
      setArchived(new Set(JSON.parse(savedArchived)));
    }
    // Load folders
    const savedFolders = localStorage.getItem('folders');
    if (savedFolders) {
      setFolders(JSON.parse(savedFolders));
    }
    // Load tags
    const savedTags = localStorage.getItem('tags');
    if (savedTags) {
      setTags(JSON.parse(savedTags));
    }
  }, []);

  const saveFavorites = (newFavorites) => {
    localStorage.setItem('favorites', JSON.stringify([...newFavorites]));
    setFavorites(newFavorites);
  };

  const saveArchived = (newArchived) => {
    localStorage.setItem('archived', JSON.stringify([...newArchived]));
    setArchived(newArchived);
  };

  const saveFolders = (newFolders) => {
    localStorage.setItem('folders', JSON.stringify(newFolders));
    setFolders(newFolders);
  };

  const saveTags = (newTags) => {
    localStorage.setItem('tags', JSON.stringify(newTags));
    setTags(newTags);
  };

  const toggleFavorite = (sessionId, e) => {
    e?.stopPropagation();
    const newFavorites = new Set(favorites);
    if (newFavorites.has(sessionId)) {
      newFavorites.delete(sessionId);
    } else {
      newFavorites.add(sessionId);
    }
    saveFavorites(newFavorites);
  };

  const toggleArchive = (sessionId, e) => {
    e?.stopPropagation();
    const newArchived = new Set(archived);
    if (newArchived.has(sessionId)) {
      newArchived.delete(sessionId);
    } else {
      newArchived.add(sessionId);
    }
    saveArchived(newArchived);
    setContextMenuId(null);
  };

  const assignFolder = (sessionId, folderName) => {
    const newFolders = { ...folders, [sessionId]: folderName };
    saveFolders(newFolders);
  };

  const addTag = (sessionId, tag) => {
    const sessionTags = tags[sessionId] || [];
    if (!sessionTags.includes(tag)) {
      const newTags = { ...tags, [sessionId]: [...sessionTags, tag] };
      saveTags(newTags);
    }
  };

  const handleRename = (sessionId) => {
    if (renameValue.trim() && onRenameSession) {
      onRenameSession(sessionId, renameValue.trim());
      setRenamingId(null);
      setRenameValue('');
    }
  };

  const handleBulkDelete = () => {
    if (window.confirm('Delete all archived conversations?')) {
      archived.forEach(sessionId => {
        onDeleteSession(sessionId);
      });
      setArchived(new Set());
      localStorage.setItem('archived', JSON.stringify([]));
    }
  };

  const filteredSessions = sessions.filter(session => {
    // Search filter
    if (searchQuery && !session.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    // Archive filter
    if (!showArchived && archived.has(session.session_id)) {
      return false;
    }
    if (showArchived && !archived.has(session.session_id)) {
      return false;
    }
    // Favorites filter
    if (filterBy === 'favorites' && !favorites.has(session.session_id)) {
      return false;
    }
    // Folder filter
    if (selectedFolder !== 'all' && folders[session.session_id] !== selectedFolder) {
      return false;
    }
    return true;
  });

  const folderList = [...new Set(Object.values(folders))];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">
          <Sparkles size={24} className="pasupathy-icon" />
          <h2>Pasupathy</h2>
        </div>
        <div className="sidebar-actions">
          <button onClick={onCreateNewChat} className="new-chat-btn" title="New Chat (⌘+N)">
            <Plus size={20} />
          </button>
          <button onClick={onOpenSettings} className="settings-btn" title="Settings">
            <SettingsIcon size={20} />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="sidebar-search">
        <Search size={16} className="search-icon" />
        <input
          type="text"
          placeholder="Search conversations... (⌘+K)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        {searchQuery && (
          <button onClick={() => setSearchQuery('')} className="clear-search-btn">
            <X size={14} />
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="sidebar-filters">
        <button
          className={`filter-btn ${filterBy === 'all' ? 'active' : ''}`}
          onClick={() => setFilterBy('all')}
        >
          All
        </button>
        <button
          className={`filter-btn ${filterBy === 'favorites' ? 'active' : ''}`}
          onClick={() => setFilterBy('favorites')}
        >
          <Star size={14} /> Favorites
        </button>
        <button
          className={`filter-btn ${showArchived ? 'active' : ''}`}
          onClick={() => setShowArchived(!showArchived)}
        >
          <Archive size={14} /> {showArchived ? 'Hide' : 'Show'} Archived
        </button>
      </div>

      {/* Folders */}
      {folderList.length > 0 && (
        <div className="folder-list">
          <button
            className={`folder-btn ${selectedFolder === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedFolder('all')}
          >
            <Folder size={14} /> All Folders
          </button>
          {folderList.map(folder => (
            <button
              key={folder}
              className={`folder-btn ${selectedFolder === folder ? 'active' : ''}`}
              onClick={() => setSelectedFolder(folder)}
            >
              <Folder size={14} /> {folder}
            </button>
          ))}
        </div>
      )}

      {/* Show health status only if there's an issue */}
      {healthStatus && (
        healthStatus.status !== 'ready' || 
        healthStatus.database !== 'connected' ||
        !healthStatus.initialized
      ) && (
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
            <span>DB: {healthStatus?.database || 'Unknown'}</span>
          </div>
        </div>
      )}

      <div className="sessions-list">
        <div className="sessions-header">
          <h3>Conversations ({filteredSessions.length})</h3>
          {showArchived && archived.size > 0 && (
            <button onClick={handleBulkDelete} className="bulk-delete-btn" title="Delete all archived">
              <Trash2 size={14} />
            </button>
          )}
        </div>
        {filteredSessions.length === 0 ? (
          <div className="no-sessions">
            {searchQuery ? 'No matches found' : 'No conversations yet'}
          </div>
        ) : (
          filteredSessions.map((session) => (
            <div
              key={session.session_id}
              className={`session-item ${currentSession?.session_id === session.session_id ? 'active' : ''} ${archived.has(session.session_id) ? 'archived' : ''}`}
              onClick={() => onSelectSession(session)}
            >
              <MessageCircle size={16} />
              
              {renamingId === session.session_id ? (
                <div className="rename-wrapper" onClick={e => e.stopPropagation()}>
                  <input
                    type="text"
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    className="rename-input"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleRename(session.session_id);
                      if (e.key === 'Escape') setRenamingId(null);
                    }}
                  />
                  <button onClick={() => handleRename(session.session_id)} className="rename-save">
                    <Check size={12} />
                  </button>
                  <button onClick={() => setRenamingId(null)} className="rename-cancel">
                    <X size={12} />
                  </button>
                </div>
              ) : (
                <>
                  <div className="session-content">
                    <span className="session-title">{session.title}</span>
                    <div className="session-meta">
                      {favorites.has(session.session_id) && (
                        <Star size={12} className="favorite-icon" fill="currentColor" />
                      )}
                      {folders[session.session_id] && (
                        <span className="folder-badge">{folders[session.session_id]}</span>
                      )}
                      {tags[session.session_id]?.map(tag => (
                        <span key={tag} className="tag-badge">{tag}</span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="session-actions">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(session.session_id);
                      }}
                      className="session-action-btn"
                      title={favorites.has(session.session_id) ? 'Remove from favorites' : 'Add to favorites'}
                    >
                      <Star size={14} fill={favorites.has(session.session_id) ? 'currentColor' : 'none'} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setContextMenuId(contextMenuId === session.session_id ? null : session.session_id);
                      }}
                      className="session-action-btn"
                      title="More options"
                    >
                      <MoreVertical size={14} />
                    </button>
                  </div>

                  {contextMenuId === session.session_id && (
                    <div className="context-menu" onClick={e => e.stopPropagation()}>
                      <button onClick={() => {
                        setRenamingId(session.session_id);
                        setRenameValue(session.title);
                        setContextMenuId(null);
                      }}>
                        <Edit2 size={14} /> Rename
                      </button>
                      <button onClick={(e) => toggleArchive(session.session_id, e)}>
                        <Archive size={14} /> {archived.has(session.session_id) ? 'Unarchive' : 'Archive'}
                      </button>
                      <button onClick={() => {
                        const folder = prompt('Folder name:');
                        if (folder) assignFolder(session.session_id, folder);
                        setContextMenuId(null);
                      }}>
                        <Folder size={14} /> Move to folder
                      </button>
                      <button onClick={() => {
                        const tag = prompt('Tag name:');
                        if (tag) addTag(session.session_id, tag);
                        setContextMenuId(null);
                      }}>
                        <Tag size={14} /> Add tag
                      </button>
                      <button onClick={() => {
                        onDeleteSession(session.session_id);
                        setContextMenuId(null);
                      }} className="danger">
                        <Trash2 size={14} /> Delete
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <div className="dataset-info">
          <Sparkles size={16} />
          <span>Arvind's AI Assistant</span>
        </div>
        <div className="shortcuts-hint">
          <kbd>⌘</kbd>+<kbd>K</kbd> Search • <kbd>⌘</kbd>+<kbd>N</kbd> New
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
