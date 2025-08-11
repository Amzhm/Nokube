/**
 * Hook pour la gestion des projets
 */

'use client';

import { useState, useEffect } from 'react';
import { projectsUseCases } from '../domain/projects.use-cases';
import type { Project } from '@/shared/types/project.types';

export const useProjects = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await projectsUseCases.getAllProjects();
      
      if (result.success && result.projects) {
        setProjects(result.projects);
      } else {
        setError(result.error || 'Erreur lors du chargement des projets');
      }
    } catch (err) {
      setError('Erreur lors du chargement des projets');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  return {
    projects,
    isLoading,
    error,
    refetch: loadProjects,
  };
};