"""Income bracket determination — purely deterministic, based on ANAH 2026 thresholds."""

from __future__ import annotations

import json
from pathlib import Path
from functools import lru_cache

from ..models.citizen import IncomeBracket, BracketColor, BRACKET_COLOR_MAP


DATA_PATH = Path(__file__).parent.parent / "data" / "income_thresholds.json"


@lru_cache(maxsize=1)
def _load_thresholds() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def determine_income_bracket(
    rfr: int,
    household_size: int,
    is_ile_de_france: bool,
) -> dict:
    """
    Determine the MaPrimeRénov' income bracket for a household.

    Args:
        rfr: Revenu fiscal de référence (€, from tax notice N-1)
        household_size: Number of people in the household (≥ 1)
        is_ile_de_france: Whether the household is in Île-de-France

    Returns:
        dict with keys: bracket, color, label_fr, label_en, source, thresholds_used
    """
    data = _load_thresholds()
    region_key = "ile_de_france" if is_ile_de_france else "hors_ile_de_france"
    region = data[region_key]
    thresholds_dict = region["thresholds"]  # dict keyed by str(household_size)
    per_extra = region["per_extra_person"]

    # Find thresholds for this household size
    size_key = str(min(household_size, 5))
    row = thresholds_dict.get(size_key, thresholds_dict["5"])

    if household_size <= 5:
        thresholds = {
            "tres_modeste": row["tres_modeste"],
            "modeste": row["modeste"],
            "intermediaire": row["intermediaire"],
        }
    else:
        # Household size > 5: base on 5 + extra persons
        extra = household_size - 5
        thresholds = {
            "tres_modeste": row["tres_modeste"] + extra * per_extra["tres_modeste"],
            "modeste": row["modeste"] + extra * per_extra["modeste"],
            "intermediaire": row["intermediaire"] + extra * per_extra["intermediaire"],
        }

    # Classify
    if rfr <= thresholds["tres_modeste"]:
        bracket = IncomeBracket.TRES_MODESTE
    elif rfr <= thresholds["modeste"]:
        bracket = IncomeBracket.MODESTE
    elif rfr <= thresholds["intermediaire"]:
        bracket = IncomeBracket.INTERMEDIAIRE
    else:
        bracket = IncomeBracket.SUPERIEUR

    color = BRACKET_COLOR_MAP[bracket]
    metadata = data.get("metadata", {})

    label_map_fr = {
        "tres_modeste": "Très modeste (bleu)",
        "modeste": "Modeste (jaune)",
        "intermediaire": "Intermédiaire (violet)",
        "superieur": "Supérieur (rose)",
    }
    label_map_en = {
        "tres_modeste": "Very low income (blue)",
        "modeste": "Low income (yellow)",
        "intermediaire": "Intermediate (purple)",
        "superieur": "Higher income (pink)",
    }

    return {
        "bracket": bracket.value,
        "color": color.value,
        "label_fr": label_map_fr.get(bracket.value, bracket.value),
        "label_en": label_map_en.get(bracket.value, bracket.value),
        "region": region["label"],
        "thresholds_used": thresholds,
        "rfr": rfr,
        "household_size": household_size,
        "source": metadata.get("source", "ANAH 2026"),
        "source_url": metadata.get("source_url", ""),
        "effective_date": metadata.get("effective_date", "2026"),
    }
