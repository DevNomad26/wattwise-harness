import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { BillUploader } from './components/BillUploader';
import { ChatList } from './components/ChatList';
import { QuickChips } from './components/QuickChips';
import { MessageInput } from './components/MessageInput';
import { ImageModal } from './components/ImageModal';
import { checkHealth, sendChatMessage, deleteSession } from './services/api';

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('wattwise_theme') || 'dark');
  const [health, setHealth] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [zoomedImage, setZoomedImage] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Apply Theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('wattwise_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Check Backend Health
  const verifyHealth = useCallback(async () => {
    const res = await checkHealth();
    setHealth(res);
  }, []);

  useEffect(() => {
    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => clearInterval(interval);
  }, [verifyHealth]);

  // File Handling
  const handleFileSelect = (file) => {
    setSelectedFile(file);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleFileRemove = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
  };

  // Reset Session
  const handleNewSession = async () => {
    if (sessionId) {
      await deleteSession(sessionId);
    }
    handleFileRemove();
    setSessionId(null);
    setMessages([]);
  };

  // Send Message
  const handleSendMessage = async (text) => {
    if (!text || isProcessing) return;

    const userMessageId = `user-${Date.now()}`;
    const currentPreview = previewUrl;
    const currentFile = selectedFile;

    // Optimistically append user message
    const newUserMsg = {
      id: userMessageId,
      role: 'user',
      content: text,
      imagePreview: currentPreview,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newUserMsg]);
    setIsProcessing(true);

    try {
      const response = await sendChatMessage({
        message: text,
        sessionId: sessionId,
        imageFile: currentFile,
      });

      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }

      // Add Assistant Message
      const newAssistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        trace: response.trace || [],
        seconds: response.seconds,
        error: response.error,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, newAssistantMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `**Error:** ${err.message || 'Unable to complete request. Please ensure the backend and Ollama are running.'}`,
        error: true,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="app-layout">
      {/* Header */}
      <Navbar
        health={health}
        theme={theme}
        onToggleTheme={toggleTheme}
        onNewSession={handleNewSession}
        isProcessing={isProcessing}
      />

      {/* Main Workspace */}
      <div className="main-workspace">
        {/* Left Sidebar: Photo Uploader & Guidelines */}
        <BillUploader
          selectedFile={selectedFile}
          previewUrl={previewUrl}
          onFileSelect={handleFileSelect}
          onFileRemove={handleFileRemove}
          onImageZoom={(url) => setZoomedImage(url)}
          disabled={isProcessing}
        />

        {/* Right Area: Chat & Reasoning Stream */}
        <main className="chat-container">
          <ChatList
            messages={messages}
            isProcessing={isProcessing}
            onImageZoom={(url) => setZoomedImage(url)}
          />

          {/* Quick Action Chips */}
          <QuickChips
            onSelectPrompt={(prompt) => handleSendMessage(prompt)}
            disabled={isProcessing}
          />

          {/* Input Bar */}
          <MessageInput
            onSendMessage={handleSendMessage}
            isProcessing={isProcessing}
            onFileSelect={handleFileSelect}
            hasImage={!!selectedFile}
          />
        </main>
      </div>

      {/* Bill Image Enlargement Modal */}
      {zoomedImage && (
        <ImageModal imageUrl={zoomedImage} onClose={() => setZoomedImage(null)} />
      )}
    </div>
  );
}
