"""Module for managing plans in the plans database."""

from datetime import datetime
from pathlib import Path

from tinydb import TinyDB

_ROOT = Path(__file__).resolve().parent.parent
_PLANS_DB_PATH = _ROOT / "data" / "plans.json"
_CONFIG_PATH = _ROOT / "config.json"

_DEFAULT_CONFIG = {
    "daily_targets": {"protein_g": 160, "carbs_g": 220, "fat_g": 70, "calories": 2200},
    "slot_splits": {
        "breakfast":  {"protein": 0.25, "carbs": 0.30, "fat": 0.25, "calories": 0.25},
        "lunch":      {"protein": 0.30, "carbs": 0.30, "fat": 0.30, "calories": 0.30},
        "pre_snack":  {"protein": 0.15, "carbs": 0.20, "fat": 0.15, "calories": 0.15},
        "dinner":     {"protein": 0.30, "carbs": 0.20, "fat": 0.30, "calories": 0.30},
    },
    "hemisphere": "north",
    "macro_tolerance_pct": 15,
}


def _plans_db() -> TinyDB:
    _PLANS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(str(_PLANS_DB_PATH))


def _inject_id(doc, doc_id: int) -> dict:
    return {**doc, "id": doc_id}


def save_plan(plan: dict) -> int:
    """Save a new plan and return its ID."""
    plan = dict(plan)
    plan.setdefault("generated_at", datetime.now().isoformat())
    
    with _plans_db() as db:
        return db.table("plans").insert(plan)


def get_plan_by_id(plan_id: int) -> dict | None:
    """Get a plan by its ID."""
    with _plans_db() as db:
        doc = db.table("plans").get(doc_id=plan_id)
        return _inject_id(doc, plan_id) if doc else None


def get_last_plan() -> dict | None:
    """Get the most recently generated plan."""
    plans = get_plan_history()
    return plans[0] if plans else None


def get_plan_history() -> list[dict]:
    """Get all plans sorted by generated_at (newest first)."""
    with _plans_db() as db:
        plans = db.table("plans").all()
    return sorted(
        [_inject_id(p, p.doc_id) for p in plans],
        key=lambda p: p.get("generated_at", ""),
        reverse=True,
    )


def delete_plan(plan_id: int) -> None:
    """Delete a plan."""
    with _plans_db() as db:
        db.table("plans").remove(doc_ids=[plan_id])


# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    import json
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            data = json.load(f)
        # Merge missing keys from defaults without overwriting existing ones
        for k, v in _DEFAULT_CONFIG.items():
            data.setdefault(k, v)
        return data
    return dict(_DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    import json
    with open(_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
