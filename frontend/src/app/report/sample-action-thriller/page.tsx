"use client";

import { useEffect, useState } from 'react';
import { SAMPLE_SCRIPTS } from '@/lib/sampleData';
import Link from 'next/link';
import ClaimCard from '@/components/ClaimCard';

export default function SampleActionThrillerReport() {
  const [sampleData, setSampleData] = useState(null);

  useEffect(() => {
    const sample = SAMPLE_SCRIPTS.find(s => s.id === 'sample-action-thriller');
    setSampleData(sample);
  }, []);

  if (!sampleData) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center">Loading sample report...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="mb-8">
        <Link 
          href="/dashboard" 
          className="text-sm text-blue-600 hover:text-blue-800 mb-4 inline-block"
        >
          ← Back to Dashboard
        </Link>
        
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">{sampleData.title}</h1>
            <p className="text-gray-600 mb-4">{sampleData.description}</p>
            
            <div className="flex items-center gap-4 text-sm">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                {sampleData.genre}
              </span>
              <span className="text-gray-500">{sampleData.scenes} scenes</span>
              <span className={`px-3 py-1 rounded-full text-white ${
                sampleData.status === 'production-ready' ? 'bg-green-500' :
                sampleData.status === 'in-review' ? 'bg-yellow-500' : 'bg-gray-500'
              }`}>
                {sampleData.status.replace('-', ' ')}
              </span>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-orange-500 mb-1">
              {sampleData.riskScore}
            </div>
            <div className="text-sm text-gray-500">Risk Score</div>
          </div>
        </div>
      </div>

      {/* Analysis Results Tabs */}
      <div className="bg-white rounded-lg shadow-sm border mb-8">
        <div className="border-b">
          <div className="flex">
            <button className="px-6 py-3 border-b-2 border-blue-500 text-blue-600 font-medium">
              Overview
            </button>
            <button className="px-6 py-3 text-gray-500 hover:text-gray-700">
              Research ({sampleData.analysisResults.research.length})
            </button>
            <button className="px-6 py-3 text-gray-500 hover:text-gray-700">
              Legal ({sampleData.analysisResults.legal.length})
            </button>
            <button className="px-6 py-3 text-gray-500 hover:text-gray-700">
              Continuity ({sampleData.analysisResults.continuity.length})
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Overview Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-800">
                {sampleData.analysisResults.overview.totalClaims}
              </div>
              <div className="text-sm text-gray-600">Total Claims</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {sampleData.analysisResults.overview.verifiedClaims}
              </div>
              <div className="text-sm text-gray-600">Verified</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {sampleData.analysisResults.overview.flaggedClaims}
              </div>
              <div className="text-sm text-gray-600">Flagged</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {sampleData.analysisResults.overview.processingTime}
              </div>
              <div className="text-sm text-gray-600">Processing Time</div>
            </div>
          </div>

          {/* Sample Claims */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">Key Findings</h3>
            
            {sampleData.analysisResults.research.slice(0, 2).map((claim) => (
              <ClaimCard 
                key={claim.id}
                claim={claim.claim}
                status={claim.status}
                confidence={claim.confidence}
                explanation={claim.explanation}
                sources={claim.sources}
              />
            ))}

            {sampleData.analysisResults.legal.slice(0, 1).map((issue) => (
              <div key={issue.id} className="border rounded-lg p-4 bg-yellow-50 border-yellow-200">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium text-yellow-800">Legal Notice</h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    issue.risk === 'high' ? 'bg-red-100 text-red-800' :
                    issue.risk === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {issue.risk} risk
                  </span>
                </div>
                <p className="text-sm text-yellow-700 mb-2">{issue.issue}</p>
                <p className="text-sm text-yellow-600 mb-2">{issue.recommendation}</p>
                <p className="text-sm font-medium">Estimated cost: ${issue.estimatedCost.toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sample Badge */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
        <div className="text-blue-800 mb-2">
          🎬 <strong>This is a sample analysis</strong>
        </div>
        <p className="text-sm text-blue-600 mb-3">
          This demo shows what a real analysis report looks like. Upload your own script to get started!
        </p>
        <Link 
          href="/analyze"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Analyze Your Own Script
        </Link>
      </div>
    </div>
  );
}
