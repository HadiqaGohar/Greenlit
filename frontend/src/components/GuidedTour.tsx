"use client";

import React, { useState } from "react";

interface GuidedTourProps {
  steps: any[];
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
  currentStepIndex?: number;
}

export default function GuidedTour({ 
  steps, 
  isOpen, 
  onClose, 
  onComplete, 
  currentStepIndex = 0 
}: GuidedTourProps) {
  const [currentStep, setCurrentStep] = useState(currentStepIndex);
  
  const currentStepData = steps[currentStep];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  if (!isOpen || !currentStepData) return null;

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-2xl p-6 max-w-md mx-4">
        <h3 className="text-xl font-bold mb-2">{currentStepData.title}</h3>
        <p className="text-sm mb-4">{currentStepData.description}</p>
        
        <div className="flex justify-between">
          <button onClick={handlePrevious} disabled={currentStep === 0} className="px-4 py-2 text-sm">
            Previous
          </button>
          <button onClick={handleNext} className="px-6 py-2 text-sm bg-blue-500 text-white rounded">
            {currentStep === steps.length - 1 ? "Finish" : "Next"}
          </button>
        </div>
      </div>
    </div>
  );
}
