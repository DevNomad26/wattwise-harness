import React, { useRef } from 'react';
import { UploadCloud, Image as ImageIcon, Trash2, Maximize2, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';

export function BillUploader({
  selectedFile,
  previewUrl,
  onFileSelect,
  onFileRemove,
  onImageZoom,
  disabled
}) {
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/')) {
        onFileSelect(file);
      }
    }
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  const formatSize = (bytes) => {
    if (!bytes) return '';
    const kb = bytes / 1024;
    return kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${Math.round(kb)} KB`;
  };

  return (
    <aside className="sidebar">
      <div>
        <h2 className="sidebar-title">Electricity Bill</h2>
        
        {/* If file is selected, show preview card; else show dropzone */}
        {selectedFile && previewUrl ? (
          <div className="bill-preview-card">
            <div className="preview-img-wrapper" onClick={() => onImageZoom(previewUrl)}>
              <img src={previewUrl} alt="Electricity Bill preview" />
              <div className="preview-zoom-overlay">
                <Maximize2 size={16} />
                <span>Click to expand</span>
              </div>
            </div>
            <div className="preview-meta">
              <div>
                <div className="preview-filename" title={selectedFile.name}>
                  {selectedFile.name}
                </div>
                <div className="preview-size">{formatSize(selectedFile.size)}</div>
              </div>
              <button
                className="icon-btn"
                onClick={onFileRemove}
                disabled={disabled}
                title="Remove photo"
                style={{ color: 'var(--rose-primary)' }}
              >
                <Trash2 size={15} />
              </button>
            </div>
          </div>
        ) : (
          <div
            className="dropzone"
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleInputChange}
              accept="image/jpeg,image/png,image/webp"
              style={{ display: 'none' }}
              disabled={disabled}
            />
            <div className="dropzone-icon">
              <UploadCloud size={22} />
            </div>
            <div>
              <div className="dropzone-text-main">Upload Bill Photo</div>
              <div className="dropzone-text-sub">PNG, JPEG, WebP up to 15MB</div>
            </div>
          </div>
        )}
      </div>

      {/* Checklist / Capabilities */}
      <div className="info-section">
        <h3 className="sidebar-title" style={{ marginTop: '0.5rem' }}>Audit Capabilities</h3>
        
        <div className="info-item">
          <CheckCircle2 size={16} />
          <div>
            <strong>Tariff Verification</strong>
            <div>Checks against domestic state tariff slabs, fixed charges & duties.</div>
          </div>
        </div>

        <div className="info-item">
          <CheckCircle2 size={16} />
          <div>
            <strong>Anomaly Detection</strong>
            <div>Flags meter reading jumps, arrears, and unusual surcharge spikes.</div>
          </div>
        </div>

        <div className="info-item">
          <ShieldCheck size={16} />
          <div>
            <strong>Private & Local</strong>
            <div>All OCR and reasoning run locally on your machine via Ollama & MCP.</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
