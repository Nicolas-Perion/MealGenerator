from collections import defaultdict

from .database import get_dish_by_id


def compute_grocery_list(plan: dict) -> list[dict]:
    """Aggregate all ingredients across the plan.

    Batch dishes (batch_size > 1) contribute their ingredients exactly once
    (full batch quantities), regardless of how many servings appear in the plan.
    """
    seen_batch_ids: set[int] = set()
    # totals[ingredient_name] = {"quantity_g": float, "quantity_ml": float, "quantity_units": float}
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"quantity_g": 0.0, "quantity_ml": 0.0, "quantity_units": 0.0}
    )

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
                    key = ing["name"].strip().lower()
                    totals[key]["quantity_g"] += ing.get("quantity_g", 0)
                    totals[key]["quantity_ml"] += ing.get("quantity_ml", 0)
                    totals[key]["quantity_units"] += ing.get("quantity_units", 0)

    result = []
    for name in sorted(totals):
        parts = []
        t = totals[name]
        if t["quantity_g"] > 0:
            parts.append(f"{_fmt(t['quantity_g'])}g")
        if t["quantity_ml"] > 0:
            parts.append(f"{_fmt(t['quantity_ml'])}ml")
        if t["quantity_units"] > 0:
            parts.append(f"{_fmt(t['quantity_units'])} unit(s)")
        result.append({"name": name.title(), "total": " + ".join(parts)})

    return result


def _fmt(v: float) -> str:
    return str(int(v)) if v == int(v) else f"{v:.1f}"
