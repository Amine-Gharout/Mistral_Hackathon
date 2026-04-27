"""Éco-PTZ (zero-rate loan) calculator."""

from __future__ import annotations


def calculate_eco_ptz(
    parcours: str,
    nb_gestes: int = 1,
    cost_remaining: float = 0,
) -> dict:
    """
    Calculate Éco-PTZ eligibility and maximum amount.

    Args:
        parcours: "par_geste" or "ampleur"
        nb_gestes: Number of renovation actions (for par geste)
        cost_remaining: Remaining cost after subsidies

    Returns:
        dict with eligibility, max amount, duration
    """
    # Éco-PTZ tiers
    if parcours == "ampleur":
        max_amount = 50000
        duration_years = 20
        label = "Éco-PTZ Performance globale (rénovation d'ampleur)"
    elif nb_gestes >= 3:
        max_amount = 30000
        duration_years = 15
        label = f"Éco-PTZ — 3 actions ou plus"
    elif nb_gestes == 2:
        max_amount = 25000
        duration_years = 15
        label = "Éco-PTZ — 2 actions"
    else:
        max_amount = 15000
        duration_years = 15
        label = "Éco-PTZ — 1 action"

    # The actual loan amount is the lesser of max_amount and remaining cost
    loan_amount = min(
        max_amount, cost_remaining) if cost_remaining > 0 else max_amount

    return {
        "eligible": True,
        "label_fr": label,
        "label_en": label.replace("actions", "actions").replace("ou plus", "or more"),
        "max_amount": max_amount,
        "loan_amount": loan_amount,
        "amount_display": f"Jusqu'à {max_amount:,.0f} €".replace(",", " "),
        "duration_years": duration_years,
        "interest_rate": 0,
        "interest_note_fr": "Prêt à taux zéro — aucun intérêt à rembourser.",
        "interest_note_en": "Zero-rate loan — no interest to repay.",
        "parcours": parcours,
        "nb_gestes": nb_gestes,
        "conditions_fr": [
            "Logement achevé depuis plus de 2 ans",
            "Résidence principale (propriétaire occupant ou bailleur)",
            "Travaux réalisés par un professionnel RGE",
            "Demande auprès d'une banque partenaire",
        ],
        "conditions_en": [
            "Dwelling completed over 2 years ago",
            "Primary residence (owner-occupier or landlord)",
            "Works carried out by an RGE-certified professional",
            "Application through a partner bank",
        ],
        "source": "Service-Public.gouv.fr — Éco-prêt à taux zéro",
        "source_url": "https://www.service-public.fr/particuliers/vosdroits/F19905",
    }
