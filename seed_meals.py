"""Populate the database with sample dishes. Safe to run multiple times — skips
dishes whose name already exists."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import add_dish, get_all_dishes

DISHES = [
    # ── Breakfasts (main) ──────────────────────────────────────────────────
    {
        "name": "Oatmeal + Banana + Peanut Butter",
        "dish_type": "main",
        "compatible_slots": ["breakfast"],
        "ingredients": [
            {"name": "rolled oats", "quantity_g": 80},
            {"name": "banana", "quantity_units": 1},
            {"name": "peanut butter", "quantity_g": 30},
            {"name": "milk", "quantity_ml": 200},
        ],
        "macros": {"protein_g": 12, "carbs_g": 58, "fat_g": 10, "calories": 374},
        "seasons": ["winter", "autumn"],
        "tags": ["vegetarian"],
        "prep_minutes": 10,
    },
    {
        "name": "Scrambled Eggs + Whole Grain Toast",
        "dish_type": "main",
        "compatible_slots": ["breakfast"],
        "ingredients": [
            {"name": "eggs", "quantity_units": 3},
            {"name": "whole grain bread", "quantity_g": 70},
            {"name": "butter", "quantity_g": 10},
        ],
        "macros": {"protein_g": 24, "carbs_g": 28, "fat_g": 14, "calories": 334},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["vegetarian", "high-protein"],
        "prep_minutes": 8,
    },
    {
        "name": "Smoked Salmon + Cream Cheese Bagel",
        "dish_type": "main",
        "compatible_slots": ["breakfast"],
        "ingredients": [
            {"name": "bagel", "quantity_units": 1},
            {"name": "smoked salmon", "quantity_g": 80},
            {"name": "cream cheese", "quantity_g": 40},
            {"name": "capers", "quantity_g": 10},
        ],
        "macros": {"protein_g": 22, "carbs_g": 44, "fat_g": 18, "calories": 426},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["omega-3"],
        "prep_minutes": 5,
    },
    {
        "name": "Greek Yogurt + Berries + Granola",
        "dish_type": "main",
        "compatible_slots": ["breakfast"],
        "ingredients": [
            {"name": "greek yogurt", "quantity_g": 200},
            {"name": "mixed berries", "quantity_g": 100},
            {"name": "granola", "quantity_g": 50},
        ],
        "macros": {"protein_g": 18, "carbs_g": 42, "fat_g": 8, "calories": 314},
        "seasons": ["spring", "summer"],
        "tags": ["vegetarian", "high-protein"],
        "prep_minutes": 3,
    },
    # ── Lunches (main) ─────────────────────────────────────────────────────
    {
        "name": "Chicken + Quinoa + Cherry Tomatoes",
        "dish_type": "main",
        "compatible_slots": ["lunch", "dinner"],
        "ingredients": [
            {"name": "chicken breast", "quantity_g": 150},
            {"name": "quinoa (dry)", "quantity_g": 80},
            {"name": "cherry tomatoes", "quantity_g": 80},
            {"name": "cucumber", "quantity_g": 60},
            {"name": "olive oil", "quantity_ml": 10},
        ],
        "macros": {"protein_g": 42, "carbs_g": 51, "fat_g": 9, "calories": 453},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["high-protein", "gluten-free"],
        "prep_minutes": 20,
    },
    {
        "name": "Tuna Nicoise Salad",
        "dish_type": "main",
        "compatible_slots": ["lunch"],
        "ingredients": [
            {"name": "canned tuna", "quantity_g": 160},
            {"name": "green beans", "quantity_g": 100},
            {"name": "eggs", "quantity_units": 2},
            {"name": "olives", "quantity_g": 30},
            {"name": "olive oil", "quantity_ml": 15},
            {"name": "cherry tomatoes", "quantity_g": 80},
        ],
        "macros": {"protein_g": 35, "carbs_g": 22, "fat_g": 14, "calories": 354},
        "seasons": ["spring", "summer"],
        "tags": ["gluten-free", "omega-3"],
        "prep_minutes": 15,
    },
    {
        "name": "Lentil Soup + Crusty Bread",
        "dish_type": "main",
        "compatible_slots": ["lunch"],
        "ingredients": [
            {"name": "red lentils (dry)", "quantity_g": 100},
            {"name": "carrots", "quantity_g": 80},
            {"name": "onion", "quantity_g": 60},
            {"name": "crusty bread", "quantity_g": 80},
            {"name": "olive oil", "quantity_ml": 10},
            {"name": "vegetable stock", "quantity_ml": 400},
        ],
        "macros": {"protein_g": 18, "carbs_g": 62, "fat_g": 5, "calories": 369},
        "seasons": ["winter", "autumn"],
        "tags": ["vegetarian", "vegan"],
        "prep_minutes": 30,
    },
    {
        "name": "Turkey & Avocado Wrap",
        "dish_type": "main",
        "compatible_slots": ["lunch"],
        "ingredients": [
            {"name": "tortilla wrap", "quantity_units": 1},
            {"name": "turkey breast slices", "quantity_g": 120},
            {"name": "avocado", "quantity_units": 0.5},
            {"name": "lettuce", "quantity_g": 30},
            {"name": "tomato", "quantity_g": 60},
            {"name": "mustard", "quantity_g": 10},
        ],
        "macros": {"protein_g": 32, "carbs_g": 38, "fat_g": 16, "calories": 428},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["high-protein"],
        "prep_minutes": 8,
    },
    # ── Dinners (main) ─────────────────────────────────────────────────────
    {
        "name": "Grilled Salmon + Sweet Potato + Broccoli",
        "dish_type": "main",
        "compatible_slots": ["dinner"],
        "ingredients": [
            {"name": "salmon fillet", "quantity_g": 180},
            {"name": "sweet potato", "quantity_g": 200},
            {"name": "broccoli florets", "quantity_g": 150},
            {"name": "olive oil", "quantity_ml": 15},
            {"name": "lemon", "quantity_units": 0.5},
        ],
        "macros": {"protein_g": 44, "carbs_g": 38, "fat_g": 16, "calories": 476},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["omega-3", "gluten-free"],
        "prep_minutes": 30,
    },
    {
        "name": "Beef Stir-Fry + Brown Rice",
        "dish_type": "main",
        "compatible_slots": ["dinner"],
        "ingredients": [
            {"name": "beef sirloin strips", "quantity_g": 160},
            {"name": "brown rice (dry)", "quantity_g": 90},
            {"name": "bell peppers", "quantity_g": 100},
            {"name": "broccoli florets", "quantity_g": 80},
            {"name": "soy sauce", "quantity_ml": 20},
            {"name": "sesame oil", "quantity_ml": 8},
        ],
        "macros": {"protein_g": 38, "carbs_g": 55, "fat_g": 14, "calories": 506},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["high-protein"],
        "prep_minutes": 25,
    },
    {
        "name": "Chicken Tikka Masala + Basmati Rice",
        "dish_type": "main",
        "compatible_slots": ["dinner"],
        "ingredients": [
            {"name": "chicken breast", "quantity_g": 180},
            {"name": "basmati rice (dry)", "quantity_g": 90},
            {"name": "canned tomatoes", "quantity_g": 200},
            {"name": "coconut milk", "quantity_ml": 100},
            {"name": "tikka masala paste", "quantity_g": 40},
            {"name": "onion", "quantity_g": 60},
        ],
        "macros": {"protein_g": 40, "carbs_g": 62, "fat_g": 18, "calories": 570},
        "seasons": ["winter", "autumn"],
        "tags": ["high-protein"],
        "prep_minutes": 35,
    },
    {
        "name": "Grilled Sea Bass + Ratatouille",
        "dish_type": "main",
        "compatible_slots": ["dinner"],
        "ingredients": [
            {"name": "sea bass fillet", "quantity_g": 200},
            {"name": "courgette", "quantity_g": 100},
            {"name": "aubergine", "quantity_g": 100},
            {"name": "bell peppers", "quantity_g": 80},
            {"name": "canned tomatoes", "quantity_g": 150},
            {"name": "olive oil", "quantity_ml": 15},
        ],
        "macros": {"protein_g": 36, "carbs_g": 20, "fat_g": 12, "calories": 332},
        "seasons": ["summer"],
        "tags": ["gluten-free", "omega-3"],
        "prep_minutes": 35,
    },
    # ── Pre-training snacks ─────────────────────────────────────────────────
    {
        "name": "Rice Cakes + Almond Butter",
        "dish_type": "snack",
        "compatible_slots": ["pre_snack"],
        "ingredients": [
            {"name": "rice cakes", "quantity_units": 3},
            {"name": "almond butter", "quantity_g": 30},
        ],
        "macros": {"protein_g": 8, "carbs_g": 32, "fat_g": 12, "calories": 268},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["vegan", "gluten-free"],
        "prep_minutes": 2,
    },
    {
        "name": "Cottage Cheese + Walnuts",
        "dish_type": "snack",
        "compatible_slots": ["pre_snack", "breakfast"],
        "ingredients": [
            {"name": "cottage cheese", "quantity_g": 200},
            {"name": "walnuts", "quantity_g": 30},
        ],
        "macros": {"protein_g": 20, "carbs_g": 8, "fat_g": 14, "calories": 238},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["vegetarian", "high-protein", "gluten-free"],
        "prep_minutes": 2,
    },
    {
        "name": "Whey Protein Shake + Banana",
        "dish_type": "snack",
        "compatible_slots": ["pre_snack"],
        "ingredients": [
            {"name": "whey protein powder", "quantity_g": 30},
            {"name": "banana", "quantity_units": 1},
            {"name": "milk", "quantity_ml": 250},
        ],
        "macros": {"protein_g": 25, "carbs_g": 30, "fat_g": 3, "calories": 247},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["high-protein"],
        "prep_minutes": 3,
    },
    {
        "name": "Edamame + Hard-Boiled Eggs",
        "dish_type": "snack",
        "compatible_slots": ["pre_snack"],
        "ingredients": [
            {"name": "edamame (shelled)", "quantity_g": 100},
            {"name": "eggs", "quantity_units": 2},
        ],
        "macros": {"protein_g": 18, "carbs_g": 10, "fat_g": 9, "calories": 189},
        "seasons": ["spring", "summer"],
        "tags": ["vegetarian", "gluten-free"],
        "prep_minutes": 10,
    },
    # ── Desserts ────────────────────────────────────────────────────────────
    {
        "name": "Apple Pie",
        "dish_type": "dessert",
        "compatible_slots": ["lunch", "dinner"],
        "batch_size": 4,
        "shelf_life_days": 5,
        "ingredients": [
            {"name": "plain flour", "quantity_g": 300},
            {"name": "butter", "quantity_g": 150},
            {"name": "apples", "quantity_units": 4},
            {"name": "sugar", "quantity_g": 100},
            {"name": "egg", "quantity_units": 1},
            {"name": "cinnamon", "quantity_g": 5},
        ],
        "macros": {"protein_g": 3, "carbs_g": 34, "fat_g": 12, "calories": 255},
        "seasons": ["autumn", "winter"],
        "tags": ["vegetarian", "batch"],
        "prep_minutes": 60,
    },
    {
        "name": "Fresh Fruit Salad",
        "dish_type": "dessert",
        "compatible_slots": ["breakfast", "lunch", "dinner"],
        "ingredients": [
            {"name": "strawberries", "quantity_g": 80},
            {"name": "melon", "quantity_g": 80},
            {"name": "kiwi", "quantity_units": 1},
            {"name": "mint leaves", "quantity_g": 3},
        ],
        "macros": {"protein_g": 2, "carbs_g": 22, "fat_g": 0, "calories": 96},
        "seasons": ["spring", "summer"],
        "tags": ["vegan", "gluten-free"],
        "prep_minutes": 5,
    },
    {
        "name": "Dark Chocolate",
        "dish_type": "dessert",
        "compatible_slots": ["lunch", "dinner", "pre_snack"],
        "ingredients": [
            {"name": "dark chocolate (70%+)", "quantity_g": 30},
        ],
        "macros": {"protein_g": 3, "carbs_g": 18, "fat_g": 11, "calories": 179},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["vegan", "gluten-free"],
        "prep_minutes": 0,
    },
    {
        "name": "Plain Yogurt + Honey",
        "dish_type": "dessert",
        "compatible_slots": ["breakfast", "lunch", "dinner"],
        "ingredients": [
            {"name": "plain yogurt", "quantity_g": 150},
            {"name": "honey", "quantity_g": 20},
        ],
        "macros": {"protein_g": 8, "carbs_g": 20, "fat_g": 3, "calories": 139},
        "seasons": ["spring", "summer", "autumn", "winter"],
        "tags": ["vegetarian", "gluten-free"],
        "prep_minutes": 1,
    },
]


def seed():
    existing_names = {d["name"] for d in get_all_dishes()}
    inserted = 0
    skipped = 0
    for dish in DISHES:
        if dish["name"] in existing_names:
            skipped += 1
        else:
            add_dish(dish)
            inserted += 1
    print(f"Seeded {inserted} dishes ({skipped} already existed).")


if __name__ == "__main__":
    seed()
