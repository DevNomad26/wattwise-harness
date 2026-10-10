import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export function ImageModal({ imageUrl, onClose }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!imageUrl) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose} aria-label="Close image preview">
          <X size={20} />
        </button>
        <img src={imageUrl} alt="Enlarged electricity bill preview" />
      </div>
    </div>
  );
}
