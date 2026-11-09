"""Module for managing ingredients in the centralized ingredients database."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from tinydb import TinyDB, Query

_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _ROOT / "data" / "ingredients.json"


def _ingredients_db() -> TinyDB:
    """Return a TinyDB instance for ingredients.json."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(str(_DB_PATH))


def _inject_id(doc, doc_id: int) -> dict:
    """Inject the document ID into the document."""
    return {**doc, "id": doc_id}


def get_ingredient_by_id(ingredient_id: int) -> Optional[dict]:
    """Get an ingredient by its ID from ingredients.json."""
    with _ingredients_db() as db:
        table = db.table("ingredients")
        doc = table.get(doc_id=ingredient_id)
        return _inject_id(doc, ingredient_id) if doc else None


def get_ingredient_by_name(name: str) -> Optional[dict]:
    """Get an ingredient by its name (case-insensitive)."""
    with _ingredients_db() as db:
        table = db.table("ingredients")
        Ing = Query()
        # Search for exact match (case-insensitive)
        name_lower = name.lower()
        results = table.search(Ing.name == name_lower)
        if results:
            return _inject_id(results[0], results[0].doc_id)
        
        return None


def get_all_ingredients() -> list[dict]:
    """Return all ingredients from ingredients.json."""
    with _ingredients_db() as db:
        table = db.table("ingredients")
        return [_inject_id(d, d.doc_id) for d in table.all()]


def add_ingredient(ingredient: dict) -> int:
    """Add a new ingredient and return its ID.
    
    Expected ingredient structure:
    {
        "name": str (must be lowercase),
        "unit": "g" | "ml" | "unit",
        "macros_per_unit": {
            "protein_g": float,
            "carbs_g": float,
            "fat_g": float,
            "calories": float
        },
        "category": Optional[str],
        "shelf_life_days": Optional[int],
    }
    """
    ingredient = dict(ingredient)
    ingredient.setdefault("created_at", datetime.now().isoformat())
    
    with _ingredients_db() as db:
        return db.table("ingredients").insert(ingredient)


def update_ingredient(ingredient_id: int, updates: dict) -> None:
    """Update an ingredient."""
    with _ingredients_db() as db:
        db.table("ingredients").update(updates, doc_ids=[ingredient_id])


def delete_ingredient(ingredient_id: int) -> None:
    """Delete an ingredient."""
    with _ingredients_db() as db:
        db.table("ingredients").remove(doc_ids=[ingredient_id])


def get_ingredients_by_category(category: str) -> list[dict]:
    """Get all ingredients in a specific category."""
    with _ingredients_db() as db:
        table = db.table("ingredients")
        Ing = Query()
        results = table.search(Ing.category == category)
        return [_inject_id(r, r.doc_id) for r in results]


def search_ingredients(query: str) -> list[dict]:
    """Search ingredients by name (case-insensitive, substring match)."""
    with _ingredients_db() as db:
        table = db.table("ingredients")
        all_ingredients = table.all()
        query_lower = query.lower()
        results = [
            _inject_id(ing, ing.doc_id)
            for ing in all_ingredients
            if query_lower in ing.get("name", "")
        ]
        return results


def ingredient_exists(name: str) -> bool:
    """Check if an ingredient with the given name exists (case-insensitive)."""
    return get_ingredient_by_name(name) is not None


def get_next_ingredient_id() -> int:
    """Get the next available ingredient ID."""
    ingredients = get_all_ingredients()
    if not ingredients:
        return 1
    return max(ing["id"] for ing in ingredients) + 1
