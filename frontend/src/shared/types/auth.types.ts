/**
 * Types pour l'authentification
 */

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface AuthResponse {
  message: string;
  user: User;
  token: AuthToken;
}

export interface AuthError {
  detail: string;
}

// DTOs pour les requêtes
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}