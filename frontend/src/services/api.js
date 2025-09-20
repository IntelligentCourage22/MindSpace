import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with better error handling
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API with better error handling
export const authAPI = {
  login: async (credentials) => {
    try {
      console.log('API: Attempting login to', `${API_BASE_URL}/auth/login/`);
      const response = await api.post('/auth/login/', credentials);
      console.log('API: Login successful', response.data);
      return response;
    } catch (error) {
      console.error('API: Login failed', error);
      throw error;
    }
  },
  
  register: async (userData) => {
    try {
      console.log('API: Attempting registration to', `${API_BASE_URL}/auth/register/`);
      const response = await api.post('/auth/register/', userData);
      console.log('API: Registration successful', response.data);
      return response;
    } catch (error) {
      console.error('API: Registration failed', error);
      throw error;
    }
  },
  
  createAnonymousUser: async () => {
    try {
      console.log('API: Creating anonymous user at', `${API_BASE_URL}/auth/anonymous/`);
      const response = await api.post('/auth/anonymous/');
      console.log('API: Anonymous user created', response.data);
      return response;
    } catch (error) {
      console.error('API: Anonymous user creation failed', error);
      throw error;
    }
  },
  
  logout: () => api.post('/auth/logout/'),
  getProfile: () => api.get('/auth/profile/').then(res => res.data),
  updateProfile: (data) => api.patch('/auth/profile/', data).then(res => res.data),
  updateAlias: (alias) => api.post('/auth/update-alias/', { alias }).then(res => res.data),
  getStats: () => api.get('/auth/stats/').then(res => res.data),
};

// Test API connection
export const testAPIConnection = async () => {
  try {
    console.log('Testing API connection to:', API_BASE_URL);
    const response = await axios.get(`${API_BASE_URL.replace('/api', '')}/admin/`);
    console.log('API connection test successful');
    return true;
  } catch (error) {
    console.error('API connection test failed:', error);
    return false;
  }
};

export default api;