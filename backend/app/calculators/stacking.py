"""Stacking rules engine — checks compatibility between aids."""

from __future__ import annotations

import json
from pathlib import Path
from functools import lru_cache


DATA_PATH = Path(__file__).parent.parent / "data" / "stacking_rules.json"


@lru_cache(maxsize=1)
def _load_rules() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def check_stacking(aid_ids: list[str], total_cost: float = 0) -> dict:
    """
    Check compatibility between a set of aids.

    Args:
        aid_ids: List of aid IDs being combined
        total_cost: Total cost of works (for cap checks)

    Returns:
        dict with compatible status, warnings, incompatible pairs
    """
    data = _load_rules()
    pairs = data["pairs"]
    global_rules = data["global_rules"]

    warnings = []
    incompatible = []
    notes = []
    all_compatible = True

    # Check all pairs
    for i, aid_a in enumerate(aid_ids):
        for aid_b in aid_ids[i + 1:]:
            # Normalize: check both orderings
            match = _find_pair(pairs, aid_a, aid_b)
            if match:
                if not match["compatible"]:
                    all_compatible = False
                    incompatible.append((aid_a, aid_b))
                    warnings.append(
                        match.get("note_fr", f"{aid_a} et {aid_b} ne sont pas cumulables."))
                else:
                    cap = match.get("cap")
                    if cap:
                        notes.append(cap)

    # Global rules
    cap_notes = []
    for rule in global_rules:
        cap_notes.append(rule["rule_fr"])

    return {
        "compatible": all_compatible,
        "warnings": warnings,
        "incompatible_pairs": incompatible,
        "notes": notes,
        "global_cap_notes": cap_notes,
        "source": data["meta"]["source"],
    }


def _find_pair(pairs: list, aid_a: str, aid_b: str) -> dict | None:
    """Find a matching stacking rule for a pair of aids."""
    for pair in pairs:
        pa = pair["aid_a"]
        pb = pair["aid_b"]
        # Exact match
        if (pa == aid_a and pb == aid_b) or (pa == aid_b and pb == aid_a):
            return pair
        # Wildcard match (e.g., "mpr_*")
        if _wildcard_match(pa, aid_a) and _wildcard_match(pb, aid_b):
            return pair
        if _wildcard_match(pa, aid_b) and _wildcard_match(pb, aid_a):
            return pair
    return None


def _wildcard_match(pattern: str, value: str) -> bool:
    """Simple wildcard matching with * at end."""
    if pattern == value:
        return True
    if pattern.endswith("*"):
        prefix = pattern[:-1]
        return value.startswith(prefix)
    return False
