/**
 * Hook pour la page de register - Gestion des états et logique
 */

'use client';

import { useState } from 'react';
import { useAuth } from './useAuth.hook';
import type { RegisterRequest } from '@/shared/types/auth.types';

export const useRegister = () => {
  const { register, isLoading, error, clearError } = useAuth();
  const [formData, setFormData] = useState<RegisterRequest>({
    username: '',
    email: '',
    password: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleConfirmPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfirmPassword(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    
    if (formData.password !== confirmPassword) {
      return;
    }
    
    await register(formData);
  };

  const passwordsMatch = formData.password === confirmPassword;
  const showPasswordError = confirmPassword && !passwordsMatch;
  const isFormValid = formData.username && 
                     formData.email && 
                     formData.password && 
                     confirmPassword && 
                     passwordsMatch;

  return {
    // State
    formData,
    confirmPassword,
    isLoading,
    error,
    passwordsMatch,
    showPasswordError,
    isFormValid,
    
    // Actions
    handleChange,
    handleConfirmPasswordChange,
    handleSubmit,
    clearError,
  };
};