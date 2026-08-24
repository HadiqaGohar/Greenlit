"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useSampleLoader, useLoadedSamples } from '@/hooks/useSampleLoader';
import { SAMPLE_SCRIPTS } from '@/lib/sampleData';

export default function SampleScriptsPanel() {
  const { loadingSample, loadSampleScript } = useSampleLoader();
  const { loadedSamples } = useLoadedSamples();
  const [loadError, setLoadError] = useState<string | null>(null);

  const handleLoadSample = async (sampleId: string) => {
    try {
      setLoadError(null);
      await loadSampleScript(sampleId);
    } catch (error) {
      console.error('Failed to load sample:', error);
      setLoadError('Failed to load sample script. Please try again.');
    }
  };

  const getRiskLevelColor = (riskScore: number) => {
    if (riskScore >= 85) return 'rgb(239, 68, 68)';
    if (riskScore >= 60) return 'rgb(249, 115, 22)';
    if (riskScore >= 30) return 'rgb(245, 158, 11)';
    return 'rgb(34, 197, 94)';
  };

  return (
    <div className="sample-scripts">
      <h3 className="text-xl font-semibold mb-4">Try Sample Scripts</h3>
      
      {loadError && (
        <div className="mb-4 p-3 rounded bg-red-50 text-red-700 text-sm">
          {loadError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {SAMPLE_SCRIPTS.map((sample) => {
          const isLoading = loadingSample === sample.id;
          const isLoaded = loadedSamples.includes(sample.id);
          
          return (
            <div key={sample.id} className="claim-card rounded-lg p-4 border">
              <h4 className="font-semibold mb-2">{sample.title}</h4>
              <p className="text-sm text-gray-600 mb-3">{sample.description}</p>
              
              <div className="mb-3">
                <div className="flex justify-between text-sm mb-1">
                  <span>Risk Score</span>
                  <span style={{ color: getRiskLevelColor(sample.riskScore) }}>
                    {sample.riskScore}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="h-2 rounded-full"
                    style={{ 
                      backgroundColor: getRiskLevelColor(sample.riskScore),
                      width: `${sample.riskScore}%` 
                    }}
                  />
                </div>
              </div>

              <div className="text-xs text-gray-500 mb-4">
                {sample.issues.critical} critical • {sample.issues.warnings} warnings
              </div>

              {isLoaded ? (
                <Link 
                  href={`/report/${sample.id}`}
                  className="block w-full py-2 text-center bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  View Report
                </Link>
              ) : (
                <button
                  onClick={() => handleLoadSample(sample.id)}
                  disabled={isLoading}
                  className="w-full py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  {isLoading ? 'Loading...' : 'Analyze Sample'}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
