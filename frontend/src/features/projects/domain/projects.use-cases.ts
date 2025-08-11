/**
 * Use cases pour la gestion des projets
 */

import { projectsApiRepository } from '../infrastructure/projects.api';
import type { Project, CreateProjectRequest } from '@/shared/types/project.types';

class ProjectsUseCases {
  async getAllProjects(): Promise<{
    success: boolean;
    projects?: Project[];
    error?: string;
  }> {
    try {
      const projects = await projectsApiRepository.getAllProjects();
      return { success: true, projects };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Erreur lors de la récupération des projets'
      };
    }
  }

  async getProject(id: number): Promise<{
    success: boolean;
    project?: Project;
    error?: string;
  }> {
    try {
      const project = await projectsApiRepository.getProject(id);
      return { success: true, project };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Erreur lors de la récupération du projet'
      };
    }
  }

  async createProject(data: CreateProjectRequest): Promise<{
    success: boolean;
    project?: Project;
    error?: string;
  }> {
    try {
      const project = await projectsApiRepository.createProject(data);
      return { success: true, project };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Erreur lors de la création du projet'
      };
    }
  }

  async deleteProject(id: number): Promise<{
    success: boolean;
    error?: string;
  }> {
    try {
      await projectsApiRepository.deleteProject(id);
      return { success: true };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Erreur lors de la suppression du projet'
      };
    }
  }
}

export const projectsUseCases = new ProjectsUseCases();