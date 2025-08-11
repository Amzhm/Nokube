/**
 * Étape 2 - Configuration du build multi-services avec onglets
 */

'use client';

import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Plus, Trash2, Server, Globe, Cpu, CheckCircle, Clock, AlertCircle, Terminal } from 'lucide-react';
import { useMultiServiceBuild } from '../../presentation/useMultiServiceBuild.hook';
import type { ServiceBuildConfig, ProjectArchitecture } from '@/shared/types/deployment.types';

interface BuildStepProps {
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

const statusIcons = {
  configured: CheckCircle,
  partial: AlertCircle,
  pending: Clock,
};

const statusColors = {
  configured: 'text-green-600',
  partial: 'text-yellow-600',
  pending: 'text-gray-400',
};

export const BuildStep = ({ serviceBuildConfigs, onChange, architecture }: BuildStepProps) => {
  const {
    buildableServices,
    activeServiceIndex,
    activeService,
    activeServiceBuildConfig,
    selectedDomain,
    domainOptions,
    setActiveServiceIndex,
    setSelectedDomain,
    updateBuildConfig,
    generateDockerfile,
    getServiceConfigStatus,
    applyDomainTemplate,
    getAvailableLanguagesForDomain,
    getFrameworkSuggestions,
    updateFrameworkSuggestions,
  } = useMultiServiceBuild({ serviceBuildConfigs, onChange, architecture });

  // Utiliser directement les valeurs du service actuel
  const currentBuildConfig = activeServiceBuildConfig?.buildConfig;
  
  const language = currentBuildConfig?.language || 'javascript';
  const framework = currentBuildConfig?.framework || '';
  const buildCommands = currentBuildConfig?.buildCommands || [];
  const runCommand = currentBuildConfig?.runCommand || '';
  const workingDirectory = currentBuildConfig?.workingDirectory || '/app';
  const containerPort = currentBuildConfig?.containerPort || 3000;
  
  const updateCurrentBuildConfig = (updates: Partial<any>) => {
    const updatedConfig = {
      ...currentBuildConfig,
      ...updates,
    };
    updateBuildConfig(activeServiceIndex, updatedConfig);
  };
  
  const setLanguage = (lang: string) => updateCurrentBuildConfig({ language: lang });
  const setFramework = (fw: string) => {
    updateCurrentBuildConfig({ framework: fw });
    // Appliquer les suggestions seulement si le framework change vraiment
    if (fw && fw !== framework && selectedDomain !== 'custom') {
      updateFrameworkSuggestions(activeServiceIndex, fw);
    }
  };
  const setRunCommand = (cmd: string) => updateCurrentBuildConfig({ runCommand: cmd });
  const setWorkingDirectory = (dir: string) => updateCurrentBuildConfig({ workingDirectory: dir });
  const setContainerPort = (port: number) => updateCurrentBuildConfig({ containerPort: port });
  
  const addBuildCommand = () => {
    updateCurrentBuildConfig({ 
      buildCommands: [...buildCommands, ''] 
    });
  };

  // S'assurer qu'il y a au moins une commande vide si aucune commande
  const displayBuildCommands = buildCommands.length === 0 ? [''] : buildCommands;
  
  const updateBuildCommand = (index: number, command: string) => {
    // Si c'est la première commande et que buildCommands est vide, créer un nouveau tableau
    if (buildCommands.length === 0 && index === 0) {
      updateCurrentBuildConfig({ buildCommands: [command] });
    } else {
      const updated = buildCommands.map((cmd, i) => i === index ? command : cmd);
      updateCurrentBuildConfig({ buildCommands: updated });
    }
  };
  
  const removeBuildCommand = (index: number) => {
    const updated = buildCommands.filter((_, i) => i !== index);
    updateCurrentBuildConfig({ buildCommands: updated });
  };
  
  const handleDomainChange = (domain: string) => {
    setSelectedDomain(domain);
    if (domain) {
      applyDomainTemplate(activeServiceIndex, domain);
    }
  };
  
  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    // Le langage est maintenant géré automatiquement par framework
  };

  if (buildableServices.length === 0) {
    return (
      <div className="text-center py-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Aucun service à configurer
        </h3>
        <p className="text-gray-600">
          Tous vos services sont des bases de données qui ne nécessitent pas de build.
        </p>
      </div>
    );
  }

  const dockerfile = generateDockerfile(currentBuildConfig || {
    language: 'javascript',
    framework: 'Node.js',
    buildCommands: [],
    runCommand: 'npm start',
    dependencies: [],
    environmentVars: [],
  });

  return (
    <div className="space-y-6">
      {/* Service Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {buildableServices.map((service, index) => {
            const Icon = serviceIcons[service.type as keyof typeof serviceIcons];
            const status = getServiceConfigStatus(index);
            const StatusIcon = statusIcons[status];
            
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
                <StatusIcon className={`w-4 h-4 ${statusColors[status]}`} />
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
              Configuration de {activeService.name}
            </h3>
            <p className="text-gray-600">
              Service de type {activeService.type} - {activeService.replicas} réplica(s)
            </p>
          </div>

          {/* Domain Selection */}
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Domaine d'application</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {domainOptions.map(domain => (
                <button
                  key={domain.id}
                  onClick={() => handleDomainChange(domain.id)}
                  className={`p-3 text-left border rounded-lg transition-colors ${
                    selectedDomain === domain.id
                      ? 'border-blue-500 bg-blue-50 text-blue-900'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium text-sm">{domain.label}</div>
                  <div className="text-xs text-gray-500 mt-1">{domain.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Language & Framework */}
          {selectedDomain && (
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Langage et Framework</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Langage</label>
                  <select
                    value={language}
                    onChange={(e) => handleLanguageChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Sélectionner un langage</option>
                    {getAvailableLanguagesForDomain(selectedDomain).map(lang => (
                      <option key={lang} value={lang}>
                        {lang.charAt(0).toUpperCase() + lang.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Framework / Technologies</label>
                  <div className="relative">
                    <Input
                      value={framework}
                      onChange={(e) => setFramework(e.target.value)}
                      placeholder={selectedDomain === 'custom' ? 'Votre framework...' : 'Tapez pour suggestions intelligentes'}
                      list={`frameworks-${activeServiceIndex}`}
                    />
                    {selectedDomain !== 'custom' && language && (
                      <datalist id={`frameworks-${activeServiceIndex}`}>
                        {getFrameworkSuggestions(selectedDomain, language).map((fw: string, index: number) => (
                          <option key={index} value={fw} />
                        ))}
                      </datalist>
                    )}
                  </div>
                  {framework && selectedDomain !== 'custom' && (
                    <p className="text-xs text-blue-600 mt-1">
                      Le framework influence les commandes de build et le Dockerfile
                    </p>
                  )}
                </div>
              </div>
              
              {selectedDomain === 'custom' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-yellow-800">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">Configuration libre</span>
                  </div>
                  <p className="text-sm text-yellow-700 mt-1">
                    Vous gerez tous les champs manuellement. Aucune suggestion automatique.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Build Commands */}
          {selectedDomain && language && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-gray-900">Commandes de build</h4>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={addBuildCommand}
                  className="flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Ajouter
                </Button>
              </div>

              <div className="space-y-2">
                {displayBuildCommands.map((command, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="flex items-center gap-2 flex-1">
                      <Terminal className="w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={command}
                        onChange={(e) => updateBuildCommand(index, e.target.value)}
                        placeholder="npm install, npm run build..."
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    {displayBuildCommands.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeBuildCommand(index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>

              {/* Run Command */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Commande d'exécution</h4>
                <Input
                  value={runCommand}
                  onChange={(e) => setRunCommand(e.target.value)}
                  placeholder="npm start, python main.py..."
                  className="font-mono"
                />
              </div>

              {/* Configuration Container */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Configuration Container</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Répertoire de travail
                    </label>
                    <Input
                      value={workingDirectory}
                      onChange={(e) => setWorkingDirectory(e.target.value)}
                      placeholder="/app"
                      className="font-mono"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      WORKDIR dans le Dockerfile
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Port du container
                    </label>
                    <Input
                      type="number"
                      value={containerPort}
                      onChange={(e) => setContainerPort(parseInt(e.target.value) || 3000)}
                      placeholder="3000"
                      min="1"
                      max="65535"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Port exposé par votre application
                    </p>
                  </div>
                </div>
              </div>

              {/* Generated Dockerfile Preview */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Dockerfile généré pour {activeService.name}</h4>
                <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                  <pre>{dockerfile}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};