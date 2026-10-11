/**
 * API Service for communicating with the WattWise FastAPI backend.
 */

const API_BASE = '/api';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      return { ok: false, error: `HTTP ${res.status}: ${res.statusText}` };
    }
    return await res.json();
  } catch (err) {
    return { ok: false, error: err.message || 'Cannot reach WattWise backend' };
  }
}

export async function sendChatMessage({ message, sessionId, imageFile, signal }) {
  const formData = new FormData();
  formData.append('message', message);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }
  if (imageFile) {
    formData.append('image', imageFile);
  }

  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    body: formData,
    signal,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}

export async function sendChatMessageStream({ message, sessionId, imageFile, signal, onEvent }) {
  const formData = new FormData();
  formData.append('message', message);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }
  if (imageFile) {
    formData.append('image', imageFile);
  }

  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    body: formData,
    signal,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status} ${response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let finalResult = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';

    for (const part of parts) {
      const line = part.trim();
      if (line.startsWith('data: ')) {
        try {
          const item = JSON.parse(line.slice(6));
          if (onEvent) {
            onEvent(item);
          }
          if (item.type === 'done') {
            finalResult = item.data;
          } else if (item.type === 'error') {
            throw new Error(item.data?.error || 'Streaming error');
          }
        } catch (e) {
          if (e.message && !e.message.includes('JSON')) {
            throw e;
          }
        }
      }
    }
  }

  if (buffer.trim().startsWith('data: ')) {
    try {
      const item = JSON.parse(buffer.trim().slice(6));
      if (onEvent) onEvent(item);
      if (item.type === 'done') {
        finalResult = item.data;
      }
    } catch {}
  }

  if (!finalResult) {
    throw new Error('Stream completed without final response.');
  }

  return finalResult;
}

export async function deleteSession(sessionId) {
  if (!sessionId) return;
  try {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    return await res.json();
  } catch (err) {
    console.error('Failed to clear session:', err);
  }
}
