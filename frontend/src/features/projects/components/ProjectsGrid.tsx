/**
 * Composant pour afficher la grille des projets
 */

'use client';

import { useProjects } from '@/features/projects/presentation/useProjects.hook';
import { Button } from '@/shared/ui/Button';
import { 
  FolderOpen, 
  Calendar, 
  Activity,
  Settings,
  Play,
  MoreVertical 
} from 'lucide-react';
import type { Project } from '@/shared/types/project.types';

export const ProjectsGrid = () => {
  const { projects, isLoading, error } = useProjects();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-2/3"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">
          Erreur lors du chargement des projets
        </div>
        <Button variant="outline">
          Réessayer
        </Button>
      </div>
    );
  }

  if (!projects?.length) {
    return (
      <div className="text-center py-12">
        <FolderOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Aucun projet
        </h3>
        <p className="text-gray-500 mb-6">
          Créez votre premier projet pour commencer à déployer sur Kubernetes
        </p>
        <Button>
          Créer un projet
        </Button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
};

interface ProjectCardProps {
  project: Project;
}

const ProjectCard = ({ project }: ProjectCardProps) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800';
      case 'stopped':
        return 'bg-red-100 text-red-800';
      case 'building':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running':
        return 'En cours';
      case 'stopped':
        return 'Arrêté';
      case 'building':
        return 'Construction';
      default:
        return 'Inconnu';
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
            <FolderOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{project.name}</h3>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
              {getStatusText(project.status)}
            </span>
          </div>
        </div>
        
        <button className="text-gray-400 hover:text-gray-600">
          <MoreVertical className="w-5 h-5" />
        </button>
      </div>

      {/* Description */}
      <p className="text-gray-600 text-sm mb-4 line-clamp-2">
        {project.description || 'Aucune description disponible'}
      </p>

      {/* Metadata */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-500">
          <Calendar className="w-4 h-4 mr-2" />
          Créé {new Date(project.created_at).toLocaleDateString('fr-FR')}
        </div>
        <div className="flex items-center text-sm text-gray-500">
          <Activity className="w-4 h-4 mr-2" />
          {project.services?.length || 0} service(s)
        </div>
      </div>

      {/* Actions */}
      <div className="flex space-x-2">
        <Button size="sm" className="flex-1">
          <Play className="w-4 h-4 mr-1" />
          Déployer
        </Button>
        <Button variant="outline" size="sm">
          <Settings className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};