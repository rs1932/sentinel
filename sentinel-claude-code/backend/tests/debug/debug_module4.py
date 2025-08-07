#!/usr/bin/env python3
"""Debug script for Module 4 failing tests"""
import asyncio
import httpx
import json
import time

async def debug_failures():
    client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
    timestamp = int(time.time())
    
    # Login
    login = await client.post('http://localhost:8000/api/v1/auth/login', json={
        'email': 'test@example.com', 'password': 'password123', 'tenant_code': 'TEST'
    })
    
    if login.status_code != 200:
        print(f'Login failed: {login.status_code}')
        return
        
    token = login.json()['access_token']
    user_id = login.json()['user_id']
    headers = {'Authorization': f'Bearer {token}'}
    
    print('Testing the 4 failing scenarios...')
    print('=' * 60)
    
    # 1. Manager role creation conflict (409)
    print('1. Testing Manager Role Creation...')
    root_role = await client.post('http://localhost:8000/api/v1/roles/', headers=headers, json={
        'name': f'debug_root_{timestamp}',
        'display_name': 'Debug Root',
        'type': 'custom',
        'priority': 1000
    })
    
    if root_role.status_code == 201:
        root_id = root_role.json()['id']
        print(f'   Root role created: {root_id}')
        
        # Try creating manager role with unique name
        manager_role = await client.post('http://localhost:8000/api/v1/roles/', headers=headers, json={
            'name': f'debug_manager_{timestamp}',  
            'display_name': 'Debug Manager',
            'parent_role_id': root_id,
            'type': 'custom',
            'priority': 800
        })
        print(f'   Manager role creation: {manager_role.status_code}')
        if manager_role.status_code != 201:
            print(f'   Error: {manager_role.text[:200]}')
    
    print()
    
    # 2. Role assignment failure (500)
    print('2. Testing Role Assignment...')
    test_role = await client.post('http://localhost:8000/api/v1/roles/', headers=headers, json={
        'name': f'debug_assign_{timestamp}',
        'display_name': 'Debug Assign',
        'type': 'custom',
        'is_assignable': True
    })
    
    if test_role.status_code == 201:
        role_id = test_role.json()['id']
        print(f'   Test role created: {role_id}')
        
        # Try assignment
        assign = await client.post(f'http://localhost:8000/api/v1/roles/{role_id}/users', headers=headers, json={
            'user_id': user_id,
            'role_id': role_id,
            'is_active': True
        })
        print(f'   Role assignment: {assign.status_code}')
        if assign.status_code != 201:
            print(f'   Full error response:')
            print(f'   {assign.text}')
    
    print()
    
    # 3. Role validation (422)
    print('3. Testing Role Validation...')
    validate = await client.post('http://localhost:8000/api/v1/roles/validate', headers=headers, params={
        'role_id': role_id if 'role_id' in locals() else None,
        'parent_role_id': None
    })
    print(f'   Validation: {validate.status_code}')
    if validate.status_code != 200:
        print(f'   Error: {validate.text[:200]}')
    
    await client.aclose()

if __name__ == '__main__':
    asyncio.run(debug_failures())