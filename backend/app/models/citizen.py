"""Pydantic models for citizen profile and related data."""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class IncomeBracket(str, Enum):
    TRES_MODESTE = "tres_modeste"
    MODESTE = "modeste"
    INTERMEDIAIRE = "intermediaire"
    SUPERIEUR = "superieur"


class BracketColor(str, Enum):
    BLEU = "bleu"
    JAUNE = "jaune"
    VIOLET = "violet"
    ROSE = "rose"


BRACKET_COLOR_MAP = {
    IncomeBracket.TRES_MODESTE: BracketColor.BLEU,
    IncomeBracket.MODESTE: BracketColor.JAUNE,
    IncomeBracket.INTERMEDIAIRE: BracketColor.VIOLET,
    IncomeBracket.SUPERIEUR: BracketColor.ROSE,
}


class DPEClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


DPE_ORDER = {c: i for i, c in enumerate(DPEClass)}


class PropertyType(str, Enum):
    MAISON = "maison"
    APPARTEMENT = "appartement"
    COPROPRIETE = "copropriete"


class OwnershipType(str, Enum):
    OCCUPANT = "occupant"
    BAILLEUR = "bailleur"


class HeatingType(str, Enum):
    CHAUDIERE_GAZ = "chaudiere_gaz"
    CHAUDIERE_FIOUL = "chaudiere_fioul"
    CHAUDIERE_CHARBON = "chaudiere_charbon"
    CONVECTEUR_ELECTRIQUE = "convecteur_electrique"
    PAC = "pac"
    BOIS = "bois"
    RESEAU_CHALEUR = "reseau_chaleur"
    AUTRE = "autre"


class FuelType(str, Enum):
    ESSENCE = "essence"
    DIESEL = "diesel"
    HYBRIDE = "hybride"
    ELECTRIQUE = "electrique"
    GPL = "gpl"


class TargetVehicleType(str, Enum):
    VOITURE_ELECTRIQUE = "voiture_electrique"
    VOITURE_HYBRIDE_RECHARGEABLE = "voiture_hybride_rechargeable"
    VELO_ELECTRIQUE = "velo_electrique"
    VELO_CARGO_ELECTRIQUE = "velo_cargo_electrique"
    DEUX_ROUES_ELECTRIQUE = "deux_roues_electrique"


class Parcours(str, Enum):
    PAR_GESTE = "par_geste"
    AMPLEUR = "ampleur"
    UNDECIDED = "undecided"


class PropertyProfile(BaseModel):
    type: Optional[PropertyType] = None
    dpe_class: Optional[DPEClass] = None
    construction_year: Optional[int] = None
    surface_m2: Optional[float] = None
    heating_type: Optional[HeatingType] = None
    is_residence_principale: Optional[bool] = None
    ownership_type: Optional[OwnershipType] = None


class VehicleProfile(BaseModel):
    critair: Optional[str] = None  # "0"-"5" or "non_classe"
    fuel_type: Optional[FuelType] = None
    year: Optional[int] = None
    target_vehicle_type: Optional[TargetVehicleType] = None


class PlannedRenovation(BaseModel):
    geste_id: str
    surface_m2: Optional[float] = None
    nb_equipements: Optional[int] = None
    estimated_cost: Optional[float] = None


class CitizenProfile(BaseModel):
    """Progressive citizen profile — all fields optional, filled over conversation turns."""
    # Financial
    rfr: Optional[int] = Field(
        None, description="Revenu fiscal de référence (€)")
    household_size: Optional[int] = Field(
        None, ge=1, description="Nombre de personnes dans le foyer")
    is_ile_de_france: Optional[bool] = None
    income_bracket: Optional[IncomeBracket] = None
    bracket_color: Optional[BracketColor] = None

    # Location
    commune: Optional[str] = None
    departement: Optional[str] = None

    # Property
    property: Optional[PropertyProfile] = PropertyProfile()

    # Vehicle
    vehicle: Optional[VehicleProfile] = VehicleProfile()

    # Project
    parcours: Optional[Parcours] = None
    planned_renovations: list[PlannedRenovation] = Field(default_factory=list)

    def get_missing_fields(self) -> list[str]:
        """Return list of important missing fields for conversation guidance."""
        missing = []
        if self.rfr is None:
            missing.append("rfr")
        if self.household_size is None:
            missing.append("household_size")
        if self.is_ile_de_france is None:
            missing.append("is_ile_de_france")
        if self.commune is None:
            missing.append("commune")
        if self.property and self.property.dpe_class is None:
            missing.append("dpe_class")
        if self.property and self.property.type is None:
            missing.append("property_type")
        if self.property and self.property.heating_type is None:
            missing.append("heating_type")
        if self.property and self.property.surface_m2 is None:
            missing.append("surface_m2")
        return missing

    def can_calculate_bracket(self) -> bool:
        return self.rfr is not None and self.household_size is not None and self.is_ile_de_france is not None

    def can_calculate_renovation(self) -> bool:
        return (
            self.income_bracket is not None
            and self.property is not None
            and self.property.dpe_class is not None
            and len(self.planned_renovations) > 0
        )
