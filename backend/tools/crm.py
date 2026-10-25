"""CRM memory tool — persist customer profile across sessions (Assignment 3 bonus)."""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, Optional

from backend.tools.base import Tool

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_DEFAULT_STORE_PATH = os.path.join(_PROJECT_ROOT, "data", "crm_store.json")
_lock = threading.Lock()


class CRMMemoryTool(Tool):
    """Get or update persisted CRM records keyed by user_id / session_id."""

    name = "crm_memory"
    description = (
        "Remember or recall a customer across sessions. Use action='get' at the start "
        "of a returning visit to greet them by name and recall past interactions. "
        "Use action='update' when the customer shares name, email, phone, preferences, "
        "or what they asked about. Key records by user_id (email preferred) or session_id."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get", "update"],
                "description": "get = retrieve profile; update = merge new fields.",
            },
            "user_id": {
                "type": "string",
                "description": "Stable customer key (email or CRM id).",
            },
            "session_id": {
                "type": "string",
                "description": "Fallback key when user_id is unknown.",
            },
            "name": {"type": "string", "description": "Customer display name."},
            "email": {"type": "string", "description": "Contact email."},
            "phone": {"type": "string", "description": "Contact phone."},
            "preferences": {
                "type": "string",
                "description": "Free-text preferences (e.g. prefers express shipping).",
            },
            "last_interaction": {
                "type": "string",
                "description": "Short summary of what they asked about this turn.",
            },
        },
        "required": ["action"],
    }

    def __init__(self, store_path: Optional[str] = None) -> None:
        self.store_path = store_path or _DEFAULT_STORE_PATH

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = str(kwargs.get("action", "")).strip().lower()
        user_id = str(kwargs.get("user_id") or "").strip()
        session_id = str(kwargs.get("session_id") or "").strip()
        key = user_id or session_id
        if not key:
            return {
                "ok": False,
                "error": "user_id or session_id is required to identify the customer.",
            }

        if action == "get":
            record = self._get(key)
            if record is None and user_id and session_id:
                record = self._get(session_id)
            if record is None:
                return {
                    "ok": True,
                    "found": False,
                    "key": key,
                    "message": "No CRM record yet for this customer.",
                }
            return {"ok": True, "found": True, "key": key, "record": record}

        if action == "update":
            updates = {
                k: v
                for k, v in {
                    "name": kwargs.get("name"),
                    "email": kwargs.get("email"),
                    "phone": kwargs.get("phone"),
                    "preferences": kwargs.get("preferences"),
                    "last_interaction": kwargs.get("last_interaction"),
                }.items()
                if v is not None and str(v).strip()
            }
            if not updates:
                return {"ok": False, "error": "No fields provided to update."}
            record = self._upsert(key, updates)
            # Also index by email when present
            email = str(updates.get("email") or record.get("email") or "").strip()
            if email and email.lower() != key.lower():
                self._upsert(email.lower(), {**record, **updates})
            return {"ok": True, "found": True, "key": key, "record": record}

        return {"ok": False, "error": "action must be 'get' or 'update'"}

    def _load(self) -> Dict[str, Any]:
        if not os.path.isfile(self.store_path):
            return {}
        try:
            with open(self.store_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.store_path) or ".", exist_ok=True)
        tmp_path = f"{self.store_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.store_path)

    def _get(self, key: str) -> Optional[Dict[str, Any]]:
        with _lock:
            data = self._load()
            record = data.get(key) or data.get(key.lower())
            return dict(record) if isinstance(record, dict) else None

    def _upsert(self, key: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        with _lock:
            data = self._load()
            existing = data.get(key) if isinstance(data.get(key), dict) else {}
            merged = {**existing, **updates, "updated_at": time.time()}
            data[key] = merged
            self._save(data)
            return dict(merged)
