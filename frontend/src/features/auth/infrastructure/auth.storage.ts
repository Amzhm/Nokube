/**
 * Infrastructure - Gestion du stockage local (cookies/localStorage)
 */

import Cookies from 'js-cookie';
import { AUTH_CONSTANTS } from '@/shared/constants/auth.constants';
import type { User, AuthToken } from '@/shared/types/auth.types';

export class AuthStorageRepository {
  // Token management
  setToken(token: string): void {
    Cookies.set(AUTH_CONSTANTS.STORAGE_KEYS.TOKEN, token, {
      expires: AUTH_CONSTANTS.TOKEN.EXPIRE_DAYS,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax'
    });
  }

  getToken(): string | null {
    return Cookies.get(AUTH_CONSTANTS.STORAGE_KEYS.TOKEN) || null;
  }

  removeToken(): void {
    Cookies.remove(AUTH_CONSTANTS.STORAGE_KEYS.TOKEN);
  }

  // User data management
  setUser(user: User): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(
        AUTH_CONSTANTS.STORAGE_KEYS.USER, 
        JSON.stringify(user)
      );
    }
  }

  getUser(): User | null {
    if (typeof window === 'undefined') return null;
    
    const userData = localStorage.getItem(AUTH_CONSTANTS.STORAGE_KEYS.USER);
    return userData ? JSON.parse(userData) : null;
  }

  removeUser(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(AUTH_CONSTANTS.STORAGE_KEYS.USER);
    }
  }

  // Clear all auth data
  clearAll(): void {
    this.removeToken();
    this.removeUser();
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }
}

export const authStorageRepository = new AuthStorageRepository();