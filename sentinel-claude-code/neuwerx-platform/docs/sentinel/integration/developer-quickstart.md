# ⚡ Developer Quickstart: Sentinel Integration

**Get up and running with Sentinel RBAC in 30 minutes or less**

---

## 🎯 What You'll Build

A simple web application with:
- ✅ User authentication via Sentinel
- ✅ Permission-based feature access  
- ✅ Dynamic menus based on user roles
- ✅ Field-level data filtering

---

## 📋 Prerequisites

- [ ] **Sentinel tenant set up** (follow [Setup Guide](./setup-guide.md) if needed)
- [ ] **Development environment** (Node.js/Python/etc.)
- [ ] **Sentinel credentials** (tenant ID, API access)
- [ ] **Test users created** with different roles

---

## 🚀 Quick Setup (Choose Your Stack)

<details>
<summary><strong>🟨 JavaScript/Node.js + Express</strong></summary>

### **1. Project Setup**

```bash
# Create project
mkdir my-sentinel-app && cd my-sentinel-app
npm init -y

# Install dependencies
npm install express axios jsonwebtoken cors dotenv
npm install -D nodemon
```

### **2. Environment Configuration**

```bash
# Create .env file
cat > .env << EOF
SENTINEL_BASE_URL=https://your-sentinel-instance.com
SENTINEL_TENANT_ID=your-tenant-uuid-here
PORT=3000
JWT_SECRET=your-jwt-secret-here
EOF
```

### **3. Basic Server Setup**

```javascript
// server.js
const express = require('express');
const axios = require('axios');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(express.static('public'));

// Sentinel client
class SentinelClient {
  constructor(baseUrl, tenantId) {
    this.baseUrl = baseUrl;
    this.tenantId = tenantId;
  }

  async login(email, password) {
    try {
      const response = await axios.post(`${this.baseUrl}/api/v1/auth/login`, {
        email,
        password,
        tenant_id: this.tenantId
      });
      return response.data;
    } catch (error) {
      throw new Error('Login failed');
    }
  }

  async checkPermission(userId, resource, action, token) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/v1/permissions/check`,
        { user_id: userId, resource_id: resource, action },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      return response.data.allowed;
    } catch (error) {
      return false;
    }
  }

  async getUserMenu(userId, token) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/v1/navigation/menu/${userId}`,
        { headers: { Authorization: `Bearer ${token}` }}
      );
      return response.data.menu_items;
    } catch (error) {
      return [];
    }
  }
}

const sentinel = new SentinelClient(
  process.env.SENTINEL_BASE_URL,
  process.env.SENTINEL_TENANT_ID
);

// Login endpoint
app.post('/api/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const result = await sentinel.login(email, password);
    res.json(result);
  } catch (error) {
    res.status(401).json({ error: 'Invalid credentials' });
  }
});

// Protected route example
app.get('/api/customers', async (req, res) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'No token' });

  try {
    const decoded = jwt.decode(token);
    const canRead = await sentinel.checkPermission(
      decoded.sub, 'customer-data', 'READ', token
    );

    if (!canRead) {
      return res.status(403).json({ error: 'Permission denied' });
    }

    // Return mock customer data
    res.json([
      { id: 1, name: 'John Doe', email: 'john@example.com' },
      { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
    ]);
  } catch (error) {
    res.status(403).json({ error: 'Invalid token' });
  }
});

// User menu endpoint
app.get('/api/menu', async (req, res) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'No token' });

  try {
    const decoded = jwt.decode(token);
    const menu = await sentinel.getUserMenu(decoded.sub, token);
    res.json(menu);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch menu' });
  }
});

app.listen(process.env.PORT, () => {
  console.log(`Server running on port ${process.env.PORT}`);
});
```

### **4. Frontend (HTML + JavaScript)**

```html
<!-- public/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Sentinel App Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .login-form { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .menu { background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .content { background: #f9f9f9; padding: 15px; border-radius: 8px; }
        .hidden { display: none; }
        button { background: #2196f3; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        input { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <div id="loginSection">
        <div class="login-form">
            <h2>🔐 Login to Sentinel App</h2>
            <input type="email" id="email" placeholder="Email" value="manager@myawesome.com">
            <input type="password" id="password" placeholder="Password" value="manager_password">
            <button onclick="login()">Login</button>
        </div>
    </div>

    <div id="appSection" class="hidden">
        <div class="menu">
            <h3>🧭 Navigation Menu</h3>
            <div id="menuItems">Loading menu...</div>
        </div>

        <div class="content">
            <h3>📊 Application Content</h3>
            <button onclick="loadCustomers()">Load Customers</button>
            <button onclick="loadReports()">Load Financial Reports</button>
            <div id="contentArea">Click a button to load content...</div>
        </div>

        <button onclick="logout()">Logout</button>
    </div>

    <script>
        let currentToken = null;

        async function login() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (response.ok) {
                    const data = await response.json();
                    currentToken = data.access_token;
                    
                    document.getElementById('loginSection').classList.add('hidden');
                    document.getElementById('appSection').classList.remove('hidden');
                    
                    loadMenu();
                } else {
                    alert('Login failed');
                }
            } catch (error) {
                alert('Login error: ' + error.message);
            }
        }

        async function loadMenu() {
            try {
                const response = await fetch('/api/menu', {
                    headers: { 'Authorization': `Bearer ${currentToken}` }
                });

                if (response.ok) {
                    const menu = await response.json();
                    const menuDiv = document.getElementById('menuItems');
                    menuDiv.innerHTML = menu.map(item => 
                        `<div>🔗 ${item.display_name} (${item.url})</div>`
                    ).join('');
                } else {
                    document.getElementById('menuItems').innerHTML = 'Failed to load menu';
                }
            } catch (error) {
                document.getElementById('menuItems').innerHTML = 'Menu error: ' + error.message;
            }
        }

        async function loadCustomers() {
            try {
                const response = await fetch('/api/customers', {
                    headers: { 'Authorization': `Bearer ${currentToken}` }
                });

                if (response.ok) {
                    const customers = await response.json();
                    document.getElementById('contentArea').innerHTML = 
                        '<h4>👥 Customers:</h4>' + 
                        customers.map(c => `<div>${c.name} - ${c.email}</div>`).join('');
                } else {
                    document.getElementById('contentArea').innerHTML = '❌ Access denied to customer data';
                }
            } catch (error) {
                document.getElementById('contentArea').innerHTML = 'Error: ' + error.message;
            }
        }

        async function loadReports() {
            // This will demonstrate permission denial
            document.getElementById('contentArea').innerHTML = '❌ Access denied to financial reports (not implemented)';
        }

        function logout() {
            currentToken = null;
            document.getElementById('loginSection').classList.remove('hidden');
            document.getElementById('appSection').classList.add('hidden');
        }
    </script>
</body>
</html>
```

### **5. Run the Application**

```bash
# Start server
npm run dev  # or node server.js

# Open browser to http://localhost:3000
```

</details>

<details>
<summary><strong>🐍 Python + Flask</strong></summary>

### **1. Project Setup**

```bash
# Create project
mkdir my-sentinel-app && cd my-sentinel-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask requests pyjwt python-dotenv flask-cors
```

### **2. Environment Configuration**

```bash
# Create .env file
cat > .env << EOF
SENTINEL_BASE_URL=https://your-sentinel-instance.com
SENTINEL_TENANT_ID=your-tenant-uuid-here
FLASK_ENV=development
JWT_SECRET=your-jwt-secret-here
EOF
```

### **3. Flask Application**

```python
# app.py
import os
import requests
import jwt
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

class SentinelClient:
    def __init__(self, base_url, tenant_id):
        self.base_url = base_url
        self.tenant_id = tenant_id
    
    def login(self, email, password):
        """Authenticate user with Sentinel."""
        response = requests.post(f"{self.base_url}/api/v1/auth/login", json={
            "email": email,
            "password": password,
            "tenant_id": self.tenant_id
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Login failed")
    
    def check_permission(self, user_id, resource, action, token):
        """Check user permission."""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/permissions/check",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "user_id": user_id,
                    "resource_id": resource,
                    "action": action
                }
            )
            return response.json().get("allowed", False)
        except:
            return False
    
    def get_user_menu(self, user_id, token):
        """Get user's menu structure."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/navigation/menu/{user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.json().get("menu_items", [])
        except:
            return []

sentinel = SentinelClient(
    os.getenv("SENTINEL_BASE_URL"),
    os.getenv("SENTINEL_TENANT_ID")
)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sentinel Python Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .form-group { margin: 10px 0; }
            input, button { padding: 10px; margin: 5px; }
            .hidden { display: none; }
            .menu { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 10px 0; }
            .content { background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div id="loginSection">
            <h2>🐍 Python Sentinel App</h2>
            <div class="form-group">
                <input type="email" id="email" placeholder="Email" value="manager@myawesome.com">
            </div>
            <div class="form-group">
                <input type="password" id="password" placeholder="Password" value="manager_password">
            </div>
            <button onclick="login()">Login</button>
        </div>

        <div id="appSection" class="hidden">
            <div class="menu">
                <h3>📱 Your Menu</h3>
                <div id="menuItems">Loading...</div>
            </div>
            
            <div class="content">
                <h3>📊 Protected Content</h3>
                <button onclick="loadCustomers()">Load Customers</button>
                <button onclick="loadAdminData()">Admin Panel</button>
                <div id="contentArea">Select an action above</div>
            </div>
            
            <button onclick="logout()">Logout</button>
        </div>

        <script>
            let token = null;

            async function login() {
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;

                try {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        token = data.access_token;
                        
                        document.getElementById('loginSection').classList.add('hidden');
                        document.getElementById('appSection').classList.remove('hidden');
                        
                        loadMenu();
                    } else {
                        alert('Login failed');
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function loadMenu() {
                const response = await fetch('/api/menu', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const menu = await response.json();
                    document.getElementById('menuItems').innerHTML = 
                        menu.map(item => `<div>🔹 ${item.display_name}</div>`).join('') || 'No menu items';
                }
            }

            async function loadCustomers() {
                const response = await fetch('/api/customers', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const data = await response.json();
                    document.getElementById('contentArea').innerHTML = 
                        '<h4>✅ Customer Data:</h4>' + 
                        data.map(c => `<div>${c.name} - ${c.email}</div>`).join('');
                } else {
                    document.getElementById('contentArea').innerHTML = '❌ Access denied to customers';
                }
            }

            async function loadAdminData() {
                document.getElementById('contentArea').innerHTML = '❌ Access denied to admin panel';
            }

            function logout() {
                token = null;
                document.getElementById('loginSection').classList.remove('hidden');
                document.getElementById('appSection').classList.add('hidden');
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        result = sentinel.login(data['email'], data['password'])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/api/menu')
def menu():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "No token"}), 401
    
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get('sub')
        menu_items = sentinel.get_user_menu(user_id, token)
        return jsonify(menu_items)
    except:
        return jsonify({"error": "Invalid token"}), 401

@app.route('/api/customers')
def customers():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "No token"}), 401
    
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get('sub')
        
        can_read = sentinel.check_permission(user_id, 'customer-data', 'READ', token)
        if not can_read:
            return jsonify({"error": "Permission denied"}), 403
        
        # Mock customer data
        return jsonify([
            {"id": 1, "name": "Alice Johnson", "email": "alice@company.com"},
            {"id": 2, "name": "Bob Wilson", "email": "bob@company.com"}
        ])
    except:
        return jsonify({"error": "Invalid token"}), 401

if __name__ == '__main__':
    app.run(debug=True)
```

### **4. Run the Application**

```bash
# Start Flask app
python app.py

# Open browser to http://localhost:5000
```

</details>

<details>
<summary><strong>🟦 React Frontend</strong></summary>

### **1. Project Setup**

```bash
# Create React app
npx create-react-app my-sentinel-react-app
cd my-sentinel-react-app

# Install additional dependencies
npm install axios
```

### **2. Sentinel Hook**

```javascript
// src/hooks/useSentinel.js
import { useState, useEffect } from 'react';
import axios from 'axios';

const SENTINEL_BASE_URL = process.env.REACT_APP_SENTINEL_BASE_URL;
const TENANT_ID = process.env.REACT_APP_SENTINEL_TENANT_ID;

export const useSentinel = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('sentinel_token'));
  const [permissions, setPermissions] = useState({});
  const [menu, setMenu] = useState([]);
  const [loading, setLoading] = useState(false);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const response = await axios.post(`${SENTINEL_BASE_URL}/api/v1/auth/login`, {
        email,
        password,
        tenant_id: TENANT_ID
      });

      const { access_token, user } = response.data;
      setToken(access_token);
      setUser(user);
      localStorage.setItem('sentinel_token', access_token);
      
      // Load user permissions and menu
      await loadUserData(user.id, access_token);
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setPermissions({});
    setMenu([]);
    localStorage.removeItem('sentinel_token');
  };

  const loadUserData = async (userId, authToken) => {
    try {
      // Load permissions
      const permResponse = await axios.get(
        `${SENTINEL_BASE_URL}/api/v1/permissions/evaluate?user_id=${userId}`,
        { headers: { Authorization: `Bearer ${authToken}` }}
      );
      setPermissions(permResponse.data);

      // Load menu
      const menuResponse = await axios.get(
        `${SENTINEL_BASE_URL}/api/v1/navigation/menu/${userId}`,
        { headers: { Authorization: `Bearer ${authToken}` }}
      );
      setMenu(menuResponse.data.menu_items || []);
    } catch (error) {
      console.error('Failed to load user data:', error);
    }
  };

  const checkPermission = (resource, action) => {
    const userPermissions = permissions.permissions || [];
    return userPermissions.some(p => 
      p.resource_id === resource && p.actions.includes(action)
    );
  };

  return {
    user,
    token,
    menu,
    loading,
    login,
    logout,
    checkPermission
  };
};
```

### **3. Permission Gate Component**

```javascript
// src/components/PermissionGate.js
import { useSentinel } from '../hooks/useSentinel';

export const PermissionGate = ({ resource, action, children, fallback = null }) => {
  const { checkPermission } = useSentinel();
  
  if (checkPermission(resource, action)) {
    return children;
  }
  
  return fallback;
};
```

### **4. Main App Component**

```javascript
// src/App.js
import React, { useState } from 'react';
import { useSentinel } from './hooks/useSentinel';
import { PermissionGate } from './components/PermissionGate';
import './App.css';

function App() {
  const { user, token, menu, loading, login, logout, checkPermission } = useSentinel();
  const [email, setEmail] = useState('manager@myawesome.com');
  const [password, setPassword] = useState('manager_password');
  const [customers, setCustomers] = useState([]);

  const handleLogin = async (e) => {
    e.preventDefault();
    const success = await login(email, password);
    if (!success) {
      alert('Login failed');
    }
  };

  const loadCustomers = async () => {
    if (!checkPermission('customer-data', 'READ')) {
      alert('Permission denied');
      return;
    }

    // Mock data - replace with actual API call
    setCustomers([
      { id: 1, name: 'Customer 1', email: 'customer1@example.com' },
      { id: 2, name: 'Customer 2', email: 'customer2@example.com' }
    ]);
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!token) {
    return (
      <div className="login-container">
        <h2>🔐 Sentinel React App</h2>
        <form onSubmit={handleLogin}>
          <div>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit">Login</button>
        </form>
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <h1>Welcome, {user?.first_name}!</h1>
        <button onClick={logout}>Logout</button>
      </header>

      <nav className="menu">
        <h3>📱 Your Menu</h3>
        {menu.map(item => (
          <div key={item.id} className="menu-item">
            {item.icon} {item.display_name}
          </div>
        ))}
      </nav>

      <main>
        <PermissionGate resource="customer-data" action="READ">
          <div className="section">
            <h3>👥 Customer Management</h3>
            <button onClick={loadCustomers}>Load Customers</button>
            <div className="customer-list">
              {customers.map(customer => (
                <div key={customer.id} className="customer">
                  {customer.name} - {customer.email}
                </div>
              ))}
            </div>
          </div>
        </PermissionGate>

        <PermissionGate 
          resource="admin-panel" 
          action="READ"
          fallback={<div className="denied">❌ Admin access denied</div>}
        >
          <div className="section">
            <h3>⚙️ Admin Panel</h3>
            <p>Admin features would go here</p>
          </div>
        </PermissionGate>
      </main>
    </div>
  );
}

export default App;
```

### **5. Environment Variables**

```bash
# Create .env file
REACT_APP_SENTINEL_BASE_URL=https://your-sentinel-instance.com
REACT_APP_SENTINEL_TENANT_ID=your-tenant-uuid-here
```

### **6. Run the Application**

```bash
npm start
# Opens browser to http://localhost:3000
```

</details>

---

## 🧪 Testing Your Integration

### **Test Different User Roles**

1. **Login as Manager** (`manager@myawesome.com`)
   - ✅ Should see dashboard and customer menus
   - ✅ Should access customer data
   - ❌ Should NOT see admin panel

2. **Login as Employee** (`employee@myawesome.com`)  
   - ✅ Should see dashboard menu
   - ❌ Should NOT see customer management
   - ❌ Should NOT access admin features

3. **Login as Admin** (`admin@myawesome.com`)
   - ✅ Should see all menus
   - ✅ Should access all features
   - ✅ Should see admin panel

### **Test Permission Scenarios**

```bash
# Test permission checks
curl -X POST http://localhost:3000/api/customers \
  -H "Authorization: Bearer MANAGER_TOKEN" \
  -H "Content-Type: application/json"
# Should return customer data

curl -X POST http://localhost:3000/api/admin \
  -H "Authorization: Bearer MANAGER_TOKEN" \
  -H "Content-Type: application/json"  
# Should return 403 Forbidden
```

---

## 🔧 Advanced Features

### **Real-Time Permission Updates**

```javascript
// WebSocket connection for live updates
const connectPermissionUpdates = (userId, token) => {
  const ws = new WebSocket(`wss://sentinel.com/ws/permissions/${userId}?token=${token}`);
  
  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    
    if (update.type === 'PERMISSION_REVOKED') {
      // Hide features user can no longer access
      hideFeature(update.resource);
    } else if (update.type === 'MENU_UPDATED') {
      // Refresh user menu
      loadUserMenu();
    }
  };
};
```

### **Field-Level Permission Demo**

```javascript
// Filter customer data based on field permissions
const filterCustomerFields = (customer, fieldPermissions) => {
  const filtered = {};
  
  Object.keys(customer).forEach(field => {
    const permission = fieldPermissions[field];
    if (permission === 'VISIBLE') {
      filtered[field] = customer[field];
    } else if (permission === 'MASKED') {
      filtered[field] = '***';
    }
    // HIDDEN fields are not included
  });
  
  return filtered;
};
```

### **Caching for Performance**

```javascript
// Simple permission cache
const PermissionCache = {
  cache: new Map(),
  ttl: 5 * 60 * 1000, // 5 minutes
  
  get(key) {
    const item = this.cache.get(key);
    if (!item || Date.now() > item.expires) {
      this.cache.delete(key);
      return null;
    }
    return item.value;
  },
  
  set(key, value) {
    this.cache.set(key, {
      value,
      expires: Date.now() + this.ttl
    });
  }
};
```

---

## 🚀 Production Considerations

### **Security Checklist**

- [ ] **HTTPS Only**: Ensure all Sentinel communication uses HTTPS
- [ ] **Token Storage**: Use secure storage (httpOnly cookies preferred over localStorage)
- [ ] **Token Refresh**: Implement automatic token refresh
- [ ] **Error Handling**: Fail securely when Sentinel is unavailable
- [ ] **Input Validation**: Validate all user inputs before sending to Sentinel

### **Performance Optimization**

```javascript
// Batch permission checks
const checkMultiplePermissions = async (checks) => {
  const results = await Promise.all(
    checks.map(({ resource, action }) => 
      sentinel.checkPermission(userId, resource, action, token)
    )
  );
  
  return checks.reduce((acc, check, index) => {
    acc[`${check.resource}:${check.action}`] = results[index];
    return acc;
  }, {});
};

// Usage
const permissions = await checkMultiplePermissions([
  { resource: 'customer-data', action: 'READ' },
  { resource: 'customer-data', action: 'UPDATE' },
  { resource: 'financial-reports', action: 'READ' }
]);
```

### **Error Boundaries**

```javascript
// React Error Boundary for permission failures
class PermissionErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Permission error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div>🔒 Access control error. Please refresh the page.</div>;
    }

    return this.props.children;
  }
}
```

---

## 📊 Monitoring & Debugging

### **Add Logging**

```javascript
const logPermissionCheck = (userId, resource, action, result) => {
  console.log(`Permission Check: ${userId} tried ${action} on ${resource}: ${result ? 'ALLOWED' : 'DENIED'}`);
  
  // Send to analytics
  if (window.analytics) {
    window.analytics.track('Permission Check', {
      userId,
      resource,
      action,
      result: result ? 'allowed' : 'denied'
    });
  }
};
```

### **Health Check Endpoint**

```javascript
app.get('/health/sentinel', async (req, res) => {
  try {
    const response = await axios.get(`${SENTINEL_BASE_URL}/health`, { timeout: 5000 });
    res.json({
      status: 'healthy',
      sentinel_status: response.status,
      response_time: response.config.timeout
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});
```

---

## ✅ Next Steps

1. **Customize** the code for your specific application needs
2. **Add** more resources and permissions based on your requirements  
3. **Implement** field-level permissions for sensitive data
4. **Set up** monitoring and logging
5. **Deploy** to your staging environment for testing
6. **Review** the [Best Practices](./best-practices.md) guide
7. **Go to production** with confidence! 🚀

---

## 🆘 Troubleshooting

### **Common Issues & Solutions**

| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid/expired token | Implement token refresh logic |
| `403 Forbidden` | User lacks permission | Check role and permission assignments |
| `CORS errors` | Cross-origin request blocked | Configure CORS properly |
| Empty menu | User has no accessible menu items | Verify role assignments and menu permissions |
| Slow performance | Too many API calls | Implement caching and batch requests |

### **Debug Commands**

```bash
# Check user permissions
GET /api/v1/permissions/evaluate?user_id=USER_ID

# Debug user menu
GET /api/v1/navigation/menu/USER_ID/debug

# Check role assignments
GET /api/v1/users/USER_ID/roles

# Test specific permission
POST /api/v1/permissions/check
{
  "user_id": "USER_ID",
  "resource_id": "customer-data", 
  "action": "READ"
}
```

---

**🎉 Congratulations! You now have a working Sentinel-integrated application. Your users can securely access features based on their roles and permissions, with personalized menus and field-level security.**

**Want to dive deeper? Check out the [Technical Integration Guide](./technical-integration.md) for advanced patterns and optimizations!**