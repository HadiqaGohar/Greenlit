"""
Services Package - Centralized business logic and utility helpers
"""

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Sample report data for instant zero-friction demos
SAMPLE_REPORTS = {
    "sample-action-thriller": {
        "title": "Urban Strike",
        "risk_score": 78.0,
        "risk_level": "high",
        "script_text": "INT. ABANDONED WAREHOUSE - NIGHT\n\nSARAH CHEN (30s) checks her vintage Rolex Submariner. We have four minutes before LAPD responds.\n\nEXT. DOWNTOWN LOS ANGELES - CONTINUOUS\n\nPolice cruisers race down Spring Street past the Walt Disney Concert Hall, designed by Frank Gehry.",
        "claims": [
            {
                "id": "claim_sample_1",
                "text": "Average LAPD emergency response time in Downtown LA is 4 minutes",
                "type": "factual",
                "verdict": "flagged",
                "confidence": 0.88,
                "sources": [
                    {"title": "LAPD Response Time Statistics 2023", "url": "https://www.lapdonline.org/reports", "credibility": 0.95},
                    {"title": "LA City Emergency Response Audit", "url": "https://controller.lacity.gov", "credibility": 0.9}
                ],
                "note": "Actual LAPD priority response time averages 6.2 minutes.",
                "location": "Scene 1, line 3"
            },
            {
                "id": "claim_sample_2",
                "text": "Walt Disney Concert Hall was designed by Frank Gehry",
                "type": "factual",
                "verdict": "verified",
                "confidence": 0.98,
                "sources": [
                    {"title": "Los Angeles Conservancy", "url": "https://www.laconservancy.org/locations/walt-disney-concert-hall", "credibility": 0.95}
                ],
                "note": "Verified: Completed in 2003 by architect Frank Gehry.",
                "location": "Scene 2, line 2"
            },
            {
                "id": "claim_sample_3",
                "text": "Rolex Submariner reference in dialogue and close-up",
                "type": "licensing",
                "verdict": "flagged",
                "confidence": 0.92,
                "sources": [
                    {"title": "Rolex Trademark Guidelines", "url": "https://www.rolex.com", "credibility": 0.95}
                ],
                "note": "Trademark clearance required for prominent logo depiction in prop.",
                "location": "Scene 1, line 2"
            }
        ],
        "scenes": [
            {"scene_number": 1, "heading": "INT. ABANDONED WAREHOUSE - NIGHT", "location": "ABANDONED WAREHOUSE", "time": "NIGHT", "characters": ["SARAH CHEN", "MARCUS"], "page_length": 1.2},
            {"scene_number": 2, "heading": "EXT. DOWNTOWN LOS ANGELES - CONTINUOUS", "location": "DOWNTOWN LOS ANGELES", "time": "NIGHT", "characters": ["POLICE UNITS"], "page_length": 0.8}
        ],
        "characters": [
            {"name": "SARAH CHEN", "role": "Team Leader", "dialogue_count": 8, "scenes": [1]},
            {"name": "MARCUS", "role": "Demolitions Expert", "dialogue_count": 4, "scenes": [1]}
        ]
    },
    "sample-period-drama": {
        "title": "The Gilded Cage",
        "risk_score": 62.0,
        "risk_level": "medium",
        "script_text": "INT. VICTORIAN PARLOR - 1885 - EVENING\n\nELEANOR (20s) adjusts her corset, looking out at the gaslit London streets. A copy of Bram Stoker's Dracula rests on the mahogany table.",
        "claims": [
            {
                "id": "claim_period_1",
                "text": "Dracula novel on table in 1885",
                "type": "historical",
                "verdict": "flagged",
                "confidence": 0.95,
                "sources": [
                    {"title": "British Library Literary Timeline", "url": "https://www.bl.uk", "credibility": 0.98}
                ],
                "note": "Anachronism: Bram Stoker's Dracula was published in 1897, 12 years after this scene.",
                "location": "Scene 1"
            }
        ],
        "scenes": [
            {"scene_number": 1, "heading": "INT. VICTORIAN PARLOR - 1885 - EVENING", "location": "VICTORIAN PARLOR", "time": "EVENING", "characters": ["ELEANOR"], "page_length": 1.0}
        ],
        "characters": [
            {"name": "ELEANOR", "role": "Protagonist", "dialogue_count": 5}
        ]
    },
    "sample-sci-fi": {
        "title": "Quantum Horizon",
        "risk_score": 45.0,
        "risk_level": "low",
        "script_text": "INT. STARSHIP BRIDGE - DEEP SPACE\n\nCOMMANDER VANCE monitors the Alcubierre warp drive fluctuation.",
        "claims": [
            {
                "id": "claim_scifi_1",
                "text": "Alcubierre warp metric requires negative mass-energy",
                "type": "scientific",
                "verdict": "verified",
                "confidence": 0.9,
                "sources": [
                    {"title": "NASA Breakthrough Propulsion Physics", "url": "https://www.nasa.gov", "credibility": 0.95}
                ],
                "note": "Accurate theoretical physics formulation.",
                "location": "Scene 1"
            }
        ],
        "scenes": [
            {"scene_number": 1, "heading": "INT. STARSHIP BRIDGE - DEEP SPACE", "location": "STARSHIP BRIDGE", "time": "CONTINUOUS", "characters": ["COMMANDER VANCE"], "page_length": 1.0}
        ],
        "characters": [
            {"name": "COMMANDER VANCE", "role": "Captain", "dialogue_count": 6}
        ]
    }
}


def load_report_data(report_id: str, orchestrator: Any = None) -> Optional[Dict[str, Any]]:
    """
    Safely load report dictionary from:
    1. In-memory orchestrator cache
    2. Disk file storage (with 0-byte/corruption protection)
    3. Sample fallback
    """
    # 1. Check in-memory orchestrator cache
    if orchestrator and hasattr(orchestrator, 'recent_reports'):
        report_obj = orchestrator.recent_reports.get(report_id)
        if report_obj:
            return _dump_orchestrator_report(report_obj)
    
    # 2. Check disk file storage safely
    report_file = f"data/reports/{report_id}.json"
    if os.path.exists(report_file):
        try:
            if os.path.getsize(report_file) > 0:
                with open(report_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data:
                        return data
        except Exception as e:
            logger.warning(f"Error reading report file {report_file}: {e}")
    
    # 3. Check sample fallback
    if report_id in SAMPLE_REPORTS or report_id.startswith("sample-") or "sample" in report_id:
        sample = SAMPLE_REPORTS.get(report_id, SAMPLE_REPORTS["sample-action-thriller"])
        return {
            "report_id": report_id,
            "status": "completed",
            "script_text": sample["script_text"],
            "claims": sample.get("claims", []),
            "scenes": sample.get("scenes", []),
            "characters": sample.get("characters", []),
            "risk_assessment": {
                "overall_risk_score": sample.get("risk_score", 50.0),
                "risk_level": sample.get("risk_level", "medium")
            },
            "agent_results": {}
        }
    
    return None


def _dump_orchestrator_report(report_obj: Any) -> Dict[str, Any]:
    """Extract dictionary from OrchestratorReport or MockReport"""
    if isinstance(report_obj, dict):
        return report_obj
    
    return {
        "report_id": getattr(report_obj, 'report_id', ''),
        "timestamp": report_obj.timestamp.isoformat() if hasattr(getattr(report_obj, 'timestamp', None), 'isoformat') else str(getattr(report_obj, 'timestamp', '')),
        "script_text": getattr(report_obj, 'script_text', '') or "",
        "scenes": getattr(report_obj, 'scenes', []) or [],
        "characters": getattr(report_obj, 'characters', []) or [],
        "risk_assessment": {
            "overall_risk_score": getattr(getattr(report_obj, 'risk_assessment', None), 'overall_risk_score', 50.0),
            "risk_level": getattr(getattr(report_obj, 'risk_assessment', None), 'risk_level', "medium")
        },
        "agent_results": getattr(report_obj, 'agent_results', {}) or {}
    }