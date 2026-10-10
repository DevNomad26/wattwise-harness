import React, { useEffect, useRef } from 'react';
import { Zap, Sparkles } from 'lucide-react';
import { MessageItem } from './MessageItem';

export function ChatList({ messages, isProcessing, onImageZoom }) {
  const scrollEndRef = useRef(null);

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  if (messages.length === 0) {
    return (
      <div className="messages-scroll-area">
        <div className="welcome-screen">
          <div className="welcome-badge">
            <Sparkles size={16} />
            <span>AI Electricity Bill Auditor</span>
          </div>

          <h1 className="welcome-title">Audit, Verify & Optimize Energy Bills</h1>

          <p className="welcome-desc">
            Upload your electricity bill photo on the left or select a quick action below.
            WattWise will read meter readings, verify state tariff slabs, flag arithmetic discrepancies, and calculate rooftop solar ROI.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="messages-scroll-area">
      {messages.map((msg) => (
        <MessageItem key={msg.id} message={msg} onImageZoom={onImageZoom} />
      ))}

      {isProcessing && (
        <div className="message-bubble-wrapper assistant">
          <div className="avatar assistant">
            <Zap size={18} />
          </div>
          <div className="message-content">
            <div className="message-bubble assistant">
              <div className="loading-typing">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
                <span style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginLeft: '0.4rem' }}>
                  Auditing bill & consulting tariff slabs...
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div ref={scrollEndRef} />
    </div>
  );
}
