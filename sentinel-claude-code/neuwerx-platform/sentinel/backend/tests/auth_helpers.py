"""
Authentication helper functions for test scripts
"""
from typing import Dict, Optional
import httpx
from fastapi.testclient import TestClient

# Standard test credentials
DEFAULT_USER_CREDENTIALS = {
    "email": "test@example.com",
    "password": "password123",
    "tenant_code": "TEST"
}

ADMIN_CREDENTIALS = {
    "email": "admin@sentinel.com", 
    "password": "Admin123!@#",
    "tenant_code": "PLATFORM"
}

SERVICE_ACCOUNT_CREDENTIALS = {
    "client_id": "service@example.com",
    "client_secret": "test-service-key-123",
    "scope": "tenant:read tenant:write tenant:admin"
}

class AuthHelper:
    """Helper class for handling authentication in tests"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_url = f"{base_url}/api/v1/auth/login"
        self.token_url = f"{base_url}/api/v1/auth/token"
    
    async def get_user_token(self, client: httpx.AsyncClient, credentials: Dict = None) -> str:
        """Get authentication token for regular user"""
        creds = credentials or DEFAULT_USER_CREDENTIALS
        response = await client.post(self.auth_url, json=creds)
        
        if response.status_code != 200:
            raise Exception(f"User authentication failed: {response.status_code} - {response.text}")
        
        return response.json()["access_token"]
    
    async def get_admin_token(self, client: httpx.AsyncClient) -> str:
        """Get authentication token for admin user"""
        response = await client.post(self.auth_url, json=ADMIN_CREDENTIALS)
        
        if response.status_code != 200:
            raise Exception(f"Admin authentication failed: {response.status_code} - {response.text}")
        
        return response.json()["access_token"]
    
    async def get_service_token(self, client: httpx.AsyncClient, scopes: str = None) -> str:
        """Get authentication token for service account"""
        creds = SERVICE_ACCOUNT_CREDENTIALS.copy()
        if scopes:
            creds["scope"] = scopes
            
        response = await client.post(self.token_url, json=creds)
        
        if response.status_code != 200:
            raise Exception(f"Service account authentication failed: {response.status_code} - {response.text}")
        
        return response.json()["access_token"]
    
    def get_headers(self, token: str) -> Dict[str, str]:
        """Format authentication headers"""
        return {"Authorization": f"Bearer {token}"}
    
    async def get_user_headers(self, client: httpx.AsyncClient, credentials: Dict = None) -> Dict[str, str]:
        """Get authentication headers for regular user"""
        token = await self.get_user_token(client, credentials)
        return self.get_headers(token)
    
    async def get_admin_headers(self, client: httpx.AsyncClient) -> Dict[str, str]:
        """Get authentication headers for admin user"""
        token = await self.get_admin_token(client)
        return self.get_headers(token)
    
    async def get_service_headers(self, client: httpx.AsyncClient, scopes: str = None) -> Dict[str, str]:
        """Get authentication headers for service account"""
        token = await self.get_service_token(client, scopes)
        return self.get_headers(token)

# Synchronous versions for pytest TestClient
class SyncAuthHelper:
    """Synchronous helper class for handling authentication in pytest"""
    
    def __init__(self, base_url: str = ""):
        self.base_url = base_url
        self.auth_url = f"{base_url}/api/v1/auth/login"
        self.token_url = f"{base_url}/api/v1/auth/token"
    
    def get_user_token(self, client: TestClient, credentials: Dict = None) -> str:
        """Get authentication token for regular user"""
        creds = credentials or DEFAULT_USER_CREDENTIALS
        response = client.post(self.auth_url, json=creds)
        
        if response.status_code != 200:
            raise Exception(f"User authentication failed: {response.status_code} - {response.text}")
        
        return response.json()["access_token"]
    
    def get_admin_token(self, client: TestClient) -> str:
        """Get authentication token for admin user"""
        response = client.post(self.auth_url, json=ADMIN_CREDENTIALS)
        
        if response.status_code != 200:
            raise Exception(f"Admin authentication failed: {response.status_code} - {response.text}")
        
        return response.json()["access_token"]
    
    def get_service_token(self, client: TestClient, scopes: str = None) -> str:
        """Get authentication token for service account"""
        creds = SERVICE_ACCOUNT_CREDENTIALS.copy()
        if scopes:
            creds["scope"] = scopes
            
        response = client.post(self.token_url, json=creds)
        
        if response.status_code != 200:
            raise Exception(f"Service account authentication failed: {response.status_code} - {response.text}")
        
        return response.json()["access_token"]
    
    def get_headers(self, token: str) -> Dict[str, str]:
        """Format authentication headers"""
        return {"Authorization": f"Bearer {token}"}
    
    def get_user_headers(self, client: TestClient, credentials: Dict = None) -> Dict[str, str]:
        """Get authentication headers for regular user"""
        token = self.get_user_token(client, credentials)
        return self.get_headers(token)
    
    def get_admin_headers(self, client: TestClient) -> Dict[str, str]:
        """Get authentication headers for admin user"""
        token = self.get_admin_token(client)
        return self.get_headers(token)
    
    def get_service_headers(self, client: TestClient, scopes: str = None) -> Dict[str, str]:
        """Get authentication headers for service account"""
        token = self.get_service_token(client, scopes)
        return self.get_headers(token)

# Convenience functions for quick usage
async def get_authenticated_client(base_url: str = "http://localhost:8000", 
                                  user_type: str = "user",
                                  credentials: Optional[Dict] = None) -> tuple[httpx.AsyncClient, Dict[str, str]]:
    """Get an authenticated HTTP client with headers"""
    client = httpx.AsyncClient()
    auth_helper = AuthHelper(base_url)
    
    if user_type == "admin":
        headers = await auth_helper.get_admin_headers(client)
    elif user_type == "service":
        headers = await auth_helper.get_service_headers(client)
    else:
        headers = await auth_helper.get_user_headers(client, credentials)
    
    return client, headers

def create_test_credentials(email: str, password: str, tenant_code: str) -> Dict[str, str]:
    """Create test credentials dictionary"""
    return {
        "email": email,
        "password": password,
        "tenant_code": tenant_code
    }