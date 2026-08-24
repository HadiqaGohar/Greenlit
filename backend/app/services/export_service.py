"""
Export Service - Generates PDF, JSON, and CSV exports of analysis reports
"""

import csv
import io
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

logger = logging.getLogger(__name__)

EXPORTS_DIR = "data/exports"


def _ensure_exports_dir():
    os.makedirs(EXPORTS_DIR, exist_ok=True)


# ─── PDF Generation ───────────────────────────────────────────────────────────


def generate_pdf(
    report_data: Dict[str, Any],
    sections: List[str],
    include_comments: bool = True,
    branding: Optional[Dict[str, str]] = None,
) -> str:
    """Generate a professional PDF report. Returns the file path."""
    _ensure_exports_dir()
    report_id = report_data.get("report_id", str(uuid4()))
    filename = f"report_{report_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(EXPORTS_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    elements: List[Any] = []

    # Custom styles
    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=20, spaceAfter=12, textColor=colors.HexColor("#1a1a2e"))
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, spaceAfter=8, textColor=colors.HexColor("#16213e"))
    body_style = ParagraphStyle("CustomBody", parent=styles["Normal"], fontSize=10, spaceAfter=6, leading=14)
    small_style = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    # Title page
    brand_name = branding.get("name", "GreenLit AI") if branding else "GreenLit AI"
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph(brand_name, title_style))
    elements.append(Paragraph("Production Report", heading_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Report metadata
    risk = report_data.get("risk_assessment", {})
    meta_data = [
        ["Report ID", str(report_id)[:12] + "..."],
        ["Generated", datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p")],
        ["Risk Score", f"{risk.get('overall_risk_score', 'N/A')}/100"],
        ["Risk Level", risk.get("risk_level", "N/A").upper()],
        ["Claims Found", str(len(report_data.get("claims", [])))],
    ]
    meta_table = Table(meta_data, colWidths=[2 * inch, 4 * inch])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(meta_table)
    elements.append(PageBreak())

    # Overview section
    if "overview" in sections:
        elements.append(Paragraph("Overview", heading_style))
        elements.append(Paragraph(
            f"Overall Risk Score: <b>{risk.get('overall_risk_score', 'N/A')}/100</b> "
            f"({risk.get('overall_risk_level', risk.get('risk_level', 'N/A'))})",
            body_style,
        ))
        risk_factors = risk.get("risk_factors", [])
        if risk_factors:
            elements.append(Paragraph("Risk Factors:", body_style))
            for factor in risk_factors:
                elements.append(Paragraph(f"  • {factor}", body_style))
        recommended = risk.get("recommended_actions", [])
        if recommended:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph("Recommended Actions:", body_style))
            for i, action in enumerate(recommended, 1):
                elements.append(Paragraph(f"  {i}. {action}", body_style))
        elements.append(Spacer(1, 12))

    # Claims / Research section
    if "claims" in sections or "research" in sections:
        claims = report_data.get("claims", [])
        elements.append(Paragraph("Claims & Research Findings", heading_style))
        if not claims:
            elements.append(Paragraph("No claims found.", body_style))
        else:
            for claim in claims[:20]:  # Limit to first 20
                verdict_color = {"verified": "green", "flagged": "red", "uncertain": "orange"}.get(
                    claim.get("verdict", ""), "black"
                )
                elements.append(Paragraph(
                    f'<font color="{verdict_color}"><b>{claim.get("verdict", "unknown").upper()}</b></font> '
                    f'— "{claim.get("text", "")}"',
                    body_style,
                ))
                if claim.get("note"):
                    elements.append(Paragraph(f"  Note: {claim['note']}", small_style))
                elements.append(Spacer(1, 4))
        elements.append(Spacer(1, 12))

    # Legal section
    if "legal" in sections:
        agent_results = report_data.get("agent_results", {})
        legal = agent_results.get("legal", {})
        legal_data = legal.get("data", {}) if isinstance(legal, dict) else {}
        elements.append(Paragraph("Legal Clearance", heading_style))

        cost = legal_data.get("estimated_clearance_cost", "Unknown")
        elements.append(Paragraph(f"Estimated Clearance Cost: <b>${cost}</b>" if isinstance(cost, (int, float)) else f"Estimated Clearance Cost: {cost}", body_style))

        copyright_risks = legal_data.get("copyright_risks", [])
        if copyright_risks:
            elements.append(Paragraph(f"Copyright Risks: {len(copyright_risks)}", body_style))
        trademark_issues = legal_data.get("trademark_issues", [])
        if trademark_issues:
            elements.append(Paragraph(f"Trademark Issues: {len(trademark_issues)}", body_style))
        recommendations = legal_data.get("legal_recommendations", [])
        if recommendations:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph("Legal Recommendations:", body_style))
            for rec in recommendations:
                elements.append(Paragraph(f"  • {rec}", body_style))
        elements.append(Spacer(1, 12))

    # Continuity section
    if "continuity" in sections:
        agent_results = report_data.get("agent_results", {})
        cont = agent_results.get("continuity", {})
        cont_data = cont.get("data", {}) if isinstance(cont, dict) else {}
        elements.append(Paragraph("Continuity Analysis", heading_style))

        char_issues = cont_data.get("character_inconsistencies", [])
        timeline_issues = cont_data.get("timeline_issues", [])
        location_issues = cont_data.get("location_continuity", [])
        prop_issues = cont_data.get("prop_tracking", [])

        summary_items = [
            ("Character Inconsistencies", char_issues),
            ("Timeline Issues", timeline_issues),
            ("Location Continuity", location_issues),
            ("Prop Tracking", prop_issues),
        ]
        for label, issues in summary_items:
            if issues:
                elements.append(Paragraph(f"{label}: {len(issues)}", body_style))
                for issue in issues[:5]:
                    desc = issue if isinstance(issue, str) else issue.get("description", str(issue))
                    elements.append(Paragraph(f"  • {desc}", small_style))
        elements.append(Spacer(1, 12))

    # Agent performance
    if "overview" in sections:
        agent_results = report_data.get("agent_results", {})
        if agent_results:
            elements.append(Paragraph("Agent Performance", heading_style))
            agent_table_data = [["Agent", "Status", "Confidence", "Time"]]
            for name, result in agent_results.items():
                if isinstance(result, dict):
                    agent_table_data.append([
                        name.title(),
                        "Success" if result.get("success") else "Failed",
                        f"{result.get('confidence', 0) * 100:.0f}%",
                        f"{result.get('processing_time', 0):.1f}s",
                    ])
            agent_table = Table(agent_table_data, colWidths=[1.5 * inch, 1.2 * inch, 1.2 * inch, 1 * inch])
            agent_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ]))
            elements.append(agent_table)

    # Footer
    elements.append(Spacer(1, 1 * inch))
    elements.append(Paragraph(
        f"Generated by {brand_name} • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        small_style,
    ))

    doc.build(elements)
    logger.info(f"PDF generated: {filepath}")
    return filepath


# ─── JSON Export ──────────────────────────────────────────────────────────────


def generate_json(
    report_data: Dict[str, Any],
    sections: List[str],
) -> str:
    """Generate a JSON export. Returns the file path."""
    _ensure_exports_dir()
    report_id = report_data.get("report_id", str(uuid4()))
    filename = f"report_{report_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(EXPORTS_DIR, filename)

    export_data = {"report_id": report_id, "exported_at": datetime.now(timezone.utc).isoformat(), "sections": sections}

    if "overview" in sections or "claims" in sections:
        export_data["claims"] = report_data.get("claims", [])
        export_data["risk_assessment"] = report_data.get("risk_assessment", {})

    if "legal" in sections:
        agent_results = report_data.get("agent_results", {})
        legal = agent_results.get("legal", {})
        export_data["legal"] = legal.get("data", {}) if isinstance(legal, dict) else {}

    if "continuity" in sections:
        agent_results = report_data.get("agent_results", {})
        cont = agent_results.get("continuity", {})
        export_data["continuity"] = cont.get("data", {}) if isinstance(cont, dict) else {}

    if "overview" in sections:
        export_data["agent_results"] = report_data.get("agent_results", {})
        export_data["processing_time"] = report_data.get("processing_time")

    with open(filepath, "w") as f:
        json.dump(export_data, f, indent=2, default=str)

    logger.info(f"JSON exported: {filepath}")
    return filepath


# ─── CSV Export ───────────────────────────────────────────────────────────────


def generate_csv(
    report_data: Dict[str, Any],
    sections: List[str],
) -> str:
    """Generate a CSV export of claims. Returns the file path."""
    _ensure_exports_dir()
    report_id = report_data.get("report_id", str(uuid4()))
    filename = f"report_{report_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(EXPORTS_DIR, filename)

    claims = report_data.get("claims", [])
    risk = report_data.get("risk_assessment", {})

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)

        # Risk summary row
        writer.writerow(["Risk Score", risk.get("overall_risk_score", "")])
        writer.writerow(["Risk Level", risk.get("risk_level", "")])
        writer.writerow([])

        # Claims table
        writer.writerow(["Claim ID", "Text", "Type", "Verdict", "Confidence", "Note"])
        for claim in claims:
            writer.writerow([
                claim.get("id", ""),
                claim.get("text", ""),
                claim.get("type", ""),
                claim.get("verdict", ""),
                claim.get("confidence", ""),
                claim.get("note", ""),
            ])

    logger.info(f"CSV exported: {filepath}")
    return filepath


# ─── Share Link Generation ───────────────────────────────────────────────────


def generate_share_token(report_id: str) -> str:
    """Generate a unique share token for a report"""
    token = f"{report_id}_{uuid4().hex[:12]}"
    return token


def get_export_path(filepath: str) -> Optional[str]:
    """Get a download URL for an exported file"""
    if os.path.exists(filepath):
        return f"/api/export/download/{os.path.basename(filepath)}"
    return None
