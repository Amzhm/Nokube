/**
 * Étape 1 - Configuration de l'architecture
 */

'use client';

import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Plus, Trash2, Server, Database, Globe, Cpu } from 'lucide-react';
import { useArchitectureStep } from '../../presentation/useArchitectureStep.hook';
import type { ProjectArchitecture, ServiceConfig } from '@/shared/types/deployment.types';

interface ArchitectureStepProps {
  value: ProjectArchitecture | null;
  onChange: (architecture: ProjectArchitecture) => void;
}

const serviceTypes = [
  { value: 'web', label: 'Web App', icon: Globe, description: 'Frontend, interface utilisateur' },
  { value: 'api', label: 'API', icon: Server, description: 'Backend, services REST/GraphQL' },
  { value: 'database', label: 'Base de données', icon: Database, description: 'PostgreSQL, MongoDB, Redis' },
  { value: 'worker', label: 'Worker', icon: Cpu, description: 'Tâches en arrière-plan' },
];

export const ArchitectureStep = ({ value, onChange }: ArchitectureStepProps) => {
  const {
    projectName,
    description,
    services,
    metrics,
    canRemoveService,
    setProjectName,
    setDescription,
    addService,
    removeService,
    updateService,
  } = useArchitectureStep({ value, onChange });

  return (
    <div className="space-y-8">
      {/* Project Info */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Informations du projet</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Nom du projet"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="mon-super-projet"
            required
          />
          
          <Input
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description courte du projet"
          />
        </div>
      </div>

      {/* Services Configuration */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Services</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={addService}
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Ajouter un service
          </Button>
        </div>

        <div className="space-y-4">
          {services.map((service, index) => (
            <ServiceCard
              key={index}
              service={service}
              onUpdate={(updates) => updateService(index, updates)}
              onRemove={() => removeService(index)}
              canRemove={canRemoveService}
            />
          ))}
        </div>
      </div>

      {/* Architecture Preview */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Aperçu de l'architecture</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Services :</span>
            <span className="ml-2 font-medium">{metrics.totalServices}</span>
          </div>
          <div>
            <span className="text-gray-600">Réplicas totaux :</span>
            <span className="ml-2 font-medium">{metrics.totalReplicas}</span>
          </div>
          <div>
            <span className="text-gray-600">CPU demandé :</span>
            <span className="ml-2 font-medium">{metrics.totalCpu}m</span>
          </div>
          <div>
            <span className="text-gray-600">Mémoire demandée :</span>
            <span className="ml-2 font-medium">{metrics.totalMemory}Mi</span>
          </div>
        </div>
      </div>
    </div>
  );
};

interface ServiceCardProps {
  service: ServiceConfig;
  onUpdate: (updates: Partial<ServiceConfig>) => void;
  onRemove: () => void;
  canRemove: boolean;
}

const ServiceCard = ({ service, onUpdate, onRemove, canRemove }: ServiceCardProps) => {
  const selectedType = serviceTypes.find(t => t.value === service.type);
  const Icon = selectedType?.icon || Server;

  return (
    <div className="border border-gray-200 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <Icon className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h4 className="font-medium">{service.name || 'Nouveau service'}</h4>
            <p className="text-sm text-gray-500">{selectedType?.description}</p>
          </div>
        </div>
        
        {canRemove && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRemove}
            className="text-red-600 hover:text-red-700"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input
          label="Nom du service"
          value={service.name}
          onChange={(e) => onUpdate({ name: e.target.value })}
          placeholder="frontend, api, database..."
          required
        />
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
          <select
            value={service.type}
            onChange={(e) => onUpdate({ type: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {serviceTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="Réplicas"
          type="number"
          min="1"
          max="10"
          value={service.replicas}
          onChange={(e) => onUpdate({ replicas: parseInt(e.target.value) || 1 })}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">CPU</label>
          <select
            value={service.resources.cpu}
            onChange={(e) => onUpdate({ 
              resources: { ...service.resources, cpu: e.target.value }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="100m">100m (0.1 CPU)</option>
            <option value="250m">250m (0.25 CPU)</option>
            <option value="500m">500m (0.5 CPU)</option>
            <option value="1">1 (1 CPU)</option>
            <option value="2">2 (2 CPU)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Mémoire</label>
          <select
            value={service.resources.memory}
            onChange={(e) => onUpdate({ 
              resources: { ...service.resources, memory: e.target.value }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="128Mi">128Mi</option>
            <option value="256Mi">256Mi</option>
            <option value="512Mi">512Mi</option>
            <option value="1Gi">1Gi</option>
            <option value="2Gi">2Gi</option>
            <option value="4Gi">4Gi</option>
          </select>
        </div>
      </div>
    </div>
  );
};