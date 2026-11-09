from collections import defaultdict

from .database import get_dish_by_id
from .ingredients_db import get_ingredient_by_id


def compute_grocery_list(plan: dict) -> list[dict]:
    """Aggregate all ingredients across the plan.

    With the new centralized ingredient system:
    - Each dish ingredient references an ingredient_id and has a quantity
    - Each ingredient has a single reference unit (g, ml, or unit)
    - We aggregate quantities by ingredient and display with the ingredient's unit

    Batch dishes (batch_size > 1) contribute their ingredients exactly once
    (full batch quantities), regardless of how many servings appear in the plan.
    """
    seen_batch_ids: set[int] = set()
    # totals[ingredient_id] = {"quantity": float, "ingredient": dict}
    totals: dict[int, dict] = {}

    for day in plan.get("days", []):
        for slot_ids in day["meals"].values():
            for dish_id in slot_ids:
                dish = get_dish_by_id(dish_id)
                if not dish:
                    continue

                is_batch = dish.get("batch_size", 1) > 1

                if is_batch:
                    if dish_id in seen_batch_ids:
                        continue  # full batch already counted
                    seen_batch_ids.add(dish_id)

                for ing in dish.get("ingredients", []):
                    ingredient_id = ing.get("ingredient_id")
                    quantity = ing.get("quantity", 0)
                    
                    if not ingredient_id:
                        continue
                    
                    if ingredient_id not in totals:
                        ingredient = get_ingredient_by_id(ingredient_id)
                        if ingredient:
                            totals[ingredient_id] = {
                                "quantity": 0.0,
                                "ingredient": ingredient
                            }
                        else:
                            # Ingredient not found, create a placeholder
                            totals[ingredient_id] = {
                                "quantity": 0.0,
                                "ingredient": {
                                    "id": ingredient_id,
                                    "name": f"Unknown ({ingredient_id})",
                                    "unit": "g"
                                }
                            }
                    
                    totals[ingredient_id]["quantity"] += quantity

    result = []
    for ingredient_id in sorted(totals.keys()):
        data = totals[ingredient_id]
        ingredient = data["ingredient"]
        quantity = data["quantity"]
        unit = ingredient.get("unit", "g")
        
        # Format quantity based on unit
        quantity_str = _fmt(quantity)
        
        # Create display string with unit
        if unit == "unit":
            unit_str = "unit(s)" if quantity != 1 else "unit"
        else:
            unit_str = unit
        
        result.append({
            "name": ingredient.get("name", "Unknown"),
            "ingredient_id": ingredient_id,
            "total": f"{quantity_str} {unit_str}",
            "quantity": quantity,
            "unit": unit
        })

    return result


def _fmt(v: float) -> str:
    """Format a float value, removing .0 if it's an integer."""
    return str(int(v)) if v == int(v) else f"{v:.1f}"
