/**
 * Hook pour la page de login - Gestion des états et logique
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '../context/AuthProvider';
import { AUTH_CONSTANTS } from '@/shared/constants/auth.constants';
import type { LoginRequest } from '@/shared/types/auth.types';

export const useLogin = () => {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthContext();
  const [formData, setFormData] = useState<LoginRequest>({
    username: '',
    password: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    
    const result = await login(formData);
    
    if (result.success) {
      router.push(AUTH_CONSTANTS.ROUTES.DASHBOARD);
    }
  };

  const isFormValid = formData.username && formData.password;

  return {
    // State
    formData,
    isLoading,
    error,
    isFormValid,
    
    // Actions
    handleChange,
    handleSubmit,
    clearError,
  };
};