"""
Export Router - PDF, JSON, CSV export and report sharing
"""

import os
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.colors import HexColor

logger = logging.getLogger(__name__)
router = APIRouter()


class ExportRequestModel(BaseModel):
    script_id: str
    format: str = "pdf"
    sections: List[str] = ["overview", "claims", "legal", "continuity"]
    include_comments: bool = True
    report_data: Optional[Dict[str, Any]] = None


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


def _normalize_report_for_export(raw: Dict[str, Any], script_id: str) -> Dict[str, Any]:
    """Extract a consistent report shape from various report structures.

    Handles both on-disk report files, cached orchestrator reports, and
    frontend-supplied report objects (e.g. sample reports) so that JSON/CSV
    exports are populated regardless of where the report originated.
    """
    risk = raw.get("risk_assessment", {}) or {}
    risk_score = raw.get("risk_score", risk.get("overall_risk_score", 0))
    risk_level = raw.get("risk_level", risk.get("risk_level", "unknown"))

    # Claims may live at the top level or nested under an agent result.
    claims = raw.get("claims")
    if not claims:
        for res in (raw.get("agent_results", {}) or {}).values():
            data = res.get("data", {}) if isinstance(res, dict) else {}
            if isinstance(data, dict) and data.get("claims"):
                claims = data["claims"]
                break
    if not claims:
        claims = []

    return {
        "script_id": raw.get("report_id") or raw.get("script_id") or script_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "claims": claims,
        "agent_results": raw.get("agent_results", {}) or {},
    }


@router.post("/export")
async def create_export(request: ExportRequestModel, user_id: str = Query("default-user")):
    """Create a new export request and generate the file"""
    export_id = str(uuid4())
    
    # Resolve report data: explicit payload > in-memory cache > disk file > live orchestrator cache.
    raw_data = request.report_data
    if not raw_data:
        raw_data = _report_cache.get(request.script_id)
    if not raw_data:
        report_file = os.path.join("data/reports", f"{request.script_id}.json")
        if os.path.exists(report_file):
            try:
                with open(report_file, "r") as f:
                    raw_data = json.load(f)
            except Exception:
                raw_data = None
    if not raw_data:
        try:
            app_orchestrator = getattr(request.app.state, 'orchestrator', None)
            if app_orchestrator and hasattr(app_orchestrator, "recent_reports"):
                raw_data = app_orchestrator.recent_reports.get(request.script_id)
        except Exception:
            raw_data = None
    if not raw_data:
        raise HTTPException(
            status_code=404,
            detail="Report data not found. Analyze the script (or open a saved report) before exporting.",
        )

    # Normalize report data into the shape used by the exporters.
    report_data = _normalize_report_for_export(raw_data, request.script_id)

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

    elif request.format == "pdf":
        risk_score = report_data.get("risk_score", report_data.get("risk_assessment", {}).get("overall_risk_score", 0))
        risk_level = report_data.get("risk_level", report_data.get("risk_assessment", {}).get("risk_level", "unknown"))
        claims = report_data.get("claims", [])

        GREEN = HexColor("#16a34a")
        RED = HexColor("#dc2626")
        ORANGE = HexColor("#f59e0b")
        GRAY = HexColor("#6b7280")

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=22, textColor=GREEN, spaceAfter=6)
        heading_style = ParagraphStyle("Heading2", parent=styles["Heading2"], fontSize=14, textColor=HexColor("#1e293b"), spaceBefore=16, spaceAfter=8)
        body_style = ParagraphStyle("Body2", parent=styles["BodyText"], fontSize=10, leading=14, textColor=HexColor("#334155"))
        small_style = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=9, leading=12, textColor=GRAY)
        header_cell_style = ParagraphStyle(
            "HeaderCell", parent=styles["Normal"], fontSize=9, leading=11,
            textColor=HexColor("#ffffff"), fontName="Helvetica-Bold",
        )
        body_cell_style = ParagraphStyle(
            "BodyCell", parent=styles["Normal"], fontSize=9, leading=11,
            textColor=HexColor("#334155"),
        )

        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.6*inch, bottomMargin=0.6*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
        story = []

        story.append(Paragraph("GREENLIT AI", title_style))
        story.append(Paragraph("Script Analysis Report", ParagraphStyle("Sub", parent=styles["Normal"], fontSize=12, textColor=GRAY, spaceAfter=12)))
        story.append(HRFlowable(width="100%", color=GREEN, thickness=2))
        story.append(Spacer(1, 12))

        story.append(Paragraph(f"<b>Report ID:</b> {export_id}", body_style))
        story.append(Paragraph(f"<b>Script ID:</b> {request.script_id}", body_style))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
        story.append(Paragraph(f"<b>Sections:</b> {', '.join(request.sections)}", body_style))
        story.append(Spacer(1, 16))

        story.append(Paragraph("Risk Assessment", heading_style))
        story.append(HRFlowable(width="100%", color=HexColor("#e2e8f0"), thickness=1))
        story.append(Spacer(1, 6))

        risk_color = RED if risk_score >= 70 else ORANGE if risk_score >= 40 else GREEN
        risk_data = [
            [Paragraph("<b>Overall Risk Score</b>", body_cell_style), Paragraph(f'<font color="{risk_color.hexval()}">{risk_score}%</font>', body_cell_style)],
            [Paragraph("<b>Risk Level</b>", body_cell_style), Paragraph(risk_level.upper(), body_cell_style)],
        ]
        t = Table(risk_data, colWidths=[2.5*inch, 3*inch])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Claims Analysis", heading_style))
        story.append(HRFlowable(width="100%", color=HexColor("#e2e8f0"), thickness=1))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Total Claims Found: {len(claims)}", body_style))
        story.append(Spacer(1, 8))

        if claims:
            claim_header = [
                Paragraph(h, header_cell_style) for h in ["#", "Text", "Type", "Confidence"]
            ]
            claim_rows = []
            for i, claim in enumerate(claims, 1):
                text = claim.get("text", "N/A")
                ctype = claim.get("type", claim.get("verdict", "unknown"))
                conf = claim.get("confidence", 0)
                claim_rows.append([
                    Paragraph(str(i), body_cell_style),
                    Paragraph(text, body_cell_style),
                    Paragraph(ctype, body_cell_style),
                    Paragraph(f"{conf*100:.0f}%", body_cell_style),
                ])
            ct = Table([claim_header] + claim_rows, colWidths=[0.4*inch, 3*inch, 1.2*inch, 1*inch])
            ct.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8fafc"), HexColor("#ffffff")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(ct)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Agent Performance", heading_style))
        story.append(HRFlowable(width="100%", color=HexColor("#e2e8f0"), thickness=1))
        story.append(Spacer(1, 6))

        agents = report_data.get("agent_results", {})
        if agents:
            agent_header = [
                Paragraph(h, header_cell_style) for h in ["Agent", "Status", "Confidence", "Time"]
            ]
            agent_rows = []
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
                agent_rows.append([
                    Paragraph(name.upper(), body_cell_style),
                    Paragraph(status, body_cell_style),
                    Paragraph(f"{conf*100:.1f}%", body_cell_style),
                    Paragraph(f"{time_s:.1f}s", body_cell_style),
                ])
            at = Table([agent_header] + agent_rows, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1*inch])
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1e293b")),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8fafc"), HexColor("#ffffff")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(at)

        story.append(Spacer(1, 24))
        story.append(HRFlowable(width="100%", color=GREEN, thickness=2))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Generated by GreenLit AI — https://greenlit-ai.com", small_style))

        doc.build(story)
        content_type = "application/pdf"

    else:  # txt fallback
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
        filename = f"{export_id}.txt"
        filepath = os.path.join("data/exports", filename)
        with open(filepath, "w") as f:
            f.write(txt_content)
        content_type = "text/plain"

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
        ".pdf": "application/pdf",
    }
    media_type = media_types.get(ext, "application/octet-stream")

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

    # Get report data from cache, or try to load from file storage
    report_data = _report_cache.get(request.script_id, {})
    
    if not report_data:
        # Try loading from file storage
        import os
        report_file = f"data/reports/{request.script_id}.json"
        if os.path.exists(report_file):
            try:
                with open(report_file, "r") as f:
                    report_data = json.load(f)
                logger.info(f"Loaded report data from file storage for share: {request.script_id}")
            except Exception as e:
                logger.warning(f"Failed to load report for share: {e}")
                report_data = {}
    
    # If still empty, create minimal data
    if not report_data:
        report_data = {
            "script_id": request.script_id,
            "risk_assessment": {"overall_risk_score": 0, "risk_level": "unknown"},
            "claims": [],
        }

    _share_tokens[token] = {
        "script_id": request.script_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "access_count": 0,
        "report_data": report_data,
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
