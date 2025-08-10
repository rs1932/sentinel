#!/usr/bin/env python3
"""
Test auth validation endpoint
"""
import asyncio
import httpx

async def test_validation():
    async with httpx.AsyncClient() as client:
        # Get token
        auth_response = await client.post(
            'http://localhost:8000/api/v1/auth/login',
            json={'email': 'test@example.com', 'password': 'password123', 'tenant_code': 'TEST'}
        )
        
        if auth_response.status_code != 200:
            print(f'Login failed: {auth_response.status_code}')
            return
            
        token_data = auth_response.json()
        access_token = token_data['access_token']
        print(f'Token: {access_token[:50]}...')
        
        # Test validation endpoint
        validate_response = await client.get(
            'http://localhost:8000/api/v1/auth/validate',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        print(f'Validation status: {validate_response.status_code}')
        if validate_response.status_code != 200:
            print(f'Validation response: {validate_response.text}')
        else:
            print('Validation successful')

if __name__ == "__main__":
    asyncio.run(test_validation())