// Sample data for onboarding and demo purposes

export interface SampleScript {
  id: string;
  title: string;
  description: string;
  genre: string;
  riskScore: number;
  status: 'draft' | 'in-review' | 'production-ready';
  scenes: number;
  issues: {
    critical: number;
    warnings: number;
  };
  content: string;
  analysisResults: {
    research: Array<{
      id: string;
      claim: string;
      status: 'verified' | 'flagged' | 'needs_review';
      confidence: number;
      sources: string[];
      explanation: string;
    }>;
    legal: Array<{
      id: string;
      issue: string;
      risk: 'low' | 'medium' | 'high';
      recommendation: string;
      estimatedCost: number;
    }>;
    continuity: Array<{
      id: string;
      character: string;
      issue: string;
      scenes: number[];
      severity: 'minor' | 'moderate' | 'major';
    }>;
    overview: {
      totalClaims: number;
      verifiedClaims: number;
      flaggedClaims: number;
      processingTime: string;
    };
  };
}

export const SAMPLE_SCRIPTS: SampleScript[] = [
  {
    id: 'sample-action-thriller',
    title: 'Urban Strike',
    description: 'A high-octane action thriller about a covert ops team dismantling a terrorist cell in downtown Los Angeles.',
    genre: 'Action/Thriller',
    riskScore: 78,
    status: 'in-review',
    scenes: 87,
    issues: {
      critical: 3,
      warnings: 12
    },
    content: `FADE IN:

INT. ABANDONED WAREHOUSE - NIGHT

The team moves through shadows, tactical gear gleaming under moonlight streaming through broken windows. SARAH CHEN (30s), team leader, signals with precise hand movements.

SARAH
(whispered into comms)
Target building secured. Moving to Phase Two.

A distant explosion RATTLES the building. Car alarms wail in the distance.

MARCUS (40s), demolitions expert, checks his watch - a vintage Rolex Submariner.

MARCUS
Charges set. We have exactly four minutes before LAPD responds.

EXT. DOWNTOWN LOS ANGELES - CONTINUOUS

Sirens pierce the night as police cruisers race down Spring Street past the Walt Disney Concert Hall, their red and blue lights painting the Frank Gehry-designed building in an urgent glow.`,
    analysisResults: {
      research: [
        {
          id: 'research-1',
          claim: 'Police response time to downtown LA is 4 minutes',
          status: 'flagged',
          confidence: 85,
          sources: ['LAPD Response Time Statistics 2023', 'LA Emergency Services Report'],
          explanation: 'Average LAPD response time to downtown LA is 6.2 minutes, not 4 minutes as stated in the script.'
        },
        {
          id: 'research-2', 
          claim: 'Walt Disney Concert Hall designed by Frank Gehry',
          status: 'verified',
          confidence: 100,
          sources: ['Los Angeles Conservancy', 'Walt Disney Concert Hall Official Website'],
          explanation: 'Confirmed - Frank Gehry designed the Walt Disney Concert Hall, completed in 2003.'
        }
      ],
      legal: [
        {
          id: 'legal-1',
          issue: 'Filming permits required for downtown LA locations',
          risk: 'high',
          recommendation: 'Obtain City of Los Angeles filming permits. Coordinate with LAPD for street closures.',
          estimatedCost: 15000
        },
        {
          id: 'legal-2',
          issue: 'Trademark clearance for Rolex brand mention',
          risk: 'medium', 
          recommendation: 'Consider generic luxury watch reference or obtain Rolex product placement agreement.',
          estimatedCost: 5000
        }
      ],
      continuity: [
        {
          id: 'continuity-1',
          character: 'Marcus',
          issue: 'Age inconsistency - described as 40s but dialogue suggests younger',
          scenes: [1, 23, 45],
          severity: 'minor'
        }
      ],
      overview: {
        totalClaims: 15,
        verifiedClaims: 8,
        flaggedClaims: 7,
        processingTime: '2m 34s'
      }
    }
  },
  {
    id: 'sample-period-drama',
    title: 'Letters from Normandy', 
    description: 'A World War II drama following a nurse stationed in Normandy during the D-Day invasion.',
    genre: 'Period Drama',
    riskScore: 45,
    status: 'production-ready',
    scenes: 52,
    issues: {
      critical: 1,
      warnings: 4
    },
    content: `FADE IN:

EXT. NORMANDY BEACH - DAWN, JUNE 6, 1944

Gray waves crash against blood-stained sand. The cacophony of war - artillery, shouting, crying - fills the air.

NURSE ELIZABETH HARTWELL (25) tends to wounded soldiers behind makeshift medical station. Her pristine Red Cross armband now bears mud and worse.

ELIZABETH
(to wounded SOLDIER)
Hold still, this morphine will help with the pain.

She injects a small glass vial of morphine sulfate, the standard Army medical issue.

SOLDIER
(weakly)
Thank you, ma'am. You're like an angel.

In the distance, P-51 Mustang fighters streak across the dawn sky, their distinctive engine roar cutting through the chaos.`,
    analysisResults: {
      research: [
        {
          id: 'research-3',
          claim: 'Morphine sulfate was standard Army medical issue in 1944',
          status: 'verified',
          confidence: 95,
          sources: ['U.S. Army Medical History', 'WWII Medical Corps Documentation'],
          explanation: 'Confirmed - morphine sulfate in glass vials was standard issue for Army medics during WWII.'
        },
        {
          id: 'research-4',
          claim: 'P-51 Mustang fighters were active over Normandy on D-Day',
          status: 'verified', 
          confidence: 100,
          sources: ['D-Day Air Operations', 'U.S. Air Force Historical Division'],
          explanation: 'P-51 Mustangs provided air support during D-Day operations, first sorties began at dawn.'
        }
      ],
      legal: [
        {
          id: 'legal-3',
          issue: 'Red Cross trademark and emblem usage',
          risk: 'medium',
          recommendation: 'Obtain permission from American Red Cross for use of trademark and emblem in commercial production.',
          estimatedCost: 2500
        }
      ],
      continuity: [],
      overview: {
        totalClaims: 8,
        verifiedClaims: 7,
        flaggedClaims: 1,
        processingTime: '1m 47s'
      }
    }
  },
  {
    id: 'sample-sci-fi',
    title: 'Quantum Paradox',
    description: 'A mind-bending sci-fi thriller exploring parallel dimensions and the consequences of quantum mechanics.',
    genre: 'Science Fiction',
    riskScore: 92,
    status: 'draft',
    scenes: 73,
    issues: {
      critical: 8,
      warnings: 23
    },
    content: `FADE IN:

INT. CERN LABORATORY - DAY

DR. MAYA PATEL (35) adjusts the massive particle accelerator controls. Banks of monitors display complex quantum calculations and wave functions.

MAYA
(to her team)
We're about to accelerate protons to 99.9% the speed of light. The Higgs field should become visible at 14 TeV.

COLLEAGUE
What if we create a micro black hole?

MAYA
Hawking radiation would cause it to evaporate instantly. The calculations show it's impossible for it to be stable.

Red warning lights flash as the machine powers up to full capacity.

MAYA (CONT'D)
Initiating collision sequence in T-minus 10 seconds.

The machine HUMS with incredible energy. Suddenly, reality begins to SHIMMER and WARP around them.`,
    analysisResults: {
      research: [
        {
          id: 'research-5',
          claim: 'LHC accelerates protons to 99.9% speed of light',
          status: 'flagged',
          confidence: 90,
          sources: ['CERN Technical Documentation', 'Physics Review Letters'],
          explanation: 'The LHC actually accelerates protons to 99.9999991% the speed of light, not 99.9% as stated.'
        },
        {
          id: 'research-6',
          claim: 'Micro black holes would evaporate via Hawking radiation',
          status: 'verified',
          confidence: 85,
          sources: ['Stephen Hawking Research Papers', 'Theoretical Physics Quarterly'],
          explanation: 'Current theory supports that micro black holes would evaporate almost instantaneously via Hawking radiation.'
        }
      ],
      legal: [
        {
          id: 'legal-4',
          issue: 'CERN facility filming permissions and representation',
          risk: 'high',
          recommendation: 'Coordinate with CERN public relations for facility usage rights and scientific accuracy review.',
          estimatedCost: 25000
        }
      ],
      continuity: [
        {
          id: 'continuity-2',
          character: 'Dr. Maya Patel',
          issue: 'Character expertise level inconsistent with dialogue complexity',
          scenes: [5, 18, 34],
          severity: 'moderate'
        }
      ],
      overview: {
        totalClaims: 23,
        verifiedClaims: 9,
        flaggedClaims: 14,
        processingTime: '4m 12s'
      }
    }
  }
];

export interface TutorialStep {
  id: string;
  title: string;
  description: string;
  target: string;
  position: 'top' | 'bottom' | 'left' | 'right';
  action?: 'click' | 'hover' | 'none';
  nextText?: string;
}

export const TUTORIAL_STEPS: TutorialStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to Greenlit AI!',
    description: 'Your intelligent film production assistant is ready to help you analyze scripts, identify risks, and streamline production workflows. Let\'s explore the key features together.',
    target: 'body',
    position: 'top',
    nextText: 'Start Tour'
  },
  {
    id: 'dashboard-stats',
    title: 'Production Overview',
    description: 'Monitor your script analysis statistics at a glance. See total scripts analyzed, claims verified, and flagged issues that need attention.',
    target: '.stats-grid',
    position: 'bottom',
    action: 'none'
  },
  {
    id: 'sample-scripts',
    title: 'Try Sample Scripts',
    description: 'Get started immediately with our curated demo scripts. Each represents different genres and complexity levels to showcase our AI capabilities.',
    target: '.sample-scripts',
    position: 'top',
    action: 'none'
  },
  {
    id: 'sample-script-card',
    title: 'Script Analysis Preview',
    description: 'Each sample script shows risk scores, issue counts, and genre information. Click "Analyze Sample" to see full AI analysis results.',
    target: '.sample-scripts .claim-card:first-child',
    position: 'right',
    action: 'hover'
  },
  {
    id: 'analyze-button',
    title: 'Analyze Your Scripts',
    description: 'Upload your own screenplay to get comprehensive analysis from our multi-agent AI system including research verification, legal clearance, and continuity checking.',
    target: '.analyze-button',
    position: 'left',
    action: 'hover'
  },
  {
    id: 'script-card',
    title: 'Analysis Results',
    description: 'Once analyzed, scripts appear here with risk scores, scene counts, and critical issues. Click "View Report" to see detailed findings.',
    target: '.script-card:first-child',
    position: 'right',
    action: 'hover'
  },
  {
    id: 'report-features',
    title: 'Detailed Analysis Reports',
    description: 'Reports include findings from Research, Legal, Continuity, and Director agents, plus scene-by-scene breakdowns and character analysis.',
    target: 'body',
    position: 'top'
  },
  {
    id: 'collaboration',
    title: 'Team Collaboration',
    description: 'Add comments, resolve issues, and collaborate with your production team in real-time. Track review status and get notifications.',
    target: 'body',
    position: 'top'
  },
  {
    id: 'finish',
    title: 'You\'re All Set!',
    description: 'Start by trying a sample script to see our AI in action, or upload your own screenplay for comprehensive production analysis. Need help? Check our tutorials anytime.',
    target: 'body',
    position: 'top',
    nextText: 'Get Started'
  }
];

// User preferences for onboarding
export interface OnboardingState {
  hasCompletedOnboarding: boolean;
  hasSeenTutorial: boolean;
  currentStep: number;
  skippedSteps: string[];
  lastVisit: Date;
}

export const getInitialOnboardingState = (): OnboardingState => ({
  hasCompletedOnboarding: false,
  hasSeenTutorial: false,
  currentStep: 0,
  skippedSteps: [],
  lastVisit: new Date()
});

export const isNewUser = (user: any): boolean => {
  if (!user) return false;
  
  const onboardingData = localStorage.getItem(`onboarding_${user.uid}`);
  if (!onboardingData) return true;
  
  try {
    const state: OnboardingState = JSON.parse(onboardingData);
    return !state.hasCompletedOnboarding;
  } catch {
    return true;
  }
};

export const getOnboardingState = (user: any): OnboardingState => {
  if (!user) return getInitialOnboardingState();
  
  const onboardingData = localStorage.getItem(`onboarding_${user.uid}`);
  if (!onboardingData) return getInitialOnboardingState();
  
  try {
    return JSON.parse(onboardingData);
  } catch {
    return getInitialOnboardingState();
  }
};

export const saveOnboardingState = (user: any, state: OnboardingState): void => {
  if (!user) return;
  
  localStorage.setItem(`onboarding_${user.uid}`, JSON.stringify({
    ...state,
    lastVisit: new Date()
  }));
};