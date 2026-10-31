import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.database import (
    add_dish, delete_dish, get_all_dishes, get_dish_by_id,
    get_last_plan, get_plan_by_id, get_plan_history,
    load_config, save_config, save_plan,
)
from src.grocery import compute_grocery_list
from src.planner import generate_plan as algo_generate

app = FastAPI(title="MealGenerator")

_WEB = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(_WEB / "static")), name="static")

SLOTS = ["breakfast", "lunch", "pre_snack", "dinner"]
SLOT_LABELS = {
    "breakfast": "Breakfast",
    "lunch": "Lunch",
    "pre_snack": "Pre-Training",
    "dinner": "Dinner",
}


def _day_macros(day: dict) -> dict:
    total = {"protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "calories": 0.0}
    for dishes in day["meals"].values():
        for d in dishes:
            m = d.get("macros", {})
            for k in total:
                total[k] += m.get(k, 0)
    return {k: round(v) for k, v in total.items()}


def _slot_macros(dishes: list) -> dict:
    total = {"protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "calories": 0.0}
    for d in dishes:
        m = d.get("macros", {})
        for k in total:
            total[k] += m.get(k, 0)
    return {k: round(v) for k, v in total.items()}


def _ctx_processor(request: Request) -> dict:
    return {
        "SLOTS": SLOTS,
        "SLOT_LABELS": SLOT_LABELS,
        "day_macros": _day_macros,
        "slot_macros": _slot_macros,
    }


templates = Jinja2Templates(
    directory=str(_WEB / "templates"),
    context_processors=[_ctx_processor],
)


def _resolve_plan(plan: dict) -> dict:
    resolved = dict(plan)
    resolved["days"] = []
    for day in plan["days"]:
        resolved_day = dict(day)
        resolved_day["meals"] = {}
        for slot, ids in day["meals"].items():
            dishes = [d for did in ids if (d := get_dish_by_id(did))]
            resolved_day["meals"][slot] = dishes
        resolved["days"].append(resolved_day)
    return resolved


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    plan = get_last_plan()
    resolved = _resolve_plan(plan) if plan else None
    config = load_config()
    return templates.TemplateResponse(request, "index.html", {"plan": resolved, "config": config})


# ── Settings ──────────────────────────────────────────────────────────────────

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    config = load_config()
    return templates.TemplateResponse(request, "settings.html", {"config": config})


@app.post("/settings")
async def settings_save(
    request: Request,
    protein_g: float = Form(...),
    carbs_g: float = Form(...),
    fat_g: float = Form(...),
    calories: float = Form(...),
    hemisphere: str = Form(...),
    macro_tolerance_pct: float = Form(15),
    breakfast_cal: float = Form(0.25),
    lunch_cal: float = Form(0.30),
    pre_snack_cal: float = Form(0.15),
    dinner_cal: float = Form(0.30),
    breakfast_protein: float = Form(0.25),
    lunch_protein: float = Form(0.30),
    pre_snack_protein: float = Form(0.15),
    dinner_protein: float = Form(0.30),
    breakfast_carbs: float = Form(0.30),
    lunch_carbs: float = Form(0.30),
    pre_snack_carbs: float = Form(0.20),
    dinner_carbs: float = Form(0.20),
    breakfast_fat: float = Form(0.25),
    lunch_fat: float = Form(0.30),
    pre_snack_fat: float = Form(0.15),
    dinner_fat: float = Form(0.30),
):
    config = {
        "daily_targets": {
            "protein_g": protein_g, "carbs_g": carbs_g,
            "fat_g": fat_g, "calories": calories,
        },
        "slot_splits": {
            "breakfast":  {"protein": breakfast_protein, "carbs": breakfast_carbs, "fat": breakfast_fat, "calories": breakfast_cal},
            "lunch":      {"protein": lunch_protein, "carbs": lunch_carbs, "fat": lunch_fat, "calories": lunch_cal},
            "pre_snack":  {"protein": pre_snack_protein, "carbs": pre_snack_carbs, "fat": pre_snack_fat, "calories": pre_snack_cal},
            "dinner":     {"protein": dinner_protein, "carbs": dinner_carbs, "fat": dinner_fat, "calories": dinner_cal},
        },
        "hemisphere": hemisphere,
        "macro_tolerance_pct": macro_tolerance_pct,
    }
    save_config(config)
    return RedirectResponse("/", status_code=303)


# ── Plan generation & display ─────────────────────────────────────────────────

@app.post("/plan/generate")
async def plan_generate(request: Request, mode: str = Query(default="auto")):
    config = load_config()
    plan = algo_generate(config)
    plan_id = save_plan(plan)
    return RedirectResponse(f"/plan/{plan_id}", status_code=303)


@app.get("/plan", response_class=HTMLResponse)
async def plan_latest(request: Request):
    plan = get_last_plan()
    if not plan:
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(f"/plan/{plan['id']}", status_code=303)


@app.get("/plan/{plan_id}", response_class=HTMLResponse)
async def plan_view(request: Request, plan_id: int):
    plan = get_plan_by_id(plan_id)
    if not plan:
        return templates.TemplateResponse(request, "404.html", {}, status_code=404)
    resolved = _resolve_plan(plan)
    return templates.TemplateResponse(request, "plan.html", {"plan": resolved})


# ── History ───────────────────────────────────────────────────────────────────

@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    plans = get_plan_history()
    return templates.TemplateResponse(request, "history.html", {"plans": plans})


# ── Grocery list ──────────────────────────────────────────────────────────────

@app.get("/grocery", response_class=HTMLResponse)
async def grocery_latest(request: Request):
    plan = get_last_plan()
    if not plan:
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(f"/grocery/{plan['id']}", status_code=303)


@app.get("/grocery/{plan_id}", response_class=HTMLResponse)
async def grocery_view(request: Request, plan_id: int):
    plan = get_plan_by_id(plan_id)
    if not plan:
        return templates.TemplateResponse(request, "404.html", {}, status_code=404)
    items = compute_grocery_list(plan)
    return templates.TemplateResponse(request, "grocery.html", {
        "items": items,
        "plan_id": plan_id,
        "generated_at": plan.get("generated_at", ""),
    })


@app.get("/grocery/{plan_id}/text", response_class=PlainTextResponse)
async def grocery_text(plan_id: int):
    plan = get_plan_by_id(plan_id)
    if not plan:
        return PlainTextResponse("Plan not found", status_code=404)
    items = compute_grocery_list(plan)
    lines = [f"{item['name']}: {item['total']}" for item in items]
    return PlainTextResponse("\n".join(lines))


# ── Dishes ────────────────────────────────────────────────────────────────────

@app.get("/dishes", response_class=HTMLResponse)
async def dishes_list(
    request: Request,
    dish_type: str = "",
    slot: str = "",
    season: str = "",
    tag: str = "",
):
    all_dishes = get_all_dishes()
    all_tags = sorted({t for d in all_dishes for t in d.get("tags", []) if t})
    dishes = all_dishes
    if dish_type:
        dishes = [d for d in dishes if d.get("dish_type") == dish_type]
    if slot:
        dishes = [d for d in dishes if slot in d.get("compatible_slots", [])]
    if season:
        dishes = [d for d in dishes if season in d.get("seasons", [])]
    if tag:
        dishes = [d for d in dishes if tag in d.get("tags", [])]
    return templates.TemplateResponse(request, "dishes.html", {
        "dishes": dishes,
        "filter_type": dish_type,
        "filter_slot": slot,
        "filter_season": season,
        "filter_tag": tag,
        "all_tags": all_tags,
    })


@app.get("/dishes/add", response_class=HTMLResponse)
async def dish_add_form(request: Request):
    return templates.TemplateResponse(request, "add_dish.html", {"dish": None, "errors": []})


@app.post("/dishes/add")
async def dish_add_submit(request: Request):
    form = await request.form()
    errors = []

    name = form.get("name", "").strip()
    if not name:
        errors.append("Dish name is required.")

    dish_type = form.get("dish_type", "")
    compatible_slots = form.getlist("compatible_slots")
    seasons = form.getlist("seasons")
    tags_raw = form.get("tags", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    prep_minutes = int(form.get("prep_minutes", 0) or 0)

    is_batch = form.get("is_batch") == "on"
    batch_size = int(form.get("batch_size", 1) or 1) if is_batch else 1
    shelf_life_days = int(form.get("shelf_life_days", 1) or 1) if is_batch else 1

    try:
        protein_g = float(form.get("protein_g", 0))
        carbs_g = float(form.get("carbs_g", 0))
        fat_g = float(form.get("fat_g", 0))
        calories = round(protein_g * 4 + carbs_g * 4 + fat_g * 9)
    except ValueError:
        errors.append("Macros must be numbers.")
        protein_g = carbs_g = fat_g = calories = 0

    ingredients = []
    i = 0
    while True:
        ing_name = form.get(f"ing_name_{i}", "").strip()
        if not ing_name:
            break
        qty_raw = form.get(f"ing_qty_{i}", "0")
        unit = form.get(f"ing_unit_{i}", "g")
        try:
            qty = float(qty_raw)
        except ValueError:
            qty = 0.0
        ing = {"name": ing_name}
        if unit == "g":
            ing["quantity_g"] = qty
        elif unit == "ml":
            ing["quantity_ml"] = qty
        else:
            ing["quantity_units"] = qty
        ingredients.append(ing)
        i += 1

    if not ingredients:
        errors.append("At least one ingredient is required.")
    if not compatible_slots:
        errors.append("Select at least one compatible slot.")

    if errors:
        return templates.TemplateResponse(request, "add_dish.html", {
            "dish": dict(form),
            "errors": errors,
        })

    dish = {
        "name": name,
        "dish_type": dish_type,
        "compatible_slots": compatible_slots,
        "ingredients": ingredients,
        "macros": {"protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g, "calories": calories},
        "seasons": seasons if seasons else ["spring", "summer", "autumn", "winter"],
        "tags": tags,
        "prep_minutes": prep_minutes,
        "batch_size": batch_size,
        "shelf_life_days": shelf_life_days,
    }
    add_dish(dish)
    return RedirectResponse("/dishes", status_code=303)


@app.post("/dishes/{dish_id}/delete")
async def dish_delete(dish_id: int):
    delete_dish(dish_id)
    return RedirectResponse("/dishes", status_code=303)


# ── PDF export ────────────────────────────────────────────────────────────────

@app.get("/plan/{plan_id}/export")
async def plan_export_pdf(request: Request, plan_id: int):
    plan = get_plan_by_id(plan_id)
    if not plan:
        return PlainTextResponse("Plan not found", status_code=404)

    resolved = _resolve_plan(plan)
    items = compute_grocery_list(plan)

    html_content = templates.get_template("plan_print.html").render(
        request=request,
        plan=resolved,
        items=items,
        day_macros=_day_macros,
        slot_macros=_slot_macros,
        SLOTS=SLOTS,
        SLOT_LABELS=SLOT_LABELS,
    )

    try:
        import weasyprint
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=meal_plan_{plan_id}.pdf"},
        )
    except ImportError:
        return PlainTextResponse(
            "WeasyPrint is not installed. Run: pip install weasyprint", status_code=501
        )


# ── JSON API ──────────────────────────────────────────────────────────────────

@app.get("/api/dishes")
async def api_dishes():
    return get_all_dishes()


@app.get("/api/plan/current")
async def api_plan_current():
    plan = get_last_plan()
    return _resolve_plan(plan) if plan else {}


@app.get("/api/plan/{plan_id}")
async def api_plan(plan_id: int):
    plan = get_plan_by_id(plan_id)
    return _resolve_plan(plan) if plan else {}
