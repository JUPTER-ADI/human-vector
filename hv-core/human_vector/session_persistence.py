from __future__ import annotations

import hashlib
import json

from dataclasses import asdict, fields
from typing import Any

from .orchestrator import SystemOrchestrator


SCHEMA_VERSION = 1

# Transient authorization/control fields must never be restored as active grants.
TRANSIENT_FIELDS = {
    "_human_iteration_decision_transition_authorization_hash",
    "_manual_transfer_lock_authorization_hash",
    "_memory_selection_lock_authorization_hash",
    "_memory_negative_resolution_authorized",
    "_reconstruction_package_lock_authorization_hash",
    "_vf_human_reconsideration_transition_authorization_hash",
}


def build_session_snapshot(orchestrator: SystemOrchestrator) -> dict[str, Any]:
    """Create a durable HUMAN VECTOR session snapshot."""
    ensure_session_id(orchestrator)
    payload = asdict(orchestrator)

    for field_name in TRANSIENT_FIELDS:
        payload.pop(field_name, None)

    return {
        "schema_version": SCHEMA_VERSION,
        "orchestrator": payload,
    }


def declared_orchestrator_fields() -> set[str]:
    """Return the current LIVE dataclass field names for compatibility checks."""
    return {field_info.name for field_info in fields(SystemOrchestrator)}



def _session_envelope_digest(identity: dict[str, str], snapshot: dict[str, object]) -> str:
    payload = {"identity": identity, "snapshot": snapshot}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def build_session_envelope(
    orchestrator: SystemOrchestrator,
    *,
    user_id: str,
    actor_id: str,
    actor_role: str,
) -> dict[str, Any]:
    """Wrap the CORE snapshot with persistent external session identity."""
    if not user_id.strip():
        raise ValueError("user_id is required")
    if not actor_id.strip():
        raise ValueError("actor_id is required")
    if not actor_role.strip():
        raise ValueError("actor_role is required")

    session_id = ensure_session_id(orchestrator)

    identity = {
        "user_id": user_id,
        "session_id": session_id,
        "actor_id": actor_id,
        "actor_role": actor_role,
    }
    snapshot = build_session_snapshot(orchestrator)

    return {
        "schema_version": SCHEMA_VERSION,
        "identity": identity,
        "snapshot": snapshot,
        "integrity_digest": _session_envelope_digest(identity, snapshot),
    }


from uuid import uuid4


def ensure_session_id(orchestrator: SystemOrchestrator) -> str:
    """Ensure every persistent HUMAN VECTOR session has a stable unique id."""
    if orchestrator.session_id is None or not str(orchestrator.session_id).strip():
        orchestrator.session_id = str(uuid4())

    return str(orchestrator.session_id)


from dataclasses import is_dataclass
from enum import Enum
from types import UnionType
from typing import get_args, get_origin, get_type_hints, Union


def _restore_typed_value(value: Any, target_type: Any) -> Any:
    """Restore JSON-compatible data into the declared LIVE Python type."""
    if value is None:
        return None

    origin = get_origin(target_type)

    # HV_GENERIC_TYPED_COLLECTION_RESTORE_V1
    # JSON snapshots turn tuples/sets into JSON arrays. Restore both
    # the declared collection type and the declared nested element type.
    if origin in (list, tuple, set):
        args = get_args(target_type)

        if origin is tuple:
            if len(args) == 2 and args[1] is Ellipsis:
                item_type = args[0]
                return tuple(
                    _restore_typed_value(item, item_type)
                    for item in value
                )

            if args:
                if len(value) != len(args):
                    raise ValueError(
                        "Fixed-length tuple restore length mismatch."
                    )
                return tuple(
                    _restore_typed_value(item, item_type)
                    for item, item_type in zip(value, args)
                )

            return tuple(value)

        item_type = args[0] if args else Any
        restored = [
            _restore_typed_value(item, item_type)
            for item in value
        ]

        if origin is set:
            return set(restored)

        return restored
    args = get_args(target_type)

    if origin in (list,):
        item_type = args[0] if args else Any
        return [_restore_typed_value(item, item_type) for item in value]

    if origin in (dict,):
        key_type = args[0] if args else Any
        value_type = args[1] if len(args) > 1 else Any
        return {
            _restore_typed_value(k, key_type): _restore_typed_value(v, value_type)
            for k, v in value.items()
        }

    if origin in (Union, UnionType):
        non_none = [arg for arg in args if arg is not type(None)]
        for candidate in non_none:
            try:
                return _restore_typed_value(value, candidate)
            except (TypeError, ValueError, KeyError):
                continue
        return value

    if isinstance(target_type, type) and issubclass(target_type, Enum):
        return target_type(value)

    if isinstance(target_type, type) and is_dataclass(target_type):
        hints = get_type_hints(target_type)
        kwargs = {
            field_name: _restore_typed_value(field_value, hints[field_name])
            for field_name, field_value in value.items()
            if field_name in hints
        }
        return target_type(**kwargs)

    if target_type in (str, int, float, bool):
        return target_type(value)

    return value


def restore_session_snapshot(snapshot: dict[str, Any]) -> SystemOrchestrator:
    """Restore a durable snapshot into a LIVE SystemOrchestrator instance."""
    if not isinstance(snapshot, dict):
        raise TypeError("snapshot must be a dict")

    if snapshot.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported session snapshot schema_version")

    payload = snapshot.get("orchestrator")
    if not isinstance(payload, dict):
        raise ValueError("snapshot orchestrator payload is required")

    hints = get_type_hints(SystemOrchestrator)
    declared = declared_orchestrator_fields()

    unknown_fields = set(payload) - declared
    if unknown_fields:
        raise ValueError(
            "Unknown orchestrator fields: " + ",".join(sorted(unknown_fields))
        )

    kwargs = {
        field_name: _restore_typed_value(field_value, hints[field_name])
        for field_name, field_value in payload.items()
        if field_name not in TRANSIENT_FIELDS
    }

    orchestrator = SystemOrchestrator(**kwargs)

    for field_name in TRANSIENT_FIELDS:
        value = getattr(orchestrator, field_name)
        if field_name.endswith("_authorized"):
            if value is not False:
                raise ValueError(f"Unsafe transient restore value: {field_name}")
        elif value is not None:
            raise ValueError(f"Unsafe transient restore value: {field_name}")

    return orchestrator


from pathlib import Path
from tempfile import NamedTemporaryFile


def save_session_snapshot(
    orchestrator: SystemOrchestrator,
    path: str | Path,
) -> Path:
    """Persist a HUMAN VECTOR session snapshot atomically as JSON."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    snapshot = build_session_snapshot(orchestrator)

    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        json.dump(snapshot, temp_file, ensure_ascii=False, separators=(",", ":"))
        temp_path = Path(temp_file.name)

    temp_path.replace(destination)
    return destination


def load_session_snapshot(path: str | Path) -> SystemOrchestrator:
    """Load and restore a persisted HUMAN VECTOR session snapshot."""
    source = Path(path)

    if not source.is_file():
        raise FileNotFoundError(f"Session snapshot not found: {source}")

    with source.open("r", encoding="utf-8") as file_handle:
        snapshot = json.load(file_handle)

    return restore_session_snapshot(snapshot)


def save_session_envelope(
    orchestrator: SystemOrchestrator,
    path: str | Path,
    *,
    user_id: str,
    actor_id: str,
    actor_role: str,
) -> Path:
    """Persist external identity together with the durable CORE snapshot."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    envelope = build_session_envelope(
        orchestrator,
        user_id=user_id,
        actor_id=actor_id,
        actor_role=actor_role,
    )

    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        json.dump(envelope, temp_file, ensure_ascii=False, separators=(",", ":"))
        temp_path = Path(temp_file.name)

    temp_path.replace(destination)
    return destination


def load_session_envelope(path: str | Path) -> dict[str, Any]:
    """Load external identity and restore its bound CORE session."""
    source = Path(path)

    if not source.is_file():
        raise FileNotFoundError(f"Session envelope not found: {source}")

    with source.open("r", encoding="utf-8") as file_handle:
        envelope = json.load(file_handle)

    if not isinstance(envelope, dict):
        raise ValueError("Session envelope must be a dict")

    if envelope.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported session envelope schema_version")

    identity = envelope.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("Session identity is required")

    required_identity = {"user_id", "session_id", "actor_id", "actor_role"}
    missing_identity = required_identity - set(identity)
    if missing_identity:
        raise ValueError(
            "Missing session identity fields: "
            + ",".join(sorted(missing_identity))
        )

    snapshot = envelope.get("snapshot")
    integrity_digest = envelope.get("integrity_digest")
    if not isinstance(integrity_digest, str) or not integrity_digest:
        raise ValueError("Session envelope integrity digest is required")
    expected_digest = _session_envelope_digest(identity, snapshot)
    if integrity_digest != expected_digest:
        raise ValueError("Session envelope integrity check failed")

    orchestrator = restore_session_snapshot(snapshot)

    # HV_MANUAL_TRANSFER_ITEM_RESTORE_V1
    _hv_manual_transfer = getattr(orchestrator, "manual_transfer_artifact", None)
    if _hv_manual_transfer is not None:
        _hv_items = getattr(_hv_manual_transfer, "items", None)
        if isinstance(_hv_items, (list, tuple)) and any(
            isinstance(_hv_item, dict) for _hv_item in _hv_items
        ):
            from dataclasses import replace as _hv_dc_replace
            from human_vector.orchestrator import ManualTransferItem as _HVManualTransferItem

            _hv_restored_items = tuple(
                _HVManualTransferItem(**_hv_item)
                if isinstance(_hv_item, dict)
                else _hv_item
                for _hv_item in _hv_items
            )
            orchestrator.manual_transfer_artifact = _hv_dc_replace(
                _hv_manual_transfer,
                items=_hv_restored_items,
            )

    if identity["session_id"] != orchestrator.session_id:
        raise ValueError("Session identity does not match CORE snapshot")

    return {
        "schema_version": SCHEMA_VERSION,
        "identity": identity,
        "orchestrator": orchestrator,
    }
