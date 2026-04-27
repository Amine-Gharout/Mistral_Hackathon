"""In-memory session store with TTL-based cleanup."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from ..config import settings
from ..models.session import SessionState
from ..models.citizen import CitizenProfile


class SessionStore:
    """In-memory session store with automatic cleanup of expired sessions."""

    def __init__(self, ttl_hours: int = 24):
        self._sessions: dict[str, SessionState] = {}
        self._ttl = timedelta(hours=ttl_hours)
        self._cleanup_task: Optional[asyncio.Task] = None

    def create_session(
        self,
        language: str = "fr",
        demo_mode: bool = False,
        demo_profile: Optional[str] = None,
    ) -> SessionState:
        """Create a new session and return it."""
        session = SessionState(
            session_id=str(uuid.uuid4()),
            language=language,
            demo_mode=demo_mode,
        )

        # Load demo profile if requested
        if demo_mode and demo_profile:
            self._load_demo_profile(session, demo_profile)

        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieve a session by ID. Returns None if not found or expired."""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        # Check TTL
        now = datetime.now(timezone.utc)
        if now - session.created_at > self._ttl:
            del self._sessions[session_id]
            return None
        # Update last access
        session.updated_at = now
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        return self._sessions.pop(session_id, None) is not None

    def get_session_count(self) -> int:
        """Return the number of active sessions."""
        return len(self._sessions)

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns number removed."""
        now = datetime.now(timezone.utc)
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.created_at > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    async def start_cleanup_loop(self, interval_minutes: int = 30):
        """Start a background task that periodically cleans expired sessions."""
        async def _loop():
            while True:
                await asyncio.sleep(interval_minutes * 60)
                removed = self.cleanup_expired()
                if removed > 0:
                    print(f"[SessionStore] Cleaned {removed} expired sessions")

        self._cleanup_task = asyncio.create_task(_loop())

    def stop_cleanup_loop(self):
        """Stop the background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    def _load_demo_profile(self, session: SessionState, profile_name: str):
        """Load a demo profile into the session."""
        import json
        from ..config import settings

        demo_path = settings.DATA_DIR / "demo_profiles.json"
        if not demo_path.exists():
            return

        with open(demo_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        raw = profiles.get("profiles", [])
        data = None
        if isinstance(raw, list):
            data = next((p for p in raw if p.get("id") ==
                        profile_name or p.get("name") == profile_name), None)
        elif isinstance(raw, dict):
            data = raw.get(profile_name)

        if data is None:
            return
        profile = session.citizen_profile

        # Map demo profile fields to CitizenProfile
        if "rfr" in data:
            profile.rfr = data["rfr"]
        if "household_size" in data:
            profile.household_size = data["household_size"]
        if "is_ile_de_france" in data:
            profile.is_ile_de_france = data["is_ile_de_france"]
        if "commune" in data:
            profile.commune = data["commune"]
        if "income_bracket" in data:
            from ..models.citizen import IncomeBracket
            profile.income_bracket = IncomeBracket(data["income_bracket"])

        # Property
        if "dpe_class" in data or "property_type" in data:
            from ..models.citizen import PropertyProfile, DPEClass, PropertyType
            profile.property = PropertyProfile()
            if "dpe_class" in data:
                profile.property.dpe_class = DPEClass(data["dpe_class"])
            if "property_type" in data:
                profile.property.type = PropertyType(data["property_type"])
            if "surface_m2" in data:
                profile.property.surface_m2 = data["surface_m2"]

        # Vehicle
        if "critair" in data or "fuel_type" in data:
            from ..models.citizen import VehicleProfile, FuelType
            profile.vehicle = VehicleProfile()
            if "critair" in data:
                profile.vehicle.critair = data["critair"]
            if "fuel_type" in data:
                profile.vehicle.fuel_type = FuelType(data["fuel_type"])


# Singleton
session_store = SessionStore(ttl_hours=settings.SESSION_TTL_HOURS)
