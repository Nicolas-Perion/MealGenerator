"""Database module - provides access to dishes and plans databases.

This module re-exports functions from dishes_db and plans_db for backward compatibility.
Use dishes_db.py and plans_db.py directly for new code.
"""

# Re-export from dishes_db
from .dishes_db import (
    get_all_dishes,
    get_dishes_by_type,
    get_dish_by_id,
    add_dish,
    update_dish,
    delete_dish,
)

# Re-export from plans_db
from .plans_db import (
    save_plan,
    get_plan_by_id,
    get_last_plan,
    get_plan_history,
    delete_plan,
    load_config,
    save_config,
)

__all__ = [
    # Dishes
    "get_all_dishes",
    "get_dishes_by_type",
    "get_dish_by_id",
    "add_dish",
    "update_dish",
    "delete_dish",
    # Plans
    "save_plan",
    "get_plan_by_id",
    "get_last_plan",
    "get_plan_history",
    "delete_plan",
    # Config
    "load_config",
    "save_config",
]
