/**
 * Presentation - Hook React pour l'authentification
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import type { User, LoginRequest, RegisterRequest } from '@/shared/types/auth.types';
import { authUseCases } from '../domain/auth.use-cases';
import { AUTH_CONSTANTS } from '@/shared/constants/auth.constants';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export const useAuth = () => {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // Initialize auth state
  useEffect(() => {
    const initializeAuth = () => {
      try {
        // TEMPORAIRE : Utiliser le storage local sans vérification serveur
        // TODO: Fixer la route /api/v1/auth/verify dans le backend
        const token = authStorageRepository.getToken();
        const storedUser = authStorageRepository.getUser();
        
        if (token && storedUser) {
          setState({
            user: storedUser,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } else {
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } catch (error) {
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = useCallback(async (credentials: LoginRequest) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    const result = await authUseCases.login(credentials);
    
    if (result.success && result.user) {
      setState({
        user: result.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      return { success: true };
    } else {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: result.error || 'Login failed',
      }));
      
      return { success: false, error: result.error };
    }
  }, [router]);

  // Register function
  const register = useCallback(async (userData: RegisterRequest) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    const result = await authUseCases.register(userData);
    
    if (result.success && result.user) {
      setState({
        user: result.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      return { success: true };
    } else {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: result.error || 'Registration failed',
      }));
      
      return { success: false, error: result.error };
    }
  }, [router]);

  // Logout function
  const logout = useCallback(async () => {
    await authUseCases.logout();
    
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    
    router.push(AUTH_CONSTANTS.ROUTES.LOGIN);
  }, [router]);

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    // State
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    
    // Actions
    login,
    register,
    logout,
    clearError,
  };
};