/**
 * Page de connexion - NoKube
 */

'use client';

import Link from 'next/link';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { useLogin } from '@/features/auth/presentation/useLogin.hook';

export default function LoginPage() {
  const {
    formData,
    isLoading,
    error,
    isFormValid,
    handleChange,
    handleSubmit,
  } = useLogin();

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
            Connexion à NoKube
          </h2>
          <p className="mt-2 text-gray-600">
            Connectez-vous pour accéder à votre plateforme PaaS
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
              placeholder="Votre nom d'utilisateur"
              required
              disabled={isLoading}
            />

            <Input
              label="Mot de passe"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Votre mot de passe"
              showPasswordToggle
              required
              disabled={isLoading}
            />

            <Button
              type="submit"
              fullWidth
              isLoading={isLoading}
              disabled={!isFormValid}
            >
              Se connecter
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Pas encore de compte ?{' '}
              <Link 
                href="/register" 
                className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                Créer un compte
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