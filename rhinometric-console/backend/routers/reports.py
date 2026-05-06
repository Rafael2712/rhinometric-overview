from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.user import User as UserModel
from routers.auth import get_current_user
from services.report_service import (
    SUPPORTED_RANGES,
    generate_executive_report,
    generate_technical_report,
)

router = APIRouter()


class ReportPdfRequest(BaseModel):
    range: str = "7d"


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf(title: str, lines: List[str]) -> bytes:
    # Minimal single-font PDF generator (no external dependency).
    content_lines = [
        "BT",
        "/F1 11 Tf",
        "50 790 Td",
        f"({_escape_pdf_text(title)}) Tj",
    ]
    y_step = 15
    current_offset = y_step
    for line in lines:
        text = _escape_pdf_text(line[:1500])
        content_lines.append(f"0 -{current_offset} Td ({text}) Tj")
        current_offset = y_step
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects: List[bytes] = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(
        f"5 0 obj << /Length {len(content)} >> stream\n".encode("latin-1")
        + content
        + b"\nendstream endobj\n"
    )

    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(out.tell())
        out.write(obj)
    xref_start = out.tell()
    out.write(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    out.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.write(f"{off:010d} 00000 n \n".encode("latin-1"))
    out.write(
        (
            "trailer << /Size {size} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF".format(
                size=len(offsets), start=xref_start
            )
        ).encode("latin-1")
    )
    return out.getvalue()


def _validate_range(time_range: str) -> str:
    if time_range not in SUPPORTED_RANGES:
        raise HTTPException(status_code=400, detail="Unsupported range. Use 24h, 7d or 30d")
    return time_range


@router.get("/executive")
async def get_executive_report(
    range: str = Query("7d"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await generate_executive_report(db, _validate_range(range))


@router.get("/technical")
async def get_technical_report(
    range: str = Query("7d"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await generate_technical_report(db, _validate_range(range))


def _executive_lines(report: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    lines.append(f"Generated at: {report.get('generated_at', '-')}")
    lines.append(f"Status: {report.get('status', '-')}")
    lines.append(f"Summary: {report.get('summary', '-')}")
    lines.append("")
    k = report.get("kpis", {}) or {}
    lines.append("KPIs")
    lines.append(f"- Total incidents: {k.get('total_incidents', 0)}")
    lines.append(f"- MTTR (seconds): {k.get('mttr', 0)}")
    lines.append(f"- Uptime (%): {k.get('uptime', 0)}")
    lines.append(f"- Total alerts: {k.get('total_alerts', 0)}")
    lines.append("")
    lines.append("Top incidents")
    for item in (report.get("top_incidents", []) or []):
        lines.append(f"- {item.get('service', '-')}: {item.get('summary', '-')}")
    lines.append("")
    lines.append("Recommendations")
    for r in (report.get("recommendations", []) or []):
        lines.append(f"- {r}")
    if not (report.get("recommendations") or []):
        lines.append("- No recommendations.")
    return lines


def _technical_lines(report: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    lines.append(f"Generated at: {report.get('generated_at', '-')}")
    lines.append("")
    lines.append("Incidents")
    for i in (report.get("incidents", []) or [])[:50]:
        lines.append(
            f"- {i.get('entity_name', '-')} | {i.get('severity', '-')} | "
            f"{i.get('status', '-')} | {i.get('started_at', '-')}"
        )
    if not (report.get("incidents") or []):
        lines.append("- No incidents.")
    lines.append("")
    lines.append("Alerts")
    for a in (report.get("alerts", []) or [])[:70]:
        lines.append(
            f"- {a.get('alert_name', '-')} | {a.get('severity', '-')} | "
            f"{a.get('status', '-')} | {a.get('started_at', '-')}"
        )
    if not (report.get("alerts") or []):
        lines.append("- No alerts.")
    lines.append("")
    lines.append("Timeline")
    for t in (report.get("timeline", []) or [])[:70]:
        lines.append(
            f"- {t.get('timestamp', '-')} | {t.get('type', '-')} | "
            f"{t.get('entity', '-')}"
        )
    if not (report.get("timeline") or []):
        lines.append("- No timeline events.")
    return lines


@router.post("/executive/pdf")
async def download_executive_pdf(
    body: ReportPdfRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    range_value = _validate_range(body.range)
    report = await generate_executive_report(db, range_value)
    pdf = _build_simple_pdf("Rhinometric Executive Report", _executive_lines(report))
    filename = f"executive-report-{range_value}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.pdf"
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/technical/pdf")
async def download_technical_pdf(
    body: ReportPdfRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    range_value = _validate_range(body.range)
    report = await generate_technical_report(db, range_value)
    pdf = _build_simple_pdf("Rhinometric Technical Report", _technical_lines(report))
    filename = f"technical-report-{range_value}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.pdf"
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
