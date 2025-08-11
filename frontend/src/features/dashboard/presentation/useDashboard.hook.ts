/**
 * Hook pour le dashboard principal
 */

'use client';

import { useAuthContext } from '@/features/auth/context/AuthProvider';

export const useDashboard = () => {
  const { user, isAuthenticated, isLoading } = useAuthContext();

  return {
    user,
    isAuthenticated,
    isLoading,
  };
};