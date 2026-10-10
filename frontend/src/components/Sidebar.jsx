import React from 'react';
import { Plus, MessageSquare, Trash2, ChevronLeft } from 'lucide-react';

export function Sidebar({
  threads,
  activeThreadId,
  onSelectThread,
  onNewChat,
  onDeleteThread,
  isOpen,
  onClose,
}) {
  return (
    <aside className={`sidebar ${!isOpen ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          <Plus size={15} />
          <span>New Chat</span>
        </button>

        <button
          className="icon-btn-minimal"
          onClick={onClose}
          title="Collapse sidebar"
          style={{ width: '28px', height: '28px', border: 'none' }}
        >
          <ChevronLeft size={15} />
        </button>
      </div>

      {/* Chat History Section */}
      <div className="history-section">
        <div className="history-title">Chat History</div>

        {threads.length === 0 ? (
          <div className="history-empty">
            <MessageSquare size={16} />
            <span>No previous chats</span>
          </div>
        ) : (
          <div className="history-list">
            {threads.map((thread) => {
              const isActive = thread.id === activeThreadId;
              return (
                <div
                  key={thread.id}
                  className={`history-item ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectThread(thread.id)}
                >
                  <MessageSquare size={14} className="history-item-icon" />
                  <span className="history-item-title" title={thread.title}>
                    {thread.title || 'Untitled conversation'}
                  </span>
                  <button
                    className="history-delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteThread(thread.id);
                    }}
                    title="Delete chat"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
}
