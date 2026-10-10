import React, { useState, useRef, useEffect } from 'react';
import { Send, ImagePlus, Loader2 } from 'lucide-react';

export function MessageInput({ onSendMessage, isProcessing, onFileSelect, hasImage }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!input.trim() || isProcessing) return;
    onSendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <footer className="input-area">
      <form onSubmit={handleSubmit} className="input-box-wrapper">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/jpeg,image/png,image/webp"
          style={{ display: 'none' }}
          disabled={isProcessing}
        />

        <button
          type="button"
          className="icon-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={isProcessing}
          title={hasImage ? 'Bill photo attached' : 'Attach bill photo'}
          style={{
            color: hasImage ? 'var(--emerald-primary)' : 'var(--text-secondary)',
            borderColor: hasImage ? 'var(--emerald-border)' : 'var(--border-subtle)',
          }}
        >
          <ImagePlus size={18} />
        </button>

        <textarea
          ref={textareaRef}
          rows={1}
          className="chat-textarea"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question or request a bill audit..."
          disabled={isProcessing}
        />

        <button
          type="submit"
          className="send-btn"
          disabled={!input.trim() || isProcessing}
          title="Send message (Enter)"
          aria-label="Send message"
        >
          {isProcessing ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
        </button>
      </form>
    </footer>
  );
}
