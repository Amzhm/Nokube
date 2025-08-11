/**
 * Page de déploiement - Interface 2 étapes
 */

'use client';

import { AuthGuard } from '@/features/auth/components/AuthGuard';
import { DashboardLayout } from '@/features/dashboard/components/DashboardLayout';
import { DeploymentWizard } from '@/features/deployment/components/DeploymentWizard';

export default function DeployPage() {
  return (
    <AuthGuard>
      <DashboardLayout>
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">
              Nouveau Déploiement
            </h1>
            <p className="text-gray-600 mt-2">
              Configurez votre architecture puis définissez votre build
            </p>
          </div>

          <DeploymentWizard />
        </div>
      </DashboardLayout>
    </AuthGuard>
  );
}