"""HUMAN VECTOR — M07 Working / Internal Memory.

Temporary working memory for HUMAN requests and Builder variants evaluated
inside Canonical Selector cycles.

M07_WORKING_MEMORY_V1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


@dataclass
class WorkingBuilderVersion:
    round: int
    content: str
    content_hash: str
    created_at: datetime
    selector_decision: str | None = None
    selector_reasons: tuple[str, ...] = ()
    reconstruction_requirements: tuple[str, ...] = ()

    def apply_selector_result(
        self,
        *,
        decision: str,
        reasons: tuple[str, ...] = (),
        reconstruction_requirements: tuple[str, ...] = (),
    ) -> None:
        self.selector_decision = str(decision).strip().upper()
        self.selector_reasons = tuple(str(x) for x in reasons)
        self.reconstruction_requirements = tuple(
            str(x) for x in reconstruction_requirements
        )

    def to_dict(self) -> dict:
        return {
            "round": self.round,
            "content": self.content,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
            "selector_decision": self.selector_decision,
            "selector_reasons": list(self.selector_reasons),
            "reconstruction_requirements": list(
                self.reconstruction_requirements
            ),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "WorkingBuilderVersion":
        return cls(
            round=int(payload["round"]),
            content=str(payload["content"]),
            content_hash=str(payload["content_hash"]),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            selector_decision=payload.get("selector_decision"),
            selector_reasons=tuple(payload.get("selector_reasons", [])),
            reconstruction_requirements=tuple(
                payload.get("reconstruction_requirements", [])
            ),
        )


@dataclass
class WorkingCycle:
    cycle_id: str
    human_request: str
    human_request_hash: str
    created_at: datetime
    builder_versions: list[WorkingBuilderVersion] = field(
        default_factory=list
    )

    def add_builder_version(
        self,
        *,
        round: int,
        content: str,
    ) -> WorkingBuilderVersion:
        normalized = str(content).strip()

        if not normalized:
            raise ValueError("Builder working-memory content cannot be empty.")

        version = WorkingBuilderVersion(
            round=int(round),
            content=normalized,
            content_hash=_content_hash(normalized),
            created_at=_utc_now(),
        )

        self.builder_versions.append(version)
        return version

    def get_round(
        self,
        round: int,
    ) -> WorkingBuilderVersion | None:
        for version in reversed(self.builder_versions):
            if version.round == int(round):
                return version
        return None

    def to_dict(self) -> dict:
        return {
            "cycle_id": self.cycle_id,
            "human_request": self.human_request,
            "human_request_hash": self.human_request_hash,
            "created_at": self.created_at.isoformat(),
            "builder_versions": [
                item.to_dict()
                for item in self.builder_versions
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "WorkingCycle":
        return cls(
            cycle_id=str(payload["cycle_id"]),
            human_request=str(payload["human_request"]),
            human_request_hash=str(payload["human_request_hash"]),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            builder_versions=[
                WorkingBuilderVersion.from_dict(item)
                for item in payload.get("builder_versions", [])
            ],
        )


class WorkingMemory:
    """Temporary bounded memory for HUMAN/Builder/Selector working cycles."""

    def __init__(
        self,
        *,
        max_cycles: int | None = None,
    ) -> None:
        if max_cycles is not None and max_cycles <= 0:
            raise ValueError("max_cycles must be positive or None.")

        self.max_cycles = max_cycles
        self._cycles: list[WorkingCycle] = []

    @property
    def cycles(self) -> tuple[WorkingCycle, ...]:
        return tuple(self._cycles)

    def open_cycle(
        self,
        *,
        cycle_id: str,
        human_request: str,
    ) -> WorkingCycle:
        normalized = str(human_request).strip()

        if not normalized:
            raise ValueError("HUMAN request cannot be empty.")

        for cycle in self._cycles:
            if cycle.cycle_id == str(cycle_id):
                return cycle

        cycle = WorkingCycle(
            cycle_id=str(cycle_id),
            human_request=normalized,
            human_request_hash=_content_hash(normalized),
            created_at=_utc_now(),
        )

        self._cycles.append(cycle)
        self.prune()
        return cycle

    def get_cycle(
        self,
        cycle_id: str,
    ) -> WorkingCycle | None:
        for cycle in self._cycles:
            if cycle.cycle_id == str(cycle_id):
                return cycle
        return None

    def prune(self) -> tuple[str, ...]:
        removed: list[str] = []

        if (
            self.max_cycles is not None
            and len(self._cycles) > self.max_cycles
        ):
            remove_count = len(self._cycles) - self.max_cycles
            removed = [
                cycle.cycle_id
                for cycle in self._cycles[:remove_count]
            ]
            self._cycles = self._cycles[remove_count:]

        return tuple(removed)

    def to_dict(self) -> dict:
        self.prune()

        return {
            "max_cycles": self.max_cycles,
            "cycles": [
                cycle.to_dict()
                for cycle in self._cycles
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "WorkingMemory":
        memory = cls(
            max_cycles=payload.get("max_cycles"),
        )

        memory._cycles = [
            WorkingCycle.from_dict(item)
            for item in payload.get("cycles", [])
        ]

        memory.prune()
        return memory
