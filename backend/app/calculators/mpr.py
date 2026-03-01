"""MaPrimeRénov' calculators — par geste and rénovation d'ampleur."""

from __future__ import annotations

import json
from pathlib import Path
from functools import lru_cache
from typing import Optional

from ..models.citizen import IncomeBracket, DPEClass, DPE_ORDER


DATA_PATH = Path(__file__).parent.parent / "data" / "subsidies.json"


@lru_cache(maxsize=1)
def _load_subsidies() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_available_gestes() -> list[dict]:
    """Return list of all available renovation actions with their IDs and labels."""
    data = _load_subsidies()
    return [
        {
            "id": g["id"],
            "label_fr": g["label_fr"],
            "label_en": g["label_en"],
            "category": g["category"],
            "unit": g["unit"],
        }
        for g in data["par_geste"]
    ]


def calculate_mpr_par_geste(
    bracket: str,
    geste_id: str,
    surface_m2: Optional[float] = None,
    nb_equipements: Optional[int] = None,
) -> dict:
    """
    Calculate MaPrimeRénov' par geste amount for a specific renovation action.

    Args:
        bracket: Income bracket (tres_modeste, modeste, intermediaire, superieur)
        geste_id: ID of the renovation action (e.g., 'pac_air_eau')
        surface_m2: Surface area for per-m² actions
        nb_equipements: Number of equipment items for per-unit actions

    Returns:
        dict with amount, plafond, eligible, source, etc.
    """
    data = _load_subsidies()

    # Find the geste
    geste = next((g for g in data["par_geste"] if g["id"] == geste_id), None)
    if geste is None:
        return {
            "eligible": False,
            "error": f"Geste '{geste_id}' non trouvé dans la base de données.",
            "amount": 0,
        }

    meta_source = data.get("metadata", {}).get("source", "ANAH 2026")

    # Check bracket eligibility
    unit_amount = geste["amounts"].get(bracket)
    if unit_amount is None:
        return {
            "eligible": False,
            "geste_id": geste_id,
            "geste_label_fr": geste["label_fr"],
            "geste_label_en": geste["label_en"],
            "amount": 0,
            "reason_fr": f"Les ménages de catégorie '{bracket}' ne sont pas éligibles au parcours par geste pour cette aide.",
            "reason_en": f"Households in the '{bracket}' bracket are not eligible for this per-action aid.",
            "source": meta_source,
        }

    # Calculate total amount based on unit
    unit = geste["unit"]
    plafond = geste["plafond_depense"]

    if unit == "€/m2":
        if surface_m2 is None or surface_m2 <= 0:
            return {
                "eligible": True,
                "geste_id": geste_id,
                "geste_label_fr": geste["label_fr"],
                "geste_label_en": geste["label_en"],
                "unit_amount": unit_amount,
                "unit": "€/m²",
                "amount": unit_amount,  # Per m²
                "amount_note": f"{unit_amount} €/m² — veuillez préciser la surface pour le calcul total.",
                "plafond_per_m2": plafond,
                "rge_required": geste["rge_required"],
                "conditions": geste["conditions"],
                "legal_ref": geste["legal_ref"],
                "source": meta_source,
                "needs_surface": True,
            }
        total = unit_amount * surface_m2
        plafond_total = plafond * surface_m2
        return {
            "eligible": True,
            "geste_id": geste_id,
            "geste_label_fr": geste["label_fr"],
            "geste_label_en": geste["label_en"],
            "unit_amount": unit_amount,
            "unit": "€/m²",
            "surface_m2": surface_m2,
            "amount": total,
            "amount_display": f"{total:,.0f} €".replace(",", " "),
            "plafond_per_m2": plafond,
            "plafond_total": plafond_total,
            "rge_required": geste["rge_required"],
            "conditions": geste["conditions"],
            "legal_ref": geste["legal_ref"],
            "source": meta_source,
        }

    elif unit == "€/équipement":
        qty = nb_equipements or 1
        total = unit_amount * qty
        return {
            "eligible": True,
            "geste_id": geste_id,
            "geste_label_fr": geste["label_fr"],
            "geste_label_en": geste["label_en"],
            "unit_amount": unit_amount,
            "unit": "€/équipement",
            "nb_equipements": qty,
            "amount": total,
            "amount_display": f"{total:,.0f} €".replace(",", " "),
            "plafond_per_equip": plafond,
            "rge_required": geste["rge_required"],
            "conditions": geste["conditions"],
            "legal_ref": geste["legal_ref"],
            "source": meta_source,
        }

    else:  # forfait
        return {
            "eligible": True,
            "geste_id": geste_id,
            "geste_label_fr": geste["label_fr"],
            "geste_label_en": geste["label_en"],
            "amount": unit_amount,
            "amount_display": f"{unit_amount:,.0f} €".replace(",", " "),
            "plafond_depense": plafond,
            "unit": "forfait",
            "rge_required": geste["rge_required"],
            "conditions": geste["conditions"],
            "legal_ref": geste["legal_ref"],
            "source": meta_source,
        }


def calculate_mpr_ampleur(
    bracket: str,
    current_dpe: str,
    target_dpe: str,
    cost_ht: float,
) -> dict:
    """
    Calculate MaPrimeRénov' rénovation d'ampleur (parcours accompagné).

    Args:
        bracket: Income bracket
        current_dpe: Current DPE class (A-G)
        target_dpe: Target DPE class after renovation (A-G)
        cost_ht: Total renovation cost excluding tax (HT)

    Returns:
        dict with amount, percentage, bonification, eligibility details
    """
    data = _load_subsidies()
    ampleur = data["renovation_ampleur"]
    meta_source = data.get("metadata", {}).get("source", "ANAH 2026")
    source = ampleur.get("source", meta_source)

    # Check DPE eligibility
    eligible_classes = ampleur["eligibility"].get("dpe_entry_classes",
                                                  ampleur["eligibility"].get("dpe_classes_eligible", ["E", "F", "G"]))
    if current_dpe not in eligible_classes:
        return {
            "eligible": False,
            "reason_fr": f"Le DPE actuel ({current_dpe}) n'est pas éligible. Classes éligibles : {', '.join(eligible_classes)}.",
            "reason_en": f"Current DPE ({current_dpe}) is not eligible. Eligible classes: {', '.join(eligible_classes)}.",
            "source": source,
        }

    # Calculate class gain
    current_order = DPE_ORDER.get(DPEClass(current_dpe), 0)
    target_order = DPE_ORDER.get(DPEClass(target_dpe), 0)
    # Higher order = worse, so gain is positive
    class_gain = current_order - target_order

    min_gain = ampleur["eligibility"]["min_class_gain"]
    if class_gain < min_gain:
        return {
            "eligible": False,
            "reason_fr": f"Gain de {class_gain} classe(s) insuffisant. Minimum requis : {min_gain} classes.",
            "reason_en": f"Gain of {class_gain} class(es) insufficient. Minimum required: {min_gain} classes.",
            "current_dpe": current_dpe,
            "target_dpe": target_dpe,
            "class_gain": class_gain,
            "source": source,
        }

    # Determine tier — tiers is a list of objects with class_gain key
    tiers = ampleur["tiers"]
    tier = None
    for t in tiers:
        if class_gain >= 4 and t.get("class_gain") == 4:
            tier = t
            break
        elif t.get("class_gain") == class_gain:
            tier = t
            break
    if tier is None:
        tier = tiers[-1]  # fallback to highest

    rate_pct = tier.get("rates", {}).get(bracket, 0)
    plafond_ht = tier["plafond_ht"]

    # Apply plafond
    eligible_cost = min(cost_ht, plafond_ht)
    base_amount = eligible_cost * rate_pct / 100

    # Bonification sortie passoire
    bonification = ampleur.get("bonification_sortie_passoire",
                               ampleur.get("bonification_passoire", {}))
    is_passoire = current_dpe in ("F", "G")
    target_meets_minimum = DPE_ORDER.get(
        DPEClass(target_dpe), 99) <= DPE_ORDER.get(DPEClass.D, 3)
    bonus_pct = bonification.get("bonus_pct",
                                 bonification.get("amount_pct", 10)) if (is_passoire and target_meets_minimum) else 0
    bonus_amount = eligible_cost * bonus_pct / 100

    total_amount = base_amount + bonus_amount

    # Accompagnement
    accomp = ampleur.get("accompagnement", {})
    accomp_rates = accomp.get("rates", {})
    accomp_rate = accomp_rates.get(bracket, 0)
    accomp_plafond = accomp.get("plafond", 2000)
    accomp_amount = accomp_plafond * accomp_rate / 100

    logement_age = ampleur["eligibility"].get("logement_age_min_years", 15)

    return {
        "eligible": True,
        "current_dpe": current_dpe,
        "target_dpe": target_dpe,
        "class_gain": class_gain,
        "bracket": bracket,
        "rate_pct": rate_pct,
        "bonus_passoire_pct": bonus_pct,
        "total_rate_pct": rate_pct + bonus_pct,
        "plafond_ht": plafond_ht,
        "eligible_cost": eligible_cost,
        "base_amount": base_amount,
        "bonus_amount": bonus_amount,
        "total_amount": total_amount,
        "amount_display": f"{total_amount:,.0f} €".replace(",", " "),
        "accompagnement_amount": accomp_amount,
        "conditions_fr": [
            f"Gain d'au moins {min_gain} classes DPE",
            "Au moins 2 gestes d'isolation",
            "Accompagnement par un Accompagnateur Rénov' obligatoire",
            f"Logement de plus de {logement_age} ans",
            "Résidence principale",
        ],
        "conditions_en": [
            f"At least {min_gain} DPE class improvement",
            "At least 2 insulation actions",
            "Mandatory support by an authorized renovation advisor",
            f"Dwelling over {logement_age} years old",
            "Primary residence",
        ],
        "source": source,
    }


def calculate_cee_estimate(bracket: str, geste_id: str) -> dict:
    """
    Estimate CEE Coup de pouce bonus for a given geste.

    Args:
        bracket: Income bracket
        geste_id: Renovation action ID

    Returns:
        dict with estimated CEE amount
    """
    data = _load_subsidies()
    cee = data.get("cee_coup_de_pouce", {})

    eligible_equipment = cee.get("eligible_equipment", [])
    if geste_id not in eligible_equipment:
        return {
            "eligible": False,
            "geste_id": geste_id,
            "reason_fr": "Ce type de travaux n'est pas éligible au Coup de pouce CEE chauffage.",
            "reason_en": "This type of work is not eligible for the CEE Coup de pouce heating bonus.",
        }

    amounts = cee.get("amounts", {})
    amount = amounts.get(bracket, amounts.get("intermediaire", 2500))

    return {
        "eligible": True,
        "geste_id": geste_id,
        "amount": amount,
        "amount_display": f"{amount:,.0f} €".replace(",", " "),
        "amount_note_fr": cee.get("amount_note", "Montant indicatif — varie selon le fournisseur d'énergie."),
        "amount_note_en": "Indicative amount — varies by energy supplier.",
        "condition_fr": cee.get("condition", ""),
        "cumulative_with_mpr": cee.get("cumulative_with_mpr", True),
        "source": cee.get("source", ""),
    }
