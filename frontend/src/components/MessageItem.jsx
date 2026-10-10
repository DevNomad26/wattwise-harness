import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Copy, Check, Clock, AlertTriangle } from 'lucide-react';

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
        {isUser ? <User size={15} /> : <Bot size={15} />}
      </div>

      <div className="message-content">
        <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
          {/* Attached image thumbnail */}
          {message.imagePreview && (
            <div
              className="msg-image-thumb"
              onClick={() => onImageZoom(message.imagePreview)}
              style={{ cursor: 'pointer' }}
              title="Click to view original photo"
            >
              <img src={message.imagePreview} alt="Attached electricity bill" />
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
                    fontSize: '0.85rem',
                  }}
                >
                  <AlertTriangle size={15} />
                  <span>Notice</span>
                </div>
              )}
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Minimal Footer: Execution time & Copy Action */}
        {!isUser && (
          <div className="message-footer">
            <div>
              {message.seconds !== undefined && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Clock size={11} />
                  <span>{message.seconds}s</span>
                </span>
              )}
            </div>

            <button className="copy-btn" onClick={handleCopy} title="Copy response">
              {copied ? (
                <>
                  <Check size={12} style={{ color: 'var(--emerald-primary)' }} />
                  <span style={{ color: 'var(--emerald-primary)' }}>Copied</span>
                </>
              ) : (
                <>
                  <Copy size={12} />
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
