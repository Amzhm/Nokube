/**
 * Page d'inscription - NoKube
 */

'use client';

import Link from 'next/link';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { useRegister } from '@/features/auth/presentation/useRegister.hook';

export default function RegisterPage() {
  const {
    formData,
    confirmPassword,
    isLoading,
    error,
    showPasswordError,
    isFormValid,
    handleChange,
    handleConfirmPasswordChange,
    handleSubmit,
  } = useRegister();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <span className="text-2xl font-bold text-white">N</span>
            </div>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">
            Créer un compte NoKube
          </h2>
          <p className="mt-2 text-gray-600">
            Rejoignez NoKube et déployez vos applications facilement
          </p>
        </div>

        {/* Form */}
        <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <Input
              label="Nom d'utilisateur"
              name="username"
              type="text"
              value={formData.username}
              onChange={handleChange}
              placeholder="Choisissez un nom d'utilisateur"
              required
              disabled={isLoading}
            />

            <Input
              label="Email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="votre.email@exemple.com"
              required
              disabled={isLoading}
            />

            <Input
              label="Mot de passe"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Choisissez un mot de passe sécurisé"
              showPasswordToggle
              required
              disabled={isLoading}
              helpText="Minimum 8 caractères recommandé"
            />

            <Input
              label="Confirmer le mot de passe"
              name="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={handleConfirmPasswordChange}
              placeholder="Confirmez votre mot de passe"
              showPasswordToggle
              required
              disabled={isLoading}
              error={showPasswordError ? "Les mots de passe ne correspondent pas" : undefined}
            />

            <Button
              type="submit"
              fullWidth
              isLoading={isLoading}
              disabled={!isFormValid}
            >
              Créer mon compte
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Déjà un compte ?{' '}
              <Link 
                href="/login" 
                className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                Se connecter
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>NoKube - Votre PaaS Kubernetes simplifié</p>
        </div>
      </div>
    </div>
  );
}