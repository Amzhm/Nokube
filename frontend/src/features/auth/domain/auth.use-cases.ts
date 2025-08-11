/**
 * Domain - Use Cases pour l'authentification
 */

import type { 
  AuthResponse, 
  LoginRequest, 
  RegisterRequest,
  User 
} from '@/shared/types/auth.types';
import { authApiRepository } from '../infrastructure/auth.api';
import { authStorageRepository } from '../infrastructure/auth.storage';

export class AuthUseCases {
  // Login use case
  async login(credentials: LoginRequest): Promise<{
    success: boolean;
    user?: User;
    error?: string;
  }> {
    try {
      const response = await authApiRepository.login(credentials);
      
      // Store auth data
      authStorageRepository.setToken(response.token.access_token);
      authStorageRepository.setUser(response.user);
      
      return {
        success: true,
        user: response.user
      };
    } catch (error: any) {
      console.error('❌ Login error:', error);
      console.error('Error response:', error.response?.data);
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      };
    }
  }

  // Register use case
  async register(userData: RegisterRequest): Promise<{
    success: boolean;
    user?: User;
    error?: string;
  }> {
    try {
      const response = await authApiRepository.register(userData);
      
      // Store auth data
      authStorageRepository.setToken(response.token.access_token);
      authStorageRepository.setUser(response.user);
      
      return {
        success: true,
        user: response.user
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      };
    }
  }

  // Logout use case
  async logout(): Promise<void> {
    authStorageRepository.clearAll();
    // Redirect will be handled by the presentation layer
  }

  // Get current user
  getCurrentUser(): User | null {
    return authStorageRepository.getUser();
  }

  // Check authentication status
  isAuthenticated(): boolean {
    return authStorageRepository.isAuthenticated();
  }

  // Verify token validity
  async verifyToken(): Promise<{
    isValid: boolean;
    user?: User;
  }> {
    const token = authStorageRepository.getToken();
    
    if (!token) {
      return { isValid: false };
    }

    try {
      const user = await authApiRepository.verifyToken(token);
      authStorageRepository.setUser(user); // Update user data
      
      return {
        isValid: true,
        user
      };
    } catch (error) {
      // Token is invalid, clear storage
      authStorageRepository.clearAll();
      return { isValid: false };
    }
  }
}

export const authUseCases = new AuthUseCases();