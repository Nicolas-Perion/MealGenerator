# MealGenerator

A Python web application that generates varied 7-day meal plans with a grocery list.

## Features

- **7-day meal plans** with 4 slots per day: Breakfast, Lunch, Pre-Training Snack, Dinner
- **Dish-based composition**: each slot is filled with 1–2 dishes (a main + optional dessert/side)
- **Batch cooking support**: batch dishes (e.g. an apple pie → 4 slices) are automatically spread across the week and counted once in the grocery list
- **Macronutrient constraints**: configurable daily targets + per-slot calorie splits
- **Seasonal ingredients**: filters dishes by current season and hemisphere
- **Variety**: avoids repeating dishes from the previous week's plan
- **Grocery list**: exact ingredient aggregation by code — no hallucinations
- **Plan history**: browse and re-export any past plan
- **PDF export**: one-click download of the plan + grocery list

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **PDF export** requires WeasyPrint. On Windows, follow the
> [WeasyPrint installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)
> for GTK runtime dependencies.

### 2. Seed the database

```bash
python seed_meals.py
```

This populates the database with 20 sample dishes. Safe to run multiple times.

### 3. Run the app

```bash
uvicorn web.app:app --reload
```

Then open **http://localhost:8001** in your browser.

## Usage

| Page | URL | What it does |
|---|---|---|
| Dashboard | `/` | Overview + generate button |
| Generate plan | Click "Generate 7-Day Plan" | Creates a new plan, redirects to plan view |
| Plan view | `/plan` | 7-day table with meal names + macros |
| Grocery list | `/grocery` | Aggregated ingredient list |
| History | `/history` | All past plans |
| Dishes | `/dishes` | Browse + filter the dish library |
| Add dish | `/dishes/add` | Form to add a new dish to the database |
| Settings | `/settings` | Macro targets, slot splits, hemisphere |
| PDF export | Plan page → "Export PDF" | Download plan + grocery list as PDF |

## Adding Dishes

Go to **Dishes → Add Dish**. Fill in:
- Name, dish type (main / dessert / side / snack / drink)
- Compatible meal slots
- Seasons (leave blank for year-round)
- **Ingredients** — enter quantities for the **full batch** (or 1 serving if not a batch dish)
- **Macros** — enter values per **one serving**; calories are auto-computed

For batch dishes (e.g. a pie, a cake), tick "This is a batch dish" and enter the batch size and shelf life. The planner will spread servings across the week automatically.

## Project Structure

```
MealGenerator/
├── data/meals.json       # TinyDB database
├── src/
│   ├── database.py       # CRUD layer
│   ├── seasonality.py    # Season helpers
│   ├── planner.py        # Algorithmic planner
│   └── grocery.py        # Grocery aggregation
├── web/
│   ├── app.py            # FastAPI routes
│   ├── templates/        # Jinja2 HTML templates
│   └── static/           # CSS + JS
├── seed_meals.py         # DB seeding script
├── config.json           # User settings
└── requirements.txt
```
