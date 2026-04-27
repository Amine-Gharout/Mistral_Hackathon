"""Chat router — handles the conversational AI endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

from ..services.session_store import session_store
from ..agents.orchestrator import run_agent_turn, run_agent_turn_stream

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="fr", pattern="^(fr|en)$")
    demo_mode: bool = False
    demo_profile: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    language: str
    profile_summary: Optional[dict] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI advisor and get a response."""
    # Get or create session
    session = None
    if request.session_id:
        session = session_store.get_session(request.session_id)

    if session is None:
        session = session_store.create_session(
            language=request.language,
            demo_mode=request.demo_mode,
            demo_profile=request.demo_profile,
        )

    # Update language if changed
    session.language = request.language

    # Run the agent
    try:
        response_text = await run_agent_turn(request.message, session)
    except Exception as e:
        print(f"[Chat] Error in agent turn: {e}")
        raise HTTPException(
            status_code=500, detail="Erreur interne du conseiller IA")

    # Build profile summary for frontend
    profile = session.citizen_profile
    profile_summary = {}
    if profile.rfr is not None:
        profile_summary["rfr"] = profile.rfr
    if profile.household_size is not None:
        profile_summary["household_size"] = profile.household_size
    if profile.income_bracket:
        profile_summary["income_bracket"] = profile.income_bracket.value
    if profile.bracket_color:
        profile_summary["bracket_color"] = profile.bracket_color.value
    if profile.commune:
        profile_summary["commune"] = profile.commune
    if profile.property:
        p = profile.property
        if p.dpe_class:
            profile_summary["dpe_class"] = p.dpe_class.value
        if p.type:
            profile_summary["property_type"] = p.type.value
        if p.surface_m2:
            profile_summary["surface_m2"] = p.surface_m2

    return ChatResponse(
        session_id=session.session_id,
        response=response_text,
        language=session.language,
        profile_summary=profile_summary if profile_summary else None,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Send a message and receive a streaming SSE response with real-time tokens."""
    # Get or create session
    session = None
    if request.session_id:
        session = session_store.get_session(request.session_id)

    if session is None:
        session = session_store.create_session(
            language=request.language,
            demo_mode=request.demo_mode,
            demo_profile=request.demo_profile,
        )

    session.language = request.language

    import json

    async def event_generator():
        # First event: send session_id so the client can track it
        yield f"data: {json.dumps({'type': 'session', 'session_id': session.session_id})}\n\n"

        try:
            async for event in run_agent_turn_stream(request.message, session):
                yield event
        except Exception as e:
            print(f"[Chat-Stream] Error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Erreur interne du conseiller IA'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class SessionCreateRequest(BaseModel):
    language: str = Field(default="fr", pattern="^(fr|en)$")
    demo_mode: bool = False
    demo_profile: Optional[str] = None


class SessionCreateResponse(BaseModel):
    session_id: str
    demo_mode: bool
    welcome_message: str


@router.post("/session", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest):
    """Create a new chat session."""
    session = session_store.create_session(
        language=request.language,
        demo_mode=request.demo_mode,
        demo_profile=request.demo_profile,
    )

    if request.language == "fr":
        welcome = (
            "Bonjour ! Je suis **GreenRights**, votre conseiller en aides à la transition écologique. 🌿\n\n"
            "Je peux vous aider à découvrir les aides financières pour :\n"
            "- 🏠 **La rénovation énergétique** de votre logement (MaPrimeRénov', CEE, Éco-PTZ…)\n"
            "- 🚗 **La mobilité propre** (prime à la conversion, bonus vélo, prime ZFE…)\n\n"
            "Par quoi souhaitez-vous commencer ?"
        )
    else:
        welcome = (
            "Hello! I'm **GreenRights**, your green transition subsidy advisor. 🌿\n\n"
            "I can help you discover financial aids for:\n"
            "- 🏠 **Home energy renovation** (MaPrimeRénov', CEE, Éco-PTZ…)\n"
            "- 🚗 **Clean mobility** (trade-in bonus, e-bike bonus, ZFE premium…)\n\n"
            "What would you like to start with?"
        )

    if request.demo_mode and request.demo_profile:
        welcome += f"\n\n*Mode démo activé avec le profil **{request.demo_profile}**. Vos informations ont été pré-remplies.*"

    return SessionCreateResponse(
        session_id=session.session_id,
        demo_mode=session.demo_mode,
        welcome_message=welcome,
    )


@router.get("/session/{session_id}/history")
async def get_history(session_id: str):
    """Get conversation history for a session."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in session.conversation_history
        ],
        "language": session.language,
    }
