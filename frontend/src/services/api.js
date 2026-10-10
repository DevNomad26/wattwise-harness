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

export async function sendChatMessage({ message, sessionId, imageFile }) {
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
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status} ${response.statusText}`);
  }

  return await response.json();
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
