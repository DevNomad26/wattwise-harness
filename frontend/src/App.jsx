import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ChatList } from './components/ChatList';
import { QuickChips } from './components/QuickChips';
import { MessageInput } from './components/MessageInput';
import { ImageModal } from './components/ImageModal';
import { checkHealth, sendChatMessageStream, deleteSession } from './services/api';

const STORAGE_THREADS_KEY = 'wattwise_chat_threads';
const STORAGE_ACTIVE_KEY = 'wattwise_active_thread_id';

function loadStoredThreads() {
  try {
    const raw = localStorage.getItem(STORAGE_THREADS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function createNewThread() {
  return {
    id: `thread-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
    title: 'New conversation',
    sessionId: null,
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('wattwise_theme') || 'dark');
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    const saved = localStorage.getItem('wattwise_sidebar');
    return saved !== null ? JSON.parse(saved) : true;
  });

  const [threads, setThreads] = useState(loadStoredThreads);
  const [activeThreadId, setActiveThreadId] = useState(() => {
    const savedActive = localStorage.getItem(STORAGE_ACTIVE_KEY);
    const loaded = loadStoredThreads();
    if (savedActive && loaded.some((t) => t.id === savedActive)) {
      return savedActive;
    }
    return loaded.length > 0 ? loaded[0].id : null;
  });

  const [health, setHealth] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [zoomedImage, setZoomedImage] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [liveProgress, setLiveProgress] = useState(null);
  const abortControllerRef = useRef(null);

  // Stop Generation Handler
  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsProcessing(false);
    setLiveProgress(null);
  };

  // Sync threads to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_THREADS_KEY, JSON.stringify(threads));
  }, [threads]);

  // Sync active thread ID to localStorage
  useEffect(() => {
    if (activeThreadId) {
      localStorage.setItem(STORAGE_ACTIVE_KEY, activeThreadId);
    } else {
      localStorage.removeItem(STORAGE_ACTIVE_KEY);
    }
  }, [activeThreadId]);

  // Current active thread object
  const activeThread = threads.find((t) => t.id === activeThreadId) || null;
  const currentMessages = activeThread ? activeThread.messages : [];

  // Apply Theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('wattwise_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const toggleSidebar = () => {
    setSidebarOpen((prev) => {
      const next = !prev;
      localStorage.setItem('wattwise_sidebar', JSON.stringify(next));
      return next;
    });
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

  // New Chat Handler
  const handleNewChat = () => {
    // If currently already on an empty thread, just stay on it
    if (activeThread && activeThread.messages.length === 0) {
      return;
    }
    const newThread = createNewThread();
    setThreads((prev) => [newThread, ...prev]);
    setActiveThreadId(newThread.id);
    handleFileRemove();
  };

  // Select a Chat Thread
  const handleSelectThread = (threadId) => {
    if (threadId === activeThreadId) return;
    setActiveThreadId(threadId);
    handleFileRemove();
  };

  // Delete a Chat Thread
  const handleDeleteThread = async (threadId) => {
    const target = threads.find((t) => t.id === threadId);
    if (target?.sessionId) {
      deleteSession(target.sessionId);
    }

    const remaining = threads.filter((t) => t.id !== threadId);
    setThreads(remaining);

    if (activeThreadId === threadId) {
      if (remaining.length > 0) {
        setActiveThreadId(remaining[0].id);
      } else {
        const fresh = createNewThread();
        setThreads([fresh]);
        setActiveThreadId(fresh.id);
      }
      handleFileRemove();
    }
  };

  // Send Message
  const handleSendMessage = async (text) => {
    if ((!text && !selectedFile) || isProcessing) return;

    let targetThreadId = activeThreadId;
    let targetThread = activeThread;

    // If no active thread exists, initialize one
    if (!targetThread) {
      targetThread = createNewThread();
      targetThreadId = targetThread.id;
      setThreads((prev) => [targetThread, ...prev]);
      setActiveThreadId(targetThreadId);
    }

    const currentPreview = previewUrl;
    const currentFile = selectedFile;
    const promptText = text || 'Please check this attached electricity bill.';

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: promptText,
      imagePreview: currentPreview,
      timestamp: new Date().toISOString(),
    };

    // Update active thread title if this is the first message
    const updatedTitle =
      targetThread.messages.length === 0
        ? promptText.length > 36
          ? `${promptText.slice(0, 36).trim()}...`
          : promptText
        : targetThread.title;

    // Optimistically update messages
    const updatedMessagesWithUser = [...targetThread.messages, userMessage];

    setThreads((prev) =>
      prev.map((t) =>
        t.id === targetThreadId
          ? {
              ...t,
              title: updatedTitle,
              messages: updatedMessagesWithUser,
              updatedAt: new Date().toISOString(),
            }
          : t
      )
    );

    setIsProcessing(true);
    setLiveProgress({ step: 1, action: 'Initializing agent loop & tools...', tool: null });

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const handleStreamEvent = (evt) => {
      if (!evt || !evt.type) return;
      if (evt.type === 'step_start') {
        setLiveProgress((prev) => ({
          ...prev,
          step: evt.data.step,
          maxSteps: evt.data.max_steps,
          action: 'Reasoning next action...',
          tool: null,
        }));
      } else if (evt.type === 'thought') {
        setLiveProgress((prev) => ({
          ...prev,
          step: evt.data.step,
          thought: evt.data.thought,
        }));
      } else if (evt.type === 'tool_call') {
        const toolName = evt.data.tool || 'MCP Tool';
        let actionLabel = `Running ${toolName}...`;
        if (toolName === 'extract_bill_data' || toolName === 'vision') {
          actionLabel = 'Extracting meter readings & data from bill...';
        } else if (toolName === 'get_tariff_info' || toolName === 'tariff') {
          actionLabel = `Checking official tariff slabs for ${evt.data.args?.state || 'state'}...`;
        } else if (toolName === 'compute_bill') {
          actionLabel = `Calculating bill for ${evt.data.args?.units ?? ''} units (${evt.data.args?.state || ''})...`;
        } else if (toolName === 'calculate') {
          actionLabel = 'Running arithmetic verification...';
        } else if (toolName === 'load_skill') {
          actionLabel = `Loading specialized skill: ${evt.data.args?.name || ''}...`;
        }
        setLiveProgress((prev) => ({
          ...prev,
          step: evt.data.step,
          action: actionLabel,
          tool: toolName,
          thought: evt.data.thought || prev?.thought,
        }));
      } else if (evt.type === 'tool_result') {
        setLiveProgress((prev) => ({
          ...prev,
          step: evt.data.step,
          action: `Completed ${evt.data.tool}, reasoning next action...`,
        }));
      } else if (evt.type === 'final_answer') {
        setLiveProgress((prev) => ({
          ...prev,
          action: 'Formulating final verified response...',
          tool: null,
        }));
      }
    };

    try {
      const response = await sendChatMessageStream({
        message: promptText,
        sessionId: targetThread.sessionId,
        imageFile: currentFile,
        signal: controller.signal,
        onEvent: handleStreamEvent,
      });

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        trace: response.trace || [],
        seconds: response.seconds,
        error: response.error,
        timestamp: new Date().toISOString(),
      };

      const finalMessages = [...updatedMessagesWithUser, assistantMessage];

      setThreads((prev) =>
        prev.map((t) =>
          t.id === targetThreadId
            ? {
                ...t,
                sessionId: response.session_id || t.sessionId,
                messages: finalMessages,
                updatedAt: new Date().toISOString(),
              }
            : t
        )
      );

      // Clear staged file after successful upload so follow-ups don't re-upload
      handleFileRemove();
    } catch (err) {
      if (err.name === 'AbortError' || err.message?.toLowerCase().includes('abort')) {
        const stoppedMsg = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: '_Audit generation stopped by user._',
          seconds: 0,
          timestamp: new Date().toISOString(),
        };

        setThreads((prev) =>
          prev.map((t) =>
            t.id === targetThreadId
              ? {
                  ...t,
                  messages: [...updatedMessagesWithUser, stoppedMsg],
                  updatedAt: new Date().toISOString(),
                }
              : t
          )
        );
        return;
      }

      console.error('Chat error:', err);
      const errorMsg = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `**Error:** ${err.message || 'Unable to connect to backend server. Please verify that Ollama and FastAPI are running.'}`,
        error: true,
        timestamp: new Date().toISOString(),
      };

      setThreads((prev) =>
        prev.map((t) =>
          t.id === targetThreadId
            ? {
                ...t,
                messages: [...updatedMessagesWithUser, errorMsg],
                updatedAt: new Date().toISOString(),
              }
            : t
        )
      );
    } finally {
      setIsProcessing(false);
      setLiveProgress(null);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="app-layout">
      {/* Header */}
      <Navbar
        health={health}
        theme={theme}
        onToggleTheme={toggleTheme}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={toggleSidebar}
      />

      {/* Main Workspace */}
      <div className="main-workspace">
        {/* Left Sidebar: New Chat & Chat History */}
        <Sidebar
          threads={threads}
          activeThreadId={activeThreadId}
          onSelectThread={handleSelectThread}
          onNewChat={handleNewChat}
          onDeleteThread={handleDeleteThread}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Right Area: Chat Stream */}
        <main className="chat-container">
          <ChatList
            messages={currentMessages}
            isProcessing={isProcessing}
            liveProgress={liveProgress}
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
            onStop={handleStopGeneration}
            isProcessing={isProcessing}
            selectedFile={selectedFile}
            onFileSelect={handleFileSelect}
            onFileRemove={handleFileRemove}
          />
        </main>
      </div>

      {/* Bill Image Zoom Modal */}
      {zoomedImage && (
        <ImageModal imageUrl={zoomedImage} onClose={() => setZoomedImage(null)} />
      )}
    </div>
  );
}
