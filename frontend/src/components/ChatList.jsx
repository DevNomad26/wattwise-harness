import React, { useEffect, useRef } from 'react';
import { Zap, Cpu } from 'lucide-react';
import { MessageItem } from './MessageItem';

export function ChatList({ messages, isProcessing, liveProgress, onImageZoom }) {
  const scrollEndRef = useRef(null);

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing, liveProgress]);

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
            <div className="message-bubble assistant live-progress-bubble">
              <div className="live-progress-header">
                <div className="loading-typing">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
                <span className="live-progress-action">
                  {liveProgress?.action || 'Auditing bill & verifying tariff...'}
                </span>
              </div>

              {liveProgress?.thought && (
                <div className="live-progress-thought">
                  💭 {liveProgress.thought}
                </div>
              )}

              {liveProgress?.tool && (
                <div className="live-progress-tool">
                  <Cpu size={12} color="var(--emerald-primary)" />
                  <span>Invoking: <code>{liveProgress.tool}</code></span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div ref={scrollEndRef} />
    </div>
  );
}
