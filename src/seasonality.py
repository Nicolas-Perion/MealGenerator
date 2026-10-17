from datetime import datetime

_NORTH = {
    1: "winter", 2: "winter", 3: "spring",
    4: "spring", 5: "spring", 6: "summer",
    7: "summer", 8: "summer", 9: "autumn",
    10: "autumn", 11: "autumn", 12: "winter",
}
_OPPOSITE = {"winter": "summer", "summer": "winter", "spring": "autumn", "autumn": "spring"}
_SOUTH = {m: _OPPOSITE[s] for m, s in _NORTH.items()}


def current_season(hemisphere: str = "north") -> str:
    month = datetime.now().month
    return _NORTH[month] if hemisphere == "north" else _SOUTH[month]


def is_dish_seasonal(dish: dict, hemisphere: str = "north") -> bool:
    seasons = dish.get("seasons", [])
    if not seasons:
        return True
    return current_season(hemisphere) in seasons
