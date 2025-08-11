/**
 * Types pour les projets - Architecture microservices
 */

// Types pour l'architecture en 2 étapes
export interface ProjectArchitecture {
  name: string;
  services: ServiceConfig[];
  networking: NetworkConfig;
}

export interface ServiceConfig {
  name: string;
  type: 'web' | 'backend' | 'database' | 'cache' | 'queue' | 'custom';
  replicas: number;
  resources: ResourceConfig;
  ports: number[];
  env?: string[];
  scaling?: ScalingConfig;
}

export interface ResourceConfig {
  cpu: string;
  memory: string;
}

export interface ScalingConfig {
  min: number;
  max: number;
  targetCPU: number;
}

export interface NetworkConfig {
  loadBalancer: boolean;
  ingress?: {
    domain: string;
    ssl?: boolean;
  };
}

// Types pour la configuration build
export interface ServiceBuildConfig {
  serviceName: string;
  repository: string;
  build: BuildConfig;
}

export interface BuildConfig {
  language: string;
  dependencies: string[];
  buildSteps: string[];
  runCommand: string;
  healthCheck?: string;
  port?: number;
}

// Types existants simplifiés
export interface Project {
  id: number;
  name: string;
  description: string;
  owner: string;
  status: 'created' | 'building' | 'deployed' | 'failed';
  created_at: string;
  updated_at: string;
  // Architecture config (optionnel pour rétrocompatibilité)
  architecture?: ProjectArchitecture;
  buildConfigs?: ServiceBuildConfig[];
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
  limit: number;
  offset: number;
}