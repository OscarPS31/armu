"""
Build the self-contained demo dataset for the NutriPlan / Armu Streamlit app.

It joins the 889 fully-priced recipes (recipe_prices_complete_3chains.csv)
with their metadata and diet/time flags (recipes_clean.csv) and produces two
small, committed files that the app reads at runtime:

    data/demo_recipes.parquet          one row per recipe (metadata + flags +
                                       search_text + total cost per chain)
    data/demo_ingredient_costs.parquet one row per (recipe, ingredient, chain)
                                       used to build the shopping list

Run once locally (needs raw_data/, which is gitignored):

    python scripts/build_demo_dataset.py
"""

import ast
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_raw_data():
    """
    Locate raw_data/. It sits next to the project, but when running from a
    git worktree it lives in the main checkout instead, so we walk up a few
    parents until we find it.
    """
    for base in [PROJECT_ROOT, *PROJECT_ROOT.parents]:
        candidate = base / "raw_data"
        if (candidate / "recipe_prices_complete_3chains.csv").exists():
            return candidate
    raise FileNotFoundError(
        "Could not find raw_data/recipe_prices_complete_3chains.csv "
        "in any parent directory."
    )


RAW_DATA = find_raw_data()

PRICES_PATH = RAW_DATA / "recipe_prices_complete_3chains.csv"
RECIPES_PATH = RAW_DATA / "recipes_clean.csv"

OUT_RECIPES = PROJECT_ROOT / "data" / "demo_recipes.parquet"
OUT_COSTS = PROJECT_ROOT / "data" / "demo_ingredient_costs.parquet"

CHAINS = ["Walmart", "Soriana", "Chedraui"]

# Ingredients we do NOT charge for in the cart:
#   - water: it is tap water, not a bought product.
#   - salt / pepper: basic seasonings used in tiny real amounts, and the
#     upstream pipeline mis-homologates "pepper" to black-pepper spice with
#     absurd quantities (hundreds of grams), which wildly inflates the cart.
# See "Trabajo futuro" in the README.
EXCLUDED_INGREDIENTS = {"water", "salt", "pepper", "black pepper"}

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


def parse_list(value):
    """Turn a stringified python list into an actual list."""
    if pd.isna(value):
        return []
    try:
        result = ast.literal_eval(value)
        return result if isinstance(result, list) else []
    except Exception:
        return []


def build_search_text(row):
    """Free-text blob the TF-IDF ranker searches over."""
    name = str(row.get("name") or "")
    ingredients = " ".join(str(i) for i in row["ingredients"])
    tags = " ".join(str(t) for t in row["tags"])
    return f"{name} {ingredients} {tags}".lower()


def main():
    print("Loading priced recipes...")
    priced = pd.read_csv(PRICES_PATH)
    priced_ids = set(priced["id_receta"].unique())
    print(f"  {len(priced_ids)} recipes with a complete price")

    # --------------------------------------------------------
    # 1) ingredient-level cost table (for the shopping list)
    # --------------------------------------------------------
    costs = priced[
        [
            "id_receta",
            "ingrediente_homologado",
            "cantidad",
            "unidad",
            "cadena",
            "producto_profeco",
            "costo_ingrediente_mxn",
        ]
    ].copy()
    costs = costs.rename(
        columns={
            "id_receta": "id",
            "ingrediente_homologado": "ingredient",
            "cantidad": "quantity",
            "unidad": "unit",
            "cadena": "chain",
            "producto_profeco": "profeco_product",
            "costo_ingrediente_mxn": "cost_mxn",
        }
    )

    # Drop free / basic seasoning ingredients from costing.
    before = len(costs)
    costs = costs[~costs["ingredient"].isin(EXCLUDED_INGREDIENTS)]
    print(f"  excluded {before - len(costs)} rows (water/salt/pepper)")

    costs.to_parquet(OUT_COSTS, index=False)
    print(f"  wrote {OUT_COSTS.name} ({len(costs)} rows)")

    # --------------------------------------------------------
    # 2) total cost per recipe per chain -> wide columns
    #    Recomputed from the (filtered) ingredient costs so the recipe total
    #    always matches the shopping list.
    # --------------------------------------------------------
    totals = (
        costs.groupby(["id", "chain"], as_index=False)["cost_mxn"]
        .sum()
        .pivot(index="id", columns="chain", values="cost_mxn")
        .rename(columns={c: f"cost_{c.lower()}" for c in CHAINS})
    )
    totals = totals.reset_index()

    # --------------------------------------------------------
    # 3) recipe metadata + diet/time flags
    # --------------------------------------------------------
    print("Loading recipe metadata (this file is large)...")
    meta = pd.read_csv(
        RECIPES_PATH,
        usecols=[
            "id",
            "name",
            "ingredients",
            "steps",
            "servings",
            "tags",
            *FLAG_COLUMNS,
        ],
    )
    meta = meta[meta["id"].isin(priced_ids)].copy()
    meta = meta.drop_duplicates(subset="id", keep="first")

    meta["ingredients"] = meta["ingredients"].apply(parse_list)
    meta["steps"] = meta["steps"].apply(parse_list)
    meta["tags"] = meta["tags"].apply(parse_list)
    meta["search_text"] = meta.apply(build_search_text, axis=1)

    for col in FLAG_COLUMNS:
        meta[col] = meta[col].astype(bool)

    # --------------------------------------------------------
    # 4) join and save
    # --------------------------------------------------------
    recipes = meta.merge(totals, on="id", how="inner")

    # store list columns as JSON-friendly python objects (parquet handles lists)
    recipes.to_parquet(OUT_RECIPES, index=False)
    print(f"  wrote {OUT_RECIPES.name} ({len(recipes)} recipes)")
    print("Done.")


if __name__ == "__main__":
    main()
