import React, { useRef } from 'react';
import { UploadCloud, Trash2, Maximize2, ShieldCheck, CheckCircle2, ChevronLeft } from 'lucide-react';

export function BillUploader({
  selectedFile,
  previewUrl,
  onFileSelect,
  onFileRemove,
  onImageZoom,
  disabled,
  isOpen,
  onClose,
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
    <aside className={`sidebar ${!isOpen ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <h2 className="sidebar-title">Electricity Bill</h2>
        <button
          className="icon-btn-minimal"
          onClick={onClose}
          title="Collapse sidebar"
          style={{ width: '24px', height: '24px', border: 'none' }}
        >
          <ChevronLeft size={14} />
        </button>
      </div>

      <div>
        {/* If file is selected, show preview card; else show dropzone */}
        {selectedFile && previewUrl ? (
          <div className="bill-preview-card">
            <div className="preview-img-wrapper" onClick={() => onImageZoom(previewUrl)}>
              <img src={previewUrl} alt="Electricity Bill preview" />
              <div className="preview-zoom-overlay">
                <Maximize2 size={14} />
                <span>Zoom</span>
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
                className="icon-btn-minimal"
                onClick={onFileRemove}
                disabled={disabled}
                title="Remove photo"
                style={{ width: '28px', height: '28px' }}
              >
                <Trash2 size={13} />
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
              <UploadCloud size={18} />
            </div>
            <div>
              <div className="dropzone-text-main">Upload Bill Photo</div>
              <div className="dropzone-text-sub">PNG, JPEG, WebP up to 15MB</div>
            </div>
          </div>
        )}
      </div>

      {/* Guidelines / Capabilities */}
      <div className="info-section">
        <h3 className="sidebar-title">Audit Engine</h3>

        <div className="info-item">
          <CheckCircle2 size={14} />
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>Tariff Calculation</strong>
            <div>Domestic state slabs, fixed charges, and duty validation.</div>
          </div>
        </div>

        <div className="info-item">
          <CheckCircle2 size={14} />
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>Anomaly Warnings</strong>
            <div>Detects meter reading skips, arithmetic mismatches, and arrears.</div>
          </div>
        </div>

        <div className="info-item">
          <ShieldCheck size={14} />
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>Local & Private</strong>
            <div>OCR, math tools, and LLM reasoning run 100% locally on your machine.</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
