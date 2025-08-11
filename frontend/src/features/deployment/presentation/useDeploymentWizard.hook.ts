/**
 * Hook pour le wizard de déploiement - Gestion des états et logique
 */

'use client';

import { useState } from 'react';
import type { ProjectArchitecture, ServiceBuildConfig } from '@/shared/types/deployment.types';

type WizardStep = 'architecture' | 'build' | 'source' | 'review';

export const useDeploymentWizard = () => {
  const [currentStep, setCurrentStep] = useState<WizardStep>('architecture');
  const [architecture, setArchitecture] = useState<ProjectArchitecture | null>(null);
  const [serviceBuildConfigs, setServiceBuildConfigs] = useState<ServiceBuildConfig[]>([]);

  const steps = [
    { id: 'architecture', label: 'Architecture', description: 'Services et infrastructure' },
    { id: 'build', label: 'Build', description: 'Langages et frameworks' },
    { id: 'source', label: 'Code Source', description: 'Git repository et clés' },
    { id: 'review', label: 'Révision', description: 'Validation finale' },
  ];

  const currentStepIndex = steps.findIndex(step => step.id === currentStep);

  const handleNext = () => {
    if (currentStep === 'architecture' && architecture) {
      setCurrentStep('build');
    } else if (currentStep === 'build' && canProceedFromBuild()) {
      setCurrentStep('source');
    } else if (currentStep === 'source' && canProceedFromSource()) {
      setCurrentStep('review');
    }
  };

  const handlePrevious = () => {
    if (currentStep === 'build') {
      setCurrentStep('architecture');
    } else if (currentStep === 'source') {
      setCurrentStep('build');
    } else if (currentStep === 'review') {
      setCurrentStep('source');
    }
  };

  const canProceedFromBuild = () => {
    const buildableServices = architecture?.services.filter(s => s.type !== 'database') || [];
    return serviceBuildConfigs.length === buildableServices.length;
  };

  const canProceedFromSource = () => {
    // Vérifier que tous les services buildable ont une source config
    const buildableServices = architecture?.services.filter(s => s.type !== 'database') || [];
    return serviceBuildConfigs.every(config => 
      config.sourceConfig && 
      (config.sourceConfig.type === 'upload' || 
       (config.sourceConfig.type === 'git' && 
        config.sourceConfig.gitRepository?.url &&
        config.sourceConfig.gitRepository?.deployKey?.isConfigured))
    );
  };

  const canProceed = () => {
    if (currentStep === 'architecture') return !!architecture;
    if (currentStep === 'build') return canProceedFromBuild();
    if (currentStep === 'source') return canProceedFromSource();
    return true;
  };

  const isFirstStep = currentStep === 'architecture';
  const isLastStep = currentStep === 'review';

  return {
    // State
    currentStep,
    architecture,
    serviceBuildConfigs,
    steps,
    currentStepIndex,
    
    // Computed
    canProceed: canProceed(),
    isFirstStep,
    isLastStep,
    
    // Actions
    setArchitecture,
    setServiceBuildConfigs,
    handleNext,
    handlePrevious,
  };
};