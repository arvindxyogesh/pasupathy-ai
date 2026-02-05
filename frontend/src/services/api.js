import axios from 'axios';

// Use environment variable for API base URL, default to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

// Log API configuration (only in development)
if (process.env.NODE_ENV === 'development') {
  console.log('🔗 API Base URL:', API_BASE_URL);
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Format error message for display to user
 * @param {Error} error - Axios error object
 * @returns {string} - User-friendly error message
 */
const formatErrorMessage = (error) => {
  // Network error (no response from server)
  if (!error.response) {
    if (error.code === 'ECONNABORTED') {
      return 'Request timeout. Please try again.';
    }
    return 'Cannot connect to server. Please check your connection.';
  }

  // Server error with message
  if (error.response.data?.message) {
    return error.response.data.message;
  }

  // HTTP status codes
  const status = error.response.status;
  switch (status) {
    case 400:
      return 'Bad request. Please check your input.';
    case 401:
      return 'Unauthorized. Please login again.';
    case 403:
      return 'Forbidden. You do not have permission.';
    case 404:
      return 'Resource not found.';
    case 500:
      return 'Server error. Please try again later.';
    case 503:
      return 'Service unavailable. Please try again later.';
    default:
      return `Error: ${status} ${error.response.statusText || 'Unknown'}`;
  }
};

/**
 * Add response interceptor for better error handling
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('🚨 API Error:', {
      status: error.response?.status,
      message: error.message,
      data: error.response?.data,
    });
    throw error;
  }
);

export const HealthCheck = async () => {
  try {
    const response = await api.get('/health', { timeout: 5000 });
    return response.data;
  } catch (error) {
    const message = formatErrorMessage(error);
    const err = new Error(message);
    err.originalError = error;
    throw err;
  }
};

export const sendMessage = async (message, sessionId = null) => {
  try {
    if (!message?.trim()) {
      throw new Error('Message cannot be empty');
    }
    
    const response = await api.post('/chat', {
      message,
      session_id: sessionId
    }, { timeout: 30000 });
    
    if (!response.data) {
      throw new Error('Invalid response from server');
    }

    // If backend signals error in response, throw with backend message
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'An error occurred.');
    }
    
    return response.data;
  } catch (error) {
    const message = formatErrorMessage(error);
    const err = new Error(message);
    err.originalError = error;
    throw err;
  }
};

export const getChatHistory = async (sessionId) => {
  try {
    if (!sessionId) {
      throw new Error('Session ID is required');
    }
    
    const response = await api.get(`/chat/history?session_id=${sessionId}`, { timeout: 10000 });
    return response.data;
  } catch (error) {
    const message = formatErrorMessage(error);
    const err = new Error(message);
    err.originalError = error;
    throw err;
  }
};

export const getChatSessions = async () => {
  try {
    const response = await api.get('/chat/sessions', { timeout: 10000 });
    return response.data;
  } catch (error) {
    const message = formatErrorMessage(error);
    const err = new Error(message);
    err.originalError = error;
    throw err;
  }
};

export const clearChat = async (sessionId) => {
  try {
    if (!sessionId) {
      throw new Error('Session ID is required');
    }
    
    const response = await api.post('/chat/clear', { session_id: sessionId }, { timeout: 10000 });
    return response.data;
  } catch (error) {
    const message = formatErrorMessage(error);
    const err = new Error(message);
    err.originalError = error;
    throw err;
  }
};

export const deleteChat = async (sessionId) => {
  try {
    if (!sessionId) {
      throw new Error('Session ID is required');
    }
    
    const response = await api.delete('/chat/delete', { 
      data: { session_id: sessionId },
      timeout: 10000
    });
    return response.data;
  } catch (error) {
    const message = formatErrorMessage(error);
    const err = new Error(message);
    err.originalError = error;
    throw err;
  }
};

/**
 * Upload dataset to backend
 * Expected format: Array of objects, each with:
 * - text (required): Combined Q&A format "Question: ...\nAnswer: ..."
 * - question: The question text
 * - answer: The answer text
 * - category, subcategory, difficulty: Optional metadata
 * - source: Origin of the data
 */
export const uploadDataset = async (file) => {
  try {
    if (!file) {
      throw new Error('File is required');
    }
    
    // Validate file size (limit to 100MB for large datasets)
    const MAX_FILE_SIZE = 100 * 1024 * 1024;
    if (file.size > MAX_FILE_SIZE) {
      throw new Error('File size exceeds 100MB limit');
    }
    
    // Validate file type
    if (!file.name.endsWith('.json')) {
      throw new Error('Only JSON files are supported');
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/dataset/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });
    
    if (!response.data) {
      throw new Error('Invalid response from server');
    }
    
    return response.data;
  } catch (error) {
    const message = formatErrorMessage(error);
    const err = new Error(message);
    err.originalError = error;
    throw err;
  }
};

export const getDatasetStats = async () => {
  try {
    const response = await api.get('/dataset/stats', { timeout: 10000 });
    return response.data;
  } catch (error) {
    const message = formatErrorMessage(error);
    const err = new Error(message);
    err.originalError = error;
    throw err;
  }
};

export const regenerateResponse = async (sessionId) => {
  const response = await fetch(`${API_BASE_URL}/chat/regenerate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return response.json();
};

export const editMessage = async (sessionId, messageId, content) => {
  const response = await fetch(`${API_BASE_URL}/chat/edit`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, content }),
  });
  return response.json();
};

export const deleteSession = async (sessionId) => {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  return response.json();
};

export const renameSession = async (sessionId, title) => {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/rename`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  return response.json();
};

export const searchSessions = async (query) => {
  const response = await fetch(`${API_BASE_URL}/chat/search?q=${encodeURIComponent(query)}`);
  return response.json();
};

export const exportSession = async (sessionId, format = 'json') => {
  const response = await fetch(`${API_BASE_URL}/chat/export/${sessionId}?format=${format}`);
  if (format === 'markdown') {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_${sessionId}.md`;
    a.click();
    return { status: 'success' };
  }
  return response.json();
};

export const sendMessageStream = async (message, sessionId, onChunk) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, stream: true }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        onChunk(data);
      }
    }
  }
};

export const generateFollowUpQuestions = async (userMessage, botResponse, queryContext = null) => {
  try {
    const response = await api.post('/chat/followup', {
      user_message: userMessage,
      bot_response: botResponse,
      query_context: queryContext
    }, { timeout: 10000 });
    
    return response.data;
  } catch (error) {
    console.error('Follow-up generation error:', error);
    // Return generic fallback on error
    return {
      status: 'success',
      questions: [
        "Tell me more about that",
        "What else should I know?",
        "Can you elaborate?"
      ]
    };
  }
};