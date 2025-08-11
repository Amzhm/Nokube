/**
 * Dashboard principal - NoKube
 */

'use client';

import Link from 'next/link';
import { useDashboard } from '@/features/dashboard/presentation/useDashboard.hook';
import { DashboardLayout } from '@/features/dashboard/components/DashboardLayout';
import { ProjectsGrid } from '@/features/projects/components/ProjectsGrid';
import { AuthGuard } from '@/features/auth/components/AuthGuard';
import { Button } from '@/shared/ui/Button';
import { Plus } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useDashboard();

  return (
    <AuthGuard>
      <DashboardLayout>
        <div className="space-y-8">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Bienvenue, {user?.username}
              </h1>
              <p className="text-gray-600 mt-2">
                Gérez vos projets et déploiements Kubernetes
              </p>
            </div>
            
            <Link href="/deploy">
              <Button className="flex items-center gap-2">
                <Plus className="w-5 h-5" />
                Nouveau Déploiement
              </Button>
            </Link>
          </div>

          {/* Projects Grid */}
          <ProjectsGrid />
        </div>
      </DashboardLayout>
    </AuthGuard>
  );
}