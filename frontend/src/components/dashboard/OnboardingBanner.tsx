"use client";

import React from 'react';
import { useOnboardingProgress } from '@/hooks/useSampleLoader';

interface OnboardingBannerProps {
  onStartTour: () => void;
}

export default function OnboardingBanner({ onStartTour }: OnboardingBannerProps) {
  const { hasCompletedOnboarding, markOnboardingComplete } = useOnboardingProgress();

  if (hasCompletedOnboarding) {
    return null;
  }

  const handleDismiss = () => {
    markOnboardingComplete();
  };

  return (
    <div className="mb-8 p-6 rounded-lg border-2 border-dashed border-blue-200 bg-blue-50">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="text-3xl mb-3">🎬</div>
          <h2 className="text-xl font-bold text-blue-900 mb-2">
            Welcome to Greenlit AI!
          </h2>
          <p className="text-blue-800 mb-4 max-w-2xl">
            Your intelligent film production assistant is ready to help.
          </p>
          
          <div className="flex flex-wrap gap-3">
            <button
              onClick={onStartTour}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Take Guided Tour
            </button>
            <button
              onClick={handleDismiss}
              className="px-4 py-2 bg-white text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors font-medium"
            >
              Skip for Now
            </button>
          </div>
        </div>
        
        <button
          onClick={handleDismiss}
          className="ml-4 p-2 text-blue-400 hover:text-blue-600 transition-colors"
        >
          ×
        </button>
      </div>
    </div>
  );
}
