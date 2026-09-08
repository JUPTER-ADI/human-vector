from __future__ import annotations

from dataclasses import dataclass

from .orchestrator import SystemOrchestrator
from .session_persistence import (
    build_session_envelope,
    ensure_session_id,
    load_session_envelope,
    save_session_envelope,
)


@dataclass
class SessionContext:
    user_id: str
    actor_id: str
    actor_role: str
    orchestrator: SystemOrchestrator

    @property
    def session_id(self) -> str:
        return ensure_session_id(self.orchestrator)

    def envelope(self) -> dict:
        return build_session_envelope(
            self.orchestrator,
            user_id=self.user_id,
            actor_id=self.actor_id,
            actor_role=self.actor_role,
        )


class SessionController:
    """Own active HUMAN VECTOR sessions without bypassing CORE authority."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}

    def save_session(self, session_id: str, path: str) -> None:
        context = self.require_session(session_id)
        save_session_envelope(
            context.orchestrator,
            path,
            user_id=context.user_id,
            actor_id=context.actor_id,
            actor_role=context.actor_role,
        )

    def load_session(self, path: str) -> SessionContext:
        loaded = load_session_envelope(path)
        identity = loaded["identity"]
        orchestrator = loaded["orchestrator"]

        context = SessionContext(
            user_id=identity["user_id"],
            actor_id=identity["actor_id"],
            actor_role=identity["actor_role"],
            orchestrator=orchestrator,
        )

        self._sessions[context.session_id] = context
        return context

    def create_session(
        self,
        *,
        user_id: str,
        actor_id: str,
        actor_role: str,
    ) -> SessionContext:
        if not user_id.strip():
            raise ValueError("user_id is required")
        if not actor_id.strip():
            raise ValueError("actor_id is required")
        if not actor_role.strip():
            raise ValueError("actor_role is required")

        orchestrator = SystemOrchestrator()
        session_id = ensure_session_id(orchestrator)

        context = SessionContext(
            user_id=user_id,
            actor_id=actor_id,
            actor_role=actor_role,
            orchestrator=orchestrator,
        )

        self._sessions[session_id] = context
        return context

    def get_session(self, session_id: str) -> SessionContext | None:
        return self._sessions.get(session_id)

    def require_session(self, session_id: str) -> SessionContext:
        context = self.get_session(session_id)
        if context is None:
            raise KeyError(f"Unknown session_id: {session_id}")
        return context

    def active_session_count(self) -> int:
        return len(self._sessions)


    def require_session_for_user(
        self,
        *,
        session_id: str,
        user_id: str,
    ) -> SessionContext:
        context = self.require_session(session_id)

        if context.user_id != user_id:
            raise PermissionError("Session does not belong to this user")

        return context


    def close_session_for_user(
        self,
        *,
        session_id: str,
        user_id: str,
    ) -> SessionContext:
        context = self.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )

        del self._sessions[session_id]
        return context
