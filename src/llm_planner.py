"""Optional LLM-based planner using Ollama.

Falls back to the algorithmic planner on any error.
Requires: `pip install ollama` and the Ollama daemon running locally.
"""
import json
import logging
from typing import Optional

from .database import get_all_dishes, get_dish_by_id
from .seasonality import is_dish_seasonal, current_season
from . import planner as _algo

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a nutrition-aware meal planner.
You will receive candidate dishes grouped by slot (JSON) and daily macro targets.
Your task: for each slot select the dish IDs that best fit the macro target.

Rules:
- Use ONLY the IDs provided. Never invent new IDs.
- Select exactly one "main" dish per slot.
- Optionally add one add-on dish (dessert/side/snack) if calories allow.
- Respond ONLY with valid JSON: {"breakfast": [id], "lunch": [id, id], ...}
- No explanation, no comments.
"""


def _build_prompt(candidates: dict, daily_targets: dict, hemisphere: str) -> str:
    season = current_season(hemisphere)
    lines = [f"Season: {season}", f"Daily targets: {json.dumps(daily_targets)}", "", "Candidates by slot:"]
    for slot, dishes in candidates.items():
        lines.append(f"\n{slot}:")
        for d in dishes:
            lines.append(
                f"  id={d['id']} name={d['name']!r} type={d['dish_type']} "
                f"P={d['macros']['protein_g']}g C={d['macros']['carbs_g']}g "
                f"F={d['macros']['fat_g']}g cal={d['macros']['calories']}"
            )
    return "\n".join(lines)


def _validate(selection: dict, candidates: dict) -> bool:
    from .planner import SLOTS
    for slot in SLOTS:
        ids = selection.get(slot, [])
        if not isinstance(ids, list):
            return False
        valid_ids = {d["id"] for d in candidates.get(slot, [])}
        if not all(i in valid_ids for i in ids):
            return False
    return True


def generate_plan(config: dict) -> dict:
    try:
        import ollama  # type: ignore
    except ImportError:
        logger.warning("ollama package not installed — falling back to algorithmic planner")
        return _algo.generate_plan(config)

    model = config.get("llm_model", "llama3.2:3b")
    hemisphere = config.get("hemisphere", "north")
    all_dishes = get_all_dishes()

    # Pre-filter candidates per slot (same logic as algorithmic planner)
    from .planner import _filter_mains, _filter_addons, SLOTS, _slot_targets
    slot_targets = _slot_targets(config)
    candidates: dict = {}
    for slot in SLOTS:
        mains = _filter_mains(all_dishes, slot, hemisphere, set())
        addons = _filter_addons(
            all_dishes, slot, hemisphere, set(),
            max_calories=slot_targets[slot]["calories"],
        )
        candidates[slot] = mains + addons

    from datetime import datetime, timedelta
    import random
    from .database import save_plan

    today = datetime.now().date()
    days_out = []

    for day_idx in range(7):
        day_date = today + timedelta(days=day_idx)
        try:
            prompt = _build_prompt(candidates, config["daily_targets"], hemisphere)
            response = ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            raw = response["message"]["content"].strip()
            selection = json.loads(raw)
            if not _validate(selection, candidates):
                raise ValueError("Invalid IDs in LLM response")
            meals = {slot: selection.get(slot, []) for slot in SLOTS}
        except Exception as exc:
            logger.warning("LLM selection failed for day %d (%s) — using algorithmic fallback", day_idx + 1, exc)
            # Generate one day algorithmically
            one_day_plan = _algo.generate_plan(config, rng_seed=random.randint(0, 10**9))
            meals = one_day_plan["days"][0]["meals"]

        days_out.append({
            "day": day_idx + 1,
            "date": day_date.isoformat(),
            "meals": meals,
        })

    return {
        "generated_at": datetime.now().isoformat(),
        "days": days_out,
        "daily_targets": config["daily_targets"],
        "slot_targets": slot_targets,
        "hemisphere": hemisphere,
        "planner_mode": "llm",
        "warnings": [],
    }
