import json
from pathlib import Path


CACHE_PATH = Path("data/recipe_translations.json")


def load_cache():
    if not CACHE_PATH.exists():
        return {}

    return json.loads(
        CACHE_PATH.read_text(encoding="utf-8")
    )


def save_cache(cache):
    CACHE_PATH.write_text(
        json.dumps(
            cache,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def get_translation(recipe_id):
    cache = load_cache()
    return cache.get(str(recipe_id))


def save_translation(recipe_id, name, ingredients, steps):
    cache = load_cache()

    cache[str(recipe_id)] = {
        "name": name,
        "ingredients": ingredients,
        "steps": steps,
    }

    save_cache(cache)


def get_translations(recipe_ids):
    cache = load_cache()

    found = {}
    missing = []

    for recipe_id in recipe_ids:
        key = str(recipe_id)

        if key in cache:
            found[recipe_id] = cache[key]
        else:
            missing.append(recipe_id)

    return found, missing


def save_translations(translations):
    cache = load_cache()

    for recipe_id, translation in translations.items():
        cache[str(recipe_id)] = translation

    save_cache(cache)


def get_translated_recipe_ids():
    cache = load_cache()
    return [int(recipe_id) for recipe_id in cache.keys()]
