import React from 'react';
import { Zap, Sun, Moon, RotateCcw, PanelLeft, PanelLeftClose } from 'lucide-react';

export function Navbar({
  health,
  theme,
  onToggleTheme,
  onNewSession,
  isProcessing,
  sidebarOpen,
  onToggleSidebar,
}) {
  return (
    <header className="navbar">
      <div className="navbar-left">
        {/* Toggle Sidebar Button */}
        <button
          className={`icon-btn-minimal ${sidebarOpen ? 'active' : ''}`}
          onClick={onToggleSidebar}
          title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          aria-label="Toggle sidebar"
        >
          {sidebarOpen ? <PanelLeftClose size={16} /> : <PanelLeft size={16} />}
        </button>

        {/* Brand */}
        <div className="brand" onClick={() => window.location.reload()}>
          <div className="brand-icon">
            <Zap size={16} />
          </div>
          <span className="brand-title">WattWise</span>
          <span className="brand-badge">Audit</span>
        </div>
      </div>

      <div className="navbar-actions">
        {/* Backend & Model Health Badge */}
        <div className="health-badge" title={health?.error || `Model: ${health?.model || 'Ollama'}`}>
          <div className={`health-dot ${health?.ok ? 'online' : 'offline'}`} />
          <span>
            {health?.ok
              ? health.model || 'Agent Online'
              : health?.error
              ? 'Offline'
              : 'Connecting...'}
          </span>
        </div>

        {/* New Session Button */}
        <button
          className="btn-minimal"
          onClick={onNewSession}
          disabled={isProcessing}
          title="Start fresh conversation"
        >
          <RotateCcw size={13} />
          <span>Reset</span>
        </button>

        {/* Dark / Light Mode Switch */}
        <button
          className="icon-btn-minimal"
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>
      </div>
    </header>
  );
}
