"use client";

import React, { useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { SampleScript, SAMPLE_SCRIPTS } from '@/lib/sampleData';

interface UseSampleLoaderReturn {
  loadingSample: string | null;
  loadSampleScript: (sampleId: string) => Promise<void>;
  getAllSamples: () => SampleScript[];
  getSampleById: (id: string) => SampleScript | undefined;
}

export function useSampleLoader(): UseSampleLoaderReturn {
  const [loadingSample, setLoadingSample] = useState<string | null>(null);
  const { user } = useAuth();

  const loadSampleScript = useCallback(async (sampleId: string): Promise<void> => {
    if (!user) {
      throw new Error('User must be authenticated to load sample scripts');
    }

    setLoadingSample(sampleId);

    try {
      const sample = SAMPLE_SCRIPTS.find(s => s.id === sampleId);
      if (!sample) {
        throw new Error(`Sample script with ID ${sampleId} not found`);
      }

      // In a real implementation, this would make an API call to:
      // 1. Create a new script record in the database
      // 2. Store the sample content
      // 3. Store the pre-computed analysis results
      // 4. Return the new script ID for navigation
      
      // For demo purposes, we'll simulate the API call
      await simulateAnalysisCreation(sample, user.uid);
      
      // Store the sample data in localStorage for immediate access
      const existingSamples = JSON.parse(localStorage.getItem(`user_${user.uid}_samples`) || '[]');
      const updatedSamples = [...existingSamples.filter((s: { id: string }) => s.id !== sampleId), sample];
      localStorage.setItem(`user_${user.uid}_samples`, JSON.stringify(updatedSamples));
      
      // Mark this sample as loaded for the user
      const loadedSamples = JSON.parse(localStorage.getItem(`user_${user.uid}_loaded_samples`) || '[]');
      if (!loadedSamples.includes(sampleId)) {
        loadedSamples.push(sampleId);
        localStorage.setItem(`user_${user.uid}_loaded_samples`, JSON.stringify(loadedSamples));
      }

    } catch (error) {
      console.error('Failed to load sample script:', error);
      throw error;
    } finally {
      setLoadingSample(null);
    }
  }, [user]);

  const getAllSamples = useCallback((): SampleScript[] => {
    return SAMPLE_SCRIPTS;
  }, []);

  const getSampleById = useCallback((id: string): SampleScript | undefined => {
    return SAMPLE_SCRIPTS.find(sample => sample.id === id);
  }, []);

  return {
    loadingSample,
    loadSampleScript,
    getAllSamples,
    getSampleById
  };
}

// Simulate API call to create sample script analysis
async function simulateAnalysisCreation(sample: SampleScript, userId: string): Promise<void> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  // In a real implementation, this would:
  // 1. POST to /api/scripts with sample content
  // 2. POST to /api/analysis/{scriptId} with pre-computed results
  // 3. Return the created script ID
  
  console.log(`Sample script "${sample.title}" loaded for user ${userId}`);
}

// Hook to check which samples a user has already loaded
export function useLoadedSamples(): {
  loadedSamples: string[];
  hasSamplesLoaded: boolean;
  markSampleAsLoaded: (sampleId: string) => void;
} {
  const { user } = useAuth();
  const [loadedSamples, setLoadedSamples] = useState<string[]>([]);

  // Load user's previously loaded samples on mount
  React.useEffect(() => {
    if (user) {
      const stored = localStorage.getItem(`user_${user.uid}_loaded_samples`);
      if (stored) {
        setLoadedSamples(JSON.parse(stored));
      }
    }
  }, [user]);

  const markSampleAsLoaded = useCallback((sampleId: string) => {
    if (!user) return;
    
    setLoadedSamples(prev => {
      const updated = [...prev];
      if (!updated.includes(sampleId)) {
        updated.push(sampleId);
        localStorage.setItem(`user_${user.uid}_loaded_samples`, JSON.stringify(updated));
      }
      return updated;
    });
  }, [user]);

  return {
    loadedSamples,
    hasSamplesLoaded: loadedSamples.length > 0,
    markSampleAsLoaded
  };
}

// Get user's onboarding progress
export function useOnboardingProgress(): {
  hasCompletedOnboarding: boolean;
  hasSeenTutorial: boolean;
  markOnboardingComplete: () => void;
  markTutorialComplete: () => void;
  resetOnboarding: () => void;
} {
  const { user } = useAuth();
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
  const [hasSeenTutorial, setHasSeenTutorial] = useState(false);

  // Load onboarding state on mount
  React.useEffect(() => {
    if (user) {
      const onboardingKey = `user_${user.uid}_onboarding`;
      const stored = localStorage.getItem(onboardingKey);
      if (stored) {
        try {
          const state = JSON.parse(stored);
          setHasCompletedOnboarding(state.hasCompletedOnboarding || false);
          setHasSeenTutorial(state.hasSeenTutorial || false);
        } catch {
          // Invalid stored data, reset
          setHasCompletedOnboarding(false);
          setHasSeenTutorial(false);
        }
      }
    }
  }, [user]);

  const markOnboardingComplete = useCallback(() => {
    if (!user) return;
    
    const state = { hasCompletedOnboarding: true, hasSeenTutorial: true };
    localStorage.setItem(`user_${user.uid}_onboarding`, JSON.stringify(state));
    setHasCompletedOnboarding(true);
    setHasSeenTutorial(true);
  }, [user]);

  const markTutorialComplete = useCallback(() => {
    if (!user) return;
    
    const onboardingKey = `user_${user.uid}_onboarding`;
    const existing = localStorage.getItem(onboardingKey);
    const state = existing ? JSON.parse(existing) : {};
    
    const updated = { ...state, hasSeenTutorial: true };
    localStorage.setItem(onboardingKey, JSON.stringify(updated));
    setHasSeenTutorial(true);
  }, [user]);

  const resetOnboarding = useCallback(() => {
    if (!user) return;
    
    const onboardingKey = `user_${user.uid}_onboarding`;
    localStorage.removeItem(onboardingKey);
    setHasCompletedOnboarding(false);
    setHasSeenTutorial(false);
  }, [user]);

  return {
    hasCompletedOnboarding,
    hasSeenTutorial,
    markOnboardingComplete,
    markTutorialComplete,
    resetOnboarding
  };
}