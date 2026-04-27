"""Tool definitions for Mistral function calling."""

from __future__ import annotations

from ..calculators.income import determine_income_bracket
from ..calculators.mpr import calculate_mpr_par_geste, calculate_mpr_ampleur, calculate_cee_estimate, get_available_gestes
from ..calculators.mobility import calculate_mobility_aids, check_zfe_vehicle
from ..calculators.stacking import check_stacking
from ..calculators.eco_ptz import calculate_eco_ptz
from ..rag.retriever import search_anah_guide


# ── Tool schemas for Mistral function calling ────────────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "determine_income_bracket",
            "description": (
                "Détermine la tranche de revenus MaPrimeRénov' (bleu/jaune/violet/rose) "
                "à partir du revenu fiscal de référence, du nombre de personnes et de la localisation. "
                "Utilise les barèmes officiels ANAH 2026."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "rfr": {
                        "type": "integer",
                        "description": "Revenu fiscal de référence en euros (avis d'imposition N-1)"
                    },
                    "household_size": {
                        "type": "integer",
                        "description": "Nombre de personnes dans le foyer fiscal"
                    },
                    "is_ile_de_france": {
                        "type": "boolean",
                        "description": "true si le logement est en Île-de-France, false sinon"
                    }
                },
                "required": ["rfr", "household_size", "is_ile_de_france"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_mpr_par_geste",
            "description": (
                "Calcule le montant MaPrimeRénov' par geste pour une action de rénovation spécifique. "
                "Utilise le barème officiel ANAH 2026. Nécessite la tranche de revenus et le type de geste."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "bracket": {
                        "type": "string",
                        "enum": ["tres_modeste", "modeste", "intermediaire", "superieur"],
                        "description": "Tranche de revenus MaPrimeRénov'"
                    },
                    "geste_id": {
                        "type": "string",
                        "description": "Identifiant du geste de rénovation (ex: pac_air_eau, isolation_murs_exterieur, vmc_double_flux)"
                    },
                    "surface_m2": {
                        "type": "number",
                        "description": "Surface en m² (pour les gestes au m² comme l'isolation)"
                    },
                    "nb_equipements": {
                        "type": "integer",
                        "description": "Nombre d'équipements (pour les fenêtres par exemple)"
                    }
                },
                "required": ["bracket", "geste_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_mpr_ampleur",
            "description": (
                "Calcule le montant MaPrimeRénov' pour le parcours accompagné (rénovation d'ampleur). "
                "Nécessite le DPE actuel, le DPE cible, le coût HT des travaux et la tranche de revenus."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "bracket": {
                        "type": "string",
                        "enum": ["tres_modeste", "modeste", "intermediaire", "superieur"],
                        "description": "Tranche de revenus"
                    },
                    "current_dpe": {
                        "type": "string",
                        "enum": ["A", "B", "C", "D", "E", "F", "G"],
                        "description": "Classe DPE actuelle du logement"
                    },
                    "target_dpe": {
                        "type": "string",
                        "enum": ["A", "B", "C", "D", "E", "F", "G"],
                        "description": "Classe DPE cible après rénovation"
                    },
                    "cost_ht": {
                        "type": "number",
                        "description": "Coût total des travaux hors taxes en euros"
                    }
                },
                "required": ["bracket", "current_dpe", "target_dpe", "cost_ht"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_mobility_aid",
            "description": (
                "Calcule toutes les aides mobilité applicables : prime coup de pouce VE, prime à la conversion, "
                "surprime ZFE, bonus vélo, microcrédit mobilité. Nécessite le RFR, la taille du foyer et le projet de mobilité."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "rfr": {
                        "type": "integer",
                        "description": "Revenu fiscal de référence en euros"
                    },
                    "household_size": {
                        "type": "integer",
                        "description": "Nombre de personnes dans le foyer"
                    },
                    "is_zfe_resident": {
                        "type": "boolean",
                        "description": "true si la personne réside ou travaille dans une ZFE"
                    },
                    "scrapping_old_vehicle": {
                        "type": "boolean",
                        "description": "true si l'ancien véhicule sera mis au rebut"
                    },
                    "old_vehicle_critair": {
                        "type": "string",
                        "description": "Vignette Crit'Air de l'ancien véhicule (0-5 ou non_classe)"
                    },
                    "target_vehicle_type": {
                        "type": "string",
                        "enum": ["voiture_electrique", "voiture_hybride_rechargeable", "velo_electrique", "velo_cargo_electrique"],
                        "description": "Type de véhicule envisagé"
                    }
                },
                "required": ["rfr", "household_size", "target_vehicle_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_zfe_vehicle",
            "description": (
                "Vérifie si un véhicule est autorisé dans la zone ZFE d'une commune donnée. "
                "Retourne le statut d'interdiction, l'historique de la ZFE et le montant des amendes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "critair": {
                        "type": "string",
                        "description": "Vignette Crit'Air du véhicule (0-5 ou non_classe)"
                    },
                    "commune": {
                        "type": "string",
                        "description": "Nom de la commune"
                    },
                    "vehicle_category": {
                        "type": "string",
                        "enum": ["VL", "VUL", "PL"],
                        "description": "Catégorie de véhicule : VL (voiture), VUL (utilitaire), PL (poids lourd)"
                    }
                },
                "required": ["critair", "commune"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_stacking",
            "description": (
                "Vérifie la compatibilité entre plusieurs aides (cumul). "
                "Retourne si les aides sont cumulables, les avertissements et les plafonds globaux."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "aid_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste des identifiants des aides à vérifier (ex: ['mpr_par_geste', 'cee_coup_de_pouce', 'eco_ptz'])"
                    },
                    "total_cost": {
                        "type": "number",
                        "description": "Coût total des travaux TTC en euros (pour vérifier le plafond)"
                    }
                },
                "required": ["aid_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_eco_ptz",
            "description": (
                "Calcule l'Éco-PTZ (prêt à taux zéro) applicable. "
                "Le montant dépend du nombre de gestes et du type de parcours."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "parcours": {
                        "type": "string",
                        "enum": ["par_geste", "ampleur"],
                        "description": "Parcours de rénovation"
                    },
                    "nb_gestes": {
                        "type": "integer",
                        "description": "Nombre de gestes de rénovation (pour parcours par geste)"
                    },
                    "cost_remaining": {
                        "type": "number",
                        "description": "Reste à charge en euros après déduction des aides"
                    }
                },
                "required": ["parcours"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_anah_guide",
            "description": (
                "Recherche dans le Guide des aides financières ANAH 2026 pour trouver des informations "
                "sur les conditions d'éligibilité, les procédures, les documents nécessaires, etc. "
                "À utiliser pour les questions qualitatives (pas pour les montants, qui doivent utiliser les calculateurs)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question ou requête de recherche en français"
                    }
                },
                "required": ["query"]
            }
        }
    },
]


# ── Tool dispatch ─────────────────────────────────────────────────────────

def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool call and return the result as a string."""
    import json

    dispatchers = {
        "determine_income_bracket": lambda args: determine_income_bracket(
            rfr=args["rfr"],
            household_size=args["household_size"],
            is_ile_de_france=args["is_ile_de_france"],
        ),
        "calculate_mpr_par_geste": lambda args: calculate_mpr_par_geste(
            bracket=args["bracket"],
            geste_id=args["geste_id"],
            surface_m2=args.get("surface_m2"),
            nb_equipements=args.get("nb_equipements"),
        ),
        "calculate_mpr_ampleur": lambda args: calculate_mpr_ampleur(
            bracket=args["bracket"],
            current_dpe=args["current_dpe"],
            target_dpe=args["target_dpe"],
            cost_ht=args["cost_ht"],
        ),
        "calculate_mobility_aid": lambda args: calculate_mobility_aids(
            rfr=args["rfr"],
            household_size=args["household_size"],
            is_zfe_resident=args.get("is_zfe_resident", False),
            scrapping_old_vehicle=args.get("scrapping_old_vehicle", False),
            old_vehicle_critair=args.get("old_vehicle_critair"),
            target_vehicle_type=args.get(
                "target_vehicle_type", "voiture_electrique"),
        ),
        "check_zfe_vehicle": lambda args: check_zfe_vehicle(
            critair=args["critair"],
            commune=args["commune"],
            vehicle_category=args.get("vehicle_category", "VL"),
        ),
        "check_stacking": lambda args: check_stacking(
            aid_ids=args["aid_ids"],
            total_cost=args.get("total_cost", 0),
        ),
        "calculate_eco_ptz": lambda args: calculate_eco_ptz(
            parcours=args["parcours"],
            nb_gestes=args.get("nb_gestes", 1),
            cost_remaining=args.get("cost_remaining", 0),
        ),
        "search_anah_guide": lambda args: search_anah_guide(
            query=args["query"],
        ),
    }

    dispatcher = dispatchers.get(tool_name)
    if dispatcher is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = dispatcher(arguments)
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
