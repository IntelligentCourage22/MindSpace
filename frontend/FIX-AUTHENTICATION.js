#!/usr/bin/env node
/**
 * FIX AUTHENTICATION - This will fix your login/signup issues
 */

const fs = require('fs');
const path = require('path');

function fixAuthentication() {
    console.log('🔐 FIXING AUTHENTICATION SYSTEM');
    console.log('================================');
    
    // 1. Create a working authentication context with better error handling
    console.log('🔧 Creating improved AuthContext...');
    const improvedAuthContext = `import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const userData = await authAPI.getProfile();
          setUser(userData);
        } catch (error) {
          console.error('Auth initialization failed:', error);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setToken(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [token]);

  const login = async (credentials) => {
    try {
      console.log('Attempting login with:', credentials);
      const response = await authAPI.login(credentials);
      console.log('Login response:', response);
      
      const { access, refresh, user: userData } = response.data;
      
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      setToken(access);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.response?.data?.error || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      console.log('Attempting registration with:', userData);
      const response = await authAPI.register(userData);
      console.log('Registration response:', response);
      
      const { access, refresh, user: newUser } = response.data;
      
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      setToken(access);
      setUser(newUser);
      
      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.response?.data?.error || 'Registration failed' 
      };
    }
  };

  const createAnonymousUser = async () => {
    try {
      console.log('Creating anonymous user...');
      const response = await authAPI.createAnonymousUser();
      console.log('Anonymous user response:', response);
      
      const { access, refresh, user: userData } = response.data;
      
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      setToken(access);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      console.error('Anonymous login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.response?.data?.error || 'Anonymous login failed' 
      };
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setToken(null);
      setUser(null);
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const updatedUser = await authAPI.updateProfile(profileData);
      setUser(updatedUser);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Profile update failed' 
      };
    }
  };

  const value = {
    user,
    loading,
    token,
    login,
    register,
    createAnonymousUser,
    logout,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};`;

    fs.writeFileSync(path.join(__dirname, 'src', 'contexts', 'AuthContext.js'), improvedAuthContext);
    console.log('✅ Improved AuthContext created');
    
    // 2. Create a working API service with better error handling
    console.log('🔧 Creating improved API service...');
    const improvedAPIService = `import axios from 'axios';

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
      config.headers.Authorization = \`Bearer \${token}\`;
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
          const response = await axios.post(\`\${API_BASE_URL}/auth/token/refresh/\`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = \`Bearer \${access}\`;
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
      console.log('API: Attempting login to', \`\${API_BASE_URL}/auth/login/\`);
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
      console.log('API: Attempting registration to', \`\${API_BASE_URL}/auth/register/\`);
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
      console.log('API: Creating anonymous user at', \`\${API_BASE_URL}/auth/anonymous/\`);
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
    const response = await axios.get(\`\${API_BASE_URL.replace('/api', '')}/admin/\`);
    console.log('API connection test successful');
    return true;
  } catch (error) {
    console.error('API connection test failed:', error);
    return false;
  }
};

export default api;`;

    fs.writeFileSync(path.join(__dirname, 'src', 'services', 'api.js'), improvedAPIService);
    console.log('✅ Improved API service created');
    
    // 3. Create a working login page with better error handling
    console.log('🔧 Creating improved login page...');
    const improvedLoginPage = `import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';

const LoginPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [apiStatus, setApiStatus] = useState('checking');
  const { login, createAnonymousUser, user } = useAuth();
  const navigate = useNavigate();

  // Check if user is already logged in
  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  // Test API connection on component mount
  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await fetch('http://localhost:8000/admin/', { 
          method: 'HEAD',
          mode: 'no-cors' 
        });
        setApiStatus('connected');
      } catch (error) {
        console.error('Backend not reachable:', error);
        setApiStatus('disconnected');
      }
    };
    
    testConnection();
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    console.log('Login attempt with:', formData);
    const result = await login(formData);
    console.log('Login result:', result);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleAnonymousLogin = async () => {
    setLoading(true);
    setError('');

    console.log('Anonymous login attempt');
    const result = await createAnonymousUser();
    console.log('Anonymous login result:', result);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-md space-y-8">
        {/* API Status Indicator */}
        {apiStatus === 'disconnected' && (
          <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            <strong>Backend Not Connected!</strong><br />
            Make sure your Django backend is running on http://localhost:8000
          </div>
        )}
        
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="h-16 w-16 rounded-full bg-primary flex items-center justify-center">
                <span className="text-2xl">💙</span>
              </div>
              <div className="absolute -top-1 -right-1 h-6 w-6 rounded-full bg-yellow-400 flex items-center justify-center">
                <span className="text-sm">✨</span>
              </div>
            </div>
          </div>
          <h2 className="text-3xl font-bold text-foreground">Welcome to MindSpace</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Your safe space for mental wellness and peer support
          </p>
        </div>

        {/* Login Form */}
        <Card>
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>
              Enter your credentials to access your account
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 text-sm text-destructive-foreground bg-destructive rounded-md">
                  <strong>Error:</strong> {error}
                </div>
              )}
              
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email
                </label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Enter your email"
                />
              </div>
              
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  Password
                </label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                />
              </div>
              
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
            
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">Or</span>
                </div>
              </div>
              
              <div className="mt-6 space-y-3">
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  onClick={handleAnonymousLogin}
                  disabled={loading}
                >
                  {loading ? 'Creating account...' : 'Continue Anonymously'}
                </Button>
                
                <p className="text-xs text-center text-muted-foreground">
                  Get a random alias and start using MindSpace immediately
                </p>
              </div>
            </div>
            
            <div className="mt-6 text-center">
              <p className="text-sm text-muted-foreground">
                Don't have an account?{' '}
                <Link
                  to="/register"
                  className="font-medium text-primary hover:text-primary/80"
                >
                  Sign up
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
        
        {/* Debug Info */}
        <div className="text-center text-xs text-muted-foreground">
          <p>API Status: {apiStatus}</p>
          <p>Backend: http://localhost:8000</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;`;

    fs.writeFileSync(path.join(__dirname, 'src', 'pages', 'LoginPage.js'), improvedLoginPage);
    console.log('✅ Improved login page created');
    
    // 4. Create a working register page
    console.log('🔧 Creating improved register page...');
    const improvedRegisterPage = `import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password_confirm: '',
    alias: '',
    bio: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { register, user } = useAuth();
  const navigate = useNavigate();

  // Check if user is already logged in
  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.password !== formData.password_confirm) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    console.log('Registration attempt with:', formData);
    const result = await register(formData);
    console.log('Registration result:', result);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="h-16 w-16 rounded-full bg-primary flex items-center justify-center">
                <span className="text-2xl">💙</span>
              </div>
              <div className="absolute -top-1 -right-1 h-6 w-6 rounded-full bg-yellow-400 flex items-center justify-center">
                <span className="text-sm">✨</span>
              </div>
            </div>
          </div>
          <h2 className="text-3xl font-bold text-foreground">Join MindSpace</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Create your account and start your wellness journey
          </p>
        </div>

        {/* Register Form */}
        <Card>
          <CardHeader>
            <CardTitle>Create Account</CardTitle>
            <CardDescription>
              Fill in your details to get started
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 text-sm text-destructive-foreground bg-destructive rounded-md">
                  <strong>Error:</strong> {error}
                </div>
              )}
              
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email
                </label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Enter your email"
                />
              </div>
              
              <div className="space-y-2">
                <label htmlFor="alias" className="text-sm font-medium">
                  Display Name (Optional)
                </label>
                <Input
                  id="alias"
                  name="alias"
                  type="text"
                  value={formData.alias}
                  onChange={handleChange}
                  placeholder="Choose a display name"
                />
              </div>
              
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  Password
                </label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Create a password"
                />
              </div>
              
              <div className="space-y-2">
                <label htmlFor="password_confirm" className="text-sm font-medium">
                  Confirm Password
                </label>
                <Input
                  id="password_confirm"
                  name="password_confirm"
                  type="password"
                  required
                  value={formData.password_confirm}
                  onChange={handleChange}
                  placeholder="Confirm your password"
                />
              </div>
              
              <div className="space-y-2">
                <label htmlFor="bio" className="text-sm font-medium">
                  Bio (Optional)
                </label>
                <textarea
                  id="bio"
                  name="bio"
                  rows={3}
                  value={formData.bio}
                  onChange={handleChange}
                  placeholder="Tell us a bit about yourself"
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Creating account...' : 'Create Account'}
              </Button>
            </form>
            
            <div className="mt-6 text-center">
              <p className="text-sm text-muted-foreground">
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="font-medium text-primary hover:text-primary/80"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
        
        {/* Features */}
        <div className="text-center">
          <p className="text-xs text-muted-foreground">
            Join a supportive community focused on mental wellness
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;`;

    fs.writeFileSync(path.join(__dirname, 'src', 'pages', 'RegisterPage.js'), improvedRegisterPage);
    console.log('✅ Improved register page created');
    
    // 5. Create environment file
    console.log('🔧 Creating environment file...');
    const envContent = `# Frontend Environment Variables
REACT_APP_API_URL=http://localhost:8000/api

# For production, set this to your deployed backend URL
# REACT_APP_API_URL=https://your-backend-url.com/api`;

    fs.writeFileSync(path.join(__dirname, '.env'), envContent);
    console.log('✅ Environment file created');
    
    console.log('\n🎉 AUTHENTICATION FIX COMPLETED!');
    console.log('\n📋 What I fixed:');
    console.log('✅ Improved error handling in AuthContext');
    console.log('✅ Better API service with debugging');
    console.log('✅ Enhanced login page with backend status check');
    console.log('✅ Improved register page with validation');
    console.log('✅ Added comprehensive error messages');
    console.log('✅ Created environment configuration');
    console.log('\n🚀 Your authentication should now work!');
    console.log('\n📋 Next steps:');
    console.log('1. Make sure your Django backend is running:');
    console.log('   cd backend && python manage.py runserver');
    console.log('2. Start your React frontend:');
    console.log('   cd frontend && npm start');
    console.log('3. Visit http://localhost:3000');
    console.log('4. Try logging in or creating an account!');
    console.log('\n🔍 If it still doesn\'t work:');
    console.log('- Check browser console for errors');
    console.log('- Make sure backend is running on port 8000');
    console.log('- Check CORS settings in Django');
    
    return true;
}

if (require.main === module) {
    if (fixAuthentication()) {
        process.exit(0);
    } else {
        process.exit(1);
    }
}

module.exports = { fixAuthentication };
