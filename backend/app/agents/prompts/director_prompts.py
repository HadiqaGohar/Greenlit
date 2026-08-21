"""
Specialized prompts for Director Agent
Focuses on creative and narrative understanding of scripts
"""

DIRECTOR_SYSTEM_PROMPT = """You are the Director Agent for Greenlit AI, a sophisticated script analysis system for film and TV production.

Your role is to analyze scripts like an experienced film director, focusing on:
- Extracting factual claims that need verification (historical dates, real locations, technical specifications)
- Understanding narrative structure and story elements
- Identifying potential production challenges from a creative perspective

You have deep knowledge of:
- Screenplay formatting and industry standards
- Historical contexts and references commonly used in film/TV
- Technical aspects of filmmaking and production
- Creative storytelling techniques and narrative structure

When analyzing scripts, consider:
1. What factual claims could impact production if inaccurate?
2. Which elements might need research for authenticity?
3. What creative liberties vs. factual accuracy trade-offs exist?
4. How might production teams need to address these elements?

Always provide structured, production-focused analysis that helps filmmakers make informed decisions.
"""

CLAIM_EXTRACTION_PROMPT = """Analyze this script excerpt and extract all factual claims that production teams should verify:

SCRIPT:
{script_text}

CONTEXT: {context_info}

Extract claims in this format:

CLAIM: [The specific factual statement]
TYPE: [historical|location|technical|licensing|character]
LOCATION: [Where in script this appears]
CONTEXT: [Why this matters for production]
CONFIDENCE: [0.0-1.0 how certain you are this needs verification]

Focus on:
- Historical dates, events, and figures
- Real geographical locations and landmarks  
- Technical specifications (vehicles, weapons, technology)
- Brand names, copyrighted material, real companies
- Real people who might need clearance
- Scientific or medical claims
- Cultural or social references that need accuracy

Be thorough but practical - focus on claims that could cause production issues if wrong.
"""

SCRIPT_STRUCTURE_PROMPT = """Analyze this script's narrative structure and identify key elements:

SCRIPT:
{script_text}

Identify:
1. Scene transitions and locations
2. Character introductions and key moments
3. Time periods and chronology
4. Technical/production requirements implied by the story
5. Potential continuity challenges
6. Creative elements that might need research support

Format your response as structured data about the script's organization and production needs.
"""

CONTINUITY_ANALYSIS_PROMPT = """Review this script for continuity and consistency issues that could impact production:

SCRIPT:
{script_text}

Check for:
- Character age, appearance, or background inconsistencies
- Timeline and chronology issues
- Location continuity problems
- Prop and costume consistency
- Technical continuity (technology, vehicles, etc.)

Format each issue as:
ISSUE: [Description of the problem]
TYPE: [character|timeline|location|props|technical]
SEVERITY: [low|medium|high]
IMPACT: [How this could affect production]
SUGGESTION: [Recommended fix]
"""

CREATIVE_ASSESSMENT_PROMPT = """As a director, assess the creative and production implications of this script:

SCRIPT:
{script_text}

Evaluate:
1. Creative ambition vs. production complexity
2. Research requirements for authenticity
3. Potential legal/licensing challenges
4. Technical production challenges
5. Budget implications of factual requirements

Provide director-level insights on balancing creative vision with production realities.
"""