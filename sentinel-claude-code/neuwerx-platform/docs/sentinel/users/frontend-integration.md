# 🌐 User Management Frontend Integration

## Overview

This guide provides comprehensive examples for integrating user management features into frontend applications, including profile management, user administration, and service account handling.

## 🚀 User Management Service

### Base User Service

```javascript
class UserService {
    constructor(authService) {
        this.authService = authService;
        this.baseURL = 'http://localhost:8000/api/v1';
    }

    async getCurrentUser() {
        const response = await this.authService.apiCall(`${this.baseURL}/users/me`);
        if (!response.ok) {
            throw new Error('Failed to get current user');
        }
        return response.json();
    }

    async updateCurrentUser(userData) {
        const response = await this.authService.apiCall(`${this.baseURL}/users/me`, {
            method: 'PATCH',
            body: JSON.stringify(userData)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update profile');
        }
        return response.json();
    }

    async listUsers(params = {}) {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                searchParams.append(key, value);
            }
        });

        const response = await this.authService.apiCall(
            `${this.baseURL}/users/?${searchParams.toString()}`
        );
        if (!response.ok) {
            throw new Error('Failed to get users');
        }
        return response.json();
    }

    async getUser(userId) {
        const response = await this.authService.apiCall(`${this.baseURL}/users/${userId}`);
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('User not found');
            }
            throw new Error('Failed to get user');
        }
        return response.json();
    }

    async createUser(userData) {
        const response = await this.authService.apiCall(`${this.baseURL}/users/`, {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create user');
        }
        return response.json();
    }

    async updateUser(userId, userData) {
        const response = await this.authService.apiCall(`${this.baseURL}/users/${userId}`, {
            method: 'PATCH',
            body: JSON.stringify(userData)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update user');
        }
        return response.json();
    }

    async deleteUser(userId, hardDelete = false) {
        const response = await this.authService.apiCall(
            `${this.baseURL}/users/${userId}?hard_delete=${hardDelete}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error('Failed to delete user');
        }
    }

    async bulkOperation(operation, userIds, data = {}) {
        const response = await this.authService.apiCall(`${this.baseURL}/users/bulk`, {
            method: 'POST',
            body: JSON.stringify({
                operation,
                user_ids: userIds,
                data
            })
        });
        if (!response.ok) {
            throw new Error('Bulk operation failed');
        }
        return response.json();
    }

    async changePassword(userId, currentPassword, newPassword) {
        const response = await this.authService.apiCall(
            `${this.baseURL}/users/${userId}/change-password`, {
            method: 'POST',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to change password');
        }
    }

    async lockUser(userId, durationMinutes = 30) {
        const response = await this.authService.apiCall(
            `${this.baseURL}/users/${userId}/lock?duration_minutes=${durationMinutes}`, {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error('Failed to lock user');
        }
    }

    async unlockUser(userId) {
        const response = await this.authService.apiCall(
            `${this.baseURL}/users/${userId}/unlock`, {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error('Failed to unlock user');
        }
    }
}
```

## 📱 React Integration

### User Profile Component

```jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const UserProfile = () => {
    const { userService } = useAuth();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const [formData, setFormData] = useState({});
    const [error, setError] = useState('');

    useEffect(() => {
        loadCurrentUser();
    }, []);

    const loadCurrentUser = async () => {
        try {
            const currentUser = await userService.getCurrentUser();
            setUser(currentUser);
            setFormData({
                username: currentUser.username || '',
                attributes: currentUser.attributes || {},
                preferences: currentUser.preferences || {}
            });
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setError('');
            const updatedUser = await userService.updateCurrentUser(formData);
            setUser(updatedUser);
            setEditing(false);
        } catch (error) {
            setError(error.message);
        }
    };

    const handleAttributeChange = (key, value) => {
        setFormData(prev => ({
            ...prev,
            attributes: {
                ...prev.attributes,
                [key]: value
            }
        }));
    };

    const handlePreferenceChange = (key, value) => {
        setFormData(prev => ({
            ...prev,
            preferences: {
                ...prev.preferences,
                [key]: value
            }
        }));
    };

    if (loading) return <div>Loading profile...</div>;
    if (!user) return <div>Failed to load profile</div>;

    return (
        <div className="user-profile">
            <div className="profile-header">
                <h2>My Profile</h2>
                <button
                    onClick={() => editing ? handleSave() : setEditing(true)}
                    className="btn-primary"
                >
                    {editing ? 'Save Changes' : 'Edit Profile'}
                </button>
                {editing && (
                    <button
                        onClick={() => {
                            setEditing(false);
                            setFormData({
                                username: user.username || '',
                                attributes: user.attributes || {},
                                preferences: user.preferences || {}
                            });
                        }}
                        className="btn-secondary"
                    >
                        Cancel
                    </button>
                )}
            </div>

            {error && <div className="error">{error}</div>}

            <div className="profile-section">
                <h3>Basic Information</h3>
                <div className="form-group">
                    <label>Email</label>
                    <input type="email" value={user.email} disabled />
                </div>
                <div className="form-group">
                    <label>Username</label>
                    <input
                        type="text"
                        value={formData.username}
                        onChange={(e) => setFormData(prev => ({...prev, username: e.target.value}))}
                        disabled={!editing}
                    />
                </div>
            </div>

            <div className="profile-section">
                <h3>Attributes</h3>
                <div className="form-group">
                    <label>Department</label>
                    <input
                        type="text"
                        value={formData.attributes.department || ''}
                        onChange={(e) => handleAttributeChange('department', e.target.value)}
                        disabled={!editing}
                    />
                </div>
                <div className="form-group">
                    <label>Location</label>
                    <input
                        type="text"
                        value={formData.attributes.location || ''}
                        onChange={(e) => handleAttributeChange('location', e.target.value)}
                        disabled={!editing}
                    />
                </div>
            </div>

            <div className="profile-section">
                <h3>Preferences</h3>
                <div className="form-group">
                    <label>Theme</label>
                    <select
                        value={formData.preferences.theme || 'system'}
                        onChange={(e) => handlePreferenceChange('theme', e.target.value)}
                        disabled={!editing}
                    >
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                        <option value="system">System</option>
                    </select>
                </div>
                <div className="form-group">
                    <label>Language</label>
                    <select
                        value={formData.preferences.language || 'en'}
                        onChange={(e) => handlePreferenceChange('language', e.target.value)}
                        disabled={!editing}
                    >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                    </select>
                </div>
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={formData.preferences.notifications || false}
                            onChange={(e) => handlePreferenceChange('notifications', e.target.checked)}
                            disabled={!editing}
                        />
                        Enable Notifications
                    </label>
                </div>
            </div>

            <div className="profile-stats">
                <div className="stat">
                    <strong>Last Login:</strong>
                    <span>{user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</span>
                </div>
                <div className="stat">
                    <strong>Login Count:</strong>
                    <span>{user.login_count}</span>
                </div>
                <div className="stat">
                    <strong>Member Since:</strong>
                    <span>{new Date(user.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        </div>
    );
};

export default UserProfile;
```

### User List Component

```jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const UserList = () => {
    const { userService } = useAuth();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [pagination, setPagination] = useState({
        page: 1,
        limit: 25,
        total: 0,
        pages: 0
    });
    const [filters, setFilters] = useState({
        search: '',
        is_active: null,
        sort: 'created_at',
        order: 'desc'
    });

    useEffect(() => {
        loadUsers();
    }, [pagination.page, filters]);

    const loadUsers = async () => {
        try {
            setLoading(true);
            setError('');
            
            const params = {
                page: pagination.page,
                limit: pagination.limit,
                ...filters
            };

            // Remove empty filters
            Object.keys(params).forEach(key => {
                if (params[key] === '' || params[key] === null) {
                    delete params[key];
                }
            });

            const response = await userService.listUsers(params);
            setUsers(response.items);
            setPagination(prev => ({
                ...prev,
                total: response.total,
                pages: response.pages
            }));
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (searchTerm) => {
        setFilters(prev => ({ ...prev, search: searchTerm }));
        setPagination(prev => ({ ...prev, page: 1 }));
    };

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
        setPagination(prev => ({ ...prev, page: 1 }));
    };

    const handleBulkAction = async (action, selectedUsers) => {
        try {
            const userIds = selectedUsers.map(user => user.id);
            await userService.bulkOperation(action, userIds);
            loadUsers(); // Refresh the list
        } catch (error) {
            setError(error.message);
        }
    };

    const renderUserRow = (user) => (
        <tr key={user.id} className={!user.is_active ? 'inactive' : ''}>
            <td>
                <input
                    type="checkbox"
                    onChange={(e) => {
                        // Handle selection logic
                    }}
                />
            </td>
            <td>{user.email}</td>
            <td>{user.username || '-'}</td>
            <td>{user.attributes.department || '-'}</td>
            <td>
                <span className={`status ${user.is_active ? 'active' : 'inactive'}`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
            <td>{user.login_count}</td>
            <td>
                <button onClick={() => viewUser(user.id)} className="btn-sm">View</button>
                <button onClick={() => editUser(user.id)} className="btn-sm">Edit</button>
                <button onClick={() => deleteUser(user.id)} className="btn-sm danger">Delete</button>
            </td>
        </tr>
    );

    return (
        <div className="user-list">
            <div className="list-header">
                <h2>Users</h2>
                <button onClick={() => createUser()} className="btn-primary">Add User</button>
            </div>

            {/* Filters */}
            <div className="filters">
                <input
                    type="text"
                    placeholder="Search users..."
                    value={filters.search}
                    onChange={(e) => handleSearch(e.target.value)}
                />
                <select
                    value={filters.is_active || ''}
                    onChange={(e) => handleFilterChange('is_active', e.target.value || null)}
                >
                    <option value="">All Status</option>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                </select>
                <select
                    value={`${filters.sort}-${filters.order}`}
                    onChange={(e) => {
                        const [sort, order] = e.target.value.split('-');
                        setFilters(prev => ({ ...prev, sort, order }));
                    }}
                >
                    <option value="created_at-desc">Newest First</option>
                    <option value="created_at-asc">Oldest First</option>
                    <option value="email-asc">Email A-Z</option>
                    <option value="email-desc">Email Z-A</option>
                    <option value="last_login-desc">Recent Login</option>
                </select>
            </div>

            {error && <div className="error">{error}</div>}

            {/* User Table */}
            <div className="table-container">
                <table className="user-table">
                    <thead>
                        <tr>
                            <th><input type="checkbox" /></th>
                            <th>Email</th>
                            <th>Username</th>
                            <th>Department</th>
                            <th>Status</th>
                            <th>Last Login</th>
                            <th>Login Count</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="8">Loading...</td></tr>
                        ) : users.length === 0 ? (
                            <tr><td colSpan="8">No users found</td></tr>
                        ) : (
                            users.map(renderUserRow)
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="pagination">
                <button
                    onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                    disabled={pagination.page === 1}
                >
                    Previous
                </button>
                <span>
                    Page {pagination.page} of {pagination.pages} 
                    ({pagination.total} total users)
                </span>
                <button
                    onClick={() => setPagination(prev => ({ ...prev, page: Math.min(prev.pages, prev.page + 1) }))}
                    disabled={pagination.page === pagination.pages}
                >
                    Next
                </button>
            </div>
        </div>
    );
};

export default UserList;
```

### User Creation Form

```jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const CreateUserForm = ({ onUserCreated, onCancel }) => {
    const { userService } = useAuth();
    const [formData, setFormData] = useState({
        email: '',
        username: '',
        password: '',
        attributes: {
            department: '',
            location: ''
        },
        preferences: {
            theme: 'system',
            language: 'en',
            notifications: true
        },
        is_active: true,
        send_invitation: false
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const userData = {
                ...formData,
                // Only include password if not sending invitation
                ...(formData.send_invitation ? {} : { password: formData.password })
            };

            const newUser = await userService.createUser(userData);
            onUserCreated(newUser);
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleNestedChange = (parent, field, value) => {
        setFormData(prev => ({
            ...prev,
            [parent]: {
                ...prev[parent],
                [field]: value
            }
        }));
    };

    return (
        <form onSubmit={handleSubmit} className="create-user-form">
            <h3>Create New User</h3>

            {error && <div className="error">{error}</div>}

            <div className="form-section">
                <h4>Basic Information</h4>
                
                <div className="form-group">
                    <label>Email *</label>
                    <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleChange('email', e.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Username</label>
                    <input
                        type="text"
                        value={formData.username}
                        onChange={(e) => handleChange('username', e.target.value)}
                    />
                </div>

                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={formData.send_invitation}
                            onChange={(e) => handleChange('send_invitation', e.target.checked)}
                        />
                        Send invitation email (user sets own password)
                    </label>
                </div>

                {!formData.send_invitation && (
                    <div className="form-group">
                        <label>Password *</label>
                        <input
                            type="password"
                            value={formData.password}
                            onChange={(e) => handleChange('password', e.target.value)}
                            required={!formData.send_invitation}
                            minLength={8}
                        />
                        <small>Minimum 8 characters</small>
                    </div>
                )}
            </div>

            <div className="form-section">
                <h4>Attributes</h4>
                
                <div className="form-group">
                    <label>Department</label>
                    <input
                        type="text"
                        value={formData.attributes.department}
                        onChange={(e) => handleNestedChange('attributes', 'department', e.target.value)}
                    />
                </div>

                <div className="form-group">
                    <label>Location</label>
                    <input
                        type="text"
                        value={formData.attributes.location}
                        onChange={(e) => handleNestedChange('attributes', 'location', e.target.value)}
                    />
                </div>
            </div>

            <div className="form-section">
                <h4>Preferences</h4>
                
                <div className="form-group">
                    <label>Theme</label>
                    <select
                        value={formData.preferences.theme}
                        onChange={(e) => handleNestedChange('preferences', 'theme', e.target.value)}
                    >
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                        <option value="system">System</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>Language</label>
                    <select
                        value={formData.preferences.language}
                        onChange={(e) => handleNestedChange('preferences', 'language', e.target.value)}
                    >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={formData.preferences.notifications}
                            onChange={(e) => handleNestedChange('preferences', 'notifications', e.target.checked)}
                        />
                        Enable notifications
                    </label>
                </div>
            </div>

            <div className="form-section">
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={formData.is_active}
                            onChange={(e) => handleChange('is_active', e.target.checked)}
                        />
                        Active user
                    </label>
                </div>
            </div>

            <div className="form-actions">
                <button type="submit" disabled={loading} className="btn-primary">
                    {loading ? 'Creating...' : 'Create User'}
                </button>
                <button type="button" onClick={onCancel} className="btn-secondary">
                    Cancel
                </button>
            </div>
        </form>
    );
};

export default CreateUserForm;
```

## 🖼️ Avatar Management

### Avatar Upload Component

```jsx
import React, { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';

const AvatarUpload = ({ userId, currentAvatarUrl, onAvatarUpdated }) => {
    const { authService } = useAuth();
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');
    const [previewUrl, setPreviewUrl] = useState(currentAvatarUrl);
    const fileInputRef = useRef();

    const handleFileSelect = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file
        if (!file.type.startsWith('image/')) {
            setError('Please select an image file');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            setError('File size must be less than 5MB');
            return;
        }

        // Create preview
        const reader = new FileReader();
        reader.onload = (e) => setPreviewUrl(e.target.result);
        reader.readAsDataURL(file);

        // Upload avatar
        await uploadAvatar(file);
    };

    const uploadAvatar = async (file) => {
        setUploading(true);
        setError('');

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`http://localhost:8000/api/v1/users/${userId}/avatar`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authService.accessToken}`
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to upload avatar');
            }

            const result = await response.json();
            onAvatarUpdated(result);
            
        } catch (error) {
            setError(error.message);
            setPreviewUrl(currentAvatarUrl); // Revert preview
        } finally {
            setUploading(false);
        }
    };

    const handleRemoveAvatar = async () => {
        try {
            const response = await authService.apiCall(
                `http://localhost:8000/api/v1/users/${userId}/avatar`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setPreviewUrl(null);
                onAvatarUpdated(null);
            }
        } catch (error) {
            setError('Failed to remove avatar');
        }
    };

    return (
        <div className="avatar-upload">
            <div className="avatar-preview">
                {previewUrl ? (
                    <img 
                        src={previewUrl} 
                        alt="Avatar" 
                        className="avatar-image"
                        onError={() => setPreviewUrl(null)}
                    />
                ) : (
                    <div className="avatar-placeholder">
                        <span>No Avatar</span>
                    </div>
                )}
                
                {uploading && <div className="upload-overlay">Uploading...</div>}
            </div>

            <div className="avatar-actions">
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept="image/*"
                    style={{ display: 'none' }}
                />
                
                <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="btn-primary"
                >
                    {previewUrl ? 'Change Avatar' : 'Upload Avatar'}
                </button>
                
                {previewUrl && (
                    <button
                        onClick={handleRemoveAvatar}
                        disabled={uploading}
                        className="btn-danger"
                    >
                        Remove
                    </button>
                )}
            </div>

            {error && <div className="error">{error}</div>}
            
            <div className="upload-requirements">
                <small>
                    • PNG, JPEG, or WebP format<br/>
                    • Maximum 5MB file size<br/>
                    • Square images work best
                </small>
            </div>
        </div>
    );
};

export default AvatarUpload;
```

## 🔧 Service Account Management

### Service Account Component

```jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const ServiceAccountManager = () => {
    const { authService } = useAuth();
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [showCredentials, setShowCredentials] = useState(null);

    useEffect(() => {
        loadServiceAccounts();
    }, []);

    const loadServiceAccounts = async () => {
        try {
            const response = await authService.apiCall(
                'http://localhost:8000/api/v1/service-accounts/'
            );
            if (response.ok) {
                const data = await response.json();
                setAccounts(data.items);
            }
        } catch (error) {
            setError('Failed to load service accounts');
        } finally {
            setLoading(false);
        }
    };

    const createServiceAccount = async (accountData) => {
        try {
            const response = await authService.apiCall(
                'http://localhost:8000/api/v1/service-accounts/', {
                method: 'POST',
                body: JSON.stringify(accountData)
            });

            if (response.ok) {
                const result = await response.json();
                setAccounts(prev => [...prev, result.service_account]);
                setShowCredentials(result.credentials);
                setShowCreateForm(false);
                return result;
            }
        } catch (error) {
            throw new Error('Failed to create service account');
        }
    };

    const rotateCredentials = async (accountId) => {
        try {
            const response = await authService.apiCall(
                `http://localhost:8000/api/v1/service-accounts/${accountId}/rotate`, {
                method: 'POST',
                body: JSON.stringify({ revoke_existing: true })
            });

            if (response.ok) {
                const credentials = await response.json();
                setShowCredentials(credentials);
                return credentials;
            }
        } catch (error) {
            throw new Error('Failed to rotate credentials');
        }
    };

    const CredentialsModal = ({ credentials, onClose }) => (
        <div className="modal-overlay">
            <div className="modal">
                <div className="modal-header">
                    <h3>Service Account Credentials</h3>
                    <div className="warning">
                        ⚠️ Store these credentials securely - they won't be shown again!
                    </div>
                </div>
                <div className="credentials">
                    <div className="credential-field">
                        <label>Client ID:</label>
                        <input type="text" value={credentials.client_id} readOnly />
                        <button onClick={() => navigator.clipboard.writeText(credentials.client_id)}>
                            Copy
                        </button>
                    </div>
                    <div className="credential-field">
                        <label>Client Secret:</label>
                        <input type="text" value={credentials.client_secret} readOnly />
                        <button onClick={() => navigator.clipboard.writeText(credentials.client_secret)}>
                            Copy
                        </button>
                    </div>
                </div>
                <div className="modal-actions">
                    <button onClick={onClose} className="btn-primary">I've Stored These Safely</button>
                </div>
            </div>
        </div>
    );

    const CreateForm = ({ onSubmit, onCancel }) => {
        const [formData, setFormData] = useState({
            name: '',
            description: '',
            attributes: {},
            is_active: true
        });

        const handleSubmit = async (e) => {
            e.preventDefault();
            try {
                await onSubmit(formData);
            } catch (error) {
                setError(error.message);
            }
        };

        return (
            <form onSubmit={handleSubmit} className="create-form">
                <h3>Create Service Account</h3>
                <div className="form-group">
                    <label>Name *</label>
                    <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({...prev, name: e.target.value}))}
                        required
                        placeholder="e.g., api-integration"
                    />
                </div>
                <div className="form-group">
                    <label>Description</label>
                    <textarea
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({...prev, description: e.target.value}))}
                        placeholder="What is this service account for?"
                    />
                </div>
                <div className="form-actions">
                    <button type="submit" className="btn-primary">Create Account</button>
                    <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
                </div>
            </form>
        );
    };

    return (
        <div className="service-account-manager">
            <div className="header">
                <h2>Service Accounts</h2>
                <button
                    onClick={() => setShowCreateForm(true)}
                    className="btn-primary"
                >
                    Create Service Account
                </button>
            </div>

            {error && <div className="error">{error}</div>}

            {showCreateForm && (
                <CreateForm
                    onSubmit={createServiceAccount}
                    onCancel={() => setShowCreateForm(false)}
                />
            )}

            <div className="accounts-list">
                {loading ? (
                    <div>Loading service accounts...</div>
                ) : accounts.length === 0 ? (
                    <div>No service accounts found</div>
                ) : (
                    accounts.map(account => (
                        <div key={account.id} className="account-card">
                            <div className="account-info">
                                <h4>{account.name}</h4>
                                <p>{account.description}</p>
                                <div className="account-meta">
                                    <span className={`status ${account.is_active ? 'active' : 'inactive'}`}>
                                        {account.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                    <span>Client ID: {account.client_id}</span>
                                    <span>Last Login: {account.last_login ? 
                                        new Date(account.last_login).toLocaleDateString() : 'Never'}</span>
                                </div>
                            </div>
                            <div className="account-actions">
                                <button
                                    onClick={() => rotateCredentials(account.id)}
                                    className="btn-warning"
                                >
                                    Rotate Credentials
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {showCredentials && (
                <CredentialsModal
                    credentials={showCredentials}
                    onClose={() => setShowCredentials(null)}
                />
            )}
        </div>
    );
};

export default ServiceAccountManager;
```

## 🔍 Advanced Features

### User Search with Debouncing

```javascript
import { useCallback, useEffect, useState } from 'react';
import { debounce } from 'lodash';

const useUserSearch = (userService) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [loading, setLoading] = useState(false);

    const performSearch = useCallback(
        debounce(async (term) => {
            if (!term.trim()) {
                setSearchResults([]);
                return;
            }

            setLoading(true);
            try {
                const results = await userService.listUsers({
                    search: term,
                    limit: 10,
                    is_active: true
                });
                setSearchResults(results.items);
            } catch (error) {
                console.error('Search failed:', error);
                setSearchResults([]);
            } finally {
                setLoading(false);
            }
        }, 300),
        [userService]
    );

    useEffect(() => {
        performSearch(searchTerm);
    }, [searchTerm, performSearch]);

    return {
        searchTerm,
        setSearchTerm,
        searchResults,
        loading
    };
};
```

### Bulk Actions Component

```jsx
const BulkActions = ({ selectedUsers, onBulkAction, onClearSelection }) => {
    const [action, setAction] = useState('');
    const [confirmAction, setConfirmAction] = useState(null);

    const actions = [
        { value: 'activate', label: 'Activate Users', className: 'success' },
        { value: 'deactivate', label: 'Deactivate Users', className: 'warning' },
        { value: 'delete', label: 'Delete Users', className: 'danger' }
    ];

    const handleAction = async () => {
        if (confirmAction && selectedUsers.length > 0) {
            try {
                await onBulkAction(confirmAction, selectedUsers);
                onClearSelection();
                setConfirmAction(null);
                setAction('');
            } catch (error) {
                console.error('Bulk action failed:', error);
            }
        }
    };

    if (selectedUsers.length === 0) return null;

    return (
        <div className="bulk-actions">
            <div className="bulk-info">
                {selectedUsers.length} user{selectedUsers.length !== 1 ? 's' : ''} selected
            </div>
            
            <select
                value={action}
                onChange={(e) => setAction(e.target.value)}
                className="bulk-action-select"
            >
                <option value="">Choose action...</option>
                {actions.map(a => (
                    <option key={a.value} value={a.value}>{a.label}</option>
                ))}
            </select>

            {action && (
                <button
                    onClick={() => setConfirmAction(action)}
                    className={`btn-${actions.find(a => a.value === action)?.className || 'primary'}`}
                >
                    {actions.find(a => a.value === action)?.label}
                </button>
            )}

            <button onClick={onClearSelection} className="btn-secondary">
                Clear Selection
            </button>

            {confirmAction && (
                <div className="confirmation-modal">
                    <p>
                        Are you sure you want to {confirmAction} {selectedUsers.length} user{selectedUsers.length !== 1 ? 's' : ''}?
                    </p>
                    <button onClick={handleAction} className="btn-danger">Confirm</button>
                    <button onClick={() => setConfirmAction(null)} className="btn-secondary">Cancel</button>
                </div>
            )}
        </div>
    );
};
```

## 📱 Mobile-Responsive Components

### CSS for Mobile Support

```css
/* Mobile-first responsive design */
.user-list {
    padding: 1rem;
}

.user-table {
    width: 100%;
    border-collapse: collapse;
}

@media (max-width: 768px) {
    .user-table thead {
        display: none;
    }
    
    .user-table,
    .user-table tbody,
    .user-table tr,
    .user-table td {
        display: block;
    }
    
    .user-table tr {
        border: 1px solid #ccc;
        margin-bottom: 1rem;
        padding: 1rem;
        border-radius: 8px;
    }
    
    .user-table td {
        text-align: right;
        padding-left: 50%;
        position: relative;
        border: none;
        padding-bottom: 0.5rem;
    }
    
    .user-table td:before {
        content: attr(data-label);
        position: absolute;
        left: 6px;
        width: 45%;
        text-align: left;
        font-weight: bold;
    }
}

.avatar-upload {
    text-align: center;
    padding: 2rem;
}

.avatar-image {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid #e0e0e0;
}

.avatar-placeholder {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: #f5f5f5;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem;
    border: 2px dashed #ccc;
}

.form-section {
    margin-bottom: 2rem;
    padding: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
}

.form-group input,
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.btn-primary,
.btn-secondary,
.btn-danger {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 0.5rem;
}

.btn-primary { background: #007bff; color: white; }
.btn-secondary { background: #6c757d; color: white; }
.btn-danger { background: #dc3545; color: white; }

.error {
    color: #dc3545;
    padding: 0.5rem;
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    margin-bottom: 1rem;
}

.status.active { color: #28a745; }
.status.inactive { color: #dc3545; }
```

This comprehensive frontend integration guide provides everything needed to implement user management features in React applications, including profile management, user administration, service accounts, and avatar uploads with proper error handling and responsive design.