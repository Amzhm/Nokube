/**
 * Configuration globale d'Axios avec intercepteurs
 */

import axios from 'axios';
import { getApiUrl } from './env.config';
import { authStorageRepository } from '@/features/auth/infrastructure/auth.storage';
import { AUTH_CONSTANTS } from '@/shared/constants/auth.constants';

// Instance axios globale pour toute l'application
export const apiClient = axios.create({
  baseURL: '', // Pas de baseURL, on utilise les URLs complètes
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur de requête - Ajoute automatiquement le token
apiClient.interceptors.request.use(
  (config) => {
    const token = authStorageRepository.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur de réponse - Gère les erreurs d'authentification
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Si erreur 401, nettoyer le storage SEULEMENT
    if (error.response?.status === 401) {
      authStorageRepository.clearAll();
      // La redirection sera gérée par AuthGuard
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;