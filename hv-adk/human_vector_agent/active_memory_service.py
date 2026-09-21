from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


MEMORY_ITEMS_COLLECTION = "memory_items"
MEMORY_RETRIEVAL_RUNS_COLLECTION = "memory_retrieval_runs"
MEMORY_RETRIEVAL_RESULTS_COLLECTION = "memory_retrieval_results"

MEMORY_USE_CLASSES = frozenset(
    {
        "PROCEDURAL_CONTEXT",
        "COGNITIVE_MEMORY",
        "NORMATIVE_REFERENCE",
    }
)

MEMORY_SEMANTIC_TYPES = frozenset(
    {
        "DIRECTION_MEMORY",
        "HUMAN_CONTRIBUTION_MEMORY",
        "CRITIQUE_MEMORY",
        "CONFLICT_MEMORY",
        "DECISION_MEMORY",
        "VERSION_MEMORY",
        "PROCESS_MEMORY",
        "PROJECT_MEMORY",
        "EPISODIC_MEMORY",
    }
)

_REQUIRED_KEYS = (
    "id",
    "project_id",
    "source_session_id",
    "source_object_type",
    "source_object_id",
    "memory_use_class",
    "memory_semantic_type",
    "scope_level",
    "content",
    "summary",
    "author_type",
    "author_id",
    "reason_for_storage",
    "confidence_level",
    "lifecycle_status",
)


class ActiveMemoryError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _stable_content_hash(payload: Mapping[str, Any]) -> str:
    excluded = {"content_hash", "created_at", "updated_at"}
    stable = {
        key: value
        for key, value in payload.items()
        if key not in excluded
    }
    return hashlib.sha256(
        _canonical_json(stable).encode("utf-8")
    ).hexdigest()


def _as_plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def _flatten_text(value: Any) -> str:
    value = _as_plain(value)

    if value is None:
        return ""

    if isinstance(value, Mapping):
        # Retrieval meaning comes from cognitive values, not technical
        # field names such as "objective" or "human_contribution".
        return " ".join(
            _flatten_text(item)
            for item in value.values()
        )

    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten_text(item) for item in value)

    return str(value)


_STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that",
    "este", "sunt", "pentru", "care", "din", "sau", "prin",
    "mai", "unei", "unui", "iar", "fara", "fără", "daca", "dacă",
}


def _tokens(value: Any) -> set[str]:
    text = _flatten_text(value).lower()
    raw = re.findall(r"\b[\wÀ-ž]{3,}\b", text, flags=re.UNICODE)
    return {
        token
        for token in raw
        if token not in _STOPWORDS
    }


def prepare_memory_item(item: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(item)

    missing = [
        key
        for key in _REQUIRED_KEYS
        if key not in payload
    ]
    if missing:
        raise ActiveMemoryError(
            "Canonical memory item missing fields: "
            + ", ".join(missing)
        )

    for key in (
        "id",
        "project_id",
        "source_session_id",
        "source_object_type",
        "source_object_id",
        "content",
        "summary",
        "author_type",
        "author_id",
        "reason_for_storage",
        "lifecycle_status",
    ):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ActiveMemoryError(
                f"Canonical memory field {key!r} must be non-empty text."
            )

    memory_use_class = payload["memory_use_class"]
    if memory_use_class not in MEMORY_USE_CLASSES:
        raise ActiveMemoryError(
            f"Unsupported memory_use_class: {memory_use_class!r}"
        )

    semantic_type = payload["memory_semantic_type"]
    if semantic_type not in MEMORY_SEMANTIC_TYPES:
        raise ActiveMemoryError(
            f"Unsupported memory_semantic_type: {semantic_type!r}"
        )

    payload.setdefault("source_branch_id", None)
    payload.setdefault("source_version_id", None)

    payload.setdefault("procedural_authorization_status", None)
    payload.setdefault("procedural_authorized_by", None)
    payload.setdefault("procedural_authorization_event_id", None)
    payload.setdefault("procedural_use_scope", None)

    payload.setdefault("review_date", None)
    payload.setdefault("supersedes_memory_id", None)

    now = _utc_now()
    payload.setdefault("created_at", now)
    payload["updated_at"] = now

    expected_hash = _stable_content_hash(payload)
    supplied_hash = payload.get("content_hash")

    if supplied_hash is not None and supplied_hash != expected_hash:
        raise ActiveMemoryError(
            "Canonical memory content_hash does not match payload."
        )

    payload["content_hash"] = expected_hash
    return payload


def store_memory_item(
    *,
    project_id: str,
    item: Mapping[str, Any],
    database: str = "(default)",
    client: Any = None,
) -> dict[str, Any]:
    payload = prepare_memory_item(item)

    if payload["project_id"] != project_id:
        raise ActiveMemoryError(
            "Memory project_id does not match requested project."
        )

    if client is None:
        from google.cloud import firestore

        client = firestore.Client(
            project=project_id,
            database=database,
        )

    ref = (
        client.collection(MEMORY_ITEMS_COLLECTION)
        .document(payload["id"])
    )

    existing = ref.get()
    if getattr(existing, "exists", False):
        existing_payload = existing.to_dict() or {}

        if existing_payload.get("content_hash") == payload["content_hash"]:
            return {
                "status": "UNCHANGED",
                "memory_id": payload["id"],
                "document_path": ref.path,
                "content_hash": payload["content_hash"],
            }

        raise ActiveMemoryError(
            "Canonical memory item already exists with different content."
        )

    ref.create(payload)

    return {
        "status": "CREATED",
        "memory_id": payload["id"],
        "document_path": ref.path,
        "content_hash": payload["content_hash"],
    }


def rank_memory_items(
    *,
    items: Iterable[Mapping[str, Any]],
    query_context: Mapping[str, Any],
    limit: int = 10,
    min_score: float = 0.0,
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ActiveMemoryError("limit must be >= 1.")

    query_tokens = _tokens(query_context)
    if not query_tokens:
        raise ActiveMemoryError(
            "Active Memory retrieval requires non-empty query context."
        )

    ranked: list[dict[str, Any]] = []

    for raw_item in items:
        item = dict(raw_item)

        if item.get("memory_use_class") != "COGNITIVE_MEMORY":
            continue

        # Cognitive relevance must be demonstrated by the stored
        # cognitive material itself. Administrative metadata must not
        # create a false-positive candidate.
        searchable = {
            "content": item.get("content"),
            "summary": item.get("summary"),
        }

        memory_tokens = _tokens(searchable)
        overlap = sorted(query_tokens & memory_tokens)

        if not overlap:
            continue

        denominator = max(1, min(len(query_tokens), 24))
        score = min(1.0, len(overlap) / denominator)

        if score <= min_score:
            continue

        review_date = item.get("review_date")
        outdated_warning = None

        if isinstance(review_date, str) and review_date.strip():
            try:
                review_day = datetime.fromisoformat(
                    review_date.replace("Z", "+00:00")
                )
                if review_day.tzinfo is None:
                    review_day = review_day.replace(tzinfo=timezone.utc)
                if review_day <= datetime.now(timezone.utc):
                    outdated_warning = "REVIEW_DATE_REACHED"
            except ValueError:
                outdated_warning = "REVIEW_DATE_INVALID"

        ranked.append(
            {
                "memory_item_id": item.get("id"),
                "memory_item": item,
                "relevance_score": round(score, 6),
                "relevance_reason": (
                    "Exact contextual overlap with current authorized "
                    "reconstruction context: "
                    + ", ".join(overlap[:12])
                ),
                "conflict_warning": None,
                "outdated_warning": outdated_warning,
                "_overlap_count": len(overlap),
            }
        )

    ranked.sort(
        key=lambda row: (
            row["relevance_score"],
            row["_overlap_count"],
            str(row["memory_item_id"]),
        ),
        reverse=True,
    )

    result = ranked[:limit]
    for index, row in enumerate(result, start=1):
        row["rank_position"] = index
        row.pop("_overlap_count", None)

    return result


def _firestore_project_query(
    *,
    client: Any,
    project_id: str,
    scan_limit: int,
):
    collection = client.collection(MEMORY_ITEMS_COLLECTION)

    try:
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = collection.where(
            filter=FieldFilter("project_id", "==", project_id)
        )
    except ImportError:
        query = collection.where(
            "project_id",
            "==",
            project_id,
        )

    return query.limit(scan_limit)


def retrieve_active_memory(
    *,
    project_id: str,
    session_id: str,
    query_context: Mapping[str, Any],
    branch_id: str | None = None,
    cycle_id: str | None = None,
    filters: Mapping[str, Any] | None = None,
    database: str = "(default)",
    limit: int = 10,
    scan_limit: int = 100,
    min_score: float = 0.0,
    idempotency_key: str | None = None,
    client: Any = None,
) -> dict[str, Any]:
    if not isinstance(project_id, str) or not project_id.strip():
        raise ActiveMemoryError("project_id is required.")

    if not isinstance(session_id, str) or not session_id.strip():
        raise ActiveMemoryError("session_id is required.")

    if scan_limit < 1:
        raise ActiveMemoryError("scan_limit must be >= 1.")

    if client is None:
        from google.cloud import firestore

        client = firestore.Client(
            project=project_id,
            database=database,
        )

    retrieval_run_id = str(uuid.uuid4())
    key = idempotency_key or retrieval_run_id
    started_at = _utc_now()

    query = _firestore_project_query(
        client=client,
        project_id=project_id,
        scan_limit=scan_limit,
    )

    raw_items: list[dict[str, Any]] = []

    for snapshot in query.stream():
        payload = snapshot.to_dict() or {}
        payload.setdefault("id", snapshot.id)

        requested_filters = dict(filters or {})

        allowed_use_classes = requested_filters.get(
            "memory_use_class",
            ["COGNITIVE_MEMORY"],
        )
        if isinstance(allowed_use_classes, str):
            allowed_use_classes = [allowed_use_classes]

        if payload.get("memory_use_class") not in set(allowed_use_classes):
            continue

        semantic_filter = requested_filters.get(
            "memory_semantic_type"
        )
        if semantic_filter:
            allowed_semantic = (
                [semantic_filter]
                if isinstance(semantic_filter, str)
                else list(semantic_filter)
            )
            if payload.get("memory_semantic_type") not in set(
                allowed_semantic
            ):
                continue

        lifecycle_filter = requested_filters.get(
            "lifecycle_status"
        )
        if lifecycle_filter:
            allowed_lifecycle = (
                [lifecycle_filter]
                if isinstance(lifecycle_filter, str)
                else list(lifecycle_filter)
            )
            if payload.get("lifecycle_status") not in set(
                allowed_lifecycle
            ):
                continue

        raw_items.append(payload)

    ranked = rank_memory_items(
        items=raw_items,
        query_context=query_context,
        limit=limit,
        min_score=min_score,
    )

    outcome = (
        "CANDIDATES_FOUND"
        if ranked
        else "NO_RELEVANT_CANDIDATE_FOUND"
    )

    completed_at = _utc_now()

    run_payload = {
        "id": retrieval_run_id,
        "session_id": session_id,
        "branch_id": branch_id,
        "cycle_id": cycle_id,
        "query_context": dict(query_context),
        "filters": dict(filters or {}),
        "status": "COMPLETED",
        "retrieved_count": len(raw_items),
        "relevant_count": len(ranked),
        "retrieval_outcome": outcome,
        "outcome_reason": (
            "Relevant canonical memory candidates were produced."
            if ranked
            else "No canonical memory item matched the current context."
        ),
        "retrieval_validation_status": None,
        "validated_by": None,
        "validated_at": None,
        "started_at": started_at,
        "completed_at": completed_at,
        "error_id": None,
        "idempotency_key": key,
    }

    client.collection(
        MEMORY_RETRIEVAL_RUNS_COLLECTION
    ).document(retrieval_run_id).create(run_payload)

    persisted_results: list[dict[str, Any]] = []

    for candidate in ranked:
        result_id = str(uuid.uuid4())

        result_payload = {
            "id": result_id,
            "retrieval_run_id": retrieval_run_id,
            "memory_item_id": candidate["memory_item_id"],
            "relevance_score": candidate["relevance_score"],
            "relevance_reason": candidate["relevance_reason"],
            "conflict_warning": candidate["conflict_warning"],
            "outdated_warning": candidate["outdated_warning"],
            "rank_position": candidate["rank_position"],
            "created_at": completed_at,
        }

        client.collection(
            MEMORY_RETRIEVAL_RESULTS_COLLECTION
        ).document(result_id).create(result_payload)

        persisted_results.append(
            {
                **result_payload,
                "memory_item": candidate["memory_item"],
            }
        )

    return {
        "retrieval_run": run_payload,
        "retrieval_results": persisted_results,
        "retrieval_outcome": outcome,
        "human_review_performed": False,
        "memory_activation_performed": False,
        "memory_transfer_performed": False,
        "reconstruction_effect_active": False,
    }


def build_query_context_from_preliminary_package(
    *,
    session_id: str,
    preliminary_package: Any,
) -> dict[str, Any]:
    if preliminary_package is None:
        raise ActiveMemoryError(
            "Locked preliminary transfer package is required."
        )

    package_data = _as_plain(preliminary_package)

    if not isinstance(package_data, Mapping):
        raise ActiveMemoryError(
            "Preliminary transfer package must be serializable."
        )

    return {
        "session_id": session_id,
        "preliminary_transfer_package": dict(package_data),
    }
