# 💡 Authentication Examples

## Complete Authentication Flows

### 1. Standard User Login Flow

```javascript
// Complete login example with error handling
async function loginUser() {
    const loginForm = {
        email: 'john.doe@acme.com',
        password: 'MySecurePass123!',
        tenant_code: 'ACME',
        remember_me: false
    };

    try {
        // Step 1: Login
        const response = await fetch('http://localhost:8000/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(loginForm)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(`Login failed: ${error.error_description}`);
        }

        const tokens = await response.json();
        console.log('Login successful!', {
            access_token: tokens.access_token,
            expires_in: tokens.expires_in,
            user_id: tokens.user_id,
            tenant_id: tokens.tenant_id,
            scopes: tokens.scope
        });

        // Step 2: Store tokens securely
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);

        // Step 3: Validate token (optional)
        const validation = await validateToken(tokens.access_token);
        console.log('Token validation:', validation);

        return tokens;

    } catch (error) {
        console.error('Login error:', error.message);
        throw error;
    }
}

// Call the function
loginUser()
    .then(tokens => console.log('User logged in successfully'))
    .catch(error => console.log('Login failed:', error.message));
```

### 2. Service Account Authentication

```javascript
async function authenticateServiceAccount() {
    const serviceAccountData = {
        client_id: 'svc_abc123456',
        client_secret: 'sa_secret_key_here',
        tenant_id: 'ACME',
        scope: 'api:read api:write tenant:admin'
    };

    try {
        const response = await fetch('http://localhost:8000/api/v1/auth/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(serviceAccountData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(`Service account auth failed: ${error.error_description}`);
        }

        const tokens = await response.json();
        console.log('Service account authenticated!', {
            access_token: tokens.access_token,
            expires_in: tokens.expires_in,
            scopes: tokens.scope
        });

        // Store token for API calls
        localStorage.setItem('service_token', tokens.access_token);
        
        return tokens;

    } catch (error) {
        console.error('Service account auth error:', error.message);
        throw error;
    }
}
```

### 3. Token Refresh Flow

```javascript
async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
        throw new Error('No refresh token available');
    }

    try {
        const response = await fetch('http://localhost:8000/api/v1/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                refresh_token: refreshToken
            })
        });

        if (!response.ok) {
            const error = await response.json();
            // Refresh failed, clear tokens and redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            throw new Error(`Token refresh failed: ${error.error_description}`);
        }

        const tokens = await response.json();
        console.log('Token refreshed successfully!');

        // Update stored tokens
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);

        return tokens;

    } catch (error) {
        console.error('Token refresh error:', error.message);
        // Redirect to login page
        window.location.href = '/login';
        throw error;
    }
}
```

### 4. Automatic Token Refresh with API Calls

```javascript
async function apiCallWithAutoRefresh(url, options = {}) {
    const accessToken = localStorage.getItem('access_token');
    
    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
            ...options.headers
        }
    };

    try {
        let response = await fetch(url, config);

        // If token expired, try to refresh
        if (response.status === 401) {
            console.log('Access token expired, refreshing...');
            
            try {
                const newTokens = await refreshAccessToken();
                
                // Retry the original request with new token
                config.headers.Authorization = `Bearer ${newTokens.access_token}`;
                response = await fetch(url, config);
                
            } catch (refreshError) {
                console.error('Token refresh failed:', refreshError.message);
                // Redirect to login
                window.location.href = '/login';
                throw refreshError;
            }
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(`API call failed: ${error.detail || response.statusText}`);
        }

        return response.json();

    } catch (error) {
        console.error('API call error:', error.message);
        throw error;
    }
}

// Example usage
async function getTenants() {
    try {
        const tenants = await apiCallWithAutoRefresh('http://localhost:8000/api/v1/tenants/');
        console.log('Tenants:', tenants);
        return tenants;
    } catch (error) {
        console.error('Failed to get tenants:', error.message);
    }
}
```

### 5. Session Management

```javascript
// Get user's active sessions
async function getUserSessions() {
    const accessToken = localStorage.getItem('access_token');

    try {
        const response = await fetch('http://localhost:8000/api/v1/auth/me/tokens', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to get sessions');
        }

        const sessions = await response.json();
        console.log('Active sessions:', sessions);
        
        sessions.forEach((session, index) => {
            console.log(`Session ${index + 1}:`, {
                id: session.id,
                device: session.device_info.platform,
                ip: session.device_info.ip_address,
                created: new Date(session.created_at).toLocaleString(),
                lastUsed: session.last_used_at ? new Date(session.last_used_at).toLocaleString() : 'Never',
                expires: new Date(session.expires_at).toLocaleString()
            });
        });

        return sessions;

    } catch (error) {
        console.error('Error getting sessions:', error.message);
        throw error;
    }
}

// Revoke specific session
async function revokeSession(sessionId) {
    const accessToken = localStorage.getItem('access_token');

    try {
        const response = await fetch(`http://localhost:8000/api/v1/auth/me/tokens/${sessionId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to revoke session');
        }

        const result = await response.json();
        console.log('Session revoked:', result.message);
        return result;

    } catch (error) {
        console.error('Error revoking session:', error.message);
        throw error;
    }
}

// Logout from all devices except current
async function logoutFromAllDevices(keepCurrent = true) {
    const accessToken = localStorage.getItem('access_token');

    try {
        const response = await fetch(`http://localhost:8000/api/v1/auth/me/tokens?keep_current=${keepCurrent}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to logout from all devices');
        }

        const result = await response.json();
        console.log(`Logged out from all devices: ${result.message}`);
        return result;

    } catch (error) {
        console.error('Error logging out from all devices:', error.message);
        throw error;
    }
}
```

### 6. Complete User Logout

```javascript
async function logoutUser() {
    const accessToken = localStorage.getItem('access_token');

    try {
        // Step 1: Server-side logout (revokes tokens)
        if (accessToken) {
            await fetch('http://localhost:8000/api/v1/auth/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify({
                    revoke_all_devices: false  // Set to true to logout from all devices
                })
            });
        }
    } catch (error) {
        // Logout endpoint always returns success, but handle network errors
        console.warn('Logout request failed:', error.message);
    } finally {
        // Step 2: Clear local storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Step 3: Clear any app state
        console.log('User logged out successfully');
        
        // Step 4: Redirect to login page
        window.location.href = '/login';
    }
}
```

### 7. Token Validation

```javascript
async function validateToken(token = null) {
    const accessToken = token || localStorage.getItem('access_token');
    
    if (!accessToken) {
        return { valid: false, error: 'No token available' };
    }

    try {
        const response = await fetch('http://localhost:8000/api/v1/auth/validate', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            return { valid: false, error: 'Token validation failed' };
        }

        const validation = await response.json();
        console.log('Token validation result:', validation);
        
        return {
            valid: validation.valid,
            user_id: validation.user_id,
            tenant_id: validation.tenant_id,
            scopes: validation.scopes,
            expires_at: validation.expires_at,
            is_service_account: validation.is_service_account
        };

    } catch (error) {
        console.error('Token validation error:', error.message);
        return { valid: false, error: error.message };
    }
}
```

### 8. Password Requirements Check

```javascript
async function getPasswordRequirements() {
    try {
        const response = await fetch('http://localhost:8000/api/v1/auth/password-requirements');
        
        if (!response.ok) {
            throw new Error('Failed to get password requirements');
        }

        const requirements = await response.json();
        console.log('Password requirements:', requirements);
        
        return requirements;

    } catch (error) {
        console.error('Error getting password requirements:', error.message);
        throw error;
    }
}

// Validate password against requirements
async function validatePassword(password) {
    const requirements = await getPasswordRequirements();
    const errors = [];

    if (password.length < requirements.min_length) {
        errors.push(`Password must be at least ${requirements.min_length} characters long`);
    }

    if (requirements.require_uppercase && !/[A-Z]/.test(password)) {
        errors.push('Password must contain at least one uppercase letter');
    }

    if (requirements.require_lowercase && !/[a-z]/.test(password)) {
        errors.push('Password must contain at least one lowercase letter');
    }

    if (requirements.require_numbers && !/\d/.test(password)) {
        errors.push('Password must contain at least one number');
    }

    if (requirements.require_symbols && !/[^A-Za-z0-9]/.test(password)) {
        errors.push('Password must contain at least one special character');
    }

    // Check forbidden patterns
    for (const pattern of requirements.forbidden_patterns || []) {
        if (password.toLowerCase().includes(pattern.toLowerCase())) {
            errors.push(`Password cannot contain '${pattern}'`);
        }
    }

    return {
        valid: errors.length === 0,
        errors: errors,
        strength: calculatePasswordStrength(password, requirements)
    };
}

function calculatePasswordStrength(password, requirements) {
    let score = 0;
    
    if (password.length >= requirements.min_length) score += 20;
    if (password.length >= 12) score += 10;
    if (/[A-Z]/.test(password)) score += 15;
    if (/[a-z]/.test(password)) score += 15;
    if (/\d/.test(password)) score += 15;
    if (/[^A-Za-z0-9]/.test(password)) score += 15;
    if (password.length >= 16) score += 10;

    if (score >= 80) return 'strong';
    if (score >= 60) return 'medium';
    if (score >= 40) return 'weak';
    return 'very-weak';
}
```

### 9. Error Handling Examples

```javascript
// Comprehensive error handler
function handleAuthError(error, response) {
    if (!response) {
        // Network error
        return {
            message: 'Network error. Please check your connection.',
            type: 'network',
            retryable: true
        };
    }

    const status = response.status;
    const errorData = error;

    switch (errorData.error) {
        case 'authentication_failed':
            return {
                message: 'Invalid email or password.',
                type: 'credentials',
                retryable: true
            };

        case 'account_locked':
            return {
                message: `Account locked. Try again in ${errorData.retry_after / 60} minutes.`,
                type: 'locked',
                retryable: false,
                retryAfter: errorData.retry_after
            };

        case 'rate_limit_exceeded':
            return {
                message: `Too many attempts. Please wait ${errorData.retry_after} seconds.`,
                type: 'rate_limit',
                retryable: false,
                retryAfter: errorData.retry_after
            };

        case 'tenant_not_found':
            return {
                message: 'Organization not found. Please check your organization code.',
                type: 'tenant',
                retryable: true,
                field: 'tenant_code'
            };

        case 'validation_error':
            return {
                message: 'Please correct the errors below.',
                type: 'validation',
                retryable: true,
                fieldErrors: errorData.details
            };

        default:
            return {
                message: errorData.error_description || 'An unexpected error occurred.',
                type: 'unknown',
                retryable: true
            };
    }
}

// Usage example
async function loginWithErrorHandling(credentials) {
    try {
        const tokens = await loginUser(credentials);
        return { success: true, data: tokens };
        
    } catch (error) {
        const errorInfo = handleAuthError(error.data, error.response);
        
        // Show user-friendly error message
        showErrorMessage(errorInfo.message);
        
        // Handle specific error types
        if (errorInfo.type === 'rate_limit' || errorInfo.type === 'locked') {
            // Disable login button with countdown
            disableLoginButton(errorInfo.retryAfter);
        }
        
        if (errorInfo.fieldErrors) {
            // Show field-specific errors
            showFieldErrors(errorInfo.fieldErrors);
        }
        
        return { success: false, error: errorInfo };
    }
}
```

### 10. Complete Integration Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Sentinel Auth Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
        .error { color: red; margin: 10px 0; }
        .success { color: green; margin: 10px 0; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        input { width: 100%; padding: 8px; margin: 5px 0; }
        .token-info { background: #f5f5f5; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Sentinel Authentication Demo</h1>
    
    <div id="login-section">
        <h2>Login</h2>
        <form id="login-form">
            <input type="email" id="email" placeholder="Email" required>
            <input type="password" id="password" placeholder="Password" required>
            <input type="text" id="tenant-code" placeholder="Organization Code" required>
            <button type="submit" id="login-btn">Sign In</button>
        </form>
        <div id="login-error" class="error"></div>
    </div>

    <div id="dashboard" style="display: none;">
        <h2>Dashboard</h2>
        <div id="user-info" class="token-info"></div>
        <button onclick="testApiCall()">Test API Call</button>
        <button onclick="refreshToken()">Refresh Token</button>
        <button onclick="getUserSessions()">Show Sessions</button>
        <button onclick="logout()">Logout</button>
        <div id="api-result"></div>
        <div id="sessions-result"></div>
    </div>

    <script>
        // Include all the functions from above examples here
        // ... (loginUser, refreshAccessToken, apiCallWithAutoRefresh, etc.)

        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const tenantCode = document.getElementById('tenant-code').value.toUpperCase();
            
            const loginBtn = document.getElementById('login-btn');
            const errorDiv = document.getElementById('login-error');
            
            loginBtn.disabled = true;
            loginBtn.textContent = 'Signing in...';
            errorDiv.textContent = '';

            try {
                const tokens = await loginUser({
                    email,
                    password,
                    tenant_code: tenantCode
                });

                // Show dashboard
                document.getElementById('login-section').style.display = 'none';
                document.getElementById('dashboard').style.display = 'block';
                
                // Show user info
                const validation = await validateToken();
                document.getElementById('user-info').innerHTML = `
                    <strong>Welcome!</strong><br>
                    User ID: ${validation.user_id}<br>
                    Tenant ID: ${validation.tenant_id}<br>
                    Scopes: ${validation.scopes.join(', ')}<br>
                    Expires: ${new Date(validation.expires_at).toLocaleString()}
                `;

            } catch (error) {
                errorDiv.textContent = error.message;
            } finally {
                loginBtn.disabled = false;
                loginBtn.textContent = 'Sign In';
            }
        });

        async function testApiCall() {
            try {
                const tenants = await apiCallWithAutoRefresh('http://localhost:8000/api/v1/tenants/');
                document.getElementById('api-result').innerHTML = `
                    <h3>API Call Result:</h3>
                    <pre>${JSON.stringify(tenants, null, 2)}</pre>
                `;
            } catch (error) {
                document.getElementById('api-result').innerHTML = `
                    <h3>API Call Error:</h3>
                    <div class="error">${error.message}</div>
                `;
            }
        }

        async function logout() {
            await logoutUser();
        }

        // Auto-check authentication on page load
        window.addEventListener('load', async () => {
            const validation = await validateToken();
            if (validation.valid) {
                document.getElementById('login-section').style.display = 'none';
                document.getElementById('dashboard').style.display = 'block';
                document.getElementById('user-info').innerHTML = `
                    <strong>Welcome back!</strong><br>
                    User ID: ${validation.user_id}<br>
                    Expires: ${new Date(validation.expires_at).toLocaleString()}
                `;
            }
        });
    </script>
</body>
</html>
```

---

*These examples provide complete, working code for integrating with the Sentinel Authentication API. Adapt them to your specific frontend framework and requirements.*