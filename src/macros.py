"""Module for calculating macronutrients from ingredients."""

from typing import Dict, Optional, Union

from .database import get_dish_by_id
from .ingredients_db import get_ingredient_by_id


def calculate_dish_macros(dish: Union[dict, int]) -> Dict[str, float]:
    """Calculate the total macronutrients for a dish based on its ingredients.

    Args:
        dish: Either a dish dictionary or a dish ID (int). If an ID is provided,
              the dish will be fetched from the database.

    The dish should have ingredients in the new format:
    {
        "ingredients": [
            {"ingredient_id": 1, "quantity": 80},
            {"ingredient_id": 2, "quantity": 1},
            ...
        ]
    }

    Returns:
    {
        "protein_g": float,
        "carbs_g": float,
        "fat_g": float,
        "calories": float
    }
    """
    # If dish is an ID, fetch the dish from database
    if isinstance(dish, int):
        dish = get_dish_by_id(dish)
        if not dish:
            return {"protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "calories": 0.0}
    
    # If dish is None, return zeros
    if not dish:
        return {"protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "calories": 0.0}
    
    total = {"protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "calories": 0.0}

    for ing in dish.get("ingredients", []):
        ingredient_id = ing.get("ingredient_id")
        quantity = ing.get("quantity", 0)

        if not ingredient_id or quantity == 0:
            continue

        # Use calculate_ingredient_macros to get macros for this ingredient
        ingredient_macros = calculate_ingredient_macros(ingredient_id, quantity)
        
        # Add to total
        for macro in ["protein_g", "carbs_g", "fat_g", "calories"]:
            total[macro] += ingredient_macros.get(macro, 0)

    # Round to reasonable precision (though individual calls already round)
    for key in total:
        total[key] = round(total[key], 1)

    return total


def calculate_ingredient_macros(
    ingredient_id: int, quantity: float, unit: Optional[str] = None
) -> Dict[str, float]:
    """Calculate macros for a specific ingredient with a given quantity.

    Args:
        ingredient_id: ID of the ingredient
        quantity: Quantity of the ingredient
        unit: Optional unit override (defaults to ingredient's unit)

    Returns:
        Dictionary with protein_g, carbs_g, fat_g, calories
    """
    ingredient = get_ingredient_by_id(ingredient_id)
    if not ingredient:
        return {"protein_g": 0, "carbs_g": 0, "fat_g": 0, "calories": 0}

    macros_per_unit = ingredient.get("macros_per_unit", {})
    ingredient_unit = ingredient.get("unit", "g")

    # Use provided unit or ingredient's unit
    actual_unit = unit or ingredient_unit

    # For now, we assume quantity is in the ingredient's unit
    # In the future, we could add unit conversion here
    multiplier = quantity

    result = {
        "protein_g": round(macros_per_unit.get("protein_g", 0) * multiplier, 1),
        "carbs_g": round(macros_per_unit.get("carbs_g", 0) * multiplier, 1),
        "fat_g": round(macros_per_unit.get("fat_g", 0) * multiplier, 1),
        "calories": round(macros_per_unit.get("calories", 0) * multiplier, 1),
    }

    return result


def scale_macros(macros: Dict[str, float], scale: float) -> Dict[str, float]:
    """Scale macronutrients by a factor."""
    return {k: round(v * scale, 1) for k, v in macros.items()}


def add_macros(*macros_list: Dict[str, float]) -> Dict[str, float]:
    """Add multiple macronutrient dictionaries together."""
    total = {"protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "calories": 0.0}
    for macros in macros_list:
        for key in total:
            total[key] += macros.get(key, 0)
    return {k: round(v, 1) for k, v in total.items()}
