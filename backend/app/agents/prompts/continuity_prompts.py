"""
Specialized prompts for Continuity Agent
Focuses on script consistency and production continuity
"""

CONTINUITY_SYSTEM_PROMPT = """You are the Continuity Agent for Greenlit AI, specializing in script continuity and consistency analysis for film and TV production.

Your expertise includes:
- Character consistency (age, appearance, background, relationships)
- Timeline and chronological accuracy
- Location and geographic continuity
- Props, costumes, and physical elements tracking
- Scene transition logic
- Production continuity requirements

Your role is to identify inconsistencies that could:
- Cause continuity errors during filming
- Create plot holes or logical problems
- Require additional script revisions
- Impact production scheduling or budgets
- Confuse audiences or break story immersion

Focus on practical production concerns. Flag issues that script supervisors and continuity coordinators need to track during filming.

Consider both obvious inconsistencies and subtle continuity challenges that experienced production teams would catch.
"""

CHARACTER_TRACKING_PROMPT = """Analyze this script for character consistency and continuity issues:

SCRIPT:
{script_text}

CONTEXT: {context_info}

Track character details and identify inconsistencies in this format:

CHARACTER_ISSUE: [Description of the inconsistency]
CHARACTER: [Character name affected]
SEVERITY: [low|medium|high]
LOCATION: [Where in script this occurs]
IMPACT: [How this affects production]
SUGGESTION: [Recommended fix]

Focus on:
- Age inconsistencies (character ages changing impossibly)
- Appearance changes (eye color, height, physical traits)
- Background contradictions (hometown, family, job history)
- Relationship inconsistencies (who knows whom, relationship status)
- Character knowledge (what they should/shouldn't know at different times)
- Speech patterns and personality shifts
- Skills and abilities that appear/disappear
- Physical limitations or disabilities mentioned inconsistently

Track each major character across all their appearances and note any contradictions.
"""

TIMELINE_ANALYSIS_PROMPT = """Analyze this script for timeline and chronological consistency:

SCRIPT:
{script_text}

CONTEXT: {context_info}

Identify timeline issues in this format:

TIMELINE_ISSUE: [Description of chronological problem]
TIME_CONFLICT: [Specific dates/times that conflict]
SEVERITY: [low|medium|high]
SCENES_AFFECTED: [Which scenes have the conflict]
IMPACT: [How this affects story logic]
SUGGESTION: [Recommended timeline fix]

Check for:
- Date contradictions (events happening on conflicting dates)
- Impossible time spans (aging, travel, events occurring too quickly/slowly)
- Seasonal inconsistencies (weather, holidays, school year)
- Historical accuracy (events matching real historical timeline)
- Day/night continuity between scenes
- Flashback/flashforward clarity and consistency
- Character age progression matching timeline
- Technology anachronisms (devices appearing before invention)
- Cultural references out of time period

Pay special attention to any specific dates, years, or time periods mentioned.
"""

LOCATION_CONTINUITY_PROMPT = """Analyze location and geographic continuity in this script:

SCRIPT:
{script_text}

CONTEXT: {context_info}

Identify location issues in this format:

LOCATION_ISSUE: [Description of geographic problem]
LOCATIONS: [Specific locations involved]
SEVERITY: [low|medium|high]
TRAVEL_TIME: [Realistic travel time between locations]
IMPACT: [How this affects production logistics]
SUGGESTION: [Recommended location or schedule fix]

Check for:
- Impossible travel times between locations
- Geographic impossibilities (wrong climate, terrain, landmarks)
- International travel without proper time for visas/customs
- Location descriptions that don't match real places
- Seasonal/weather inconsistencies for geographic regions
- Time zone issues affecting character interactions
- Cultural inaccuracies for specific locations
- Language barriers not addressed
- Location accessibility for filming

Consider both story logic and practical production requirements.
"""

PROP_TRACKING_PROMPT = """Analyze props, costumes, and physical elements for continuity:

SCRIPT:
{script_text}

CONTEXT: {context_info}

Track continuity elements in this format:

PROP_ISSUE: [Description of continuity problem]
ITEM: [Specific prop, costume, or physical element]
SCENES: [Where item appears/disappears]
SEVERITY: [low|medium|high]
CONTINUITY_IMPACT: [How this affects filming]
TRACKING_NOTE: [What script supervisor should watch]

Track:
- Props that appear/disappear without explanation
- Costume changes between scenes in same time period
- Vehicles and their condition/appearance
- Weapons and their specifications
- Technology and its capabilities
- Injuries and their healing progression
- Makeup and hair changes
- Weather effects on appearance
- Food and drink continuity in scenes
- Documents and their contents

Focus on elements that will be visible on camera and require careful tracking during production.
"""

SCENE_TRANSITION_PROMPT = """Analyze scene transitions and flow for continuity:

SCRIPT:
{script_text}

Evaluate transitions between scenes for:

TRANSITION_ISSUE: [Problem with scene flow]
FROM_SCENE: [Scene number/description]
TO_SCENE: [Scene number/description] 
PROBLEM: [Specific continuity issue]
SEVERITY: [low|medium|high]
PRODUCTION_NOTE: [What crew needs to consider]

Check:
- Character positions and states between scenes
- Time of day consistency
- Weather continuity
- Emotional state progression
- Knowledge continuity (what characters learn/forget)
- Physical state (injuries, fatigue, intoxication)
- Costume/makeup consistency
- Set dressing and prop placement
- Background character continuity

Identify transitions that might confuse audiences or create filming challenges.
"""