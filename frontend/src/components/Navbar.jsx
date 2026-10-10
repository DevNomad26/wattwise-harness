import React from 'react';
import { Zap, Sun, Moon, RotateCcw, Activity } from 'lucide-react';

export function Navbar({ health, theme, onToggleTheme, onNewSession, isProcessing }) {
  return (
    <header className="navbar">
      <div className="brand" onClick={() => window.location.reload()}>
        <div className="brand-icon-box">
          <Zap size={20} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span className="brand-title">WattWise</span>
          <span className="brand-tag">Audit & Advisor</span>
        </div>
      </div>

      <div className="navbar-actions">
        {/* Backend / Ollama Model Health Badge */}
        <div className="health-badge" title={health?.error || `Model: ${health?.model || 'Ollama'}`}>
          <div className={`health-dot ${health?.ok ? 'online' : 'offline'}`} />
          <span>
            {health?.ok
              ? health.model || 'Agent Online'
              : health?.error
              ? 'Backend Offline'
              : 'Connecting...'}
          </span>
        </div>

        {/* New Session / Reset */}
        <button
          className="btn-secondary"
          onClick={onNewSession}
          disabled={isProcessing}
          title="Start fresh conversation & clear memory"
        >
          <RotateCcw size={14} />
          <span>New Session</span>
        </button>

        {/* Light/Dark Mode Switch */}
        <button
          className="icon-btn"
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>
      </div>
    </header>
  );
}
