/**
 * Hook pour l'étape Architecture - Gestion des états et logique
 */

'use client';

import { useState, useEffect } from 'react';
import type { ProjectArchitecture, ServiceConfig } from '@/shared/types/deployment.types';

const defaultService: ServiceConfig = {
  name: '',
  type: 'web',
  replicas: 1,
  resources: {
    cpu: '100m',
    memory: '128Mi',
  },
  ports: [{ container: 3000, service: 80 }],
  healthCheck: {
    path: '/health',
    interval: 30,
  },
};

interface UseArchitectureStepProps {
  value: ProjectArchitecture | null;
  onChange: (architecture: ProjectArchitecture) => void;
}

export const useArchitectureStep = ({ value, onChange }: UseArchitectureStepProps) => {
  const [projectName, setProjectName] = useState(value?.name || '');
  const [description, setDescription] = useState(value?.description || '');
  const [services, setServices] = useState<ServiceConfig[]>(value?.services || [{ ...defaultService }]);

  const addService = () => {
    setServices([...services, { ...defaultService, name: `service-${services.length + 1}` }]);
  };

  const removeService = (index: number) => {
    setServices(services.filter((_, i) => i !== index));
  };

  const updateService = (index: number, updates: Partial<ServiceConfig>) => {
    const updated = services.map((service, i) => 
      i === index ? { ...service, ...updates } : service
    );
    setServices(updated);
  };

  const updateArchitecture = () => {
    const architecture: ProjectArchitecture = {
      name: projectName,
      description,
      services,
      networking: {
        ingress: {
          enabled: true,
          paths: services
            .filter(s => s.type === 'web' || s.type === 'api')
            .map(s => ({ path: `/${s.name}/*`, service: s.name })),
        },
        loadBalancer: {
          enabled: false,
          type: 'internal',
        },
      },
      environment: 'development',
    };
    onChange(architecture);
  };

  const getArchitectureMetrics = () => {
    return {
      totalServices: services.length,
      totalReplicas: services.reduce((sum, s) => sum + s.replicas, 0),
      totalCpu: services.reduce((sum, s) => sum + parseInt(s.resources.cpu) * s.replicas, 0),
      totalMemory: services.reduce((sum, s) => sum + parseInt(s.resources.memory) * s.replicas, 0),
    };
  };

  const isValid = () => {
    return projectName && services.length > 0 && services.every(s => s.name);
  };

  useEffect(() => {
    if (isValid()) {
      updateArchitecture();
    }
  }, [projectName, description, services]);

  return {
    projectName,
    description,
    services,
    metrics: getArchitectureMetrics(),
    canRemoveService: services.length > 1,
    isValid: isValid(),
    setProjectName,
    setDescription,
    addService,
    removeService,
    updateService,
  };
};