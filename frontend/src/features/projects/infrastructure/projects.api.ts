/**
 * Infrastructure - API calls pour les projets
 */

import { apiClient } from '@/shared/config/axios.config';
import type { Project, CreateProjectRequest } from '@/shared/types/project.types';

export class ProjectsApiRepository {
  async getAllProjects(): Promise<Project[]> {
    const response = await apiClient.get<Project[]>('/api/v1/projects');
    return response.data;
  }

  async getProject(id: number): Promise<Project> {
    const response = await apiClient.get<Project>(`/api/v1/projects/${id}`);
    return response.data;
  }

  async createProject(data: CreateProjectRequest): Promise<Project> {
    const response = await apiClient.post<Project>('/api/v1/projects', data);
    return response.data;
  }

  async updateProject(id: number, data: Partial<CreateProjectRequest>): Promise<Project> {
    const response = await apiClient.put<Project>(`/api/v1/projects/${id}`, data);
    return response.data;
  }

  async deleteProject(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/projects/${id}`);
  }
}

export const projectsApiRepository = new ProjectsApiRepository();