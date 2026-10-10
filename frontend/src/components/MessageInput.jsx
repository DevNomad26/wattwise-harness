import React, { useState, useRef, useEffect } from 'react';
import { Send, ImagePlus, Loader2, X, FileImage } from 'lucide-react';

export function MessageInput({
  onSendMessage,
  isProcessing,
  selectedFile,
  onFileSelect,
  onFileRemove,
}) {
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
    if ((!input.trim() && !selectedFile) || isProcessing) return;
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
    // reset input value so re-uploading the same file works
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <footer className="input-area">
      {/* Attached file indicator preview chip */}
      {selectedFile && (
        <div className="attached-file-chip">
          <FileImage size={13} className="attached-file-icon" />
          <span className="attached-file-name" title={selectedFile.name}>
            {selectedFile.name}
          </span>
          <button
            type="button"
            className="attached-file-remove"
            onClick={onFileRemove}
            title="Remove attachment"
          >
            <X size={12} />
          </button>
        </div>
      )}

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
          className="icon-btn-minimal"
          onClick={() => fileInputRef.current?.click()}
          disabled={isProcessing}
          title={selectedFile ? 'Change attached photo' : 'Attach bill photo'}
          style={{
            color: selectedFile ? 'var(--text-primary)' : 'var(--text-muted)',
            border: 'none',
          }}
        >
          <ImagePlus size={16} />
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
          disabled={(!input.trim() && !selectedFile) || isProcessing}
          title="Send message (Enter)"
          aria-label="Send message"
        >
          {isProcessing ? <Loader2 size={16} className="animate-spin" /> : <Send size={15} />}
        </button>
      </form>
    </footer>
  );
}
