/**
 * Environment configuration
 * Centralise toutes les variables d'environnement
 */

export const envConfig = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost',
    version: 'v1',
  },
  app: {
    name: process.env.NEXT_PUBLIC_APP_NAME || 'NoKube',
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  },
  auth: {
    tokenStorageKey: 'nokube_auth_token',
    tokenExpireDays: 7,
  },
} as const;

export const getApiUrl = (endpoint: string = '') => {
  return `${envConfig.api.baseUrl}/api/${envConfig.api.version}${endpoint}`;
};