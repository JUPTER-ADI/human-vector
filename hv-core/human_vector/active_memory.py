"""HUMAN VECTOR — M07 Active Memory.

Active Memory contains only outputs accepted with canonical Selector PASS.
It is bounded by configurable capacity and optional configurable age.

M07_ACTIVE_MEMORY_V1
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable


ALLOWED_RELATIONS = {
    "SUPERSEDES",
    "COMPLEMENTS",
    "BRANCHES_FROM",
    "STILL_CURRENT",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


@dataclass
class ActiveMemoryEntry:
    entry_id: str
    content: str
    content_hash: str
    created_at: datetime
    last_accessed_at: datetime
    access_count: int = 0
    relation: str = "STILL_CURRENT"
    related_entry_id: str | None = None
    source: str = "CANONICAL_SELECTOR_PASS"

    def touch(self) -> None:
        self.last_accessed_at = _utc_now()
        self.access_count += 1

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "content": self.content,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "access_count": self.access_count,
            "relation": self.relation,
            "related_entry_id": self.related_entry_id,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ActiveMemoryEntry":
        return cls(
            entry_id=str(payload["entry_id"]),
            content=str(payload["content"]),
            content_hash=str(payload["content_hash"]),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            last_accessed_at=datetime.fromisoformat(
                str(payload["last_accessed_at"])
            ),
            access_count=int(payload.get("access_count", 0)),
            relation=str(payload.get("relation", "STILL_CURRENT")),
            related_entry_id=payload.get("related_entry_id"),
            source=str(
                payload.get(
                    "source",
                    "CANONICAL_SELECTOR_PASS",
                )
            ),
        )


class ActiveMemory:
    """Bounded memory containing canonical PASS outputs only."""

    def __init__(
        self,
        *,
        max_items: int | None = None,
        max_age_seconds: int | None = None,
    ) -> None:
        if max_items is not None and max_items <= 0:
            raise ValueError("max_items must be positive or None.")

        if max_age_seconds is not None and max_age_seconds <= 0:
            raise ValueError(
                "max_age_seconds must be positive or None."
            )

        self.max_items = max_items
        self.max_age_seconds = max_age_seconds
        self._entries: list[ActiveMemoryEntry] = []

    @property
    def entries(self) -> tuple[ActiveMemoryEntry, ...]:
        return tuple(self._entries)

    def record_selector_pass(
        self,
        *,
        entry_id: str,
        content: str,
        selector_decision: str,
        relation: str = "STILL_CURRENT",
        related_entry_id: str | None = None,
    ) -> ActiveMemoryEntry:
        decision = str(selector_decision).strip().upper()

        if decision != "PASS":
            raise ValueError(
                "Active Memory accepts only canonical Selector PASS outputs."
            )

        relation = str(relation).strip().upper()
        if relation not in ALLOWED_RELATIONS:
            raise ValueError(
                f"Unsupported Active Memory relation: {relation}"
            )

        normalized_content = str(content).strip()
        if not normalized_content:
            raise ValueError(
                "Active Memory PASS content cannot be empty."
            )

        content_hash = _content_hash(normalized_content)

        for existing in self._entries:
            if existing.content_hash == content_hash:
                existing.touch()
                return existing

        now = _utc_now()

        entry = ActiveMemoryEntry(
            entry_id=str(entry_id),
            content=normalized_content,
            content_hash=content_hash,
            created_at=now,
            last_accessed_at=now,
            access_count=0,
            relation=relation,
            related_entry_id=related_entry_id,
        )

        self._entries.append(entry)
        self.prune()

        return entry

    def get(self, entry_id: str) -> ActiveMemoryEntry | None:
        self.prune()

        for entry in self._entries:
            if entry.entry_id == entry_id:
                entry.touch()
                return entry

        return None

    def relevant_entries(
        self,
        entry_ids: Iterable[str] | None = None,
    ) -> tuple[ActiveMemoryEntry, ...]:
        self.prune()

        if entry_ids is None:
            selected = list(self._entries)
        else:
            wanted = {str(item) for item in entry_ids}
            selected = [
                entry
                for entry in self._entries
                if entry.entry_id in wanted
            ]

        for entry in selected:
            entry.touch()

        return tuple(selected)

    def prune(self) -> tuple[str, ...]:
        """Apply configured age and capacity limits."""

        removed: list[str] = []
        now = _utc_now()

        if self.max_age_seconds is not None:
            retained: list[ActiveMemoryEntry] = []

            for entry in self._entries:
                age = (now - entry.last_accessed_at).total_seconds()

                if age > self.max_age_seconds:
                    removed.append(entry.entry_id)
                else:
                    retained.append(entry)

            self._entries = retained

        if (
            self.max_items is not None
            and len(self._entries) > self.max_items
        ):
            ranked = sorted(
                self._entries,
                key=lambda item: (
                    item.last_accessed_at,
                    item.access_count,
                    item.created_at,
                ),
            )

            remove_count = len(self._entries) - self.max_items
            to_remove = {
                item.entry_id
                for item in ranked[:remove_count]
            }

            removed.extend(
                entry.entry_id
                for entry in self._entries
                if entry.entry_id in to_remove
            )

            self._entries = [
                entry
                for entry in self._entries
                if entry.entry_id not in to_remove
            ]

        return tuple(dict.fromkeys(removed))

    def to_dict(self) -> dict:
        self.prune()

        return {
            "max_items": self.max_items,
            "max_age_seconds": self.max_age_seconds,
            "entries": [
                entry.to_dict()
                for entry in self._entries
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ActiveMemory":
        memory = cls(
            max_items=payload.get("max_items"),
            max_age_seconds=payload.get("max_age_seconds"),
        )

        memory._entries = [
            ActiveMemoryEntry.from_dict(item)
            for item in payload.get("entries", [])
        ]

        memory.prune()
        return memory
