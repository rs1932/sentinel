# 🌐 Frontend Integration Guide

## Overview

This guide provides specific guidance for integrating the Sentinel Authentication API with frontend applications, including React, Vue, Angular, and vanilla JavaScript.

## 🚀 Quick Start

### Basic Authentication Service

```javascript
class AuthService {
    constructor() {
        this.baseURL = 'http://localhost:8000/api/v1/auth';
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
    }

    async login(email, password, tenantCode) {
        const response = await fetch(`${this.baseURL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                tenant_code: tenantCode,
                remember_me: false
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error_description || 'Login failed');
        }

        const tokens = await response.json();
        this.setTokens(tokens.access_token, tokens.refresh_token);
        return tokens;
    }

    setTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    }

    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    isAuthenticated() {
        return !!this.accessToken;
    }

    async logout() {
        if (!this.accessToken) return;

        try {
            await fetch(`${this.baseURL}/logout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.accessToken}`
                },
                body: JSON.stringify({ revoke_all_devices: false })
            });
        } catch (error) {
            console.warn('Logout request failed:', error);
        } finally {
            this.clearTokens();
        }
    }

    async refreshAccessToken() {
        if (!this.refreshToken) {
            throw new Error('No refresh token available');
        }

        const response = await fetch(`${this.baseURL}/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                refresh_token: this.refreshToken
            })
        });

        if (!response.ok) {
            this.clearTokens();
            throw new Error('Token refresh failed');
        }

        const tokens = await response.json();
        this.setTokens(tokens.access_token, tokens.refresh_token);
        return tokens;
    }

    async apiCall(url, options = {}) {
        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        };

        if (this.accessToken) {
            config.headers.Authorization = `Bearer ${this.accessToken}`;
        }

        let response = await fetch(url, config);

        // Handle token expiration
        if (response.status === 401 && this.refreshToken) {
            try {
                await this.refreshAccessToken();
                config.headers.Authorization = `Bearer ${this.accessToken}`;
                response = await fetch(url, config);
            } catch (error) {
                // Refresh failed, redirect to login
                this.clearTokens();
                window.location.href = '/login';
                throw error;
            }
        }

        return response;
    }
}

// Global instance
const authService = new AuthService();
export default authService;
```

## 📱 React Integration

### Auth Context

```jsx
// contexts/AuthContext.js
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import authService from '../services/AuthService';

const AuthContext = createContext();

const authReducer = (state, action) => {
    switch (action.type) {
        case 'LOGIN_START':
            return { ...state, loading: true, error: null };
        case 'LOGIN_SUCCESS':
            return { 
                ...state, 
                loading: false, 
                isAuthenticated: true, 
                user: action.payload.user,
                error: null 
            };
        case 'LOGIN_FAILURE':
            return { 
                ...state, 
                loading: false, 
                isAuthenticated: false, 
                user: null, 
                error: action.payload 
            };
        case 'LOGOUT':
            return { 
                ...state, 
                isAuthenticated: false, 
                user: null, 
                loading: false, 
                error: null 
            };
        case 'SET_LOADING':
            return { ...state, loading: action.payload };
        default:
            return state;
    }
};

export const AuthProvider = ({ children }) => {
    const [state, dispatch] = useReducer(authReducer, {
        isAuthenticated: false,
        user: null,
        loading: true,
        error: null
    });

    useEffect(() => {
        // Check if user is already logged in
        const initializeAuth = async () => {
            if (authService.isAuthenticated()) {
                try {
                    // Validate current token
                    const response = await authService.apiCall(
                        'http://localhost:8000/api/v1/auth/validate'
                    );
                    
                    if (response.ok) {
                        const tokenInfo = await response.json();
                        dispatch({
                            type: 'LOGIN_SUCCESS',
                            payload: { user: tokenInfo }
                        });
                    } else {
                        authService.clearTokens();
                        dispatch({ type: 'LOGOUT' });
                    }
                } catch (error) {
                    authService.clearTokens();
                    dispatch({ type: 'LOGOUT' });
                }
            } else {
                dispatch({ type: 'SET_LOADING', payload: false });
            }
        };

        initializeAuth();
    }, []);

    const login = async (email, password, tenantCode) => {
        dispatch({ type: 'LOGIN_START' });
        try {
            const tokens = await authService.login(email, password, tenantCode);
            
            // Get user info
            const response = await authService.apiCall(
                'http://localhost:8000/api/v1/auth/validate'
            );
            const user = await response.json();

            dispatch({
                type: 'LOGIN_SUCCESS',
                payload: { user }
            });
            
            return tokens;
        } catch (error) {
            dispatch({
                type: 'LOGIN_FAILURE',
                payload: error.message
            });
            throw error;
        }
    };

    const logout = async () => {
        await authService.logout();
        dispatch({ type: 'LOGOUT' });
    };

    const value = {
        ...state,
        login,
        logout,
        apiCall: authService.apiCall.bind(authService)
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
```

### Login Component

```jsx
// components/LoginForm.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const LoginForm = () => {
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        tenantCode: ''
    });
    const [errors, setErrors] = useState({});
    
    const { login, loading, error } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setErrors({});

        try {
            await login(formData.email, formData.password, formData.tenantCode);
            navigate('/dashboard');
        } catch (error) {
            if (error.message.includes('validation')) {
                setErrors({ form: 'Please check your input and try again.' });
            } else if (error.message.includes('credentials')) {
                setErrors({ form: 'Invalid email or password.' });
            } else if (error.message.includes('rate limit')) {
                setErrors({ form: 'Too many attempts. Please try again later.' });
            } else {
                setErrors({ form: 'Login failed. Please try again.' });
            }
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        // Clear errors when user starts typing
        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }));
        }
    };

    return (
        <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className={errors.email ? 'error' : ''}
                />
                {errors.email && <span className="error-text">{errors.email}</span>}
            </div>

            <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className={errors.password ? 'error' : ''}
                />
                {errors.password && <span className="error-text">{errors.password}</span>}
            </div>

            <div className="form-group">
                <label htmlFor="tenantCode">Organization Code</label>
                <input
                    type="text"
                    id="tenantCode"
                    name="tenantCode"
                    value={formData.tenantCode}
                    onChange={handleChange}
                    placeholder="e.g., ACME"
                    required
                    className={errors.tenantCode ? 'error' : ''}
                />
                {errors.tenantCode && <span className="error-text">{errors.tenantCode}</span>}
            </div>

            {errors.form && (
                <div className="form-error">
                    {errors.form}
                </div>
            )}

            <button 
                type="submit" 
                disabled={loading}
                className="login-button"
            >
                {loading ? 'Signing in...' : 'Sign In'}
            </button>
        </form>
    );
};

export default LoginForm;
```

### Protected Route Component

```jsx
// components/ProtectedRoute.jsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return <div>Loading...</div>; // Or your loading component
    }

    if (!isAuthenticated) {
        // Redirect to login page with return url
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
};

export default ProtectedRoute;
```

## 🎯 Vue.js Integration

### Auth Plugin

```javascript
// plugins/auth.js
import AuthService from '@/services/AuthService';

export default {
    install(app) {
        const authService = new AuthService();
        
        app.config.globalProperties.$auth = authService;
        app.provide('auth', authService);
    }
};
```

### Auth Composable

```javascript
// composables/useAuth.js
import { ref, reactive, inject } from 'vue';

export default function useAuth() {
    const authService = inject('auth');
    
    const state = reactive({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null
    });

    const login = async (email, password, tenantCode) => {
        state.loading = true;
        state.error = null;
        
        try {
            const tokens = await authService.login(email, password, tenantCode);
            
            // Validate token and get user info
            const response = await authService.apiCall('/api/v1/auth/validate');
            if (response.ok) {
                state.user = await response.json();
                state.isAuthenticated = true;
            }
            
            return tokens;
        } catch (error) {
            state.error = error.message;
            throw error;
        } finally {
            state.loading = false;
        }
    };

    const logout = async () => {
        await authService.logout();
        state.isAuthenticated = false;
        state.user = null;
        state.error = null;
    };

    return {
        ...state,
        login,
        logout,
        apiCall: authService.apiCall.bind(authService)
    };
}
```

## 🔧 HTTP Interceptors

### Axios Interceptor

```javascript
// utils/axios.js
import axios from 'axios';
import authService from '@/services/AuthService';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        const token = authService.accessToken;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                await authService.refreshAccessToken();
                originalRequest.headers.Authorization = `Bearer ${authService.accessToken}`;
                return api(originalRequest);
            } catch (refreshError) {
                authService.clearTokens();
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default api;
```

## 🔒 Security Best Practices

### Secure Token Storage

```javascript
// For web apps - consider httpOnly cookies
class SecureAuthService extends AuthService {
    constructor() {
        super();
        // Store access token in memory only
        this.accessToken = null;
        // Only store refresh token in localStorage/cookies
    }

    setTokens(accessToken, refreshToken) {
        // Store access token in memory only
        this.accessToken = accessToken;
        
        // Store refresh token securely
        if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken);
        }
    }

    clearTokens() {
        this.accessToken = null;
        localStorage.removeItem('refresh_token');
        // Clear httpOnly cookie if used
        document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; secure; httpOnly';
    }
}
```

### CSRF Protection

```javascript
// Add CSRF token to requests
const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-TOKEN': csrf
    },
    body: JSON.stringify(loginData)
});
```

## 📱 Common Patterns

### Loading States

```jsx
const LoginButton = ({ onClick, loading }) => (
    <button 
        onClick={onClick} 
        disabled={loading}
        className={`btn ${loading ? 'btn-loading' : 'btn-primary'}`}
    >
        {loading && <Spinner size="sm" />}
        {loading ? 'Signing in...' : 'Sign In'}
    </button>
);
```

### Error Handling

```javascript
const handleAuthError = (error) => {
    const errorMap = {
        'authentication_failed': 'Invalid email or password',
        'account_locked': 'Account is temporarily locked',
        'tenant_not_found': 'Organization not found',
        'validation_error': 'Please check your input',
        'rate_limit_exceeded': 'Too many attempts. Try again later'
    };

    return errorMap[error.error] || error.error_description || 'Login failed';
};
```

### Session Timeout

```javascript
// Auto-logout on token expiry
let sessionTimer;

const startSessionTimer = (expiresIn) => {
    clearTimeout(sessionTimer);
    
    // Set timer for 5 minutes before expiry to attempt refresh
    const refreshTime = (expiresIn - 300) * 1000;
    
    sessionTimer = setTimeout(async () => {
        try {
            await authService.refreshAccessToken();
            // Restart timer with new expiry
            startSessionTimer(1800); // 30 minutes
        } catch (error) {
            // Refresh failed, logout user
            await authService.logout();
            window.location.href = '/login';
        }
    }, refreshTime);
};
```

## 🔗 Additional Resources

- [React Router Authentication](https://reactrouter.com/web/example/auth-workflow)
- [Vue Router Navigation Guards](https://router.vuejs.org/guide/advanced/navigation-guards.html)
- [JWT Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

*This guide covers the most common frontend integration patterns. Adapt the examples to your specific framework and requirements.*