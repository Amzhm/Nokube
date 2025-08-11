/**
 * Étape 2.5 - Configuration du code source avec génération de clés SSH
 */

'use client';

import { useState } from 'react';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { 
  GitBranch, 
  Upload, 
  Key, 
  Copy, 
  CheckCircle, 
  ExternalLink,
  AlertCircle,
  Globe,
  Server,
  Cpu,
  FolderOpen
} from 'lucide-react';
import type { ServiceBuildConfig, ProjectArchitecture, SourceConfig, GitRepositoryConfig } from '@/shared/types/deployment.types';

interface SourceStepProps {
  serviceBuildConfigs: ServiceBuildConfig[];
  onChange: (configs: ServiceBuildConfig[]) => void;
  architecture: ProjectArchitecture | null;
}

const serviceIcons = {
  web: Globe,
  api: Server,
  worker: Cpu,
  database: Server,
};

export const SourceStep = ({ serviceBuildConfigs, onChange, architecture }: SourceStepProps) => {
  const [activeServiceIndex, setActiveServiceIndex] = useState(0);
  const [isGeneratingKey, setIsGeneratingKey] = useState(false);

  // Services qui nécessitent du code source (excluant les BDD)
  const buildableServices = architecture?.services.filter(service => 
    service.type !== 'database'
  ) || [];

  const activeService = buildableServices[activeServiceIndex];
  const activeConfig = serviceBuildConfigs[activeServiceIndex];
  const sourceConfig = activeConfig?.sourceConfig;

  const updateSourceConfig = (updates: Partial<SourceConfig>) => {
    const updatedConfigs = serviceBuildConfigs.map((config, index) =>
      index === activeServiceIndex 
        ? { 
            ...config, 
            sourceConfig: { 
              ...config.sourceConfig,
              ...updates 
            } as SourceConfig
          }
        : config
    );
    onChange(updatedConfigs);
  };

  const updateGitConfig = (updates: Partial<GitRepositoryConfig>) => {
    updateSourceConfig({
      type: 'git',
      gitRepository: {
        ...sourceConfig?.gitRepository,
        ...updates
      } as GitRepositoryConfig
    });
  };

  const generateDeployKey = async () => {
    setIsGeneratingKey(true);
    try {
      // Simuler l'appel API pour générer la clé
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // TODO: Remplacer par vraie API call
      const mockPublicKey = `ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhA... nokube-deploy-${Date.now()}`;
      const mockPrivateKeyId = `key-${Date.now()}`;

      updateGitConfig({
        deployKey: {
          publicKey: mockPublicKey,
          privateKeyId: mockPrivateKeyId,
          isConfigured: false
        }
      });
    } catch (error) {
      console.error('Erreur génération clé:', error);
    } finally {
      setIsGeneratingKey(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // TODO: Ajouter toast de succès
    } catch (error) {
      console.error('Erreur copie:', error);
    }
  };

  const markKeyAsConfigured = () => {
    if (sourceConfig?.gitRepository?.deployKey) {
      updateGitConfig({
        deployKey: {
          ...sourceConfig.gitRepository.deployKey,
          isConfigured: true
        }
      });
    }
  };

  if (buildableServices.length === 0) {
    return (
      <div className="text-center py-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Aucun service nécessitant du code source
        </h3>
        <p className="text-gray-600">
          Tous vos services sont des bases de données qui ne nécessitent pas de code source.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Service Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {buildableServices.map((service, index) => {
            const Icon = serviceIcons[service.type as keyof typeof serviceIcons];
            const hasSource = serviceBuildConfigs[index]?.sourceConfig;
            
            return (
              <button
                key={service.name}
                onClick={() => setActiveServiceIndex(index)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors
                  ${index === activeServiceIndex
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span>{service.name}</span>
                {hasSource && (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Active Service Configuration */}
      {activeService && (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Code source pour {activeService.name}
            </h3>
            <p className="text-gray-600">
              Configurez la source du code pour ce service {activeService.type}
            </p>
          </div>

          {/* Source Type Selection */}
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Type de source</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => updateSourceConfig({ type: 'git' })}
                className={`p-4 text-left border rounded-lg transition-colors ${
                  sourceConfig?.type === 'git'
                    ? 'border-blue-500 bg-blue-50 text-blue-900'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <GitBranch className="w-5 h-5" />
                  <span className="font-medium">Git Repository</span>
                </div>
                <p className="text-sm text-gray-600">
                  Clonage depuis GitHub, GitLab, etc. avec clés SSH automatiques
                </p>
              </button>

              <button
                onClick={() => updateSourceConfig({ type: 'upload' })}
                className={`p-4 text-left border rounded-lg transition-colors ${
                  sourceConfig?.type === 'upload'
                    ? 'border-blue-500 bg-blue-50 text-blue-900'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <Upload className="w-5 h-5" />
                  <span className="font-medium">Upload Fichiers</span>
                </div>
                <p className="text-sm text-gray-600">
                  Upload d'un fichier ZIP contenant votre code source
                </p>
              </button>
            </div>
          </div>

          {/* Git Configuration */}
          {sourceConfig?.type === 'git' && (
            <div className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Configuration Git</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      URL du Repository
                    </label>
                    <Input
                      value={sourceConfig.gitRepository?.url || ''}
                      onChange={(e) => updateGitConfig({ url: e.target.value })}
                      placeholder="https://github.com/user/repo.git"
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Branche
                    </label>
                    <Input
                      value={sourceConfig.gitRepository?.branch || 'main'}
                      onChange={(e) => updateGitConfig({ branch: e.target.value })}
                      placeholder="main"
                      className="w-full"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Répertoire racine (optionnel)
                  </label>
                  <div className="flex items-center gap-2">
                    <FolderOpen className="w-4 h-4 text-gray-400" />
                    <Input
                      value={sourceConfig.gitRepository?.rootDirectory || ''}
                      onChange={(e) => updateGitConfig({ rootDirectory: e.target.value })}
                      placeholder="/backend (pour les monorepos)"
                      className="flex-1"
                    />
                  </div>
                </div>
              </div>

              {/* Deploy Key Generation */}
              {sourceConfig.gitRepository?.url && (
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900 flex items-center gap-2">
                    <Key className="w-4 h-4" />
                    Clé de déploiement SSH
                  </h4>

                  {!sourceConfig.gitRepository.deployKey ? (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center gap-2 text-blue-800 mb-2">
                        <AlertCircle className="w-4 h-4" />
                        <span className="font-medium">Clé SSH requise</span>
                      </div>
                      <p className="text-blue-700 text-sm mb-3">
                        Nous allons générer automatiquement une paire de clés SSH pour accéder à votre repository en sécurité.
                      </p>
                      <Button
                        onClick={generateDeployKey}
                        disabled={isGeneratingKey}
                        className="flex items-center gap-2"
                      >
                        <Key className="w-4 h-4" />
                        {isGeneratingKey ? 'Génération...' : 'Générer la clé SSH'}
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {!sourceConfig.gitRepository.deployKey.isConfigured ? (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 text-yellow-800 mb-2">
                            <AlertCircle className="w-4 h-4" />
                            <span className="font-medium">Configuration requise</span>
                          </div>
                          <p className="text-yellow-700 text-sm mb-3">
                            Copiez la clé publique ci-dessous et ajoutez-la dans les paramètres de votre repository.
                          </p>
                          
                          <div className="space-y-3">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Clé publique à ajouter
                              </label>
                              <div className="flex items-center gap-2">
                                <textarea
                                  readOnly
                                  value={sourceConfig.gitRepository.deployKey.publicKey}
                                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 font-mono text-xs resize-none"
                                  rows={3}
                                />
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => copyToClipboard(sourceConfig.gitRepository.deployKey!.publicKey)}
                                  className="flex items-center gap-1"
                                >
                                  <Copy className="w-3 h-3" />
                                  Copier
                                </Button>
                              </div>
                            </div>

                            <div className="bg-white border border-gray-200 rounded-lg p-3">
                              <h5 className="font-medium text-gray-900 mb-2">Instructions :</h5>
                              <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                                <li>Allez dans les paramètres de votre repository</li>
                                <li>Naviguez vers "Deploy Keys" ou "SSH Keys"</li>
                                <li>Cliquez sur "Add deploy key"</li>
                                <li>Collez la clé publique ci-dessus</li>
                                <li>Activez "Allow write access" si nécessaire</li>
                              </ol>
                              <div className="mt-3 flex items-center gap-2">
                                <ExternalLink className="w-4 h-4 text-blue-600" />
                                <a
                                  href={getRepositorySettingsUrl(sourceConfig.gitRepository.url)}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:text-blue-700 text-sm"
                                >
                                  Ouvrir les paramètres du repository
                                </a>
                              </div>
                            </div>

                            <Button
                              onClick={markKeyAsConfigured}
                              className="flex items-center gap-2"
                            >
                              <CheckCircle className="w-4 h-4" />
                              J'ai configuré la clé
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 text-green-800">
                            <CheckCircle className="w-4 h-4" />
                            <span className="font-medium">Clé SSH configurée</span>
                          </div>
                          <p className="text-green-700 text-sm mt-1">
                            La clé de déploiement est prête. NoKube peut maintenant cloner votre repository.
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Upload Configuration */}
          {sourceConfig?.type === 'upload' && (
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Upload du code source</h4>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h5 className="font-medium text-gray-900 mb-2">
                  Glissez votre fichier ZIP ici
                </h5>
                <p className="text-gray-600 text-sm mb-4">
                  ou cliquez pour sélectionner un fichier
                </p>
                <Button variant="outline">
                  Sélectionner un fichier
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Helper function pour générer l'URL des paramètres selon le provider
const getRepositorySettingsUrl = (gitUrl: string): string => {
  try {
    if (gitUrl.includes('github.com')) {
      const match = gitUrl.match(/github\.com[/:]([\w-]+)\/([\w-]+)/);
      if (match) {
        return `https://github.com/${match[1]}/${match[2]}/settings/keys`;
      }
    } else if (gitUrl.includes('gitlab.com')) {
      const match = gitUrl.match(/gitlab\.com[/:]([\w-]+)\/([\w-]+)/);
      if (match) {
        return `https://gitlab.com/${match[1]}/${match[2]}/-/settings/repository`;
      }
    }
    return gitUrl; // Fallback
  } catch {
    return gitUrl;
  }
};