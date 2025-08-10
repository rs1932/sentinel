import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should redirect to login page when not authenticated', async ({ page }) => {
    await page.goto('/');
    
    // Should redirect to login page
    await expect(page).toHaveURL('/auth/login');
    
    // Should see login form
    await expect(page.getByText('Sign in to your account')).toBeVisible();
    await expect(page.getByPlaceholder('Enter your email')).toBeVisible();
    await expect(page.getByPlaceholder('Enter your password')).toBeVisible();
  });

  test('should show login form elements', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Check for app branding
    await expect(page.getByText('Sentinel')).toBeVisible();
    await expect(page.getByText('Multi-tenant User Management Platform')).toBeVisible();
    
    // Check form elements
    await expect(page.getByLabel('Email Address')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
    
    // Check demo credentials section
    await expect(page.getByText('Demo Credentials:')).toBeVisible();
    await expect(page.getByText('admin@example.com')).toBeVisible();
  });

  test('should validate form fields', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Try to submit empty form
    await page.getByRole('button', { name: 'Sign in' }).click();
    
    // Should show validation errors
    await expect(page.getByText('Email is required')).toBeVisible();
    await expect(page.getByText('Password is required')).toBeVisible();
  });

  test('should toggle password visibility', async ({ page }) => {
    await page.goto('/auth/login');
    
    const passwordInput = page.getByPlaceholder('Enter your password');
    const toggleButton = page.locator('[role="button"]').filter({ hasText: /👁/ }).last();
    
    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click toggle to show password
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click again to hide password
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should handle login with demo credentials', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Fill in demo credentials
    await page.getByPlaceholder('Enter your email').fill('admin@example.com');
    await page.getByPlaceholder('Enter your password').fill('password123');
    
    // Submit form
    await page.getByRole('button', { name: 'Sign in' }).click();
    
    // Should show loading state briefly
    await expect(page.getByText('Signing in...')).toBeVisible();
    
    // Should redirect to dashboard after successful login
    await expect(page).toHaveURL('/dashboard');
    
    // Should see dashboard content
    await expect(page.getByText('Good morning, John!')).toBeVisible();
    await expect(page.getByText('Welcome back to your Super Administrator dashboard')).toBeVisible();
  });
});