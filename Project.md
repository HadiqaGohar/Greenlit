# 🎬 Greenlit AI — Project Specification

**Tagline:** AI-powered production research, before the cameras roll.
**Hackathon:** Agentic Cinema: The Blockbuster Hackathon (Google Cloud + Parallel track)
**Deadline:** Sep 9, 2026

---

## 1. Concept Summary

Greenlit AI is an **autonomous multi-agent orchestration platform** for film/TV production teams. The system deploys specialized AI agents working in parallel:

### 🤖 **Multi-Agent Architecture** (Core Innovation)
1. **Director Agent** (Gemini Enterprise): Extracts factual claims, historical references, locations, and technical details
2. **Research Agent** (Parallel API): Verifies each claim with real-time research and sourcing
3. **Legal Agent** (Gemini + Legal DB): Assesses licensing risks, copyright issues, and clearance requirements
4. **Continuity Agent** (Gemini): Tracks character consistency, timeline accuracy, and plot coherence across scenes

### 🔄 **Autonomous Workflow**
- **Auto-trigger processing**: Monitor script folders/Google Drive for new uploads
- **Intelligent batch processing**: Scene-by-scene analysis with progress tracking
- **Differential re-analysis**: Only process changed sections on script revisions
- **Proactive risk alerts**: Automatic notifications for high-risk legal/licensing issues

Built on **Gemini Enterprise Agent Platform** orchestrating multiple specialized agents, with **Parallel API** as the core research partner.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| **Multi-Agent Orchestration** | **Google Cloud Agent Builder / Gemini Enterprise (4 specialized agents)** |
| Research API | Parallel API |
| **Automation Engine** | **Google Cloud Functions + Pub/Sub for auto-triggers** |
| **Notifications** | **Cloud Tasks + Slack/Email webhooks** |
| File Monitoring | Google Drive API + Cloud Storage |
| Deployment | Google Cloud Run (backend), Vercel (frontend) |
| Auth (optional) | Google Identity Platform

> Note: You mentioned "backend python nodejs fastapi" — FastAPI is Python-only (there's no Node FastAPI). This spec assumes **Python + FastAPI** for backend. If you specifically want a Node.js backend instead, swap FastAPI for **Express** or **Fastify** — just say the word and I'll restructure this doc.

---

## 3. Repository Structure

```
greenlit-ai/
├── README.md
├── LICENSE                      # MIT or Apache-2.0, visible in GitHub "About"
├── .gitignore
├── docker-compose.yml           # optional, local dev convenience
│
├── frontend/                    # Next.js app
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── .env.local.example
│   ├── public/
│   │   └── logo.svg
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx                 # landing / script input page
│       │   ├── report/
│       │   │   └── [id]/page.tsx        # annotated report view
│       │   └── globals.css
│       ├── components/
│       │   ├── ScriptEditor.tsx         # paste/upload script
│       │   ├── ClaimHighlight.tsx       # inline annotation highlight
│       │   ├── ReportSidebar.tsx        # claim list + verdicts
│       │   ├── ClaimCard.tsx            # single claim: verdict, source, confidence
│       │   ├── LoadingReel.tsx          # film-reel themed loading state
│       │   └── Header.tsx
│       ├── lib/
│       │   ├── api.ts                   # fetch wrapper to backend
│       │   └── types.ts                 # shared TS types
│       └── hooks/
│           └── useAnalysis.ts
│
└── backend/                     # FastAPI app
    ├── requirements.txt
    ├── Dockerfile
    ├── .env.example
    ├── main.py                          # FastAPI entrypoint
    ├── app/
    │   ├── __init__.py
    │   ├── config.py                    # env vars, settings
    │   ├── routers/
    │   │   ├── analyze.py               # POST /analyze endpoint
    │   │   ├── health.py                # GET /health
    │   │   ├── automation.py            # auto-trigger endpoints
    │   │   └── webhooks.py              # Drive/Slack integration
    │   ├── agents/                      # Multi-agent system
    │   │   ├── director_agent.py        # Gemini: claim extraction
    │   │   ├── research_agent.py        # Parallel: fact verification
    │   │   ├── legal_agent.py           # Gemini: licensing/copyright risks
    │   │   ├── continuity_agent.py      # Gemini: character/timeline consistency
    │   │   ├── orchestrator.py          # Multi-agent workflow coordinator
    │   │   └── prompts/                 # Agent-specific prompt templates
    │   │       ├── director_prompts.py
    │   │       ├── legal_prompts.py
    │   │       └── continuity_prompts.py
    │   ├── automation/
    │   │   ├── file_watcher.py          # Google Drive monitoring
    │   │   ├── batch_processor.py       # Scene-by-scene processing
    │   │   ├── diff_analyzer.py         # Changed-content detection
    │   │   └── notification_service.py  # Slack/email alerts
    │   ├── research/
    │   │   └── parallel_client.py       # Parallel API wrapper
    │   ├── models/
    │   │   ├── schemas.py               # Pydantic models
    │   │   ├── agent_schemas.py         # Multi-agent communication models
    │   │   └── automation_schemas.py    # Automation workflow models
    │   └── services/
    │       ├── report_builder.py        # Assembles final reports
    │       ├── risk_scorer.py           # Production risk assessment
    │       └── clearance_generator.py   # Auto-generate legal checklists
    └── tests/
        ├── test_analyze.py
        ├── test_multi_agents.py
        └── test_automation.py
```

---

## 4. Design Theme

**Visual identity:** Cinematic, editorial, "script supervisor's desk" feel — not a generic SaaS dashboard.

- **Color palette:** Deep charcoal/black background (`#0B0B0D`), warm amber/gold accent (`#D4A017` — think "greenlight"/marquee lights), off-white text (`#F5F1E8`), muted red for flagged issues (`#C0392B`), soft green for verified claims (`#4C9A6E`)
- **Typography:** Serif display font for headings (e.g., "Fraunces" or "Playfair Display" — screenplay/title-card feel), clean monospace for script text (e.g., "JetBrains Mono" or "Courier Prime" — literally mimics screenplay formatting), sans-serif for UI chrome (Inter)
- **Motifs:** Film sprocket-hole borders, clapperboard iconography, red-pen annotation marks (like a script supervisor's markup), subtle film-grain texture on backgrounds
- **Tone:** Feels like a professional tool a real production coordinator would use — not playful/cartoonish

---

## 5. Core Features

### 🤖 **Multi-Agent Automation** (Hackathon Differentiator)
| Feature | Description | Agent Responsible | Priority |
|---|---|---|---|
| **Multi-agent orchestration** | 4 specialized agents working in parallel pipeline | Orchestrator | Must-have |
| **Auto-trigger processing** | Monitor Google Drive/folders, process on upload | File Watcher | Must-have |
| **Differential re-analysis** | Only re-process changed sections on script updates | Diff Analyzer | Must-have |
| **Risk scoring dashboard** | Automated production risk assessment (0-100 scale) | Risk Scorer | Must-have |
| **Legal clearance automation** | Auto-generate licensing/copyright checklists | Legal Agent | Must-have |

### 📋 **Core Production Features**
| Feature | Description | Agent Responsible | Priority |
|---|---|---|---|
| Script input | Paste text or upload `.txt`/`.pdf` script | Director Agent | Must-have |
| Claim extraction | Identify factual/historical/location/technical claims | Director Agent | Must-have |
| Automated research | Each claim researched live via Parallel API | Research Agent | Must-have |
| Legal risk assessment | Flag copyrighted content, real person mentions | Legal Agent | Must-have |
| Continuity checking | Track character details, timeline consistency | Continuity Agent | Must-have |
| Structured report | Multi-agent analysis with confidence scores | Report Builder | Must-have |
| Inline annotation view | Script with color-coded agent findings | Frontend | Must-have |

### 🚨 **Proactive Automation**
| Feature | Description | Priority |
|---|---|---|
| **Auto-notifications** | Slack/email alerts for high-risk legal issues | Nice-to-have |
| **Batch scene processing** | Queue-based scene-by-scene analysis | Nice-to-have |
| **Auto-suggest fixes** | AI-generated alternative wording for flagged content | Nice-to-have |
| **Export automation** | Auto-push reports to Notion/Google Docs/Airtable | Nice-to-have |
| **Multi-scene batch analysis** | Process entire scripts automatically | Nice-to-have |
| **Shareable report links** | Public URLs with production team collaboration | Nice-to-have |

---

## 6. Multi-Agent Architecture & Data Flow

### 🎬 **Agent Roles** (Matching Hackathon Theme)
```
Director Agent    → Claims extraction, script analysis
Research Agent    → Fact verification, source gathering  
Legal Agent       → Copyright/licensing risk assessment
Continuity Agent  → Character/timeline consistency checking
```

### 🔄 **Automated Workflow**
```
Script Upload (Google Drive/Manual)
        │
        ▼
File Watcher → Auto-trigger processing
        │
        ▼
Orchestrator deploys 4 agents in parallel:
        │
        ├─→ Director Agent (Gemini) → Extract claims
        ├─→ Research Agent (Parallel) → Verify facts  
        ├─→ Legal Agent (Gemini) → Assess legal risks
        └─→ Continuity Agent (Gemini) → Check consistency
        │
        ▼
Report Builder → Risk Scorer → Clearance Generator
        │
        ▼
Auto-notifications (if high-risk) + Dashboard update
        │
        ▼
Frontend: Multi-agent annotated view + Risk dashboard
```

### 🚨 **Proactive Automation Triggers**
- **High Legal Risk**: Auto-Slack alert if copyrighted music/brand detected
- **Continuity Issues**: Flag character age inconsistencies across scenes
- **Historical Inaccuracies**: Auto-research and suggest corrections
- **Script Changes**: Differential re-analysis of only modified sections

### Key Backend Endpoints

#### **Multi-Agent Analysis**
```http
POST /analyze
Body: { 
  "script_text": string,
  "auto_mode": boolean,          // Enable auto-processing
  "agents": ["director", "research", "legal", "continuity"]  // Optional agent selection
}
Response: {
  "report_id": string,
  "processing_status": "queued" | "processing" | "complete",
  "risk_score": number,          // 0-100 overall production risk
  "agents_results": {
    "director": { "claims": [...], "confidence": 0.95 },
    "research": { "verified_claims": [...], "sources": [...] },
    "legal": { "copyright_risks": [...], "clearance_needed": [...] },
    "continuity": { "character_issues": [...], "timeline_issues": [...] }
  },
  "auto_actions": {
    "notifications_sent": [...],
    "clearance_checklist": "checklist_id",
    "suggested_fixes": [...]
  }
}
```

#### **Automation Endpoints**
```http
POST /automation/watch-folder
Body: { "google_drive_folder_id": string, "notification_webhook": string }

POST /automation/batch-process  
Body: { "script_scenes": [string], "priority": "high|normal|low" }

GET /automation/risk-dashboard/{report_id}
Response: { "risk_breakdown": {...}, "action_items": [...] }
```

---

## 7. Google Cloud + Parallel Integration Requirements (per hackathon rules)

### **Multi-Agent Google Cloud Integration** ✅
- **Gemini Enterprise Agent Platform**: Powers 3 of 4 specialized agents (Director, Legal, Continuity)
- **Google Cloud Functions**: Auto-trigger system for file monitoring  
- **Google Cloud Pub/Sub**: Agent communication and workflow orchestration
- **Google Drive API**: File monitoring and automatic processing
- **Cloud Tasks**: Notification and automation scheduling
- **Google Cloud Run**: Multi-agent backend deployment

### **Parallel API Integration** ✅
- **Research Agent Core**: All fact verification flows through Parallel API
- **Real-time Research**: Live API calls for each extracted claim
- **Source Attribution**: Parallel provides research sources and confidence scoring
- **Batch Processing**: Parallel handles scene-by-scene research automation

### **Hackathon Innovation** 🚀
- **Multi-Agent Orchestration**: Beyond single-agent, demonstrates production-ready autonomous agent networks
- **Automation-First Design**: Proactive processing vs reactive manual analysis
- **Industry-Specific Agents**: Legal, Continuity, Research - real production workflow roles

---

## 8. Enhanced Build Order (Multi-Agent Implementation)

### **Phase 1-7**: Foundation Complete ✅
1. ✅ Backend skeleton (FastAPI + `/health` endpoint) → deployed to Cloud Run
2. ✅ `parallel_client.py` → Research Agent integration working
3. ✅ `gemini_client.py` → Director Agent claim extraction working  
4. ✅ `/analyze` endpoint → single-agent workflow complete
5. ✅ Frontend core → script input, report rendering
6. ✅ UI polish → ClaimHighlight, ReportSidebar, responsive design
7. ✅ Cinematic design theme → film supervisor aesthetic complete

### **Phase 8-10**: Multi-Agent & Automation 🚀
8. **Multi-Agent Architecture** (Current Priority)
   - Implement 4 specialized agents (Director, Research, Legal, Continuity)
   - Create orchestrator for parallel agent execution
   - Build agent communication schemas

9. **Automation Engine**
   - Google Drive file monitoring
   - Auto-trigger processing system  
   - Differential analysis for script changes
   - Risk scoring and notification system

10. **Production Demo**
    - Record multi-agent workflow demonstration
    - Show automation features in action
    - Highlight hackathon technical achievements
    - Deploy with full automation pipeline

---

## 9. Open Decisions (confirm before I generate code)

- [ ] Backend confirmed as **Python FastAPI** (not Node)?
- [ ] PDF script upload needed, or plain text paste is enough for MVP?
- [ ] Deploy targets: Google Cloud Run (backend) + Vercel (frontend) — okay?


