"""
Script Comparison Router - Scene/character-aware diff between two script versions.

Builds on the existing line-level diff (version_control) by adding a higher-level
comparison: scene additions/removals/modifications, character changes, and a
structured summary. Useful for screenwriters iterating on drafts.
"""

import logging
import os
import json
import difflib
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class ScriptCompareRequest(BaseModel):
    script_a: Optional[str] = Field(default=None, description="First script text")
    script_b: Optional[str] = Field(default=None, description="Second script text")
    report_id_a: Optional[str] = Field(default=None, description="Report ID for first script")
    report_id_b: Optional[str] = Field(default=None, description="Report ID for second script")
    label_a: str = "Version A"
    label_b: str = "Version B"


def _load_script(script: Optional[str], report_id: Optional[str]) -> str:
    if script and len(script.strip()) >= 10:
        return script
    if report_id:
        report_file = f"data/reports/{report_id}.json"
        if os.path.exists(report_file):
            with open(report_file, "r") as f:
                data = json.load(f)
            txt = data.get("script_text", "")
            if txt:
                return txt
    return ""


def _line_diff(a: str, b: str) -> Dict[str, Any]:
    a_lines = a.splitlines()
    b_lines = b.splitlines()
    diff_text = "\n".join(difflib.unified_diff(a_lines, b_lines, lineterm="", n=2))
    added = sum(1 for l in b_lines if l not in set(a_lines))  # rough count
    removed = sum(1 for l in a_lines if l not in set(b_lines))
    # More accurate added/removed via diff opcodes
    added_n = removed_n = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a_lines, b_lines).get_opcodes():
        if tag in ("replace", "insert"):
            added_n += j2 - j1
        if tag in ("replace", "delete"):
            removed_n += i2 - i1
    similarity = difflib.SequenceMatcher(None, a, b).ratio() * 100
    return {
        "diff": diff_text,
        "added_lines": added_n,
        "removed_lines": removed_n,
        "similarity_percentage": round(similarity, 1),
    }


def _scene_key(scene: Dict[str, Any]) -> str:
    return str(scene.get("scene_number", 0))


def _compare_scenes(scenes_a: List[Dict], scenes_b: List[Dict]) -> List[Dict[str, Any]]:
    map_a = {_scene_key(s): s for s in scenes_a}
    map_b = {_scene_key(s): s for s in scenes_b}
    all_keys = sorted(set(map_a) | set(map_b), key=lambda k: int(k) if k.isdigit() else 0)

    result = []
    for k in all_keys:
        a = map_a.get(k)
        b = map_b.get(k)
        title = (b or a).get("title", f"Scene {k}")
        location = (b or a).get("location", "")
        chars_a = set(c.upper() for c in (a or {}).get("characters_present", []))
        chars_b = set(c.upper() for c in (b or {}).get("characters_present", []))
        if a and not b:
            result.append({
                "status": "removed", "scene_number": int(k) if k.isdigit() else k,
                "title": title, "location": location,
                "characters_a": sorted(chars_a), "characters_b": [],
                "change": "Scene removed in new version",
            })
        elif b and not a:
            result.append({
                "status": "added", "scene_number": int(k) if k.isdigit() else k,
                "title": title, "location": location,
                "characters_a": [], "characters_b": sorted(chars_b),
                "change": "New scene added",
            })
        else:
            changed = []
            if chars_a != chars_b:
                added_c = chars_b - chars_a
                removed_c = chars_a - chars_b
                if added_c:
                    changed.append(f"Characters added: {', '.join(sorted(added_c))}")
                if removed_c:
                    changed.append(f"Characters removed: {', '.join(sorted(removed_c))}")
            if (a or {}).get("location", "") != (b or {}).get("location", ""):
                changed.append(f"Location changed: {(a or {}).get('location','')} → {(b or {}).get('location','')}")
            if (a or {}).get("time_of_day", "") != (b or {}).get("time_of_day", ""):
                changed.append(f"Time changed: {(a or {}).get('time_of_day','')} → {(b or {}).get('time_of_day','')}")
            result.append({
                "status": "modified" if changed else "unchanged",
                "scene_number": int(k) if k.isdigit() else k,
                "title": title, "location": location,
                "characters_a": sorted(chars_a), "characters_b": sorted(chars_b),
                "change": "; ".join(changed) if changed else "No structural changes",
            })
    return result


@router.post("/script-compare")
async def compare_scripts(request: ScriptCompareRequest):
    """Compare two scripts at scene + character + line level."""
    start_time = datetime.now(timezone.utc)
    compare_id = str(uuid4())

    try:
        script_a = _load_script(request.script_a, request.report_id_a)
        script_b = _load_script(request.script_b, request.report_id_b)

        if len(script_a.strip()) < 10 or len(script_b.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Provide two scripts (via script_a/script_b or report_id_a/report_id_b).",
            )

        from ..services.scene_parser import parse_screenplay
        scenes_a, _ = parse_screenplay(script_a)
        scenes_b, _ = parse_screenplay(script_b)
        scenes_a = [{"scene_number": s.scene_number, "title": s.title, "location": s.location,
                     "time_of_day": s.time_of_day, "characters_present": s.characters_present} for s in scenes_a]
        scenes_b = [{"scene_number": s.scene_number, "title": s.title, "location": s.location,
                     "time_of_day": s.time_of_day, "characters_present": s.characters_present} for s in scenes_b]

        scenes = _compare_scenes(scenes_a, scenes_b)

        chars_a = set()
        chars_b = set()
        for s in scenes_a:
            chars_a.update(c.upper() for c in s["characters_present"])
        for s in scenes_b:
            chars_b.update(c.upper() for c in s["characters_present"])

        characters = {
            "added": sorted(chars_b - chars_a),
            "removed": sorted(chars_a - chars_b),
            "common": sorted(chars_a & chars_b),
        }

        line_diff = _line_diff(script_a, script_b)

        summary = {
            "similarity_pct": line_diff["similarity_percentage"],
            "added_lines": line_diff["added_lines"],
            "removed_lines": line_diff["removed_lines"],
            "scenes_added": sum(1 for s in scenes if s["status"] == "added"),
            "scenes_removed": sum(1 for s in scenes if s["status"] == "removed"),
            "scenes_modified": sum(1 for s in scenes if s["status"] == "modified"),
            "scenes_unchanged": sum(1 for s in scenes if s["status"] == "unchanged"),
            "characters_added": len(characters["added"]),
            "characters_removed": len(characters["removed"]),
        }

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        return {
            "compare_id": compare_id,
            "label_a": request.label_a,
            "label_b": request.label_b,
            "summary": summary,
            "scenes": scenes,
            "characters": characters,
            "line_diff": line_diff,
            "processing_time": processing_time,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Script comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Script comparison failed: {str(e)}")
