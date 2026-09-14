"""
Build the demo dataset for Armu / NutriPlan (simplified scope).

Joins recipe metadata + diet/time flags (recipes_clean.csv) with the per-recipe
estimated cost (recipes_with_estimated_cost.csv) and keeps only recipes whose
cost estimate is reliable. Produces one committed file the app reads at runtime:

    data/recipes_priced.parquet

Run once locally (needs raw_data/, which is gitignored):

    python scripts/build_demo_dataset.py
"""

import ast
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_raw_data():
    for base in [PROJECT_ROOT, *PROJECT_ROOT.parents]:
        candidate = base / "raw_data"
        if (candidate / "recipes_with_estimated_cost.csv").exists():
            return candidate
    raise FileNotFoundError("Could not find raw_data/recipes_with_estimated_cost.csv")


RAW_DATA = find_raw_data()
COST_PATH = RAW_DATA / "recipes_with_estimated_cost.csv"
RECIPES_PATH = RAW_DATA / "recipes_clean.csv"
OUT_PATH = PROJECT_ROOT / "data" / "recipes_priced.parquet"

FLAG_COLUMNS = [
    "is_vegan",
    "is_vegetarian",
    "is_gluten_free",
    "is_dairy_free",
    "is_lactose_free",
    "is_nut_free",
    "is_egg_free",
    "quick_15min",
    "quick_30min",
    "quick_60min",
]

# Keep only recipes whose cost estimate we trust. High-confidence keeps the
# file small and the shown costs believable, with all restrictions still usable.
MIN_CONFIDENCE = {"high"}
MIN_COVERAGE = 0.6


def parse_list(value):
    if pd.isna(value):
        return []
    try:
        result = ast.literal_eval(value)
        return result if isinstance(result, list) else []
    except Exception:
        return []


def build_search_text(row):
    name = str(row.get("name") or "")
    ingredients = " ".join(str(i) for i in row["ingredients"])
    tags = " ".join(str(t) for t in row["tags"])
    return f"{name} {ingredients} {tags}".lower()


def main():
    print("Loading cost estimates...")
    cost = pd.read_csv(
        COST_PATH,
        usecols=[
            "id",
            "estimated_cost",
            "minimum_estimate",
            "maximum_estimate",
            "confidence",
            "price_coverage",
        ],
    )

    reliable = cost[
        cost["confidence"].isin(MIN_CONFIDENCE)
        & (cost["price_coverage"] >= MIN_COVERAGE)
        & (cost["estimated_cost"] > 0)
    ].copy()
    print(f"  {len(reliable)} recipes with a reliable estimate")
    reliable_ids = set(reliable["id"])

    print("Loading recipe metadata (large file)...")
    meta = pd.read_csv(
        RECIPES_PATH,
        usecols=["id", "name", "ingredients", "steps", "servings", "tags", *FLAG_COLUMNS],
    )
    meta = meta[meta["id"].isin(reliable_ids)].copy()
    meta = meta.drop_duplicates(subset="id", keep="first")

    meta["ingredients"] = meta["ingredients"].apply(parse_list)
    meta["steps"] = meta["steps"].apply(parse_list)
    meta["tags"] = meta["tags"].apply(parse_list)
    meta["search_text"] = meta.apply(build_search_text, axis=1)
    for col in FLAG_COLUMNS:
        meta[col] = meta[col].astype(bool)

    recipes = meta.merge(
        reliable[["id", "estimated_cost", "minimum_estimate", "maximum_estimate", "confidence"]],
        on="id",
        how="inner",
    )
    recipes["estimated_cost"] = recipes["estimated_cost"].round(2)
    recipes["minimum_estimate"] = recipes["minimum_estimate"].round(2)
    recipes["maximum_estimate"] = recipes["maximum_estimate"].round(2)

    recipes.to_parquet(OUT_PATH, index=False)
    print(f"  wrote {OUT_PATH.name} ({len(recipes)} recipes)")
    print("Done.")


if __name__ == "__main__":
    main()
