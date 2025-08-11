/**
 * Infrastructure - API calls pour l'authentification
 */

import { apiClient } from '@/shared/config/axios.config';
import type { 
  AuthResponse, 
  LoginRequest, 
  RegisterRequest,
  User 
} from '@/shared/types/auth.types';

// Repository pattern pour les appels API
export class AuthApiRepository {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', credentials);
    return response.data;
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', userData);
    return response.data;
  }

  async verifyToken(token: string): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/verify', {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
}

export const authApiRepository = new AuthApiRepository();