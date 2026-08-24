"""
Export Router - PDF, JSON, CSV export and report sharing
"""

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

router = APIRouter()


class ExportRequestModel(BaseModel):
    script_id: str
    format: str = "pdf"
    sections: List[str] = ["overview", "claims", "legal", "continuity"]
    include_comments: bool = True


class ShareLinkRequest(BaseModel):
    script_id: str
    expires_in_hours: int = 72


class ShareLinkResponse(BaseModel):
    share_url: str
    token: str
    expires_at: str


# In-memory storage
_export_store: Dict[str, Dict[str, Any]] = {}
_share_tokens: Dict[str, Dict[str, Any]] = {}
_report_cache: Dict[str, Dict[str, Any]] = {}


def cache_report(script_id: str, report_data: Dict[str, Any]):
    """Cache report data for exports and sharing"""
    _report_cache[script_id] = report_data


@router.post("/export")
async def create_export(request: ExportRequestModel, user_id: str = Query("default-user")):
    """Create a new export request and generate the file"""
    export_id = str(uuid4())
    
    # Get cached report data
    report_data = _report_cache.get(request.script_id, {
        "script_id": request.script_id,
        "risk_score": 45,
        "risk_level": "medium",
        "claims": [],
        "agent_results": {},
    })

    # Create exports directory
    os.makedirs("data/exports", exist_ok=True)

    filename = f"{export_id}.{request.format}"
    filepath = os.path.join("data/exports", filename)

    if request.format == "json":
        export_content = {
            "export_id": export_id,
            "script_id": request.script_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report": report_data,
            "sections": request.sections,
        }
        with open(filepath, "w") as f:
            json.dump(export_content, f, indent=2, default=str)
        content_type = "application/json"

    elif request.format == "csv":
        lines = ["Section,Category,Status,Details\n"]
        
        # Risk info
        risk_score = report_data.get("risk_score", report_data.get("risk_assessment", {}).get("overall_risk_score", 0))
        risk_level = report_data.get("risk_level", report_data.get("risk_assessment", {}).get("risk_level", "unknown"))
        lines.append(f"Overview,Risk Score,{risk_level},{risk_score}%\n")
        
        # Claims
        claims = report_data.get("claims", [])
        for claim in claims:
            text = claim.get("text", "N/A")[:50]
            verdict = claim.get("verdict", "unknown")
            lines.append(f"Claim,Fact Check,{verdict},{text}\n")
        
        # Agent results
        agents = report_data.get("agent_results", {})
        for name, result in agents.items():
            success = result.get("success", False) if isinstance(result, dict) else getattr(result, "success", False)
            confidence = result.get("confidence_score", 0) if isinstance(result, dict) else getattr(result, "confidence_score", 0)
            lines.append(f"Agent,{name},{'Success' if success else 'Failed'},{confidence*100:.0f}% confidence\n")
        
        with open(filepath, "w") as f:
            f.writelines(lines)
        content_type = "text/csv"

    else:  # pdf/txt
        risk_score = report_data.get("risk_score", report_data.get("risk_assessment", {}).get("overall_risk_score", 0))
        risk_level = report_data.get("risk_level", report_data.get("risk_assessment", {}).get("risk_level", "unknown"))
        claims = report_data.get("claims", [])
        
        txt_content = f"""
{'='*60}
        GREENLIT AI - SCRIPT ANALYSIS REPORT
{'='*60}

Report ID:     {export_id}
Script ID:     {request.script_id}
Generated:     {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
Sections:      {', '.join(request.sections)}

{'='*60}
                    RISK ASSESSMENT
{'='*60}

Overall Risk Score:  {risk_score}%
Risk Level:          {risk_level.upper()}

{'='*60}
                    CLAIMS ANALYSIS
{'='*60}

Total Claims Found:  {len(claims)}

"""
        for i, claim in enumerate(claims, 1):
            text = claim.get("text", "N/A")
            verdict = claim.get("verdict", "unknown")
            confidence = claim.get("confidence", 0)
            txt_content += f"  Claim {i}: {text[:80]}...\n"
            txt_content += f"  Verdict: {verdict} | Confidence: {confidence*100:.0f}%\n\n"

        txt_content += f"""
{'='*60}
                    AGENT PERFORMANCE
{'='*60}

"""
        agents = report_data.get("agent_results", {})
        for name, result in agents.items():
            if isinstance(result, dict):
                success = result.get("success", False)
                conf = result.get("confidence_score", 0)
                time_s = result.get("processing_time", 0)
            else:
                success = getattr(result, "success", False)
                conf = getattr(result, "confidence_score", 0)
                time_s = getattr(result, "processing_time", 0)
            status = "SUCCESS" if success else "FAILED"
            txt_content += f"  {name.upper():15s} | {status:8s} | Confidence: {conf*100:5.1f}% | Time: {time_s:.1f}s\n"

        txt_content += f"""
{'='*60}
              Generated by GreenLit AI
              https://greenlit-ai.com
{'='*60}
"""
        with open(filepath, "w") as f:
            f.write(txt_content)
        content_type = "text/plain"
        # Keep .txt extension for readability
        filename = f"{export_id}.txt"
        filepath = os.path.join("data/exports", filename)

    _export_store[export_id] = {
        "export_id": export_id,
        "script_id": request.script_id,
        "status": "completed",
        "format": request.format,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "export_id": export_id,
        "status": "completed",
        "format": request.format,
        "download_url": f"/api/export/download/{filename}",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/export/{export_id}")
async def get_export_status(export_id: str):
    """Get export status"""
    if export_id not in _export_store:
        raise HTTPException(status_code=404, detail="Export not found")
    return _export_store[export_id]


@router.get("/export/download/{filename}")
async def download_export(filename: str):
    """Download an exported file"""
    filepath = os.path.join("data/exports", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Export file not found")

    ext = os.path.splitext(filename)[1]
    media_types = {
        ".txt": "text/plain",
        ".json": "application/json",
        ".csv": "text/csv",
    }
    media_type = media_types.get(ext, "text/plain")

    return FileResponse(
        filepath, 
        filename=filename, 
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/exports")
async def list_exports(user_id: str = Query("default-user")):
    """List recent exports"""
    exports = list(_export_store.values())[-10:]
    return {"exports": exports}


# ─── Share Link Endpoints ────────────────────────────────────────────────────

@router.post("/share")
async def create_share_link(request: ShareLinkRequest):
    """Create a shareable link for a report"""
    token = str(uuid4())[:8]
    expires_at = datetime.now(timezone.utc).timestamp() + (request.expires_in_hours * 3600)

    _share_tokens[token] = {
        "script_id": request.script_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "access_count": 0,
        "report_data": _report_cache.get(request.script_id, {}),
    }

    return ShareLinkResponse(
        share_url=f"/share/{token}",
        token=token,
        expires_at=datetime.fromtimestamp(expires_at).isoformat(),
    )


@router.get("/share/{token}")
async def get_shared_report(token: str):
    """Access a shared report via token"""
    share_data = _share_tokens.get(token)
    if not share_data:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    if datetime.now(timezone.utc).timestamp() > share_data["expires_at"]:
        del _share_tokens[token]
        raise HTTPException(status_code=410, detail="Share link has expired")

    share_data["access_count"] += 1
    
    report = share_data.get("report_data", {})
    return {
        "script_id": share_data["script_id"],
        "created_at": share_data["created_at"],
        "expires_at": datetime.fromtimestamp(share_data["expires_at"]).isoformat(),
        "access_count": share_data["access_count"],
        "report": report,
    }


@router.delete("/share/{token}")
async def revoke_share_link(token: str):
    """Revoke a share link"""
    if token in _share_tokens:
        del _share_tokens[token]
    return {"message": "Share link revoked"}
