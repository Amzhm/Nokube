/**
 * Wizard de déploiement - Interface 2 étapes
 */

'use client';

import { useState } from 'react';
import { ArchitectureStep } from './steps/ArchitectureStep';
import { BuildStep } from './steps/BuildStep';
import { Button } from '@/shared/ui/Button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { ProjectArchitecture, BuildConfig } from '@/shared/types/deployment.types';

type WizardStep = 'architecture' | 'build' | 'review';

export const DeploymentWizard = () => {
  const [currentStep, setCurrentStep] = useState<WizardStep>('architecture');
  const [architecture, setArchitecture] = useState<ProjectArchitecture | null>(null);
  const [buildConfig, setBuildConfig] = useState<BuildConfig | null>(null);

  const steps = [
    { id: 'architecture', label: 'Architecture', description: 'Services et infrastructure' },
    { id: 'build', label: 'Build', description: 'Code et configuration' },
    { id: 'review', label: 'Révision', description: 'Validation finale' },
  ];

  const currentStepIndex = steps.findIndex(step => step.id === currentStep);

  const handleNext = () => {
    if (currentStep === 'architecture' && architecture) {
      setCurrentStep('build');
    } else if (currentStep === 'build' && buildConfig) {
      setCurrentStep('review');
    }
  };

  const handlePrevious = () => {
    if (currentStep === 'build') {
      setCurrentStep('architecture');
    } else if (currentStep === 'review') {
      setCurrentStep('build');
    }
  };

  const canProceed = () => {
    if (currentStep === 'architecture') return !!architecture;
    if (currentStep === 'build') return !!buildConfig;
    return true;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Steps Navigation */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`
                flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium
                ${index <= currentStepIndex 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-600'
                }
              `}>
                {index + 1}
              </div>
              <div className="ml-3">
                <p className={`text-sm font-medium ${
                  index <= currentStepIndex ? 'text-blue-600' : 'text-gray-500'
                }`}>
                  {step.label}
                </p>
                <p className="text-xs text-gray-500">{step.description}</p>
              </div>
              {index < steps.length - 1 && (
                <ChevronRight className="w-5 h-5 text-gray-400 mx-4" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="p-6">
        {currentStep === 'architecture' && (
          <ArchitectureStep
            value={architecture}
            onChange={setArchitecture}
          />
        )}

        {currentStep === 'build' && (
          <BuildStep
            value={buildConfig}
            onChange={setBuildConfig}
            architecture={architecture}
          />
        )}

        {currentStep === 'review' && (
          <div className="text-center py-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Révision finale
            </h3>
            <p className="text-gray-600">
              Cette étape sera implémentée prochainement
            </p>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="border-t border-gray-200 px-6 py-4 flex justify-between">
        <Button
          variant="outline"
          onClick={handlePrevious}
          disabled={currentStep === 'architecture'}
          className="flex items-center gap-2"
        >
          <ChevronLeft className="w-4 h-4" />
          Précédent
        </Button>

        <div className="flex gap-3">
          {currentStep === 'review' ? (
            <Button className="flex items-center gap-2">
              Déployer
            </Button>
          ) : (
            <Button
              onClick={handleNext}
              disabled={!canProceed()}
              className="flex items-center gap-2"
            >
              Suivant
              <ChevronRight className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};