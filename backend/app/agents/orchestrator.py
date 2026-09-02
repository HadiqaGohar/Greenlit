"""
Multi-Agent Orchestrator - Coordinates specialized agents for film production analysis
Handles parallel execution, result aggregation, timeline tracking, readiness scoring, and suggestions
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

from .director_agent import DirectorAgent
from .research_agent import ResearchAgent
from .legal_agent import LegalAgent
from .continuity_agent import ContinuityAgent
from ..models.agent_schemas import (
    AgentTask, AgentResult, OrchestratorReport,
    RiskAssessment, ProductionIssue,
    AgentTimelineStep, ReadinessScore, AgentFlowStep, Suggestion
)
from ..services.scene_parser import parse_screenplay
from ..services.character_extractor import extract_characters

logger = logging.getLogger(__name__)


class AgentOrchestrator:

    def __init__(self):
        self.director = DirectorAgent()
        self.researcher = ResearchAgent()
        self.legal = LegalAgent()
        self.continuity = ContinuityAgent()
        self.recent_reports: Dict[str, OrchestratorReport] = {}

    async def analyze_script(
        self,
        script_text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> OrchestratorReport:
        report_id = str(uuid4())
        start_time = datetime.now(timezone.utc)
        timeline: List[AgentTimelineStep] = []

        logger.info(f"Starting multi-agent analysis for report {report_id}")

        try:
            scenes, scene_stats = parse_screenplay(script_text)
            characters, continuity_issues, char_stats = extract_characters(scenes, script_text)
            logger.info(f"Parsed {len(scenes)} scenes and {len(characters)} characters")

            # Phase 1: Director agent (sequential)
            director_start = datetime.now(timezone.utc)
            timeline.append(AgentTimelineStep(
                agent="director", status="running",
                start_time=director_start, phase="sequential",
                summary="Extracting factual claims from script..."
            ))

            director_task = AgentTask(
                agent_type="director",
                task_data={
                    "script_text": script_text,
                    "priority": (options or {}).get("priority", "normal"),
                    "context": (options or {}).get("context", {}),
                    "scenes": scenes,
                    "characters": characters,
                    "focus": "claims_extraction"
                },
                task_id=f"director_{uuid4().hex[:8]}"
            )

            director_result = await self.director.process_task(director_task)
            director_end = datetime.now(timezone.utc)

            extracted_claims = []
            if director_result.success and director_result.data:
                extracted_claims = director_result.data.get("claims", [])

            director_step = timeline[-1]
            director_step.status = "complete" if director_result.success else "error"
            director_step.end_time = director_end
            director_step.duration_seconds = (director_end - director_start).total_seconds()
            director_step.claims_count = len(extracted_claims)
            director_step.confidence = director_result.confidence_score
            director_step.summary = f"Extracted {len(extracted_claims)} factual claims for verification"

            logger.info(f"Director extracted {len(extracted_claims)} claims")

            # Phase 2: Research, Legal, Continuity in parallel
            parallel_start = datetime.now(timezone.utc)
            for agent_name in ["research", "legal", "continuity"]:
                timeline.append(AgentTimelineStep(
                    agent=agent_name, status="running",
                    start_time=parallel_start, phase="parallel",
                    summary=f"Running {agent_name} analysis..."
                ))

            remaining_tasks = [
                AgentTask(
                    agent_type="research",
                    task_data={
                        "script_text": script_text,
                        "claims": extracted_claims,
                        "priority": (options or {}).get("priority", "normal"),
                        "context": (options or {}).get("context", {}),
                        "scenes": scenes,
                        "characters": characters,
                        "focus": "fact_verification"
                    },
                    task_id=f"research_{uuid4().hex[:8]}"
                ),
                AgentTask(
                    agent_type="legal",
                    task_data={
                        "script_text": script_text,
                        "priority": (options or {}).get("priority", "normal"),
                        "context": (options or {}).get("context", {}),
                        "scenes": scenes,
                        "characters": characters,
                        "focus": "licensing_risks"
                    },
                    task_id=f"legal_{uuid4().hex[:8]}"
                ),
                AgentTask(
                    agent_type="continuity",
                    task_data={
                        "script_text": script_text,
                        "priority": (options or {}).get("priority", "normal"),
                        "context": (options or {}).get("context", {}),
                        "scenes": scenes,
                        "characters": characters,
                        "focus": "consistency_check"
                    },
                    task_id=f"continuity_{uuid4().hex[:8]}"
                )
            ]

            remaining_results = await self._execute_agents_parallel(remaining_tasks)
            parallel_end = datetime.now(timezone.utc)

            # Update timeline for parallel agents
            for step in timeline:
                if step.phase == "parallel" and step.status == "running":
                    result = remaining_results.get(step.agent)
                    if result:
                        step.status = "complete" if result.success else "error"
                        step.end_time = parallel_end
                        step.duration_seconds = (parallel_end - parallel_start).total_seconds()
                        step.confidence = result.confidence_score
                        if step.agent == "research" and result.data:
                            claims = result.data.get("claims", [])
                            step.claims_count = len(claims)
                            step.issues_found = len([c for c in claims if c.get("verdict") == "flagged"])
                            step.summary = f"Verified {len(claims)} claims via Parallel API"
                        elif step.agent == "legal" and result.data:
                            cr = result.data.get("copyright_risks", [])
                            tm = result.data.get("trademark_issues", [])
                            step.issues_found = len(cr) + len(tm)
                            step.summary = f"Found {step.issues_found} legal issues"
                        elif step.agent == "continuity" and result.data:
                            ci = result.data.get("character_inconsistencies", [])
                            ti = result.data.get("timeline_issues", [])
                            step.issues_found = len(ci) + len(ti)
                            step.summary = f"Found {step.issues_found} continuity issues"
                    else:
                        step.status = "error"
                        step.end_time = parallel_end
                        step.duration_seconds = (parallel_end - parallel_start).total_seconds()

            # Combine results
            agent_results = {"director": director_result}
            agent_results.update(remaining_results)

            # Risk assessment
            risk_assessment = await self._assess_production_risks(agent_results)

            # Compute readiness scores
            readiness_scores = self._calculate_readiness_scores(agent_results)

            # Compute agent flow data
            agent_flow = self._compute_agent_flow(agent_results, extracted_claims)

            # Generate suggestions
            suggestions = self._generate_suggestions(agent_results)

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Convert SceneData objects to dicts
            scenes_dicts = []
            for s in scenes:
                if hasattr(s, '__dict__'):
                    scenes_dicts.append({k: v for k, v in s.__dict__.items() if not k.startswith('_')})
                elif isinstance(s, dict):
                    scenes_dicts.append(s)
                else:
                    scenes_dicts.append({"scene_number": getattr(s, 'scene_number', 0), "title": getattr(s, 'title', str(s))})

            # Convert characters dict to list of dicts
            chars_list = []
            if isinstance(characters, dict):
                for name, profile in characters.items():
                    if hasattr(profile, '__dict__'):
                        char_dict = {k: v for k, v in profile.__dict__.items() if not k.startswith('_')}
                        char_dict['name'] = name
                        chars_list.append(char_dict)
                    elif isinstance(profile, dict):
                        profile['name'] = name
                        chars_list.append(profile)
                    else:
                        chars_list.append({"name": name})
            elif isinstance(characters, list):
                for c in characters:
                    if hasattr(c, '__dict__'):
                        chars_list.append({k: v for k, v in c.__dict__.items() if not k.startswith('_')})
                    elif isinstance(c, dict):
                        chars_list.append(c)

            report = OrchestratorReport(
                report_id=report_id,
                timestamp=start_time,
                script_length=len(script_text),
                script_text=script_text,
                agent_results=agent_results,
                risk_assessment=risk_assessment,
                processing_time=processing_time,
                automation_actions=await self._generate_automation_actions(agent_results),
                agent_timeline=timeline,
                readiness_scores=readiness_scores,
                agent_flow=agent_flow,
                suggestions=suggestions,
                scenes=scenes_dicts,
                characters=chars_list,
                scene_statistics=scene_stats if isinstance(scene_stats, dict) else {},
                character_statistics=char_stats if isinstance(char_stats, dict) else {},
                continuity_issues=continuity_issues if isinstance(continuity_issues, list) else []
            )

            self.recent_reports[report_id] = report
            if len(self.recent_reports) > 10:
                oldest = min(self.recent_reports.keys())
                del self.recent_reports[oldest]

            logger.info(f"Analysis complete: {report.report_id} ({processing_time:.1f}s)")
            return report

        except Exception as e:
            logger.error(f"Orchestration failed: {str(e)}")
            raise

    def _calculate_readiness_scores(self, agent_results: Dict[str, AgentResult]) -> ReadinessScore:
        """Calculate production readiness across 5 dimensions"""
        # Legal Clearance: 100 minus penalties for issues
        legal_score = 100.0
        legal_result = agent_results.get("legal")
        if legal_result and legal_result.success and legal_result.data:
            cr = len(legal_result.data.get("copyright_risks", []))
            tm = len(legal_result.data.get("trademark_issues", []))
            cp = len(legal_result.data.get("clearance_required", []))
            legal_score = max(0, 100 - (cr * 20) - (tm * 15) - (cp * 10))

        # Historical Accuracy: based on research verification rate
        accuracy_score = 75.0  # default if no research
        research_result = agent_results.get("research")
        if research_result and research_result.success and research_result.data:
            claims = research_result.data.get("claims", [])
            if claims:
                verified = len([c for c in claims if c.get("verdict") == "verified"])
                accuracy_score = (verified / len(claims)) * 100

        # Continuity: 100 minus penalties
        continuity_score = 100.0
        cont_result = agent_results.get("continuity")
        if cont_result and cont_result.success and cont_result.data:
            ci = len(cont_result.data.get("character_inconsistencies", []))
            ti = len(cont_result.data.get("timeline_issues", []))
            li = len(cont_result.data.get("location_continuity", []))
            pi = len(cont_result.data.get("prop_tracking", []))
            continuity_score = max(0, 100 - (ci * 15) - (ti * 12) - (li * 8) - (pi * 5))

        # Budget Feasibility: inverse of risk score
        budget_score = 100.0
        director_result = agent_results.get("director")
        if director_result and director_result.success and director_result.data:
            claims = director_result.data.get("claims", [])
            budget_score = max(0, 100 - len(claims) * 3)

        # Overall weighted average
        overall = (legal_score * 0.3) + (accuracy_score * 0.25) + \
                  (continuity_score * 0.25) + (budget_score * 0.2)

        # Grade
        if overall >= 90:
            grade = "A"
        elif overall >= 80:
            grade = "B"
        elif overall >= 70:
            grade = "C"
        elif overall >= 60:
            grade = "D"
        else:
            grade = "F"

        return ReadinessScore(
            legal_clearance=round(legal_score, 1),
            historical_accuracy=round(accuracy_score, 1),
            continuity=round(continuity_score, 1),
            budget_feasibility=round(budget_score, 1),
            overall=round(overall, 1),
            grade=grade
        )

    def _compute_agent_flow(
        self, agent_results: Dict[str, AgentResult], claims: List[Dict]
    ) -> List[AgentFlowStep]:
        """Compute data flow between agents for the flow diagram"""
        flow = []

        # Director output
        flow.append(AgentFlowStep(
            agent="director",
            claims_in=0,
            claims_out=len(claims),
            verified=0, flagged=0, uncertain=0
        ))

        # Research output
        research_result = agent_results.get("research")
        if research_result and research_result.success and research_result.data:
            r_claims = research_result.data.get("claims", [])
            flow.append(AgentFlowStep(
                agent="research",
                claims_in=len(claims),
                claims_out=len(r_claims),
                verified=len([c for c in r_claims if c.get("verdict") == "verified"]),
                flagged=len([c for c in r_claims if c.get("verdict") == "flagged"]),
                uncertain=len([c for c in r_claims if c.get("verdict") == "uncertain"])
            ))
        else:
            flow.append(AgentFlowStep(agent="research", claims_in=len(claims)))

        # Legal output
        legal_result = agent_results.get("legal")
        if legal_result and legal_result.success and legal_result.data:
            cr = legal_result.data.get("copyright_risks", [])
            tm = legal_result.data.get("trademark_issues", [])
            high = len([i for i in cr + tm if i.get("severity") == "high"])
            med = len([i for i in cr + tm if i.get("severity") == "medium"])
            low = len([i for i in cr + tm if i.get("severity") == "low"])
            flow.append(AgentFlowStep(
                agent="legal", claims_in=0, claims_out=len(cr) + len(tm),
                issues_high=high, issues_medium=med, issues_low=low
            ))
        else:
            flow.append(AgentFlowStep(agent="legal"))

        # Continuity output
        cont_result = agent_results.get("continuity")
        if cont_result and cont_result.success and cont_result.data:
            ci = len(cont_result.data.get("character_inconsistencies", []))
            ti = len(cont_result.data.get("timeline_issues", []))
            li = len(cont_result.data.get("location_continuity", []))
            pi = len(cont_result.data.get("prop_tracking", []))
            flow.append(AgentFlowStep(
                agent="continuity", claims_in=0, claims_out=ci + ti + li + pi,
                issues_high=ci, issues_medium=ti, issues_low=li + pi
            ))
        else:
            flow.append(AgentFlowStep(agent="continuity"))

        return flow

    def _generate_suggestions(self, agent_results: Dict[str, AgentResult]) -> List[Suggestion]:
        """Generate fix suggestions for flagged issues"""
        suggestions = []
        suggestion_id = 0

        # Research suggestions for flagged claims
        research_result = agent_results.get("research")
        if research_result and research_result.success and research_result.data:
            for claim in research_result.data.get("claims", []):
                if claim.get("verdict") == "flagged":
                    suggestion_id += 1
                    suggestions.append(Suggestion(
                        issue_id=f"sug_{suggestion_id}",
                        issue_type="factual",
                        severity="high",
                        original_text=claim.get("text", ""),
                        suggested_text=f"Consider revising: {claim.get('text', '')} — flagged as potentially inaccurate by research verification.",
                        rationale=f"Research agent flagged this claim with {claim.get('confidence', 0):.0%} confidence. Verify with primary sources before production."
                    ))

        # Legal suggestions
        legal_result = agent_results.get("legal")
        if legal_result and legal_result.success and legal_result.data:
            for risk in legal_result.data.get("copyright_risks", []):
                if risk.get("severity") in ("high", "medium"):
                    suggestion_id += 1
                    original = risk.get("content", risk.get("description", ""))
                    fix = risk.get("suggested_fix", "Consult entertainment lawyer for clearance options.")
                    suggestions.append(Suggestion(
                        issue_id=f"sug_{suggestion_id}",
                        issue_type="legal",
                        severity=risk.get("severity", "medium"),
                        original_text=original,
                        suggested_text=fix,
                        rationale=f"Copyright risk identified: {risk.get('type', 'unknown')}. Clearance required before distribution."
                    ))

            for issue in legal_result.data.get("trademark_issues", []):
                suggestion_id += 1
                original = issue.get("content", issue.get("description", ""))
                fix = issue.get("suggested_fix", "Replace with generic description or obtain license.")
                suggestions.append(Suggestion(
                    issue_id=f"sug_{suggestion_id}",
                    issue_type="trademark",
                    severity=issue.get("severity", "medium"),
                    original_text=original,
                    suggested_text=fix,
                    rationale=f"Trademark issue: {issue.get('brand', 'unknown')}. Use generic alternatives."
                ))

        # Continuity suggestions
        cont_result = agent_results.get("continuity")
        if cont_result and cont_result.success and cont_result.data:
            for issue in cont_result.data.get("character_inconsistencies", []):
                suggestion_id += 1
                suggestions.append(Suggestion(
                    issue_id=f"sug_{suggestion_id}",
                    issue_type="continuity",
                    severity=issue.get("severity", "low"),
                    original_text=issue.get("description", ""),
                    suggested_text=issue.get("suggested_fix", "Ensure character descriptions are consistent across all scenes."),
                    rationale="Character inconsistency detected in script. Fix before shooting."
                ))

        return suggestions

    async def _execute_agents_parallel(self, tasks: List[AgentTask]) -> Dict[str, AgentResult]:
        # Individual agent timeouts: Research gets more time (Parallel API), others get less
        AGENT_TIMEOUTS = {
            "research": 300.0,   # 5 min for Parallel API deep research
            "legal": 90.0,       # Legal agent uses Gemini (fast)
            "continuity": 90.0,  # Continuity agent uses Gemini (fast)
        }
        
        async def run_agent(task: AgentTask) -> tuple:
            agent_timeout = AGENT_TIMEOUTS.get(task.agent_type, 90.0)
            try:
                if task.agent_type == "research":
                    result = await asyncio.wait_for(
                        self.researcher.process_task(task),
                        timeout=agent_timeout
                    )
                elif task.agent_type == "legal":
                    result = await asyncio.wait_for(
                        self.legal.process_task(task),
                        timeout=agent_timeout
                    )
                elif task.agent_type == "continuity":
                    result = await asyncio.wait_for(
                        self.continuity.process_task(task),
                        timeout=agent_timeout
                    )
                else:
                    raise ValueError(f"Unknown agent type: {task.agent_type}")
                return task.agent_type, result
            except asyncio.TimeoutError:
                logger.warning(f"Agent {task.agent_type} timed out after {agent_timeout}s")
                return task.agent_type, AgentResult(
                    agent_type=task.agent_type,
                    task_id=task.task_id,
                    success=False,
                    error_message=f"Agent timed out after {agent_timeout}s",
                    processing_time=agent_timeout,
                    confidence_score=0.0
                )
            except Exception as e:
                logger.error(f"Agent {task.agent_type} failed: {str(e)}")
                return task.agent_type, AgentResult(
                    agent_type=task.agent_type,
                    task_id=task.task_id,
                    success=False,
                    error_message=str(e),
                    processing_time=0.0,
                    confidence_score=0.0
                )

        # Run all agents in parallel - each has its own timeout
        results = await asyncio.gather(*[run_agent(task) for task in tasks])

        return {agent_type: result for agent_type, result in results}

    async def _assess_production_risks(self, agent_results: Dict[str, AgentResult]) -> RiskAssessment:
        total_risk = 0.0
        risk_factors = []
        critical_issues = []

        for agent_type, result in agent_results.items():
            if not result.success:
                risk_factors.append(f"{agent_type} agent failed")
                total_risk += 20
                continue

            if agent_type == "legal" and result.data:
                legal_risks = result.data.get("copyright_risks", [])
                trademark_issues = result.data.get("trademark_issues", [])
                total_risk += len(legal_risks) * 15
                total_risk += len(trademark_issues) * 10
                critical_issues.extend([
                    ProductionIssue(
                        type="legal",
                        severity="high" if "copyright" in issue.get("type", "") else "medium",
                        description=issue.get("description", ""),
                        suggested_action=issue.get("suggested_fix", "")
                    ) for issue in legal_risks + trademark_issues
                ])

            elif agent_type == "continuity" and result.data:
                issues = result.data.get("character_inconsistencies", []) + \
                         result.data.get("timeline_issues", [])
                total_risk += len(issues) * 5

            elif agent_type == "research" and result.data:
                flagged_claims = [c for c in result.data.get("claims", []) if c.get("verdict") == "flagged"]
                total_risk += len(flagged_claims) * 10

        final_risk_score = min(total_risk, 100.0)

        return RiskAssessment(
            overall_risk_score=final_risk_score,
            risk_level="low" if final_risk_score < 30 else "medium" if final_risk_score < 70 else "high",
            risk_factors=risk_factors,
            critical_issues=critical_issues,
            recommended_actions=await self._generate_recommended_actions(critical_issues)
        )

    async def _generate_automation_actions(self, agent_results: Dict[str, AgentResult]) -> Dict[str, Any]:
        actions = {
            "notifications_triggered": [],
            "checklists_generated": [],
            "auto_fixes_suggested": [],
            "alerts_sent": []
        }

        legal_result = agent_results.get("legal")
        if legal_result and legal_result.success and legal_result.data:
            high_risk_legal = [
                risk for risk in legal_result.data.get("copyright_risks", [])
                if risk.get("severity") == "high"
            ]

            if high_risk_legal:
                actions["notifications_triggered"].append({
                    "type": "slack_alert",
                    "message": f"High-risk legal issues detected: {len(high_risk_legal)} copyright concerns",
                    "urgency": "immediate"
                })

                actions["checklists_generated"].append({
                    "type": "legal_clearance",
                    "items": [risk.get("clearance_action") for risk in high_risk_legal if risk.get("clearance_action")]
                })

        return actions

    async def _generate_recommended_actions(self, issues: List[ProductionIssue]) -> List[str]:
        actions = []

        high_severity_issues = [i for i in issues if i.severity == "high"]
        if high_severity_issues:
            actions.append("Address high-severity legal/licensing issues before production")

        legal_issues = [i for i in issues if i.type == "legal"]
        if legal_issues:
            actions.append("Review legal clearance checklist with production legal team")

        if len(issues) > 10:
            actions.append("Consider script revision to reduce production complexity")

        return actions if actions else ["No critical production issues identified"]
