from api.schemas import Recipe
from api.services.recipes import get_recipes

DAYS = ["monday", "tuesday", "wednesday", "thursday",
        "friday", "saturday", "sunday"]


def to_recipe(row: dict) -> Recipe:
    """Translate a raw parquet row into the api recipe shape"""
    return Recipe(
        id=row["id"],
        name=row.get("name") or "Sin nombre",
        servings=row.get("servings"),
        serving_size=row.get("serving_size"),
        ingredients=list(row.get("ingredients_raw") or []),
        steps=list(row.get("steps") or []),
        tags=list(row.get("tags") or []),
        is_vegan=bool(row.get("is_vegan", False)),
        is_vegetarian=bool(row.get("is_vegetarian", False)),
        is_gluten_free=bool(row.get("is_gluten_free", False)),
    )


def _placeholder(recipe_id: int) -> Recipe:
    return Recipe(id=recipe_id, name="Receta no disponible")


def _extract_id(item) -> int:
    """Accept a bare id"""
    return item if isinstance(item, int) else item["id"]


def enrich_menu(menu: dict) -> dict[str, list[Recipe]]:
    """Takes days of the week with recipe id and returns list of recipes"""
    ids = [_extract_id(item) for day in menu.values() for item in day]
    by_id = {r["id"]: to_recipe(r) for r in get_recipes(ids)}

    out = {}
    for day, items in menu.items():
        out[day] = [
            by_id.get(_extract_id(i)) or _placeholder(_extract_id(i))
            for i in items
        ]
    return out
