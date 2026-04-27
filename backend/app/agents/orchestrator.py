"""Agentic orchestrator — manages the LLM conversation loop with tool calling."""

from __future__ import annotations

import json
from typing import Optional, AsyncGenerator

from mistralai import Mistral

from ..config import settings
from ..models.session import SessionState
from ..models.citizen import IncomeBracket, BracketColor, BRACKET_COLOR_MAP
from .prompts import get_system_prompt
from .tools import TOOL_DEFINITIONS, execute_tool


_client: Optional[Mistral] = None


def _get_client() -> Mistral:
    global _client
    if _client is None:
        _client = Mistral(api_key=settings.MISTRAL_API_KEY)
    return _client


async def run_agent_turn(
    user_message: str,
    session: SessionState,
) -> str:
    """
    Run one full agent turn: send user message, handle tool calls, return final response.

    Args:
        user_message: The user's message
        session: Current session state (modified in-place)

    Returns:
        The assistant's final text response
    """
    client = _get_client()

    # Add user message to history
    session.add_message("user", user_message)

    # Build messages for the API call
    messages = _build_messages(session)

    # Agentic loop: keep calling the model until we get a final text response
    max_iterations = 10
    for iteration in range(max_iterations):
        response = await client.chat.complete_async(
            model=settings.MISTRAL_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        choice = response.choices[0]
        message = choice.message

        # Check if the model wants to call tools
        if message.tool_calls and len(message.tool_calls) > 0:
            # Add assistant message with tool calls to history
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ],
            })

            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                print(
                    f"[Agent] Calling tool: {tool_name}({json.dumps(arguments, ensure_ascii=False)[:200]})")

                # Execute the tool
                result = execute_tool(tool_name, arguments)

                # Update citizen profile from tool results
                _update_profile_from_tool(
                    session, tool_name, arguments, result)

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": result,
                    "tool_call_id": tool_call.id,
                })
        else:
            # Final text response (no more tool calls)
            assistant_text = message.content or ""
            session.add_message("assistant", assistant_text)
            return assistant_text

    # Safety: if we exceed max iterations
    fallback = "Je m'excuse, j'ai rencontré une difficulté technique. Pouvez-vous reformuler votre question ?"
    session.add_message("assistant", fallback)
    return fallback


async def run_agent_turn_stream(
    user_message: str,
    session: SessionState,
) -> AsyncGenerator[str, None]:
    """
    Run one full agent turn with streaming.
    Yields SSE-formatted events:
      - data: {"type":"tool","name":"..."}    → tool is being called
      - data: {"type":"token","content":"..."} → streamed text token
      - data: {"type":"profile","data":{...}}  → updated profile
      - data: {"type":"done"}                  → stream complete
    """
    client = _get_client()
    session.add_message("user", user_message)
    messages = _build_messages(session)

    max_iterations = 10
    for iteration in range(max_iterations):
        full_text = ""
        tool_calls_by_index: dict[int, dict] = {}

        stream = await client.chat.stream_async(
            model=settings.MISTRAL_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )
        async for chunk in stream:
            delta = chunk.data.choices[0].delta

            if delta.content:
                full_text += delta.content
                yield f"data: {json.dumps({'type': 'token', 'content': delta.content}, ensure_ascii=False)}\n\n"

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = getattr(tc, "index", 0)
                    existing = tool_calls_by_index.setdefault(
                        idx,
                        {
                            "id": None,
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        },
                    )

                    tc_id = getattr(tc, "id", None)
                    if tc_id:
                        existing["id"] = tc_id

                    tc_type = getattr(tc, "type", None)
                    if tc_type:
                        existing["type"] = tc_type

                    tc_function = getattr(tc, "function", None)
                    if tc_function:
                        name_part = getattr(tc_function, "name", None)
                        args_part = getattr(tc_function, "arguments", None)
                        if name_part:
                            existing["function"]["name"] = name_part
                        if args_part:
                            existing["function"]["arguments"] += args_part

        tool_calls = []
        for idx in sorted(tool_calls_by_index.keys()):
            tc = tool_calls_by_index[idx]
            if not tc["function"]["name"]:
                continue
            if not tc["id"]:
                tc["id"] = f"tool_call_{idx}"
            tool_calls.append(tc)

        if tool_calls:
            messages.append({
                "role": "assistant",
                "content": full_text,
                "tool_calls": tool_calls,
            })

            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args_str = tool_call["function"]["arguments"] or "{}"
                try:
                    arguments = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    arguments = {}

                print(
                    f"[Agent-Stream] Calling tool: {tool_name}({json.dumps(arguments, ensure_ascii=False)[:200]})")

                yield f"data: {json.dumps({'type': 'tool', 'name': tool_name}, ensure_ascii=False)}\n\n"

                result = execute_tool(tool_name, arguments)
                _update_profile_from_tool(session, tool_name, arguments, result)

                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": result,
                    "tool_call_id": tool_call["id"],
                })

            profile_data = _get_profile_dict(session)
            if profile_data:
                yield f"data: {json.dumps({'type': 'profile', 'data': profile_data}, ensure_ascii=False)}\n\n"
            continue

        session.add_message("assistant", full_text)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # Safety fallback
    fallback = "Je m'excuse, j'ai rencontré une difficulté technique. Pouvez-vous reformuler votre question ?"
    session.add_message("assistant", fallback)
    yield f"data: {json.dumps({'type': 'token', 'content': fallback}, ensure_ascii=False)}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


def _get_profile_dict(session: SessionState) -> dict:
    """Build a profile summary dict for the frontend."""
    profile = session.citizen_profile
    d = {}
    if profile.rfr is not None:
        d["rfr"] = profile.rfr
    if profile.household_size is not None:
        d["household_size"] = profile.household_size
    if profile.income_bracket:
        d["income_bracket"] = profile.income_bracket.value
    if profile.bracket_color:
        d["bracket_color"] = profile.bracket_color.value
    if profile.commune:
        d["commune"] = profile.commune
    if profile.property:
        p = profile.property
        if p.dpe_class:
            d["dpe_class"] = p.dpe_class.value
        if p.type:
            d["property_type"] = p.type.value
        if p.surface_m2:
            d["surface_m2"] = p.surface_m2
    return d


def _build_messages(session: SessionState) -> list[dict]:
    """Build the full message list for the API call."""
    messages = []

    # System prompt
    system_prompt = get_system_prompt(session.language)

    # Add profile context to system prompt if we have data
    profile = session.citizen_profile
    profile_context = _get_profile_context(profile, session.language)
    if profile_context:
        system_prompt += f"\n\n## Profil citoyen actuel\n{profile_context}"

    # Add missing fields hint
    missing = profile.get_missing_fields()
    if missing:
        fields_fr = {
            "rfr": "revenu fiscal de référence",
            "household_size": "nombre de personnes dans le foyer",
            "is_ile_de_france": "localisation (Île-de-France ou non)",
            "commune": "commune de résidence",
            "dpe_class": "classe DPE du logement",
            "property_type": "type de logement (maison/appartement)",
            "heating_type": "type de chauffage actuel",
            "surface_m2": "surface du logement",
        }
        missing_labels = [fields_fr.get(f, f) for f in missing]
        system_prompt += f"\n\n## Informations manquantes\nIl manque encore : {', '.join(missing_labels)}."

    messages.append({"role": "system", "content": system_prompt})

    # Conversation history (last 20 messages to avoid context overflow)
    for msg in session.conversation_history[-20:]:
        messages.append({"role": msg.role, "content": msg.content})

    return messages


def _get_profile_context(profile, language: str = "fr") -> str:
    """Generate a text summary of the current citizen profile."""
    parts = []

    if profile.rfr is not None:
        parts.append(f"- RFR : {profile.rfr:,} €".replace(",", " "))
    if profile.household_size is not None:
        parts.append(f"- Foyer : {profile.household_size} personne(s)")
    if profile.is_ile_de_france is not None:
        region = "Île-de-France" if profile.is_ile_de_france else "Hors Île-de-France"
        parts.append(f"- Région : {region}")
    if profile.income_bracket:
        color = BRACKET_COLOR_MAP.get(
            IncomeBracket(profile.income_bracket), "")
        parts.append(
            f"- Tranche : {profile.income_bracket} ({color.value if color else ''})")
    if profile.commune:
        parts.append(f"- Commune : {profile.commune}")
    if profile.property:
        p = profile.property
        if p.type:
            parts.append(f"- Logement : {p.type.value}")
        if p.dpe_class:
            parts.append(f"- DPE : {p.dpe_class.value}")
        if p.surface_m2:
            parts.append(f"- Surface : {p.surface_m2} m²")
        if p.heating_type:
            parts.append(f"- Chauffage : {p.heating_type.value}")
        if p.construction_year:
            parts.append(f"- Construction : {p.construction_year}")
    if profile.vehicle:
        v = profile.vehicle
        if v.critair:
            parts.append(f"- Crit'Air : {v.critair}")
        if v.fuel_type:
            parts.append(f"- Carburant : {v.fuel_type.value}")
    if profile.planned_renovations:
        gestes = [r.geste_id for r in profile.planned_renovations]
        parts.append(f"- Travaux prévus : {', '.join(gestes)}")

    return "\n".join(parts) if parts else ""


def _update_profile_from_tool(
    session: SessionState,
    tool_name: str,
    arguments: dict,
    result_str: str,
):
    """Update the citizen profile based on tool call results."""
    profile = session.citizen_profile

    try:
        result = json.loads(result_str) if isinstance(
            result_str, str) else result_str
    except (json.JSONDecodeError, TypeError):
        return

    if tool_name == "determine_income_bracket":
        if isinstance(result, dict) and "bracket" in result:
            profile.income_bracket = IncomeBracket(result["bracket"])
            profile.bracket_color = BracketColor(result["color"])
            profile.rfr = arguments.get("rfr", profile.rfr)
            profile.household_size = arguments.get(
                "household_size", profile.household_size)
            profile.is_ile_de_france = arguments.get(
                "is_ile_de_france", profile.is_ile_de_france)

    elif tool_name == "check_zfe_vehicle":
        if isinstance(result, dict):
            if result.get("in_zfe"):
                # Update that they're in a ZFE
                profile.commune = arguments.get("commune", profile.commune)
            if profile.vehicle and arguments.get("critair"):
                profile.vehicle.critair = arguments["critair"]

    # ── Collect computed aids into session.aids_computed ──
    _collect_aid_result(session, tool_name, result)


# Tools whose results represent computed aid data that should be stored
_AID_TOOLS = {
    "calculate_mpr_par_geste",
    "calculate_mpr_ampleur",
    "calculate_mobility_aid",
    "calculate_eco_ptz",
    "calculate_cee_estimate",
}


def _collect_aid_result(session: SessionState, tool_name: str, result):
    """Store tool results that represent computed aids into session.aids_computed."""
    if tool_name not in _AID_TOOLS:
        return
    if not isinstance(result, dict):
        return

    if tool_name == "calculate_mobility_aid":
        # Mobility returns {"aids": [...], ...} — unpack individual aids
        for aid in result.get("aids", []):
            if isinstance(aid, dict) and aid.get("eligible", True):
                aid.setdefault("category", "mobility")
                session.aids_computed.append(aid)
    else:
        # Single aid result
        if result.get("eligible", True):
            if tool_name == "calculate_eco_ptz":
                result.setdefault("category", "loan")
            else:
                result.setdefault("category", "renovation")
            session.aids_computed.append(result)
