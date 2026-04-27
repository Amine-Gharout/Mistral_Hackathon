"""Mobility aids calculator — Prime à la conversion, Prime coup de pouce VE, ZFE."""

from __future__ import annotations

import json
from pathlib import Path
from functools import lru_cache
from typing import Optional


MOBILITY_PATH = Path(__file__).parent.parent / "data" / "mobility_aids.json"
ZFE_PATH = Path(__file__).parent.parent / "data" / "zfe_zones.json"


@lru_cache(maxsize=1)
def _load_mobility() -> dict:
    with open(MOBILITY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_zfe() -> dict:
    with open(ZFE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_mobility_aids(
    rfr: int,
    household_size: int,
    is_zfe_resident: bool = False,
    scrapping_old_vehicle: bool = False,
    old_vehicle_critair: Optional[str] = None,
    target_vehicle_type: str = "voiture_electrique",
) -> dict:
    """
    Calculate all applicable mobility aids for a citizen.

    Args:
        rfr: Revenu fiscal de référence
        household_size: Number of people in household
        is_zfe_resident: Whether citizen lives/works in a ZFE
        scrapping_old_vehicle: Whether an old vehicle is being scrapped
        old_vehicle_critair: Crit'Air class of old vehicle
        target_vehicle_type: Type of new vehicle being acquired

    Returns:
        dict with all applicable aids, amounts, and total
    """
    data = _load_mobility()
    parts = _get_fiscal_parts(household_size)
    rfr_per_part = rfr / parts if parts > 0 else rfr

    aids = []
    total = 0

    # 1. Prime coup de pouce VE (replaces bonus écologique)
    if target_vehicle_type == "voiture_electrique":
        prime_ve = data["prime_coup_de_pouce_ve"]
        ve_amount = 0
        for tier in prime_ve.get("amounts", []):
            max_rfr = tier.get("rfr_per_part_max")
            if max_rfr is None or rfr_per_part <= max_rfr:
                ve_amount = tier.get("amount", 0)
                break

        if ve_amount > 0:
            aids.append({
                "aid_id": "prime_coup_de_pouce_ve",
                "aid_name_fr": prime_ve["label_fr"],
                "aid_name_en": prime_ve["label_en"],
                "amount": ve_amount,
                "amount_display": f"{ve_amount:,.0f} €".replace(",", " "),
                "eligible": True,
                "conditions_fr": prime_ve.get("conditions", []),
                "source": prime_ve.get("source", ""),
                "category": "mobility",
            })
            total += ve_amount

    # 1b. Bonus vélo
    elif target_vehicle_type in ("velo_electrique", "velo_cargo_electrique"):
        velo_data = data.get("bonus_ecologique_velo", {})
        velo_amount = 0
        for tier in velo_data.get("amounts", []):
            max_rfr = tier.get("rfr_per_part_max")
            if max_rfr is not None and rfr_per_part <= max_rfr:
                velo_amount = tier.get("amount", 0)
                break

        # Also check cargo-specific
        if target_vehicle_type == "velo_cargo_electrique":
            cargo_data = data.get("bonus_velo_cargo", {})
            for tier in cargo_data.get("amounts", []):
                max_rfr = tier.get("rfr_per_part_max")
                if max_rfr is None or rfr_per_part <= max_rfr:
                    cargo_amount = tier.get("amount", 0)
                    if cargo_amount > velo_amount:
                        velo_amount = cargo_amount
                    break

        if velo_amount > 0:
            aids.append({
                "aid_id": "bonus_velo",
                "aid_name_fr": velo_data.get("label_fr", "Bonus vélo"),
                "aid_name_en": velo_data.get("label_en", "E-bike bonus"),
                "amount": velo_amount,
                "amount_display": f"{velo_amount:,.0f} €".replace(",", " "),
                "eligible": True,
                "source": velo_data.get("source", ""),
                "category": "mobility",
            })
            total += velo_amount

    # 2. Prime à la conversion (requires scrapping old vehicle)
    if scrapping_old_vehicle and old_vehicle_critair in ("3", "4", "5", "non_classe"):
        conv = data["prime_conversion"]
        conv_amount = 0

        amount_key = f"amount_{target_vehicle_type}"
        for tier in conv.get("amounts", []):
            max_rfr = tier.get("rfr_per_part_max")
            if max_rfr is None or rfr_per_part <= max_rfr:
                # Try specific vehicle type key, then generic
                conv_amount = tier.get(amount_key, tier.get(
                    "amount_voiture_electrique", tier.get("amount", 0)))
                break

        if conv_amount > 0:
            aids.append({
                "aid_id": "prime_conversion",
                "aid_name_fr": conv["label_fr"],
                "aid_name_en": conv["label_en"],
                "amount": conv_amount,
                "amount_display": f"{conv_amount:,.0f} €".replace(",", " "),
                "eligible": True,
                "conditions_fr": conv.get("conditions_vehicule_mis_au_rebut", []),
                "source": conv.get("source", ""),
                "category": "mobility",
            })
            total += conv_amount

    # 3. ZFE surprime
    if is_zfe_resident:
        zfe = data["zfe_surprime"]
        zfe_amount = zfe.get("amount", 1000)
        aids.append({
            "aid_id": "zfe_surprime",
            "aid_name_fr": zfe["label_fr"],
            "aid_name_en": zfe["label_en"],
            "amount": zfe_amount,
            "amount_display": f"{zfe_amount:,.0f} €".replace(",", " "),
            "eligible": True,
            "conditions_fr": zfe.get("conditions", []),
            "source": zfe.get("source", ""),
            "category": "mobility",
        })
        total += zfe_amount

    # 4. Microcredit eligibility check
    micro = data.get("microcredit_mobilite", {})
    microcredit_eligible = rfr_per_part <= 7700  # Very low income proxy
    if microcredit_eligible and micro:
        max_amount = micro.get("max_amount", micro.get("montant_max", 8000))
        aids.append({
            "aid_id": "microcredit_mobilite",
            "aid_name_fr": micro.get("label_fr", "Microcrédit mobilité"),
            "aid_name_en": micro.get("label_en", "Mobility microloan"),
            "amount": max_amount,
            "amount_display": f"Jusqu'à {max_amount:,.0f} €".replace(",", " "),
            "eligible": True,
            "is_loan": True,
            "conditions_fr": micro.get("conditions", []),
            "source": micro.get("source", ""),
            "category": "mobility",
            "note_fr": "Il s'agit d'un prêt (microcrédit), pas d'une subvention.",
            "note_en": "This is a loan (microloan), not a grant.",
        })

    return {
        "aids": aids,
        "total_grants": total,
        "total_display": f"{total:,.0f} €".replace(",", " "),
        "rfr_per_part": round(rfr_per_part),
        "microcredit_eligible": microcredit_eligible,
    }


def check_zfe_vehicle(
    critair: str,
    commune: str,
    vehicle_category: str = "VL",
) -> dict:
    """
    Check if a vehicle is allowed in a specific ZFE zone.

    Args:
        critair: Crit'Air class ("0"-"5" or "non_classe")
        commune: Commune name
        vehicle_category: "VL" (car), "VUL" (van), "PL" (truck)

    Returns:
        dict with allowed status, zone details, restrictions
    """
    zfe_data = _load_zfe()
    commune_lower = commune.lower().strip()

    # Find matching ZFE zone
    matching_zone = None
    for zone in zfe_data["zones"]:
        zone_communes = [c.lower() for c in zone.get("main_communes", [])]
        if commune_lower in zone_communes:
            matching_zone = zone
            break

    if matching_zone is None:
        return {
            "in_zfe": False,
            "commune": commune,
            "message_fr": f"{commune} n'est pas dans une ZFE active référencée.",
            "message_en": f"{commune} is not in a referenced active ZFE.",
        }

    zone = matching_zone
    restrictions = zone.get("restrictions", {}).get(vehicle_category, {})
    banned = restrictions.get("banned_critair", [])

    is_banned = critair in banned

    # Get Crit'Air info
    critair_info = zfe_data.get("critair_classes", {}).get(critair, {})

    result = {
        "in_zfe": True,
        "zone_id": zone["id"],
        "zone_name": zone["name"],
        "commune": commune,
        "vehicle_category": vehicle_category,
        "critair": critair,
        "critair_label": critair_info.get("label", f"Crit Air {critair}"),
        "allowed": not is_banned,
        "banned_since": restrictions.get("since") if is_banned else None,
        "enforcement": zone.get("enforcement", "unknown"),
        "fine_amount": zone.get("fine_amount_vl" if vehicle_category == "VL" else "fine_amount_pl", 68),
        "hours": zone.get("hours", ""),
        "derogations": zone.get("derogations", []),
        "timeline": zone.get("timeline", []),
    }

    if is_banned:
        crit_label = critair_info.get('label', f'Crit Air {critair}')
        result["message_fr"] = (
            f"⚠️ Votre véhicule {crit_label} est interdit "
            f"dans la ZFE {zone['name']} depuis le {restrictions.get('since', 'N/A')}. "
            f"Amende : {result['fine_amount']} €."
        )
        result["message_en"] = (
            f"⚠️ Your {crit_label} vehicle is banned "
            f"from the {zone['name']} ZFE since {restrictions.get('since', 'N/A')}. "
            f"Fine: €{result['fine_amount']}."
        )
    else:
        crit_label2 = critair_info.get('label', f'Crit Air {critair}')
        result["message_fr"] = (
            f"✅ Votre véhicule {crit_label2} est autorisé "
            f"dans la ZFE {zone['name']}."
        )
        result["message_en"] = (
            f"✅ Your {crit_label2} vehicle is allowed "
            f"in the {zone['name']} ZFE."
        )

    return result


def _get_fiscal_parts(household_size: int) -> float:
    """Convert household size to fiscal parts (simplified French system)."""
    if household_size <= 1:
        return 1.0
    elif household_size == 2:
        return 2.0
    elif household_size == 3:
        return 2.5
    elif household_size == 4:
        return 3.0
    else:
        return 3.0 + (household_size - 4) * 0.5
