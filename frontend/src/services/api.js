import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatAPI = {
  sendMessage: async (message) => {
    const response = await api.post('/api/chat', { message });
    return response.data;
  },
};

export const uploadAPI = {
  uploadCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  resetData: async () => {
    const response = await api.delete('/api/reset');
    return response.data;
  },
};

export const analyticsAPI = {
  getSentiment: async () => {
    const response = await api.get('/api/sentiment');
    return response.data;
  },
  
  getAnalytics: async () => {
    const response = await api.get('/api/analytics');
    return response.data;
  },
};

export const healthAPI = {
  check: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },
  
  checkDataStatus: async () => {
    const response = await api.get('/api/data-status');
    return response.data;
  },
};

export default api;
