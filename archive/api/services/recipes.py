from pathlib import Path
import pyarrow.parquet as pq

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "recipes_lookup.parquet"

def get_recipes(ids):
    """
    Returns dict with content of ids. Non existent ids are skipped
    """
    ids = list(ids)
    if not ids:
        return []

    table = pq.read_table(DATA_PATH, filters = [('id', 'in', ids)])
    by_id = {row['id']: row for row in table.to_pylist()}

    return [by_id[i] for i in ids if i in by_id]

def get_recipe(recipe_id):
    """
    Individual recipe lookup
    """
    found = get_recipes([recipe_id])
    return found[0] if found else None
