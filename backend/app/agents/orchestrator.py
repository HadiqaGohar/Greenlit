"""
Multi-Agent Orchestrator - Coordinates specialized agents for film production analysis
Handles parallel execution and result aggregation across Director, Research, Legal, and Continuity agents
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from .director_agent import DirectorAgent
from .research_agent import ResearchAgent
from .legal_agent import LegalAgent
from .continuity_agent import ContinuityAgent
from ..models.agent_schemas import (
    AgentTask, AgentResult, OrchestratorReport, 
    RiskAssessment, ProductionIssue
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Coordinates multiple specialized agents for comprehensive script analysis
    Matches hackathon theme: Director/Producer/Studio Head roles
    """
    
    def __init__(self):
        self.director = DirectorAgent()
        self.researcher = ResearchAgent() 
        self.legal = LegalAgent()
        self.continuity = ContinuityAgent()
        
        # Temporary in-memory storage for reports (in production, this would be a database)
        self.recent_reports: Dict[str, OrchestratorReport] = {}
        
    async def analyze_script(
        self, 
        script_text: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> OrchestratorReport:
        """
        Orchestrate multi-agent analysis of script content
        Runs agents in parallel for maximum efficiency
        """
        report_id = str(uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Starting multi-agent analysis for report {report_id}")
        
        try:
            # Create tasks for each agent
            tasks = await self._create_agent_tasks(script_text, options or {})
            
            # Execute all agents in parallel
            agent_results = await self._execute_agents_parallel(tasks)
            
            # Aggregate results and assess risks
            risk_assessment = await self._assess_production_risks(agent_results)
            
            # Build final orchestrator report
            report = OrchestratorReport(
                report_id=report_id,
                timestamp=start_time,
                script_length=len(script_text),
                agent_results=agent_results,
                risk_assessment=risk_assessment,
                processing_time=(datetime.utcnow() - start_time).total_seconds(),
                automation_actions=await self._generate_automation_actions(agent_results)
            )
            
            # Store report temporarily for retrieval (in production, save to database)
            self.recent_reports[report_id] = report
            
            # Keep only last 10 reports in memory to prevent memory leaks
            if len(self.recent_reports) > 10:
                oldest_report_id = min(self.recent_reports.keys())
                del self.recent_reports[oldest_report_id]
            
            logger.info(f"Multi-agent analysis complete: {report.report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Multi-agent orchestration failed: {str(e)}")
            raise
    
    async def _create_agent_tasks(
        self, 
        script_text: str, 
        options: Dict[str, Any]
    ) -> List[AgentTask]:
        """Create specialized tasks for each agent based on script content"""
        
        base_task = {
            "script_text": script_text,
            "priority": options.get("priority", "normal"),
            "context": options.get("context", {})
        }
        
        tasks = [
            AgentTask(
                agent_type="director",
                task_data={**base_task, "focus": "claims_extraction"},
                task_id=f"director_{uuid4().hex[:8]}"
            ),
            AgentTask(
                agent_type="research", 
                task_data={**base_task, "focus": "fact_verification"},
                task_id=f"research_{uuid4().hex[:8]}"
            ),
            AgentTask(
                agent_type="legal",
                task_data={**base_task, "focus": "licensing_risks"},
                task_id=f"legal_{uuid4().hex[:8]}"
            ),
            AgentTask(
                agent_type="continuity",
                task_data={**base_task, "focus": "consistency_check"},
                task_id=f"continuity_{uuid4().hex[:8]}"
            )
        ]
        
        return tasks
    
    async def _execute_agents_parallel(self, tasks: List[AgentTask]) -> Dict[str, AgentResult]:
        """Execute all agents in parallel for maximum performance"""
        
        async def run_agent(task: AgentTask) -> tuple[str, AgentResult]:
            try:
                if task.agent_type == "director":
                    result = await self.director.process_task(task)
                elif task.agent_type == "research":
                    result = await self.researcher.process_task(task) 
                elif task.agent_type == "legal":
                    result = await self.legal.process_task(task)
                elif task.agent_type == "continuity":
                    result = await self.continuity.process_task(task)
                else:
                    raise ValueError(f"Unknown agent type: {task.agent_type}")
                    
                return task.agent_type, result
                
            except Exception as e:
                logger.error(f"Agent {task.agent_type} failed: {str(e)}")
                # Return failed result instead of crashing entire pipeline
                return task.agent_type, AgentResult(
                    agent_type=task.agent_type,
                    task_id=task.task_id,
                    success=False,
                    error_message=str(e),
                    processing_time=0.0,
                    confidence_score=0.0
                )
        
        # Run all agents concurrently
        results = await asyncio.gather(*[run_agent(task) for task in tasks])
        
        # Convert to dictionary
        return {agent_type: result for agent_type, result in results}
    
    async def _assess_production_risks(self, agent_results: Dict[str, AgentResult]) -> RiskAssessment:
        """
        Aggregate agent findings into production risk assessment
        Calculates overall risk score (0-100) and priority issues
        """
        
        total_risk = 0.0
        risk_factors = []
        critical_issues = []
        
        # Analyze each agent's contributions to risk
        for agent_type, result in agent_results.items():
            if not result.success:
                risk_factors.append(f"{agent_type} agent failed")
                total_risk += 20  # Failed agents increase risk
                continue
                
            # Agent-specific risk calculations
            if agent_type == "legal" and result.data:
                legal_risks = result.data.get("copyright_risks", [])
                total_risk += len(legal_risks) * 15  # Each legal issue = +15 risk
                critical_issues.extend([
                    ProductionIssue(
                        type="legal",
                        severity="high" if "copyright" in issue.get("type", "") else "medium",
                        description=issue.get("description", ""),
                        suggested_action=issue.get("suggested_fix", "")
                    ) for issue in legal_risks
                ])
            
            elif agent_type == "continuity" and result.data:
                continuity_issues = result.data.get("inconsistencies", [])
                total_risk += len(continuity_issues) * 5  # Each continuity issue = +5 risk
                
            elif agent_type == "research" and result.data:
                flagged_claims = [c for c in result.data.get("claims", []) if c.get("verdict") == "flagged"]
                total_risk += len(flagged_claims) * 10  # Each flagged fact = +10 risk
        
        # Cap risk at 100
        final_risk_score = min(total_risk, 100.0)
        
        return RiskAssessment(
            overall_risk_score=final_risk_score,
            risk_level="low" if final_risk_score < 30 else "medium" if final_risk_score < 70 else "high",
            risk_factors=risk_factors,
            critical_issues=critical_issues,
            recommended_actions=await self._generate_recommended_actions(critical_issues)
        )
    
    async def _generate_automation_actions(self, agent_results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """Generate automated actions based on agent findings"""
        
        actions = {
            "notifications_triggered": [],
            "checklists_generated": [],
            "auto_fixes_suggested": [],
            "alerts_sent": []
        }
        
        # Check if high-risk legal issues require immediate notification
        legal_result = agent_results.get("legal")
        if legal_result and legal_result.success:
            high_risk_legal = [
                risk for risk in legal_result.data.get("copyright_risks", [])
                if risk.get("severity") == "high"
            ]
            
            if high_risk_legal:
                actions["notifications_triggered"].append({
                    "type": "slack_alert",
                    "message": f"🚨 High-risk legal issues detected: {len(high_risk_legal)} copyright concerns",
                    "urgency": "immediate"
                })
                
                actions["checklists_generated"].append({
                    "type": "legal_clearance",
                    "items": [risk.get("clearance_action") for risk in high_risk_legal]
                })
        
        return actions
    
    async def _generate_recommended_actions(self, issues: List[ProductionIssue]) -> List[str]:
        """Generate specific recommended actions for production team"""
        
        actions = []
        
        high_severity_issues = [i for i in issues if i.severity == "high"]
        if high_severity_issues:
            actions.append("🚨 Address high-severity legal/licensing issues before production")
            
        legal_issues = [i for i in issues if i.type == "legal"]
        if legal_issues:
            actions.append("📋 Review legal clearance checklist with production legal team")
            
        if len(issues) > 10:
            actions.append("🔍 Consider script revision to reduce production complexity")
            
        return actions if actions else ["✅ No critical production issues identified"]