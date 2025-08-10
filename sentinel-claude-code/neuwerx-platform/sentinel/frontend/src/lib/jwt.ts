/**
 * JWT utility functions for extracting token data
 */

interface JWTPayload {
  sub: string;
  tenant_id: string;
  tenant_code: string;
  email: string;
  is_service_account: boolean;
  scopes: string[];
  exp: number;
  iat: number;
  jti: string;
  session_id?: string;
  token_type: string;
}

/**
 * Decode JWT token without verification (client-side only)
 * WARNING: This is for reading token data only, not for verification
 */
export function decodeJWT(token: string): JWTPayload | null {
  try {
    // JWT has 3 parts separated by dots: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    // Decode the payload (middle part)
    const payload = parts[1];
    
    // Add padding if needed
    const paddedPayload = payload + '='.repeat((4 - payload.length % 4) % 4);
    
    // Decode base64url
    const decoded = atob(paddedPayload.replace(/-/g, '+').replace(/_/g, '/'));
    
    return JSON.parse(decoded);
  } catch (error) {
    console.error('Error decoding JWT:', error);
    return null;
  }
}

/**
 * Extract scopes from JWT access token
 */
export function getScopesFromToken(accessToken: string): string[] {
  const payload = decodeJWT(accessToken);
  return payload?.scopes || [];
}

/**
 * Check if JWT token is expired
 */
export function isTokenExpired(token: string): boolean {
  const payload = decodeJWT(token);
  if (!payload?.exp) {
    return true;
  }
  
  return Date.now() >= payload.exp * 1000;
}

/**
 * Get token expiration time in milliseconds
 */
export function getTokenExpiration(token: string): number | null {
  const payload = decodeJWT(token);
  return payload?.exp ? payload.exp * 1000 : null;
}