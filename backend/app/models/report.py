"""Pydantic models for the entitlement report output."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AidResult(BaseModel):
    aid_id: str
    label_fr: str = ""
    label_en: str = ""
    amount: float = 0
    amount_display: str = ""  # e.g. "4 000 €"
    eligible: bool = True
    conditions: list[str] = Field(default_factory=list)
    plafond: Optional[float] = None
    plafond_note: Optional[str] = None
    source: str = ""
    source_url: Optional[str] = None
    legal_ref: Optional[str] = None
    notes: list[str] = Field(default_factory=list)
    category: str = "renovation"  # "renovation", "mobility", "loan", "local"


class StackingResult(BaseModel):
    compatible: bool = True
    warnings: list[str] = Field(default_factory=list)
    incompatible_pairs: list[tuple[str, str]] = Field(default_factory=list)
    global_cap_notes: list[str] = Field(default_factory=list)


class EcoPTZResult(BaseModel):
    eligible: bool = False
    max_amount: float = 0
    duration_years: int = 0
    parcours: str = ""
    notes: list[str] = Field(default_factory=list)


class ActionStep(BaseModel):
    title: str = ""
    description: str = ""
    url: Optional[str] = None
    documents_needed: list[str] = Field(default_factory=list)


class EntitlementReport(BaseModel):
    """Complete personalized entitlement report."""
    # Citizen summary
    income_bracket: Optional[str] = None
    bracket_color: Optional[str] = None

    # Renovation aids
    renovation_aids: list[AidResult] = Field(default_factory=list)
    renovation_total: float = 0
    cee_estimate: Optional[AidResult] = None

    # Mobility aids
    mobility_aids: list[AidResult] = Field(default_factory=list)
    mobility_total: float = 0

    # Éco-PTZ
    eco_ptz: Optional[EcoPTZResult] = None
    eco_ptz_amount: float = 0

    # Local/regional aids
    local_aids: list[AidResult] = Field(default_factory=list)
    local_total: float = 0

    # Stacking
    stacking: StackingResult = Field(default_factory=StackingResult)

    # Totals
    total_conservative: float = 0  # Only definitively stackable
    total_optimistic: float = 0  # Including conditional aids
    total_note_fr: str = ""
    total_note_en: str = ""

    # Action plan
    action_steps: list[ActionStep] = Field(default_factory=list)

    # Sources
    sources: list[str] = Field(default_factory=list)

    def format_euro(self, amount: float) -> str:
        """Format amount as French euro string."""
        if amount >= 1000:
            return f"{amount:,.0f} €".replace(",", " ")
        return f"{amount:.0f} €"
