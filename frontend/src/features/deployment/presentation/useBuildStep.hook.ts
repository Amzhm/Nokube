/**
 * Hook pour l'étape Build - Gestion des états et logique
 */

'use client';

import { useState, useEffect } from 'react';
import type { BuildConfig, ProjectArchitecture } from '@/shared/types/deployment.types';

interface UseBuildStepProps {
  value: BuildConfig | null;
  onChange: (buildConfig: BuildConfig) => void;
  architecture: ProjectArchitecture | null;
}

const languageTemplates = {
  javascript: {
    framework: 'Node.js',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm start',
    dependencies: ['express', 'cors'],
    baseImage: 'node:18-alpine',
  },
  typescript: {
    framework: 'Node.js + TypeScript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm start',
    dependencies: ['express', '@types/node', 'typescript'],
    baseImage: 'node:18-alpine',
  },
  python: {
    framework: 'Python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python main.py',
    dependencies: ['fastapi', 'uvicorn'],
    baseImage: 'python:3.11-slim',
  },
  react: {
    framework: 'React',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm start',
    dependencies: ['react', 'react-dom'],
    baseImage: 'node:18-alpine',
  },
};

export const useBuildStep = ({ value, onChange, architecture }: UseBuildStepProps) => {
  const [language, setLanguage] = useState(value?.language || 'javascript');
  const [framework, setFramework] = useState(value?.framework || '');
  const [buildCommands, setBuildCommands] = useState<string[]>(value?.buildCommands || []);
  const [runCommand, setRunCommand] = useState(value?.runCommand || '');
  const [dependencies, setDependencies] = useState<string[]>(value?.dependencies || []);
  const [environmentVars, setEnvironmentVars] = useState(value?.environmentVars || []);

  const applyTemplate = () => {
    const template = languageTemplates[language as keyof typeof languageTemplates];
    if (template) {
      setFramework(template.framework);
      setBuildCommands(template.buildCommands);
      setRunCommand(template.runCommand);
      setDependencies(template.dependencies);
    }
  };

  const addBuildCommand = () => {
    setBuildCommands([...buildCommands, '']);
  };

  const updateBuildCommand = (index: number, command: string) => {
    const updated = buildCommands.map((cmd, i) => i === index ? command : cmd);
    setBuildCommands(updated);
  };

  const removeBuildCommand = (index: number) => {
    setBuildCommands(buildCommands.filter((_, i) => i !== index));
  };

  const addDependency = () => {
    setDependencies([...dependencies, '']);
  };

  const updateDependency = (index: number, dependency: string) => {
    const updated = dependencies.map((dep, i) => i === index ? dependency : dep);
    setDependencies(updated);
  };

  const removeDependency = (index: number) => {
    setDependencies(dependencies.filter((_, i) => i !== index));
  };

  const addEnvironmentVar = () => {
    setEnvironmentVars([...environmentVars, { key: '', value: '', secret: false }]);
  };

  const updateEnvironmentVar = (index: number, updates: Partial<{ key: string; value: string; secret: boolean }>) => {
    const updated = environmentVars.map((env, i) => 
      i === index ? { ...env, ...updates } : env
    );
    setEnvironmentVars(updated);
  };

  const removeEnvironmentVar = (index: number) => {
    setEnvironmentVars(environmentVars.filter((_, i) => i !== index));
  };

  const generateDockerfile = () => {
    const template = languageTemplates[language as keyof typeof languageTemplates];
    if (!template) return '';

    let dockerfile = `FROM ${template.baseImage}\n\n`;
    dockerfile += `WORKDIR /app\n\n`;
    
    if (language === 'javascript' || language === 'typescript' || language === 'react') {
      dockerfile += `COPY package*.json ./\n`;
      dockerfile += `RUN npm ci --only=production\n\n`;
      dockerfile += `COPY . .\n\n`;
      if (buildCommands.includes('npm run build')) {
        dockerfile += `RUN npm run build\n\n`;
      }
    } else if (language === 'python') {
      dockerfile += `COPY requirements.txt ./\n`;
      dockerfile += `RUN pip install --no-cache-dir -r requirements.txt\n\n`;
      dockerfile += `COPY . .\n\n`;
    }

    dockerfile += `EXPOSE 3000\n\n`;
    dockerfile += `CMD ["${runCommand.split(' ')[0]}", "${runCommand.split(' ').slice(1).join('", "')}"]`;
    
    return dockerfile;
  };

  const updateBuildConfig = () => {
    const buildConfig: BuildConfig = {
      language,
      framework,
      buildCommands: buildCommands.filter(cmd => cmd.trim()),
      runCommand,
      dependencies: dependencies.filter(dep => dep.trim()),
      environmentVars,
    };
    onChange(buildConfig);
  };

  const isValid = () => {
    return language && runCommand && buildCommands.some(cmd => cmd.trim());
  };

  // Auto-apply template when language changes
  useEffect(() => {
    if (!value) {
      applyTemplate();
    }
  }, [language]);

  // Update build config when values change
  useEffect(() => {
    if (isValid()) {
      updateBuildConfig();
    }
  }, [language, framework, buildCommands, runCommand, dependencies, environmentVars]);

  return {
    language,
    framework,
    buildCommands,
    runCommand,
    dependencies,
    environmentVars,
    dockerfile: generateDockerfile(),
    availableLanguages: Object.keys(languageTemplates),
    isValid: isValid(),
    setLanguage,
    setFramework,
    setRunCommand,
    applyTemplate,
    addBuildCommand,
    updateBuildCommand,
    removeBuildCommand,
    addDependency,
    updateDependency,
    removeDependency,
    addEnvironmentVar,
    updateEnvironmentVar,
    removeEnvironmentVar,
  };
};