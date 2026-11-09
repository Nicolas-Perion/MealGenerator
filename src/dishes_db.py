"""Module for managing dishes in the dishes database."""

from datetime import datetime
from pathlib import Path

from tinydb import TinyDB

_ROOT = Path(__file__).resolve().parent.parent
_DISHES_DB_PATH = _ROOT / "data" / "dishes.json"


def _dishes_db() -> TinyDB:
    _DISHES_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(str(_DISHES_DB_PATH))


def _inject_id(doc, doc_id: int) -> dict:
    return {**doc, "id": doc_id}


def get_all_dishes() -> list[dict]:
    """Get all dishes from dishes.json."""
    with _dishes_db() as db:
        table = db.table("dishes")
        return [_inject_id(d, d.doc_id) for d in table.all()]


def get_dishes_by_type(dish_type: str) -> list[dict]:
    """Get dishes filtered by dish_type."""
    from tinydb import Query
    with _dishes_db() as db:
        table = db.table("dishes")
        D = Query()
        return [_inject_id(d, d.doc_id) for d in table.search(D.dish_type == dish_type)]


def get_dish_by_id(dish_id: int) -> dict | None:
    """Get a dish by its ID."""
    with _dishes_db() as db:
        table = db.table("dishes")
        doc = table.get(doc_id=dish_id)
        return _inject_id(doc, dish_id) if doc else None


def add_dish(dish: dict) -> int:
    """Add a new dish and return its ID.
    
    Expected dish structure (new format):
    {
        "name": str,
        "dish_type": str,
        "compatible_slots": list[str],
        "ingredients": [
            {"ingredient_id": int, "quantity": float},
            ...
        ],
        "macros": dict (optional, will be calculated if not provided),
        "seasons": list[str],
        "tags": list[str],
        "prep_minutes": int,
        "batch_size": int,
        "shelf_life_days": int,
    }
    """
    dish = dict(dish)
    dish.setdefault("batch_size", 1)
    dish.setdefault("shelf_life_days", 1)
    dish.setdefault("created_at", datetime.now().isoformat())
    
    with _dishes_db() as db:
        return db.table("dishes").insert(dish)


def update_dish(dish_id: int, updates: dict) -> None:
    """Update a dish."""
    with _dishes_db() as db:
        db.table("dishes").update(updates, doc_ids=[dish_id])


def delete_dish(dish_id: int) -> None:
    """Delete a dish."""
    with _dishes_db() as db:
        db.table("dishes").remove(doc_ids=[dish_id])
