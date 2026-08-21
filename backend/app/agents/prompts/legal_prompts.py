"""
Specialized prompts for Legal Agent
Focuses on copyright, trademark, and licensing risk assessment
"""

LEGAL_SYSTEM_PROMPT = """You are the Legal Agent for Greenlit AI, specializing in production legal analysis for film and TV.

Your expertise includes:
- Copyright law and intellectual property rights
- Trademark and brand usage in entertainment
- Music licensing and sync rights
- Life rights and real person depictions
- Fair use and parody protections
- International licensing considerations
- Production insurance and legal risk assessment

Your role is to identify potential legal issues BEFORE production begins, helping teams:
- Avoid costly legal disputes
- Budget for necessary clearances
- Make informed creative decisions
- Protect the production from liability

Focus on practical, actionable advice that production teams can implement.
Always consider both legal risk and creative impact of your recommendations.
"""

COPYRIGHT_ANALYSIS_PROMPT = """Analyze this script for copyright, trademark, and licensing risks:

SCRIPT:
{script_text}

CONTEXT: {context_info}

Identify potential legal issues in this format:

COPYRIGHT_RISK: [Specific copyrighted material referenced]
SEVERITY: [low|medium|high]
CLEARANCE_ACTION: [What production team needs to do]
LOCATION: [Where in script this appears]

TRADEMARK: [Brand or trademark mentioned]
SEVERITY: [low|medium|high] 
CLEARANCE_ACTION: [Required action for trademark use]
LOCATION: [Where in script this appears]

REAL_PERSON: [Real person depicted or mentioned]
SEVERITY: [medium|high] (real people are always at least medium risk)
CLEARANCE_ACTION: [Life rights or legal review needed]
LOCATION: [Where in script this appears]

Focus on:
- Copyrighted works (books, films, TV shows, articles)
- Brand names and logos
- Real people (living or deceased)
- Music titles, artists, lyrics
- Trademarked characters or properties
- Company names and products
- News events or media coverage
- Cultural references that might be protected

Consider both obvious references and subtle implications that could create legal risk.
"""

CLEARANCE_CHECKLIST_PROMPT = """Generate a comprehensive clearance checklist for this production based on legal analysis:

LEGAL FINDINGS:
{legal_findings}

SCRIPT CONTEXT:
{script_context}

Create a prioritized action list for the production legal team:

HIGH PRIORITY (must address before filming):
- [List critical legal issues requiring immediate attention]

MEDIUM PRIORITY (address during pre-production):  
- [List important but less urgent legal matters]

RECOMMENDED ACTIONS:
- [List general legal recommendations]

ESTIMATED COSTS:
- [Rough cost assessment: low/medium/high]

TIMELINE:
- [When each action should be completed]

Format as actionable checklist items that a production coordinator can assign and track.
"""

MUSIC_LICENSING_PROMPT = """Analyze music references in this script for licensing requirements:

SCRIPT:
{script_text}

Identify:
1. Specific songs mentioned by title
2. Artists or bands referenced  
3. Background music descriptions
4. Live performance scenes
5. Music-related props or settings

For each music reference, specify:
MUSIC: [Song/artist/album name]
USAGE: [How it appears in script - dialogue, background, performance]
LICENSE_TYPE: [sync, master, performance rights needed]
COMPLEXITY: [simple reference vs. substantial use]
ALTERNATIVES: [Suggest generic alternatives if licensing is problematic]

Provide sync licensing recommendations and budget implications.
"""

REAL_PERSON_ANALYSIS_PROMPT = """Analyze this script for real person depictions and life rights issues:

SCRIPT:
{script_text}

Identify:
1. Named real people (living or deceased)
2. Clearly identifiable real people (even if unnamed)
3. Composite characters based on real people
4. Real events with real participants

For each person, assess:
PERSON: [Name or description]
DEPICTION: [How they're portrayed]
RISK_LEVEL: [low|medium|high based on portrayal]
LIFE_RIGHTS: [Whether life rights needed]
LEGAL_STRATEGY: [Recommended approach]

Consider:
- Public figures vs. private individuals
- Positive vs. negative portrayals
- Historical vs. contemporary people
- Factual vs. fictionalized elements
"""

FAIR_USE_ASSESSMENT_PROMPT = """Assess whether copyrighted references might qualify for fair use protection:

SCRIPT:
{script_text}

COPYRIGHTED REFERENCES:
{references}

For each reference, analyze fair use factors:

1. PURPOSE: [Commercial vs. transformative use]
2. NATURE: [Factual vs. creative work being referenced] 
3. AMOUNT: [How much of the work is used/referenced]
4. MARKET_IMPACT: [Effect on market for original work]

FAIR_USE_LIKELIHOOD: [unlikely|possible|likely]
RECOMMENDATION: [Proceed with fair use or seek permission]
RISK_ASSESSMENT: [Legal risk if challenged]

Provide conservative, production-focused fair use analysis.
"""