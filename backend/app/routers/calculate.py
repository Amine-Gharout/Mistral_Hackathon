"""Deterministic calculation endpoints — no AI involved."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from ..calculators.income import determine_income_bracket
from ..calculators.mpr import calculate_mpr_par_geste, calculate_mpr_ampleur, calculate_cee_estimate, get_available_gestes
from ..calculators.mobility import calculate_mobility_aids, check_zfe_vehicle
from ..calculators.stacking import check_stacking
from ..calculators.eco_ptz import calculate_eco_ptz

router = APIRouter(prefix="/api/calculate", tags=["calculate"])


# ── Income Bracket ────────────────────────────────────────────────────────

class IncomeBracketRequest(BaseModel):
    rfr: int = Field(..., description="Revenu fiscal de référence")
    household_size: int = Field(..., ge=1, le=20)
    is_ile_de_france: bool


@router.post("/income-bracket")
async def api_income_bracket(req: IncomeBracketRequest):
    return determine_income_bracket(req.rfr, req.household_size, req.is_ile_de_france)


# ── MPR Par Geste ─────────────────────────────────────────────────────────

class MPRParGesteRequest(BaseModel):
    bracket: str = Field(...,
                         pattern="^(tres_modeste|modeste|intermediaire|superieur)$")
    geste_id: str
    surface_m2: Optional[float] = None
    nb_equipements: Optional[int] = None


@router.post("/mpr-par-geste")
async def api_mpr_par_geste(req: MPRParGesteRequest):
    return calculate_mpr_par_geste(
        req.bracket, req.geste_id, req.surface_m2, req.nb_equipements
    )


# ── MPR Ampleur ───────────────────────────────────────────────────────────

class MPRAmpleurRequest(BaseModel):
    bracket: str = Field(...,
                         pattern="^(tres_modeste|modeste|intermediaire|superieur)$")
    current_dpe: str = Field(..., pattern="^[A-G]$")
    target_dpe: str = Field(..., pattern="^[A-G]$")
    cost_ht: float = Field(..., gt=0)


@router.post("/mpr-ampleur")
async def api_mpr_ampleur(req: MPRAmpleurRequest):
    return calculate_mpr_ampleur(req.bracket, req.current_dpe, req.target_dpe, req.cost_ht)


# ── Mobility Aids ─────────────────────────────────────────────────────────

class MobilityRequest(BaseModel):
    rfr: int
    household_size: int = Field(..., ge=1)
    is_zfe_resident: bool = False
    scrapping_old_vehicle: bool = False
    old_vehicle_critair: Optional[str] = None
    target_vehicle_type: str = "voiture_electrique"


@router.post("/mobility")
async def api_mobility(req: MobilityRequest):
    return calculate_mobility_aids(
        rfr=req.rfr,
        household_size=req.household_size,
        is_zfe_resident=req.is_zfe_resident,
        scrapping_old_vehicle=req.scrapping_old_vehicle,
        old_vehicle_critair=req.old_vehicle_critair,
        target_vehicle_type=req.target_vehicle_type,
    )


# ── ZFE Check ─────────────────────────────────────────────────────────────

class ZFECheckRequest(BaseModel):
    critair: str
    commune: str
    vehicle_category: str = "VL"


@router.post("/zfe-check")
async def api_zfe_check(req: ZFECheckRequest):
    return check_zfe_vehicle(req.critair, req.commune, req.vehicle_category)


# ── Stacking ──────────────────────────────────────────────────────────────

class StackingRequest(BaseModel):
    aid_ids: list[str]
    total_cost: float = 0


@router.post("/stacking")
async def api_stacking(req: StackingRequest):
    return check_stacking(req.aid_ids, req.total_cost)


# ── Éco-PTZ ───────────────────────────────────────────────────────────────

class EcoPTZRequest(BaseModel):
    parcours: str = Field(..., pattern="^(par_geste|ampleur)$")
    nb_gestes: int = 1
    cost_remaining: float = 0


@router.post("/eco-ptz")
async def api_eco_ptz(req: EcoPTZRequest):
    return calculate_eco_ptz(req.parcours, req.nb_gestes, req.cost_remaining)


# ── Gestes List ───────────────────────────────────────────────────────────

@router.get("/gestes")
async def api_list_gestes():
    """List all available renovation gestes."""
    return get_available_gestes()
