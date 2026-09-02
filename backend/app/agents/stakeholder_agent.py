"""
Multi-Stakeholder Analysis Agent
Synthesizes existing agent data into role-specific perspectives for 8 production stakeholders.
No AI calls - pure data mapping and aggregation from existing agent results.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict

from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)

STAKEHOLDER_ROLES = [
    {"role": "studio_executive", "title": "Studio Executive", "icon": "🏢"},
    {"role": "director", "title": "Director", "icon": "🎬"},
    {"role": "producer", "title": "Producer", "icon": "🎥"},
    {"role": "legal_affairs", "title": "Legal Affairs", "icon": "⚖️"},
    {"role": "marketing_director", "title": "Marketing Director", "icon": "📣"},
    {"role": "insurance_underwriter", "title": "Insurance Underwriter", "icon": "🛡️"},
    {"role": "distributor", "title": "Distributor", "icon": "📦"},
    {"role": "cultural_consultant", "title": "Cultural Consultant", "icon": "🌍"},
]


class StakeholderAgent:
    """Synthesizes existing agent results into role-specific stakeholder perspectives."""

    def __init__(self):
        self.agent_type = "stakeholder"

    async def process_task(self, task: AgentTask) -> AgentResult:
        start_time = time.time()
        try:
            report_data = task.task_data.get("report_data", {})
            if not report_data:
                raise ValueError("No report data provided for stakeholder analysis")

            agent_results = report_data.get("agent_results", {})
            risk = report_data.get("risk_assessment", {})
            readiness = report_data.get("readiness_scores", {})
            scenes = report_data.get("scenes", [])
            characters = report_data.get("characters", [])
            scene_stats = report_data.get("scene_statistics", {})

            director_data = self._get_agent_data(agent_results, "director")
            research_data = self._get_agent_data(agent_results, "research")
            legal_data = self._get_agent_data(agent_results, "legal")
            continuity_data = self._get_agent_data(agent_results, "continuity")
            budget_data = self._get_agent_data(agent_results, "budget")
            cultural_data = self._get_agent_data(agent_results, "cultural")

            stakeholders = [
                self._studio_executive(risk, readiness, budget_data, research_data, legal_data),
                self._director(director_data, continuity_data, scenes, scene_stats),
                self._producer(risk, readiness, budget_data, continuity_data, scene_stats),
                self._legal_affairs(legal_data),
                self._marketing_director(characters, cultural_data, director_data, scene_stats),
                self._insurance_underwriter(risk, legal_data, continuity_data),
                self._distributor(risk, readiness, scene_stats, scenes),
                self._cultural_consultant(cultural_data),
            ]

            overall_score = readiness.get("overall", 0) if readiness else 0

            result_data = {
                "stakeholders": stakeholders,
                "overall_readiness": overall_score,
                "roles_analyzed": len(stakeholders),
            }

            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                confidence_score=0.90,
                processing_time=time.time() - start_time,
                data=result_data,
                metadata={"method": "agent_data_synthesis", "roles": len(stakeholders)},
            )

        except Exception as e:
            logger.error(f"Stakeholder analysis failed: {e}", exc_info=True)
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                error_message=str(e),
            )

    def _get_agent_data(self, agent_results: Dict, agent_name: str) -> Dict:
        result = agent_results.get(agent_name, {})
        if isinstance(result, dict):
            return result.get("data", {}) or {}
        return {}

    def _score_to_risk(self, score: float) -> str:
        if score >= 70:
            return "low"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "high"
        return "critical"

    def _score_to_label(self, score: float) -> str:
        if score >= 80:
            return "Strong"
        elif score >= 60:
            return "Moderate"
        elif score >= 40:
            return "Concerning"
        elif score >= 20:
            return "High Risk"
        return "Critical"

    def _generate_summary(self, role: str, score: float, concerns: list, findings: list) -> str:
        label = self._score_to_label(score)
        if concerns:
            return f"{label} readiness ({score}/100). {concerns[0]}."
        return f"{label} readiness ({score}/100). No major concerns detected."

    # ── Studio Executive ────────────────────────────────────────────────────

    def _studio_executive(self, risk, readiness, budget_data, research_data, legal_data):
        risk_score = risk.get("overall_risk_score", 50) if risk else 50
        legal_clearance = readiness.get("legal_clearance", 50) if readiness else 50
        budget_feasibility = readiness.get("budget_feasibility", 50) if readiness else 50

        score = round((100 - risk_score) * 0.4 + legal_clearance * 0.3 + budget_feasibility * 0.3)

        concerns = []
        if risk_score > 50:
            concerns.append(f"Overall risk score: {risk_score}/100")
        if legal_clearance < 60:
            concerns.append(f"Legal clearance at {legal_clearance}% - unresolved issues")
        if budget_feasibility < 60:
            concerns.append(f"Budget feasibility at {budget_feasibility}% - cost overruns likely")

        research = research_data or {}
        flagged = len(research.get("flagged_claims", []))
        if flagged > 0:
            concerns.append(f"{flagged} fact-check flagged claim(s) - accuracy risk")

        legal = legal_data or {}
        copyright_count = len(legal.get("copyright_risks", []))
        trademark_count = len(legal.get("trademark_issues", []))
        if copyright_count + trademark_count > 0:
            concerns.append(f"{copyright_count + trademark_count} IP clearance item(s) required")

        findings = []
        if budget_data:
            budget = budget_data.get("budget", {})
            if budget.get("total_estimated_budget"):
                findings.append({
                    "category": "Budget Estimate",
                    "severity": "info",
                    "items": [f"Estimated: {budget['total_estimated_budget']} ({budget.get('budget_level', 'unknown')} tier)"],
                })
        if risk and risk.get("risk_factors"):
            findings.append({
                "category": "Risk Factors",
                "severity": "warning" if risk_score > 50 else "info",
                "items": risk["risk_factors"][:5],
            })

        recommendations = []
        if legal_clearance < 70:
            recommendations.append("Resolve legal clearance items before greenlight")
        if risk_score > 50:
            recommendations.append("Address top risk factors to improve marketability")
        if budget_feasibility < 60:
            recommendations.append("Review budget with line producer for cost optimization")
        if not recommendations:
            recommendations.append("Script is in good shape for greenlight review")

        return {
            "role": "studio_executive", "title": "Studio Executive", "icon": "🏢",
            "overall_score": max(0, min(100, score)), "score_label": self._score_to_label(score),
            "risk_level": self._score_to_risk(100 - score),
            "key_concerns": concerns[:5], "findings": findings,
            "recommendations": recommendations,
            "summary": self._generate_summary("studio_executive", score, concerns, findings),
        }

    # ── Director ────────────────────────────────────────────────────────────

    def _director(self, director_data, continuity_data, scenes, scene_stats):
        director = director_data or {}
        continuity = continuity_data or {}

        claims = director.get("claims", [])
        total_claims = len(claims)
        high_priority = len([c for c in claims if c.get("type") in ("historical", "biographical")])

        char_issues = len(continuity.get("character_inconsistencies", []))
        timeline_issues = len(continuity.get("timeline_issues", []))

        issue_penalty = min(40, (char_issues + timeline_issues) * 5)
        research_need = min(30, high_priority * 10)
        score = max(0, 100 - issue_penalty - research_need)

        concerns = []
        if high_priority > 0:
            concerns.append(f"{high_priority} high-priority claim(s) need research (historical/biographical)")
        if char_issues > 0:
            concerns.append(f"{char_issues} character inconsistency(ies) to resolve")
        if timeline_issues > 0:
            concerns.append(f"{timeline_issues} timeline issue(s) detected")
        if total_claims > 10:
            concerns.append(f"{total_claims} total claims requiring verification")

        findings = []
        if claims:
            claims_by_type = defaultdict(list)
            for c in claims:
                claims_by_type[c.get("type", "unknown")].append(c.get("text", ""))
            for ctype, items in claims_by_type.items():
                findings.append({
                    "category": f"Claims: {ctype.title()}",
                    "severity": "warning" if ctype in ("historical", "biographical") else "info",
                    "items": [i[:80] for i in items[:3]],
                })
        if char_issues > 0:
            findings.append({
                "category": "Character Issues",
                "severity": "warning",
                "items": [i.get("description", "")[:80] for i in continuity.get("character_inconsistencies", [])[:3]],
            })

        recommendations = []
        if high_priority > 0:
            recommendations.append("Prioritize historical/biographical fact-checking")
        if char_issues > 0:
            recommendations.append("Review character arcs for consistency before shooting")
        recommendations.append("Review scene breakdown for creative opportunities")

        return {
            "role": "director", "title": "Director", "icon": "🎬",
            "overall_score": max(0, min(100, score)), "score_label": self._score_to_label(score),
            "risk_level": self._score_to_risk(100 - score),
            "key_concerns": concerns[:5], "findings": findings,
            "recommendations": recommendations,
            "summary": self._generate_summary("director", score, concerns, findings),
        }

    # ── Producer ────────────────────────────────────────────────────────────

    def _producer(self, risk, readiness, budget_data, continuity_data, scene_stats):
        risk_score = risk.get("overall_risk_score", 50) if risk else 50
        overall = readiness.get("overall", 50) if readiness else 50
        continuity_score = readiness.get("continuity", 50) if readiness else 50

        continuity = continuity_data or {}
        total_issues = continuity.get("continuity_summary", {}).get("total_issues", 0)

        score = round(overall * 0.5 + (100 - risk_score) * 0.3 + continuity_score * 0.2)

        concerns = []
        if risk_score > 50:
            concerns.append(f"Risk score {risk_score}/100 - mitigation plan needed")
        if total_issues > 5:
            concerns.append(f"{total_issues} continuity issues - rework during production")
        if overall < 60:
            concerns.append(f"Overall readiness {overall}% - production not yet feasible")

        cost_saving = budget_data.get("budget", {}).get("cost_saving_tips", []) if budget_data else []
        if cost_saving:
            concerns.append(f"{len(cost_saving)} cost-saving opportunity identified")

        findings = []
        if budget_data:
            budget = budget_data.get("budget", {})
            if budget.get("categories"):
                items = [f"{c['name']}: {c['estimated_cost']}" for c in budget["categories"][:4]]
                findings.append({"category": "Budget Breakdown", "severity": "info", "items": items})
        if risk and risk.get("recommended_actions"):
            findings.append({
                "category": "Risk Mitigation", "severity": "warning",
                "items": risk["recommended_actions"][:3],
            })

        recommendations = []
        if cost_saving:
            recommendations.append(f"Implement cost-saving: {cost_saving[0]}")
        if risk_score > 50:
            recommendations.append("Build contingency buffer (15-20%) into budget")
        recommendations.append("Schedule table read to identify production issues early")

        return {
            "role": "producer", "title": "Producer", "icon": "🎥",
            "overall_score": max(0, min(100, score)), "score_label": self._score_to_label(score),
            "risk_level": self._score_to_risk(100 - score),
            "key_concerns": concerns[:5], "findings": findings,
            "recommendations": recommendations,
            "summary": self._generate_summary("producer", score, concerns, findings),
        }

    # ── Legal Affairs ───────────────────────────────────────────────────────

    def _legal_affairs(self, legal_data):
        legal = legal_data or {}

        copyright_risks = legal.get("copyright_risks", [])
        trademark_issues = legal.get("trademark_issues", [])
        clearance_required = legal.get("clearance_required", [])
        privacy_concerns = legal.get("privacy_concerns", [])

        total_issues = len(copyright_risks) + len(trademark_issues) + len(clearance_required) + len(privacy_concerns)
        high_severity = len([i for i in copyright_risks + trademark_issues if i.get("severity") == "high"])

        issue_penalty = min(80, total_issues * 10 + high_severity * 15)
        score = max(0, 100 - issue_penalty)

        concerns = []
        if copyright_risks:
            concerns.append(f"{len(copyright_risks)} copyright risk(s) identified")
        if trademark_issues:
            concerns.append(f"{len(trademark_issues)} trademark issue(s) require clearance")
        if clearance_required:
            concerns.append(f"{len(clearance_required)} clearance item(s) pending")
        if privacy_concerns:
            concerns.append(f"{len(privacy_concerns)} privacy concern(s) flagged")

        findings = []
        if copyright_risks:
            items = [f"[{r.get('severity', 'medium')}] {r.get('content', r.get('description', ''))[:80]}" for r in copyright_risks[:4]]
            findings.append({"category": "Copyright Risks", "severity": "warning", "items": items})
        if trademark_issues:
            items = [f"[{r.get('severity', 'medium')}] {r.get('content', r.get('description', ''))[:80]}" for r in trademark_issues[:4]]
            findings.append({"category": "Trademark Issues", "severity": "warning", "items": items})
        if clearance_required:
            items = [c if isinstance(c, str) else str(c) for c in clearance_required[:4]]
            findings.append({"category": "Clearance Required", "severity": "info", "items": items})
        if privacy_concerns:
            items = [p if isinstance(p, str) else p.get("description", str(p)) for p in privacy_concerns[:4]]
            findings.append({"category": "Privacy Concerns", "severity": "warning", "items": items})

        cost = legal.get("estimated_clearance_cost", "Unknown")
        if cost and cost != "Unknown":
            findings.append({"category": "Estimated Cost", "severity": "info", "items": [f"Clearance budget: {cost}"]})

        recommendations = legal.get("legal_recommendations", [])
        if not recommendations:
            recommendations = ["No major legal issues detected"] if total_issues == 0 else ["Review flagged items with legal counsel"]

        return {
            "role": "legal_affairs", "title": "Legal Affairs", "icon": "⚖️",
            "overall_score": max(0, min(100, score)), "score_label": self._score_to_label(score),
            "risk_level": self._score_to_risk(100 - score),
            "key_concerns": concerns[:5], "findings": findings,
            "recommendations": recommendations[:5],
            "summary": self._generate_summary("legal_affairs", score, concerns, findings),
        }

    # ── Marketing Director ──────────────────────────────────────────────────

    def _marketing_director(self, characters, cultural_data, director_data, scene_stats):
        char_count = len(characters) if characters else 0
        leads = len([c for c in (characters or []) if c.get("character_type") == "lead"])
        scenes_count = scene_stats.get("total_scenes", 0) if scene_stats else 0

        cultural = cultural_data or {}
        sensitivity = cultural.get("cultural_analysis", {}).get("overall_sensitivity_score", 75)
        positive_repr = cultural.get("cultural_analysis", {}).get("positive_representations", [])

        cast_score = min(30, char_count * 3)
        repr_score = min(30, sensitivity)
        content_score = min(40, scenes_count * 2)
        score = round(cast_score + repr_score + content_score)

        concerns = []
        if sensitivity < 60:
            concerns.append(f"Cultural sensitivity score: {sensitivity}/100 - controversy risk")
        if leads < 2:
            concerns.append(f"Only {leads} lead character(s) - limited ensemble appeal")
        if char_count > 20:
            concerns.append(f"{char_count} characters - may confuse casual viewers")

        findings = []
        if characters:
            lead_names = [c.get("name", "?") for c in characters if c.get("character_type") == "lead"][:5]
            findings.append({
                "category": "Cast Profile", "severity": "info",
                "items": [f"Leads: {', '.join(lead_names)}", f"Total speaking roles: {char_count}"],
            })
        if positive_repr:
            findings.append({"category": "Positive Representations", "severity": "positive", "items": positive_repr[:3]})
        director = director_data or {}
        claims = director.get("claims", [])
        hooks = [c.get("text", "")[:60] for c in claims if c.get("type") in ("historical", "biographical")][:3]
        if hooks:
            findings.append({"category": "Story Hooks for Promotion", "severity": "info", "items": hooks})

        recommendations = []
        if sensitivity < 70:
            recommendations.append("Run focus group to test cultural reception")
        recommendations.append("Develop character-driven marketing campaign")
        if leads >= 2:
            recommendations.append("Leverage ensemble cast for social media content")
        recommendations.append("Highlight research-backed authenticity in press materials")

        return {
            "role": "marketing_director", "title": "Marketing Director", "icon": "📣",
            "overall_score": max(0, min(100, score)), "score_label": self._score_to_label(score),
            "risk_level": self._score_to_risk(100 - score),
            "key_concerns": concerns[:5], "findings": findings,
            "recommendations": recommendations[:5],
            "summary": self._generate_summary("marketing_director", score, concerns, findings),
        }

    # ── Insurance Underwriter ───────────────────────────────────────────────

    def _insurance_underwriter(self, risk, legal_data, continuity_data):
        risk_score = risk.get("overall_risk_score", 50) if risk else 50
        legal = legal_data or {}
        continuity = continuity_data or {}

        copyright_count = len(legal.get("copyright_risks", []))
        trademark_count = len(legal.get("trademark_issues", []))
        privacy_count = len(legal.get("privacy_concerns", []))
        char_issues = len(continuity.get("character_inconsistencies", []))

        liability_count = copyright_count + trademark_count + privacy_count
        total_risk_factors = len(risk.get("risk_factors", [])) if risk else 0

        liability_penalty = min(40, liability_count * 8)
        risk_penalty = min(40, risk_score * 0.4)
        issue_penalty = min(20, char_issues * 5)
        score = max(0, 100 - liability_penalty - risk_penalty - issue_penalty)

        concerns = []
        if risk_score > 60:
            concerns.append(f"Production risk score: {risk_score}/100 - elevated premium")
        if liability_count > 0:
            concerns.append(f"{liability_count} liability item(s) (IP, privacy)")
        if total_risk_factors > 3:
            concerns.append(f"{total_risk_factors} risk factors identified")

        findings = []
        if risk and risk.get("risk_factors"):
            findings.append({"category": "Risk Factors", "severity": "warning", "items": risk["risk_factors"][:5]})
        if liability_count > 0:
            items = []
            if copyright_count:
                items.append(f"{copyright_count} copyright risks")
            if trademark_count:
                items.append(f"{trademark_count} trademark issues")
            if privacy_count:
                items.append(f"{privacy_count} privacy concerns")
            findings.append({"category": "Liability Exposure", "severity": "warning", "items": items})

        recommendations = []
        if liability_count > 0:
            recommendations.append("Obtain E&O (Errors & Omissions) insurance coverage")
        if risk_score > 60:
            recommendations.append("Require stunt coordinator certification for action scenes")
        recommendations.append("Include production completion bond in insurance package")

        return {
            "role": "insurance_underwriter", "title": "Insurance Underwriter", "icon": "🛡️",
            "overall_score": max(0, min(100, score)), "score_label": self._score_to_label(score),
            "risk_level": self._score_to_risk(100 - score),
            "key_concerns": concerns[:5], "findings": findings,
            "recommendations": recommendations[:5],
            "summary": self._generate_summary("insurance_underwriter", score, concerns, findings),
        }

    # ── Distributor ─────────────────────────────────────────────────────────

    def _distributor(self, risk, readiness, scene_stats, scenes):
        risk_score = risk.get("overall_risk_score", 50) if risk else 50
        grade = readiness.get("grade", "C") if readiness else "C"
        overall = readiness.get("overall", 50) if readiness else 50

        day_scenes = scene_stats.get("day_scenes", 0) if scene_stats else 0
        night_scenes = scene_stats.get("night_scenes", 0) if scene_stats else 0
        total_scenes = scene_stats.get("total_scenes", len(scenes)) if scene_stats else len(scenes)

        grade_map = {"A+": 95, "A": 90, "B+": 80, "B": 70, "C+": 60, "C": 50, "D": 30, "F": 10}
        grade_score = grade_map.get(grade, 50)
        risk_factor = max(0, 100 - risk_score)
        score = round(grade_score * 0.5 + risk_factor * 0.3 + overall * 0.2)

        concerns = []
        if risk_score > 60:
            concerns.append(f"Risk score {risk_score}/100 may limit distribution channels")
        if grade in ("D", "F"):
            concerns.append(f"Grade '{grade}' - significant issues before release")
        if night_scenes > day_scenes:
            concerns.append("Night-heavy content - may affect TV broadcast windows")

        findings = []
        findings.append({
            "category": "Content Profile", "severity": "info",
            "items": [
                f"Total scenes: {total_scenes}",
                f"Day scenes: {day_scenes} | Night scenes: {night_scenes}",
                f"Readiness grade: {grade}",
            ],
        })
        if risk and risk.get("critical_issues"):
            items = [i.get("description", "")[:60] for i in risk["critical_issues"][:3]]
            if items:
                findings.append({"category": "Critical Issues", "severity": "warning", "items": items})

        recommendations = []
        if grade in ("D", "F"):
            recommendations.append("Resolve critical issues before seeking distribution deals")
        recommendations.append("Consider streaming-first release for niche content")
        if risk_score > 50:
            recommendations.append("Address risk factors to improve distribution terms")
        recommendations.append("Prepare international adaptation notes for global markets")

        return {
            "role": "distributor", "title": "Distributor", "icon": "📦",
            "overall_score": max(0, min(100, score)), "score_label": self._score_to_label(score),
            "risk_level": self._score_to_risk(100 - score),
            "key_concerns": concerns[:5], "findings": findings,
            "recommendations": recommendations[:5],
            "summary": self._generate_summary("distributor", score, concerns, findings),
        }

    # ── Cultural Consultant ─────────────────────────────────────────────────

    def _cultural_consultant(self, cultural_data):
        cultural = cultural_data or {}
        analysis = cultural.get("cultural_analysis", {})

        sensitivity = analysis.get("overall_sensitivity_score", 75)
        issues = analysis.get("issues", [])
        positive_repr = analysis.get("positive_representations", [])
        recommendations = analysis.get("recommendations", [])

        high_issues = len([i for i in issues if i.get("severity") == "high"])
        medium_issues = len([i for i in issues if i.get("severity") == "medium"])

        issue_penalty = min(60, high_issues * 20 + medium_issues * 8)
        bonus = min(20, len(positive_repr) * 5)
        score = max(0, min(100, sensitivity - issue_penalty + bonus))

        concerns = []
        if high_issues > 0:
            concerns.append(f"{high_issues} high-severity cultural issue(s) detected")
        if medium_issues > 0:
            concerns.append(f"{medium_issues} medium-severity cultural concern(s)")
        if sensitivity < 60:
            concerns.append(f"Overall sensitivity score: {sensitivity}/100")

        findings = []
        if issues:
            for issue in issues[:4]:
                findings.append({
                    "category": issue.get("category", "Cultural"),
                    "severity": issue.get("severity", "medium"),
                    "items": [issue.get("description", "")[:80], f"Impact: {issue.get('impact', 'N/A')[:50]}"],
                })
        if positive_repr:
            findings.append({
                "category": "Positive Representations",
                "severity": "positive",
                "items": positive_repr[:3],
            })

        if not recommendations:
            recommendations = ["No cultural issues detected - script handles representation well"] if len(issues) == 0 else ["Review flagged cultural issues with sensitivity consultant"]

        return {
            "role": "cultural_consultant", "title": "Cultural Consultant", "icon": "🌍",
            "overall_score": max(0, min(100, score)), "score_label": self._score_to_label(score),
            "risk_level": self._score_to_risk(100 - score),
            "key_concerns": concerns[:5], "findings": findings,
            "recommendations": recommendations[:5],
            "summary": self._generate_summary("cultural_consultant", score, concerns, findings),
        }
