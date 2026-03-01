"""Report endpoints — PDF generation, sharing, and report retrieval."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..services.session_store import session_store
from ..services.pdf_generator import generate_report_pdf
from ..models.report import EntitlementReport, AidResult, StackingResult, EcoPTZResult, ActionStep
from ..models.session import SessionState

router = APIRouter(prefix="/api/report", tags=["report"])


class GenerateReportRequest(BaseModel):
    session_id: str
    include_action_plan: bool = True


@router.post("/generate")
async def generate_report(request: GenerateReportRequest):
    """Generate a structured report from the session's computed aids."""
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    report = _build_report_from_session(session)
    session.computed_report = report

    return report.model_dump()


@router.get("/{session_id}")
async def get_report(session_id: str):
    """Get the last computed report for a session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.computed_report:
        raise HTTPException(status_code=404, detail="No report generated yet")

    report = session.computed_report
    if hasattr(report, 'model_dump'):
        return report.model_dump()
    return report


@router.get("/{session_id}/pdf")
async def get_report_pdf(session_id: str):
    """Download the report as a PDF."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.computed_report:
        # Try to build one
        session.computed_report = _build_report_from_session(session)

    pdf_bytes = generate_report_pdf(session.computed_report)

    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="greenrights-report-{session_id[:8]}.pdf"'
        },
    )


@router.get("/{session_id}/share")
async def get_share_link(session_id: str):
    """Get a shareable link for the report."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # In production, this would generate a signed URL or a public token
    from ..config import settings
    share_url = f"{settings.FRONTEND_URL}/report/{session_id}"

    return {
        "share_url": share_url,
        "session_id": session_id,
        "expires_in_hours": settings.SESSION_TTL_HOURS,
    }


def _build_report_from_session(session: SessionState) -> EntitlementReport:
    """Build an EntitlementReport from session data."""
    renovation_aids: list[AidResult] = []
    mobility_aids: list[AidResult] = []
    total_conservative = 0
    total_optimistic = 0

    # Extract aid results from session's aids_computed list
    if isinstance(session.aids_computed, list):
        for aid_data in session.aids_computed:
            if not isinstance(aid_data, dict):
                continue
            aid = AidResult(
                aid_id=aid_data.get(
                    "aid_id", aid_data.get("geste_id", "unknown")),
                label_fr=aid_data.get("label_fr", aid_data.get(
                    "geste_label_fr", aid_data.get("aid_name_fr", ""))),
                label_en=aid_data.get("label_en", aid_data.get(
                    "geste_label_en", aid_data.get("aid_name_en", ""))),
                amount=aid_data.get("amount", aid_data.get("total_amount", 0)),
                amount_display=aid_data.get("amount_display", ""),
                conditions=aid_data.get(
                    "conditions", aid_data.get("conditions_fr", [])),
                source=aid_data.get("source", ""),
                eligible=aid_data.get("eligible", True),
                category=aid_data.get("category", "renovation"),
            )

            if aid.category == "mobility":
                mobility_aids.append(aid)
            else:
                renovation_aids.append(aid)

            if aid.eligible:
                total_conservative += aid.amount
                total_optimistic += aid.amount

    # Build profile info
    profile = session.citizen_profile
    income_bracket = profile.income_bracket.value if profile.income_bracket else None
    bracket_color = profile.bracket_color.value if profile.bracket_color else None

    # Default action steps
    action_steps = [
        ActionStep(
            title="Creer un compte sur monprojet.anah.gouv.fr",
            description="Inscrivez-vous sur la plateforme officielle de l'ANAH pour demarrer votre dossier MaPrimeRenov'.",
            url="https://monprojet.anah.gouv.fr",
        ),
        ActionStep(
            title="Contacter un conseiller France Renov'",
            description="Un conseiller gratuit peut vous accompagner dans vos demarches. Appelez le 0 808 800 700.",
            url="https://france-renov.gouv.fr",
        ),
        ActionStep(
            title="Demander des devis a des artisans RGE",
            description="Les travaux doivent etre realises par des artisans certifies RGE (Reconnu Garant de l'Environnement).",
            url="https://france-renov.gouv.fr/annuaire-rge",
        ),
    ]

    sources = [
        "ANAH - Guide des aides financieres 2026",
        "Service-Public.gouv.fr",
        "Ministere de la Transition Ecologique",
    ]

    return EntitlementReport(
        income_bracket=income_bracket,
        bracket_color=bracket_color,
        renovation_aids=renovation_aids,
        renovation_total=sum(a.amount for a in renovation_aids if a.eligible),
        mobility_aids=mobility_aids,
        mobility_total=sum(a.amount for a in mobility_aids if a.eligible),
        total_conservative=total_conservative,
        total_optimistic=total_optimistic,
        total_note_fr="Montants estimes sur la base des baremes officiels ANAH 2026." if total_conservative else "Aucune aide calculee pour le moment. Discutez avec le conseiller pour obtenir une estimation.",
        action_steps=action_steps,
        sources=sources,
    )
