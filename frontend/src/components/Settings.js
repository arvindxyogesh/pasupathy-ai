import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Sun, Moon, Type, Sliders, Brain, Save, X } from 'lucide-react';
import '../styles/Settings.css';

const Settings = ({ isOpen, onClose }) => {
  const [settings, setSettings] = useState({
    theme: localStorage.getItem('theme') || 'dark',
    fontSize: localStorage.getItem('fontSize') || 'medium',
    temperature: parseFloat(localStorage.getItem('temperature')) || 0.7,
    maxTokens: parseInt(localStorage.getItem('maxTokens')) || 2048,
    responseStyle: localStorage.getItem('responseStyle') || 'balanced',
    responseLength: localStorage.getItem('responseLength') || 'medium',
    showTimestamps: localStorage.getItem('showTimestamps') !== 'false',
    searchK: parseInt(localStorage.getItem('searchK')) || 25,
    customInstructions: localStorage.getItem('customInstructions') || '',
    enableLearning: localStorage.getItem('enableLearning') !== 'false',
  });

  useEffect(() => {
    // Apply theme
    document.documentElement.setAttribute('data-theme', settings.theme);
    document.documentElement.style.fontSize = {
      small: '14px',
      medium: '15px',
      large: '16px',
      xlarge: '18px'
    }[settings.fontSize];
  }, [settings.theme, settings.fontSize]);

  const handleSave = () => {
    Object.entries(settings).forEach(([key, value]) => {
      localStorage.setItem(key, value.toString());
    });
    onClose();
  };

  const handleChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  if (!isOpen) return null;

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-header">
          <div className="settings-title">
            <SettingsIcon size={24} />
            <h2>Settings</h2>
          </div>
          <button onClick={onClose} className="close-btn">
            <X size={20} />
          </button>
        </div>

        <div className="settings-content">
          {/* Appearance */}
          <div className="settings-section">
            <h3>Appearance</h3>
            
            <div className="setting-item">
              <label>
                <span className="setting-label">
                  {settings.theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
                  Theme
                </span>
                <select
                  value={settings.theme}
                  onChange={e => handleChange('theme', e.target.value)}
                  className="setting-select"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="auto">Auto</option>
                </select>
              </label>
            </div>

            <div className="setting-item">
              <label>
                <span className="setting-label">
                  <Type size={16} />
                  Font Size
                </span>
                <select
                  value={settings.fontSize}
                  onChange={e => handleChange('fontSize', e.target.value)}
                  className="setting-select"
                >
                  <option value="small">Small</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                  <option value="xlarge">Extra Large</option>
                </select>
              </label>
            </div>

            <div className="setting-item">
              <label className="setting-checkbox">
                <input
                  type="checkbox"
                  checked={settings.showTimestamps}
                  onChange={e => handleChange('showTimestamps', e.target.checked)}
                />
                <span>Show message timestamps</span>
              </label>
            </div>
          </div>

          {/* AI Behavior */}
          <div className="settings-section">
            <h3>
              <Brain size={18} />
              AI Behavior
            </h3>

            <div className="setting-item">
              <label>
                <span className="setting-label">
                  <Sliders size={16} />
                  Temperature: {settings.temperature}
                </span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.temperature}
                  onChange={e => handleChange('temperature', parseFloat(e.target.value))}
                  className="setting-slider"
                />
                <div className="slider-labels">
                  <span>Precise</span>
                  <span>Creative</span>
                </div>
              </label>
            </div>

            <div className="setting-item">
              <label>
                <span className="setting-label">Response Style</span>
                <select
                  value={settings.responseStyle}
                  onChange={e => handleChange('responseStyle', e.target.value)}
                  className="setting-select"
                >
                  <option value="concise">Concise</option>
                  <option value="balanced">Balanced</option>
                  <option value="detailed">Detailed</option>
                  <option value="technical">Technical</option>
                  <option value="casual">Casual</option>
                </select>
              </label>
            </div>

            <div className="setting-item">
              <label>
                <span className="setting-label">Response Length</span>
                <select
                  value={settings.responseLength}
                  onChange={e => handleChange('responseLength', e.target.value)}
                  className="setting-select"
                >
                  <option value="short">Short</option>
                  <option value="medium">Medium</option>
                  <option value="long">Long</option>
                </select>
              </label>
            </div>

            <div className="setting-item">
              <label>
                <span className="setting-label">Max Response Tokens</span>
                <input
                  type="number"
                  min="256"
                  max="4096"
                  step="256"
                  value={settings.maxTokens}
                  onChange={e => handleChange('maxTokens', parseInt(e.target.value))}
                  className="setting-input"
                />
              </label>
            </div>

            <div className="setting-item">
              <label>
                <span className="setting-label">Search Depth (K)</span>
                <input
                  type="number"
                  min="5"
                  max="50"
                  step="5"
                  value={settings.searchK}
                  onChange={e => handleChange('searchK', parseInt(e.target.value))}
                  className="setting-input"
                />
              </label>
            </div>

            <div className="setting-item">
              <label className="setting-checkbox">
                <input
                  type="checkbox"
                  checked={settings.enableLearning}
                  onChange={e => handleChange('enableLearning', e.target.checked)}
                />
                <span>Enable learning from conversations</span>
              </label>
            </div>
          </div>

          {/* Custom Instructions */}
          <div className="settings-section">
            <h3>Custom Instructions</h3>
            <div className="setting-item">
              <label>
                <span className="setting-label">Persistent instructions for every conversation</span>
                <textarea
                  value={settings.customInstructions}
                  onChange={e => handleChange('customInstructions', e.target.value)}
                  placeholder="E.g., Always be concise, Use bullet points, Explain like I'm a beginner..."
                  className="setting-textarea"
                  rows={4}
                />
              </label>
            </div>
          </div>
        </div>

        <div className="settings-footer">
          <button onClick={onClose} className="cancel-btn">Cancel</button>
          <button onClick={handleSave} className="save-btn">
            <Save size={16} />
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
