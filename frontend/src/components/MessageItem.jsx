import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Copy, Check, Clock, AlertTriangle } from 'lucide-react';
import { TraceViewer } from './TraceViewer';

export function MessageItem({ message, onImageZoom }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`message-bubble-wrapper ${isUser ? 'user' : 'assistant'}`}>
      <div className={`avatar ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      <div className="message-content">
        <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
          {/* If user attached an image to this message */}
          {message.imagePreview && (
            <div
              className="msg-image-thumb"
              onClick={() => onImageZoom(message.imagePreview)}
              style={{ cursor: 'pointer' }}
              title="Click to view original photo"
            >
              <img src={message.imagePreview} alt="Attached bill" />
            </div>
          )}

          {isUser ? (
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          ) : (
            <div className="markdown-body">
              {message.error && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    color: 'var(--rose-primary)',
                    marginBottom: '0.5rem',
                    fontWeight: 600,
                  }}
                >
                  <AlertTriangle size={16} />
                  <span>Agent Notice</span>
                </div>
              )}
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Embedded Trace Viewer for Assistant Messages */}
        {!isUser && message.trace && message.trace.length > 0 && (
          <TraceViewer trace={message.trace} />
        )}

        {/* Message Footer: Execution time & Copy Button */}
        {!isUser && (
          <div className="message-footer">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              {message.seconds !== undefined && (
                <>
                  <Clock size={12} />
                  <span>{message.seconds}s</span>
                </>
              )}
            </div>

            <button className="copy-btn" onClick={handleCopy} title="Copy response">
              {copied ? (
                <>
                  <Check size={13} style={{ color: 'var(--emerald-primary)' }} />
                  <span style={{ color: 'var(--emerald-primary)' }}>Copied</span>
                </>
              ) : (
                <>
                  <Copy size={13} />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
