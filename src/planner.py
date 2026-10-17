import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import sqrt
from typing import Optional

from .database import get_all_dishes, get_last_plan, save_plan, get_dish_by_id
from .seasonality import is_dish_seasonal

SLOTS = ["breakfast", "lunch", "pre_snack", "dinner"]
MAIN_TYPES = {"main"}
ADDON_TYPES = {"dessert", "side", "snack", "drink"}
MIN_ADDON_CALORIES = 80  # don't bother adding an extra if budget is tiny


@dataclass
class _BatchEntry:
    dish_id: int
    remaining: int
    expires_on_day: int  # 1-indexed day within the 7-day plan


def _slot_targets(config: dict) -> dict[str, dict]:
    daily = config["daily_targets"]
    splits = config["slot_splits"]
    result = {}
    for slot, pct in splits.items():
        result[slot] = {
            "protein_g": daily["protein_g"] * pct["protein"],
            "carbs_g": daily["carbs_g"] * pct["carbs"],
            "fat_g": daily["fat_g"] * pct["fat"],
            "calories": daily["calories"] * pct["calories"],
        }
    return result


def _macro_score(dish: dict, budget: dict) -> float:
    """Fitness score: 1.0 when macros exactly match budget, → 0 as distance grows."""
    p_t = max(budget["protein_g"], 1)
    c_t = max(budget["carbs_g"], 1)
    f_t = max(budget["fat_g"], 1)
    m = dish["macros"]
    dp = (m["protein_g"] - p_t) / p_t
    dc = (m["carbs_g"] - c_t) / c_t
    df = (m["fat_g"] - f_t) / f_t
    dist = sqrt(dp**2 + dc**2 + df**2)
    return 1.0 / (1.0 + dist)


def _subtract_macros(budget: dict, dish: dict) -> dict:
    m = dish["macros"]
    return {
        "protein_g": budget["protein_g"] - m["protein_g"],
        "carbs_g": budget["carbs_g"] - m["carbs_g"],
        "fat_g": budget["fat_g"] - m["fat_g"],
        "calories": budget["calories"] - m["calories"],
    }


def _weighted_choice(candidates: list[dict], weights: list[float]) -> dict:
    return random.choices(candidates, weights=weights, k=1)[0]


def _filter_mains(
    dishes: list[dict],
    slot: str,
    hemisphere: str,
    recently_used: set[int],
    relax_recent: bool = False,
    relax_season: bool = False,
) -> list[dict]:
    out = []
    for d in dishes:
        if d["dish_type"] not in MAIN_TYPES:
            continue
        if slot not in d.get("compatible_slots", []):
            continue
        if not relax_season and not is_dish_seasonal(d, hemisphere):
            continue
        if not relax_recent and d["id"] in recently_used:
            continue
        out.append(d)
    return out


def _filter_addons(
    dishes: list[dict],
    slot: str,
    hemisphere: str,
    exclude_ids: set[int],
    max_calories: float,
    relax_season: bool = False,
) -> list[dict]:
    out = []
    for d in dishes:
        if d["dish_type"] not in ADDON_TYPES:
            continue
        if slot not in d.get("compatible_slots", []):
            continue
        if d["id"] in exclude_ids:
            continue
        if not relax_season and not is_dish_seasonal(d, hemisphere):
            continue
        if d["macros"]["calories"] > max_calories * 1.1:
            continue
        out.append(d)
    return out


def _count_future_compatible_slots(
    dish_id: int,
    all_dishes: list[dict],
    remaining_days: list[int],
    slots_per_day: list[list[str]],
    slot_index: int,
    current_day_idx: int,
) -> int:
    """Count how many (day, slot) pairs are left this week that are compatible with dish_id."""
    dish = next((d for d in all_dishes if d["id"] == dish_id), None)
    if not dish:
        return 0
    compatible = set(dish.get("compatible_slots", []))
    count = 0
    for day_i, day_slots in enumerate(slots_per_day):
        for s_i, s in enumerate(day_slots):
            # Skip already-processed slots
            if day_i < current_day_idx:
                continue
            if day_i == current_day_idx and s_i <= slot_index:
                continue
            if s in compatible:
                count += 1
    return count


def generate_plan(config: dict, rng_seed: Optional[int] = None) -> dict:
    if rng_seed is not None:
        random.seed(rng_seed)

    hemisphere = config.get("hemisphere", "north")
    slot_targets = _slot_targets(config)

    all_dishes = get_all_dishes()
    last_plan = get_last_plan()
    last_plan_ids: set[int] = set()
    if last_plan:
        for day in last_plan.get("days", []):
            for ids in day["meals"].values():
                last_plan_ids.update(ids)

    recently_used_this_week: set[int] = set(last_plan_ids)
    batch_queue: list[_BatchEntry] = []

    # Build a full 7×4 slot grid so we can compute future compatible slots
    slots_grid = [list(SLOTS) for _ in range(7)]

    today = datetime.now().date()
    days_out = []

    for day_idx in range(7):
        day_date = today + timedelta(days=day_idx)
        day_num = day_idx + 1  # 1-indexed
        day_meals: dict[str, list[int]] = {}

        for slot_idx, slot in enumerate(SLOTS):
            target = slot_targets[slot]
            forced_addon_id: Optional[int] = None

            # ── STEP A: check batch queue for forced serving ──────────────
            for entry in batch_queue:
                if entry.remaining <= 0:
                    continue
                if day_num > entry.expires_on_day:
                    continue
                dish = get_dish_by_id(entry.dish_id)
                if not dish or slot not in dish.get("compatible_slots", []):
                    continue
                future = _count_future_compatible_slots(
                    entry.dish_id, all_dishes, list(range(day_num, 8)),
                    slots_grid, slot_idx, day_idx,
                )
                if entry.remaining >= future + 1:
                    # Must use now or lose a serving
                    forced_addon_id = entry.dish_id
                    entry.remaining -= 1
                    break

            # ── STEP B: select main dish ──────────────────────────────────
            main: Optional[dict] = None
            for relax_recent, relax_season in [
                (False, False), (True, False), (True, True)
            ]:
                candidates = _filter_mains(
                    all_dishes, slot, hemisphere,
                    recently_used_this_week,
                    relax_recent=relax_recent,
                    relax_season=relax_season,
                )
                if candidates:
                    weights = [_macro_score(d, target) for d in candidates]
                    main = _weighted_choice(candidates, weights)
                    break

            if main is None:
                # Absolute fallback: any dish compatible with this slot
                candidates = [
                    d for d in all_dishes if slot in d.get("compatible_slots", [])
                ]
                if candidates:
                    main = random.choice(candidates)

            if main is None:
                day_meals[slot] = []
                continue

            recently_used_this_week.add(main["id"])
            selected_ids = [main["id"]]

            # Register new batch if needed
            if main.get("batch_size", 1) > 1:
                already = any(e.dish_id == main["id"] for e in batch_queue)
                if not already:
                    batch_queue.append(_BatchEntry(
                        dish_id=main["id"],
                        remaining=main["batch_size"] - 1,
                        expires_on_day=day_num + main.get("shelf_life_days", 1) - 1,
                    ))

            # ── STEP C: select add-on ─────────────────────────────────────
            remaining_budget = _subtract_macros(target, main)

            if forced_addon_id is not None:
                selected_ids.append(forced_addon_id)
            elif remaining_budget["calories"] >= MIN_ADDON_CALORIES:
                # Build active batch set for weight boosting
                active_batch_ids = {
                    e.dish_id for e in batch_queue
                    if e.remaining > 0 and day_num <= e.expires_on_day
                }
                addon_candidates = _filter_addons(
                    all_dishes, slot, hemisphere,
                    exclude_ids=set(selected_ids),
                    max_calories=remaining_budget["calories"],
                )
                if not addon_candidates:
                    addon_candidates = _filter_addons(
                        all_dishes, slot, hemisphere,
                        exclude_ids=set(selected_ids),
                        max_calories=remaining_budget["calories"],
                        relax_season=True,
                    )
                if addon_candidates:
                    weights = []
                    for d in addon_candidates:
                        w = _macro_score(d, remaining_budget)
                        if d["id"] in active_batch_ids:
                            w *= 5.0  # boost active batch servings
                        weights.append(w)
                    addon = _weighted_choice(addon_candidates, weights)
                    selected_ids.append(addon["id"])
                    # Decrement batch if applicable
                    for entry in batch_queue:
                        if entry.dish_id == addon["id"] and entry.remaining > 0:
                            entry.remaining -= 1
                            break
                    else:
                        # New batch addon
                        if addon.get("batch_size", 1) > 1:
                            already = any(e.dish_id == addon["id"] for e in batch_queue)
                            if not already:
                                batch_queue.append(_BatchEntry(
                                    dish_id=addon["id"],
                                    remaining=addon["batch_size"] - 1,
                                    expires_on_day=day_num + addon.get("shelf_life_days", 1) - 1,
                                ))

            day_meals[slot] = selected_ids

        days_out.append({
            "day": day_num,
            "date": day_date.isoformat(),
            "meals": day_meals,
        })

    # Collect batch warnings
    warnings = []
    for entry in batch_queue:
        if entry.remaining > 0:
            dish = get_dish_by_id(entry.dish_id)
            name = dish["name"] if dish else f"dish #{entry.dish_id}"
            warnings.append(f"{name}: {entry.remaining} serving(s) may go unused")

    plan = {
        "generated_at": datetime.now().isoformat(),
        "days": days_out,
        "daily_targets": config["daily_targets"],
        "slot_targets": _slot_targets(config),
        "hemisphere": hemisphere,
        "planner_mode": config.get("planner_mode", "auto"),
        "warnings": warnings,
    }
    return plan
