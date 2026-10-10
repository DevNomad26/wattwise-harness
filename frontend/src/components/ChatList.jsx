import React, { useEffect, useRef } from 'react';
import { Zap } from 'lucide-react';
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
          <div className="welcome-icon-box">
            <Zap size={20} />
          </div>

          <h1 className="welcome-title">Electricity Bill Auditor</h1>

          <p className="welcome-desc">
            Upload an electricity bill photo or type a question. WattWise will analyze meter readings, verify tariff slabs, detect arithmetic errors, and calculate solar ROI.
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
            <Zap size={14} />
          </div>
          <div className="message-content">
            <div className="message-bubble assistant">
              <div className="loading-typing">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '0.35rem' }}>
                  Auditing bill & verifying tariff...
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
