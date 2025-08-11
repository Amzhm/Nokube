/**
 * Constantes pour l'authentification
 */

export const AUTH_CONSTANTS = {
  STORAGE_KEYS: {
    TOKEN: 'nokube_auth_token',
    USER: 'nokube_user_data',
  },
  TOKEN: {
    EXPIRE_DAYS: 7,
    REFRESH_THRESHOLD: 30 * 60 * 1000, // 30 minutes en ms
  },
  ROUTES: {
    LOGIN: '/login',
    REGISTER: '/register',
    DASHBOARD: '/dashboard',
    PUBLIC_ROUTES: ['/login', '/register', '/', '/about'],
  },
} as const;