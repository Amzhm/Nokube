/**
 * Types pour le système de déploiement NoKube
 */

// Étape 1 - Architecture
export interface ServiceConfig {
  name: string;
  type: 'web' | 'api' | 'database' | 'worker' | 'cache';
  replicas: number;
  resources: {
    cpu: string;      // "100m", "500m", "1"
    memory: string;   // "128Mi", "512Mi", "1Gi"
  };
  ports: {
    container: number;
    service: number;
  }[];
  healthCheck?: {
    path: string;
    interval: number;
  };
}

export interface NetworkConfig {
  ingress: {
    enabled: boolean;
    domain?: string;
    paths: {
      path: string;
      service: string;
    }[];
  };
  loadBalancer: {
    enabled: boolean;
    type: 'internal' | 'external';
  };
}

export interface ProjectArchitecture {
  name: string;
  description: string;
  services: ServiceConfig[];
  networking: NetworkConfig;
  environment: 'development' | 'staging' | 'production';
}

// Étape 2 - Build Configuration
export interface BuildConfig {
  language: string;           // Auto-détecté ou choisi par l'utilisateur
  framework?: string;         // React, Vue, Django, FastAPI, etc.
  buildCommands: string[];    // ["npm install", "npm run build"]
  runCommand: string;         // "npm start", "python main.py"
  dependencies: string[];     // Packages/libraries utilisés
  workingDirectory?: string;  // WORKDIR dans le Dockerfile (défaut: /app)
  containerPort?: number;     // Port exposé dans le container
  environmentVars?: {
    key: string;
    value: string;
    secret?: boolean;
  }[];
}

export interface DockerConfig {
  baseImage: string;          // Auto-généré selon le langage
  dockerfile: string;         // Dockerfile généré automatiquement
  buildArgs?: {
    key: string;
    value: string;
  }[];
}

export interface ServiceBuildConfig {
  serviceName: string;
  buildConfig: BuildConfig;
  dockerConfig: DockerConfig;
  sourceConfig?: SourceConfig;
}

// Étape 2.5 - Configuration du code source
export interface SourceConfig {
  type: 'git' | 'upload';
  gitRepository?: GitRepositoryConfig;
  uploadedFiles?: UploadConfig;
}

export interface GitRepositoryConfig {
  url: string;
  branch: string;
  rootDirectory?: string;
  deployKey?: {
    publicKey: string;
    privateKeyId: string; // Référence sécurisée côté backend
    isConfigured: boolean;
  };
}

export interface UploadConfig {
  fileId: string;
  fileName: string;
  size: number;
}

export interface DeploymentRequest {
  projectId: number;
  architecture: ProjectArchitecture;
  serviceBuildConfigs: ServiceBuildConfig[];
}

// Statuts de déploiement
export type DeploymentStatus = 
  | 'configuring'     // Configuration en cours
  | 'building'        // Build Docker en cours
  | 'deploying'       // Déploiement K8s en cours
  | 'running'         // Déployé et fonctionnel
  | 'failed'          // Échec
  | 'stopped';        // Arrêté

export interface Deployment {
  id: number;
  projectId: number;
  name: string;
  status: DeploymentStatus;
  architecture: ProjectArchitecture;
  serviceBuildConfigs: ServiceBuildConfig[];
  createdAt: string;
  updatedAt: string;
  logs?: string[];
}