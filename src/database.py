import json
import os
from datetime import datetime
from pathlib import Path

from tinydb import TinyDB, Query

_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _ROOT / "data" / "meals.json"
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


def _db() -> TinyDB:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(str(_DB_PATH))


def _inject_id(doc, doc_id: int) -> dict:
    return {**doc, "id": doc_id}


# ── Dishes ────────────────────────────────────────────────────────────────────

def get_all_dishes() -> list[dict]:
    with _db() as db:
        table = db.table("dishes")
        return [_inject_id(d, d.doc_id) for d in table.all()]


def get_dishes_by_type(dish_type: str) -> list[dict]:
    with _db() as db:
        table = db.table("dishes")
        D = Query()
        return [_inject_id(d, d.doc_id) for d in table.search(D.dish_type == dish_type)]


def get_dish_by_id(dish_id: int) -> dict | None:
    with _db() as db:
        table = db.table("dishes")
        doc = table.get(doc_id=dish_id)
        return _inject_id(doc, dish_id) if doc else None


def add_dish(dish: dict) -> int:
    dish.setdefault("batch_size", 1)
    dish.setdefault("shelf_life_days", 1)
    dish.setdefault("created_at", datetime.now().isoformat())
    with _db() as db:
        return db.table("dishes").insert(dish)


def update_dish(dish_id: int, updates: dict) -> None:
    with _db() as db:
        db.table("dishes").update(updates, doc_ids=[dish_id])


def delete_dish(dish_id: int) -> None:
    with _db() as db:
        db.table("dishes").remove(doc_ids=[dish_id])


# ── Plans ─────────────────────────────────────────────────────────────────────

def save_plan(plan: dict) -> int:
    with _db() as db:
        return db.table("plans").insert(plan)


def get_plan_by_id(plan_id: int) -> dict | None:
    with _db() as db:
        doc = db.table("plans").get(doc_id=plan_id)
        return _inject_id(doc, plan_id) if doc else None


def get_last_plan() -> dict | None:
    with _db() as db:
        plans = db.table("plans").all()
    if not plans:
        return None
    latest = max(plans, key=lambda p: p.get("generated_at", ""))
    return _inject_id(latest, latest.doc_id)


def get_plan_history() -> list[dict]:
    with _db() as db:
        plans = db.table("plans").all()
    return sorted(
        [_inject_id(p, p.doc_id) for p in plans],
        key=lambda p: p.get("generated_at", ""),
        reverse=True,
    )


# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            data = json.load(f)
        # Merge missing keys from defaults without overwriting existing ones
        for k, v in _DEFAULT_CONFIG.items():
            data.setdefault(k, v)
        return data
    return dict(_DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    with open(_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
