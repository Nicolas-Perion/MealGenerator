# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MealGenerator is a Python FastAPI web application that generates varied 7-day meal plans with grocery lists. Key features:
- 7-day plans with 4 meal slots per day (breakfast, lunch, pre-training snack, dinner)
- Dish-based composition (1–2 dishes per slot: main + optional side/dessert)
- Batch cooking support (e.g., a pie spread across the week, counted once in groceries)
- Macronutrient constraints with configurable daily targets and per-slot splits
- Seasonal ingredient filtering
- Variety enforcement (avoids repeating dishes from the previous week)
- PDF export of plan + grocery list
- Optional LLM mode via Ollama (disabled by default)
- Plan history and browsing

## Tech Stack

- **Backend**: FastAPI 0.111+, Uvicorn, Pydantic 2.7+
- **Templates**: Jinja2 3.1.4+ with context processors
- **Database**: TinyDB 4.8+ (JSON-backed, stored in `data/meals.json`)
- **PDF export**: WeasyPrint 62+ (requires GTK runtime on Windows)
- **Optional LLM**: Ollama (not required for core functionality)

## Architecture

### Data Flow

1. **Database Layer** (`src/database.py`):
   - CRUD operations for dishes and plans via TinyDB
   - Config management (user settings, daily macros, slot splits, hemisphere, planner mode)
   - Plans store dish IDs; resolution happens at render time via `_resolve_plan()`

2. **Planner Core** (`src/planner.py`):
   - Algorithmic plan generation; selects dishes to fit macronutrient targets
   - Enforces variety (checks previous week's plan)
   - Handles batch dishes: spreads servings across the week, tracks expiry per dish
   - Macro scoring via Euclidean distance in protein/carbs/fat space

3. **LLM Planner** (`src/llm_planner.py`):
   - Optional alternative to algorithmic planner; uses Ollama
   - Falls back to algorithmic planner if Ollama is offline
   - Never invents dishes; selects from the database

4. **Grocery List** (`src/grocery.py`):
   - Aggregates ingredients by code (no hallucinations)
   - Accounts for batch dishes spreading across the week

5. **Seasonality** (`src/seasonality.py`):
   - Filters dishes by current season and hemisphere

6. **Web Routes** (`web/app.py`):
   - Starlette 1.6.0 TemplateResponse API: signature is `(request, name, context)`, not `(name, context)` ← **critical API change**
   - All routes return resolved plans (IDs → dish objects) before rendering
   - Context processors inject slot labels and macro helper functions
   - PDF export via WeasyPrint template (`web/templates/plan_print.html`)

## Key API Details

### Starlette TemplateResponse (Starlette 1.6.0+)

**Important**: The new signature requires `request` as the first argument:
```python
templates.TemplateResponse(request, "template.html", {"key": value})  # ✓ Correct
templates.TemplateResponse("template.html", {"key": value})          # ✗ Old API, will fail
```

All route handlers receive `request: Request` and must pass it to `TemplateResponse`.

### Plan Data Structure

```python
{
    "id": int,
    "generated_at": ISO string,
    "days": [
        {
            "day_index": int,
            "meals": {
                "breakfast": [dish_id, ...],
                "lunch": [dish_id, ...],
                "pre_snack": [dish_id, ...],
                "dinner": [dish_id, ...],
            }
        },
        ...
    ]
}
```

Before rendering, `_resolve_plan()` replaces dish IDs with full dish objects (name, macros, ingredients, etc.).

### Dish Data Structure

```python
{
    "id": int,
    "name": str,
    "dish_type": str,  # "main", "dessert", "side", "snack", "drink"
    "compatible_slots": [str, ...],  # e.g., ["breakfast", "lunch"]
    "ingredients": [
        {
            "name": str,
            "quantity_g": float | None,
            "quantity_ml": float | None,
            "quantity_units": float | None,
        },
        ...
    ],
    "macros": {
        "protein_g": float,
        "carbs_g": float,
        "fat_g": float,
        "calories": float,  # auto-computed: protein*4 + carbs*4 + fat*9
    },
    "seasons": [str, ...],  # ["spring", "summer", "autumn", "winter"]
    "tags": [str, ...],
    "prep_minutes": int,
    "batch_size": int,  # 1 for non-batch dishes
    "shelf_life_days": int,  # how long batch stays fresh
}
```

### Config Structure

```python
{
    "daily_targets": {
        "protein_g": float,
        "carbs_g": float,
        "fat_g": float,
        "calories": float,
    },
    "slot_splits": {
        "breakfast": {"protein": 0.25, "carbs": 0.30, "fat": 0.25, "calories": 0.25},
        "lunch": {"protein": 0.30, "carbs": 0.30, "fat": 0.30, "calories": 0.30},
        "pre_snack": {"protein": 0.15, "carbs": 0.20, "fat": 0.15, "calories": 0.15},
        "dinner": {"protein": 0.30, "carbs": 0.20, "fat": 0.30, "calories": 0.30},
    },
    "hemisphere": "north" | "south",
    "planner_mode": "auto" | "llm",  # "auto" tries LLM, falls back to algo
    "llm_model": str,  # e.g., "llama3.2:3b"
    "macro_tolerance_pct": float,  # e.g., 15 = ±15% from target
}
```

## Common Development Tasks

### Run the app
```bash
# Install dependencies (venv should be in .venv)
pip install -r requirements.txt

# Seed the database (creates 20 sample dishes)
python seed_meals.py

# Start the dev server (watches for changes)
uvicorn web.app:app --reload
```

Then open **http://localhost:8001** in your browser.

### Run tests
Currently, no automated test suite is included. Manual testing via the web UI is the standard.

### Modify the planner
Edit `src/planner.py`. The algorithm:
1. Calculates target macros per slot from config
2. Filters dishes by compatibility, seasonality, and variety rules
3. Scores dishes on macro fit (Euclidean distance in nutrient space)
4. Fills slots greedily; handles batch dishes and tracking expiry

### Enable LLM mode (Ollama)
1. Install Ollama: https://ollama.com
2. Pull a model: `ollama pull llama3.2:3b`
3. In Settings, set **Planner mode** to "LLM" and model name
4. The app automatically falls back to algorithmic planner if Ollama is offline

### Add a new meal slot or macro target
- Update `SLOTS` in `web/app.py`
- Add slot splits to config defaults in `src/database.py` (`_DEFAULT_CONFIG`)
- Update forms in `web/templates/settings.html`
- Update macros computation logic in `src/planner.py`

### Debug macro calculations
Macro helper functions in `web/app.py`:
- `_day_macros(day)` — sums all dishes in a day
- `_slot_macros(dishes)` — sums a single slot
- `_macro_score(dish, budget)` — fitness for a dish given budget

These are injected into templates via context processors so Jinja2 can compute on-the-fly.

## Known Issues & Constraints

1. **WeasyPrint on Windows**: Requires GTK runtime installation. See README for the guide.
2. **No test suite**: Validation happens via browser and manual testing. Plans to add tests are deferred.
3. **Batch dish tracking**: Batch dishes are *assumed* to use linear decay (one serving per day). Complex cooking schedules are not supported.
4. **LLM mode**: Ollama runs locally; no remote LLM integration yet. Always falls back to algorithmic planning if offline.

## File Structure

```
MealGenerator/
├── data/meals.json               # TinyDB database (created on first run)
├── config.json                   # User settings (created with defaults)
├── requirements.txt              # Python dependencies
├── seed_meals.py                 # DB seeding script (20 sample dishes)
├── src/
│   ├── __init__.py
│   ├── database.py               # CRUD layer + config I/O
│   ├── planner.py                # Algorithmic meal planning
│   ├── llm_planner.py            # Optional Ollama-based planning
│   ├── grocery.py                # Ingredient aggregation
│   └── seasonality.py            # Season/hemisphere helpers
└── web/
    ├── app.py                    # FastAPI routes (Starlette 1.6.0+)
    ├── templates/
    │   ├── base.html             # Shared layout
    │   ├── index.html            # Dashboard
    │   ├── plan.html             # 7-day plan view
    │   ├── grocery.html          # Grocery list
    │   ├── plan_print.html       # PDF export template
    │   ├── history.html          # Past plans
    │   ├── dishes.html           # Browse dish library
    │   ├── add_dish.html         # Add dish form
    │   ├── settings.html         # Config page
    │   └── 404.html              # Error page
    └── static/
        ├── style.css             # Styling
        └── app.js                # Client-side interactivity
```

## Feedback from Prior Work

- **Starlette 1.6.0 API change**: Always pass `request` as the first argument to `TemplateResponse`. This was a breaking change in Starlette; the old `(name, context)` signature no longer works.
