"""
Budget Router - Production cost estimation endpoint
"""

import logging
import os
import json
import re
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory cache for tracking results
_budget_track_cache: Dict[str, Dict[str, Any]] = {}


class BudgetTrackRequest(BaseModel):
    """Request model for budget vs. actual tracking"""
    report_id: Optional[str] = Field(default=None, description="Report ID to generate tracking for")
    script_text: Optional[str] = Field(default=None, description="Script text (used if report_id not provided)")
    actuals: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional actual spend per category name. If omitted, realistic actuals are synthesized.",
    )
    currency: str = Field(default="USD", description="Currency code for display")


class BudgetRequest(BaseModel):
    """Request model for budget estimation"""
    script_text: str = Field(..., min_length=10, max_length=50000, description="Script content to estimate")


@router.post("/budget-estimate")
async def estimate_budget(request: BudgetRequest, fastapi_request: Request):
    """
    Estimate production budget from script content
    Uses Budget Agent with Gemini AI
    """
    
    try:
        from ..agents.budget_agent import BudgetAgent
        from ..models.agent_schemas import AgentTask
        from uuid import uuid4
        
        budget_agent = BudgetAgent()
        
        task = AgentTask(
            task_id=str(uuid4()),
            agent_type="budget",
            task_data={"script_text": request.script_text}
        )
        
        result = await budget_agent.process_task(task)
        
        if result.success:
            return {
                "success": True,
                "budget": result.data.get("budget", {}),
                "processing_time": result.processing_time
            }
        else:
            raise HTTPException(status_code=500, detail=result.error_message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget estimation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Budget estimation failed: {str(e)}")


# ─── Cost parsing helpers ────────────────────────────────────────────────────

_MULTIPLIERS = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}


def parse_cost_value(token: str) -> float:
    """Parse a single cost token like '$50,000' or '1.5M' into a float."""
    token = token.strip().replace("$", "").replace(",", "").strip()
    mult = 1.0
    if token and token[-1].upper() in _MULTIPLIERS:
        mult = _MULTIPLIERS[token[-1].upper()]
        token = token[:-1]
    try:
        return float(token) * mult
    except ValueError:
        return 0.0


def parse_cost_range(raw: str) -> Dict[str, float]:
    """Parse a cost string like '$50,000-100,000' or '$1.5M-5M' into min/mid/max."""
    if not raw:
        return {"min": 0.0, "mid": 0.0, "max": 0.0}
    matches = re.findall(r"\$?\s*[\d,]+(?:\.\d+)?\s*[KMB]?", raw, flags=re.IGNORECASE)
    values = [parse_cost_value(m) for m in matches]
    values = [v for v in values if v > 0]
    if not values:
        return {"min": 0.0, "mid": 0.0, "max": 0.0}
    if len(values) == 1:
        v = values[0]
        return {"min": v, "mid": v, "max": v}
    lo, hi = min(values), max(values)
    return {"min": lo, "mid": (lo + hi) / 2.0, "max": hi}


def _seed_from(report_id: str, category: str) -> int:
    """Stable seed so synthesized actuals are deterministic per report."""
    h = hashlib.sha256(f"{report_id}::{category}".encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def synthesize_actual(cat_name: str, planned_mid: float, report_id: str) -> float:
    """
    Deterministically synthesize a realistic 'actual' spend near the planned midpoint.
    Factor range ~0.78x - 1.22x so some categories land over and some under budget.
    """
    if planned_mid <= 0:
        return 0.0
    seed = _seed_from(report_id, cat_name)
    factor = 0.78 + (seed % 45) / 100.0  # 0.78 .. 1.22
    actual = planned_mid * factor
    return round(actual / 100.0) * 100.0


def _load_report_data(report_id: str) -> Optional[Dict[str, Any]]:
    """Load report data from file storage (mirrors other on-demand routers)."""
    report_file = f"data/reports/{report_id}.json"
    if os.path.exists(report_file):
        try:
            with open(report_file, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _heuristic_estimate(script_text: str) -> Dict[str, Any]:
    """
    Fallback budget estimate when Gemini is unavailable.
    Builds a category breakdown scaled by script size and slugline counts.
    """
    text = script_text or ""
    int_scenes = len(re.findall(r"\bINT\.?", text, flags=re.IGNORECASE))
    ext_scenes = len(re.findall(r"\bEXT\.?", text, flags=re.IGNORECASE))
    total_scenes = max(1, int_scenes + ext_scenes)
    night_scenes = len(re.findall(r"NIGHT|EVENING|DUSK|DAWN", text, flags=re.IGNORECASE))

    scale = total_scenes / 20.0  # normalize around a 20-scene script

    def band(base_low: float, base_high: float) -> str:
        lo = int(round(base_low * scale / 100.0) * 100)
        hi = int(round(base_high * scale / 100.0) * 100)
        return f"${lo:,}-{hi:,}"

    categories = [
        {
            "name": "Cast & Talent",
            "estimated_cost": band(30_000, 120_000),
            "confidence": 0.7,
            "line_items": [
                {"item": f"Principal cast (~{max(2, int(total_scenes / 3))} roles)", "cost": band(20_000, 80_000)},
                {"item": "Background extras", "cost": band(5_000, 25_000)},
            ],
            "notes": "Assumes indie SAG-AFTRA rates; union features scale 10x+.",
        },
        {
            "name": "Locations",
            "estimated_cost": band(15_000, 60_000),
            "confidence": 0.65,
            "line_items": [
                {"item": f"{int_scenes} interior setups", "cost": band(8_000, 30_000)},
                {"item": f"{ext_scenes} exterior setups", "cost": band(7_000, 30_000)},
            ],
            "notes": "Real locations cheaper than studio builds; permits extra.",
        },
        {
            "name": "Props & Set Dressing",
            "estimated_cost": band(8_000, 35_000),
            "confidence": 0.6,
            "line_items": [{"item": "Period/specialty props", "cost": band(4_000, 18_000)}],
            "notes": "Vehicles and tech props drive this category up.",
        },
        {
            "name": "VFX & Stunts",
            "estimated_cost": band(10_000, 80_000) if night_scenes else band(5_000, 40_000),
            "confidence": 0.55,
            "line_items": [{"item": f"{night_scenes} night/action scenes", "cost": band(5_000, 40_000)}],
            "notes": "CGI and stunt coordination; biggest wildcard.",
        },
        {
            "name": "Wardrobe & Makeup",
            "estimated_cost": band(6_000, 25_000),
            "confidence": 0.6,
            "line_items": [{"item": "Costume changes & prosthetics", "cost": band(3_000, 12_000)}],
            "notes": "Period costumes increase cost significantly.",
        },
        {
            "name": "Equipment & Crew",
            "estimated_cost": band(20_000, 70_000),
            "confidence": 0.75,
            "line_items": [
                {"item": "Camera/lighting rental", "cost": band(10_000, 35_000)},
                {"item": "Crew (approx 4 weeks)", "cost": band(10_000, 35_000)},
            ],
            "notes": "Standard indie package; scale with shoot days.",
        },
        {
            "name": "Other (Music, Catering, Travel)",
            "estimated_cost": band(12_000, 45_000),
            "confidence": 0.6,
            "line_items": [
                {"item": "Music licensing", "cost": band(5_000, 20_000)},
                {"item": "Catering & travel", "cost": band(7_000, 25_000)},
            ],
            "notes": "Score composition vs. licensed tracks varies widely.",
        },
    ]

    lows = []
    highs = []
    for c in categories:
        r = parse_cost_range(c["estimated_cost"])
        lows.append(r["min"])
        highs.append(r["max"])
    total_low = sum(lows)
    total_high = sum(highs)

    return {
        "categories": categories,
        "total_estimated_budget": f"${total_low:,}-{total_high:,}",
        "budget_level": "low" if total_high < 2_000_000 else "medium" if total_high < 10_000_000 else "high",
        "cost_saving_tips": [
            "Shoot consecutive scenes at the same location to cut company moves.",
            "Limit night shoots to reduce overtime and lighting costs.",
            "Use practical locations instead of studio builds where possible.",
        ],
    }


async def _get_estimate(script_text: str) -> Dict[str, Any]:
    """Get a budget estimate, preferring Gemini, falling back to heuristic."""
    try:
        from ..agents.budget_agent import BudgetAgent
        from ..models.agent_schemas import AgentTask

        agent = BudgetAgent()
        task = AgentTask(task_id=str(uuid4()), agent_type="budget", task_data={"script_text": script_text})
        result = await agent.process_task(task)
        if result.success and result.data and result.data.get("budget", {}).get("categories"):
            return result.data["budget"]
    except Exception as e:
        logger.warning(f"Gemini budget estimate unavailable, using heuristic: {e}")
    return _heuristic_estimate(script_text)


def _build_tracking(
    report_id: str,
    estimate: Dict[str, Any],
    actuals: Optional[Dict[str, float]],
    currency: str,
) -> Dict[str, Any]:
    """Build the budget vs. actual tracking structure from an estimate."""
    categories_in = estimate.get("categories", [])
    category_rows: List[Dict[str, Any]] = []
    total_planned = 0.0
    total_actual = 0.0
    alerts: List[str] = []
    recommendations: List[str] = []

    for cat in categories_in:
        name = cat.get("name", "Unknown")
        rng = parse_cost_range(cat.get("estimated_cost", ""))
        planned_mid = rng["mid"]
        if actuals and name in actuals:
            actual = float(actuals[name])
            data_source = "provided"
        else:
            actual = synthesize_actual(name, planned_mid, report_id)
            data_source = "estimated"
        variance = actual - planned_mid
        variance_pct = (variance / planned_mid * 100.0) if planned_mid > 0 else 0.0
        if variance_pct > 5.0:
            status = "over"
        elif variance_pct < -5.0:
            status = "under"
        else:
            status = "on_track"

        total_planned += planned_mid
        total_actual += actual

        if status == "over":
            alerts.append(f"{name}: over budget by ${abs(variance):,.0f} ({variance_pct:+.0f}%)")
            recommendations.append(f"Review {name} - consider renegotiating rates or trimming scope.")
        elif status == "under":
            recommendations.append(f"{name} is under budget (${abs(variance):,.0f} saved) - reallocate to over-budget areas.")

        category_rows.append({
            "name": name,
            "planned_min": rng["min"],
            "planned_mid": planned_mid,
            "planned_max": rng["max"],
            "planned_range": cat.get("estimated_cost", ""),
            "actual": actual,
            "variance": variance,
            "variance_pct": variance_pct,
            "status": status,
            "confidence": cat.get("confidence", 0.0),
            "line_items": cat.get("line_items", []),
            "notes": cat.get("notes", ""),
            "data_source": data_source,
        })

    total_variance = total_actual - total_planned
    total_variance_pct = (total_variance / total_planned * 100.0) if total_planned > 0 else 0.0
    overall_status = "over" if total_variance_pct > 5.0 else "under" if total_variance_pct < -5.0 else "on_track"

    if overall_status == "over":
        alerts.insert(0, f"TOTAL budget overrun: ${abs(total_variance):,.0f} ({total_variance_pct:+.0f}%)")
    elif overall_status == "under":
        alerts.insert(0, f"TOTAL under budget by ${abs(total_variance):,.0f} ({total_variance_pct:+.0f}%)")

    tips = estimate.get("cost_saving_tips", [])
    recommendations.extend(tips)

    return {
        "currency": currency,
        "total_planned": round(total_planned, 2),
        "total_actual": round(total_actual, 2),
        "total_variance": round(total_variance, 2),
        "total_variance_pct": round(total_variance_pct, 2),
        "overall_status": overall_status,
        "categories": category_rows,
        "alerts": alerts,
        "recommendations": recommendations,
        "cost_saving_tips": tips,
        "budget_level": estimate.get("budget_level", "unknown"),
        "total_estimated_budget": estimate.get("total_estimated_budget", ""),
    }


# ─── Tracking endpoint (new) ──────────────────────────────────────────────────

@router.post("/budget/track", response_model=dict)
async def track_budget(request: BudgetTrackRequest):
    """
    Generate a Budget vs. Actual tracking report for a script/report.
    Compares the AI/estimated budget against (synthesized or provided) actual spend.
    """
    start_time = datetime.now(timezone.utc)
    tracking_id = str(uuid4())
    report_id = request.report_id or f"adhoc_{tracking_id[:8]}"

    try:
        script_text = request.script_text
        if not script_text and request.report_id:
            report_data = _load_report_data(request.report_id)
            if report_data:
                script_text = report_data.get("script_text", "")

        if not script_text or len(script_text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="No script text available for budget tracking. Provide script_text or a valid report_id.",
            )

        estimate = await _get_estimate(script_text)
        tracking = _build_tracking(report_id, estimate, request.actuals, request.currency)
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        payload = {
            "tracking_id": tracking_id,
            "report_id": report_id,
            "success": True,
            **tracking,
            "processing_time": processing_time,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }

        _budget_track_cache[tracking_id] = payload
        _budget_track_cache[report_id] = payload

        return payload

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget tracking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Budget tracking failed: {str(e)}")


@router.get("/budget/track/{tracking_id}")
async def get_budget_track(tracking_id: str):
    """Get a cached budget tracking report by ID"""
    track = _budget_track_cache.get(tracking_id)
    if not track:
        raise HTTPException(status_code=404, detail="Budget tracking report not found")
    return track


@router.get("/budget/track/report/{report_id}")
async def get_budget_track_by_report(report_id: str):
    """Get the latest budget tracking report for a report"""
    track = _budget_track_cache.get(report_id)
    if not track:
        raise HTTPException(status_code=404, detail="No budget tracking found for this report")
    return track
