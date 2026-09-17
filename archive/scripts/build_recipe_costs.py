from pathlib import Path

import numpy as np
import pandas as pd


QUANTITIES_PATH = Path(
    "data/recipe_ingredients_quantities.csv"
)

MAPPING_PATH = Path(
    "data/ingredient_mapping_all.csv"
)

PRICES_PATH = Path(
    "data/ingredient_prices_top3_chains_clean.csv"
)

RECIPES_PATH = Path(
    "data/Kaggle/recipes_ingredients.csv"
)

INGREDIENT_COSTS_PATH = Path(
    "data/recipe_ingredient_costs.csv"
)

RECIPE_COSTS_PATH = Path(
    "data/recipe_costs.csv"
)


# ============================================================
# LOAD
# ============================================================

print("Loading data...")

quantities = pd.read_csv(
    QUANTITIES_PATH,
    low_memory=False,
)

mapping = pd.read_csv(
    MAPPING_PATH,
    low_memory=False,
)

prices = pd.read_csv(
    PRICES_PATH,
    low_memory=False,
)

recipes = pd.read_csv(
    RECIPES_PATH,
    usecols=[
        "id",
        "name",
        "servings",
        "serving_size",
    ],
    low_memory=False,
)


# ============================================================
# NORMALIZE TEXT KEYS
# ============================================================

def normalize_text(series):
    return (
        series
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
        .str.replace(
            r"\s+",
            " ",
            regex=True,
        )
    )


quantities["ingredient_key"] = normalize_text(
    quantities["ingredient"]
)

mapping["ingredient_key"] = normalize_text(
    mapping["ingredient"]
)

prices["price_ingredient_key"] = normalize_text(
    prices["ingrediente"]
)


# ============================================================
# PREPARE MAPPING
# ============================================================

mapping_valid = (
    mapping[
        mapping["has_profeco_price"] == True
    ][
        [
            "ingredient_key",
            "canonical_ingredient",
            "profeco_category",
        ]
    ]
    .dropna(
        subset=[
            "canonical_ingredient",
        ]
    )
    .drop_duplicates(
        subset=[
            "ingredient_key",
        ]
    )
    .copy()
)

mapping_valid["canonical_key"] = normalize_text(
    mapping_valid["canonical_ingredient"]
)


# ============================================================
# MAP RECIPE INGREDIENT -> CANONICAL INGREDIENT
# ============================================================

q = quantities.merge(
    mapping_valid,
    on="ingredient_key",
    how="left",
)


mapped_rows = q[
    "canonical_ingredient"
].notna().sum()

print(
    f"Ingredient quantity rows: {len(q):,}"
)

print(
    f"Rows with canonical PROFECO mapping: "
    f"{mapped_rows:,}"
)


# ============================================================
# PREPARE CLEAN PRICES
#
# Option A is used because:
# - solids are MXN per gram
# - liquids remain MXN per liter
# - pieza remains MXN per pieza
# - manojo remains MXN per manojo
# ============================================================

price_base = prices[
    [
        "cadena",
        "ingrediente",
        "producto_profeco",
        "precio_opcion_a_mxn",
        "unidad_opcion_a",
        "price_ingredient_key",
    ]
].copy()


# There can be more than one price row for the same
# ingredient/chain/unit. Collapse them to one mean price.
price_base = (
    price_base
    .groupby(
        [
            "cadena",
            "price_ingredient_key",
            "unidad_opcion_a",
        ],
        as_index=False,
    )
    .agg(
        precio_mxn=(
            "precio_opcion_a_mxn",
            "mean",
        ),
        producto_profeco=(
            "producto_profeco",
            lambda x: ", ".join(
                sorted(
                    set(
                        str(v)
                        for v in x
                        if pd.notna(v)
                    )
                )
            ),
        ),
    )
)


# ============================================================
# JOIN QUANTITIES WITH PRICES
# ============================================================

q["canonical_key"] = normalize_text(
    q["canonical_ingredient"]
)

joined = q.merge(
    price_base,
    left_on="canonical_key",
    right_on="price_ingredient_key",
    how="inner",
)


# ============================================================
# COMPATIBILITY RULES
#
# Conservative:
#
# 1. gram quantity + MXN/gram
# 2. milliliter quantity + MXN/liter
# 3. explicit piece count + MXN/pieza
# 4. explicit bunch count + MXN/manojo
#
# IMPORTANT:
# implicit_count is intentionally NOT used.
# Example: "1 pint strawberries" was interpreted as 1 pieza
# by the parser, so we don't trust implicit counts for costing.
# ============================================================

joined["cost_type"] = pd.NA
joined["cost_mxn"] = np.nan


# ------------------------------------------------------------
# MASS
# ------------------------------------------------------------

mass_mask = (
    joined["conversion_type"].isin(
        [
            "mass_exact",
            "package_mass_exact",
        ]
    )
    & (
        joined["normalized_unit"]
        == "gramo"
    )
    & (
        joined["unidad_opcion_a"]
        == "gramo"
    )
)

joined.loc[
    mass_mask,
    "cost_mxn",
] = (
    joined.loc[
        mass_mask,
        "normalized_quantity",
    ]
    *
    joined.loc[
        mass_mask,
        "precio_mxn",
    ]
)

joined.loc[
    mass_mask,
    "cost_type",
] = "mass_exact"


# ------------------------------------------------------------
# LIQUID VOLUME
# normalized quantity = milliliters
# price = MXN per liter
# ------------------------------------------------------------

volume_mask = (
    (
        joined["conversion_type"]
        == "volume_exact"
    )
    & (
        joined["normalized_unit"]
        == "mililitro"
    )
    & (
        joined["unidad_opcion_a"]
        == "litro"
    )
)

joined.loc[
    volume_mask,
    "cost_mxn",
] = (
    joined.loc[
        volume_mask,
        "normalized_quantity",
    ]
    / 1000
    *
    joined.loc[
        volume_mask,
        "precio_mxn",
    ]
)

joined.loc[
    volume_mask,
    "cost_type",
] = "volume_exact"


# ------------------------------------------------------------
# EXPLICIT PIECES
#
# Only conversion_type == count.
# We intentionally exclude implicit_count.
# ------------------------------------------------------------

piece_mask = (
    (
        joined["conversion_type"]
        == "count"
    )
    & (
        joined["normalized_unit"]
        == "piece"
    )
    & (
        joined["unidad_opcion_a"]
        == "pieza"
    )
)

joined.loc[
    piece_mask,
    "cost_mxn",
] = (
    joined.loc[
        piece_mask,
        "normalized_quantity",
    ]
    *
    joined.loc[
        piece_mask,
        "precio_mxn",
    ]
)

joined.loc[
    piece_mask,
    "cost_type",
] = "explicit_piece"


# ------------------------------------------------------------
# EXPLICIT BUNCHES
# ------------------------------------------------------------

bunch_mask = (
    (
        joined["conversion_type"]
        == "count"
    )
    & (
        joined["normalized_unit"]
        == "bunch"
    )
    & (
        joined["unidad_opcion_a"]
        == "manojo"
    )
)

joined.loc[
    bunch_mask,
    "cost_mxn",
] = (
    joined.loc[
        bunch_mask,
        "normalized_quantity",
    ]
    *
    joined.loc[
        bunch_mask,
        "precio_mxn",
    ]
)

joined.loc[
    bunch_mask,
    "cost_type",
] = "explicit_bunch"


# ============================================================
# KEEP ONLY COSTABLE ROWS
# ============================================================

costed = joined[
    joined["cost_mxn"].notna()
].copy()

costed["cost_mxn"] = (
    costed["cost_mxn"]
    .round(2)
)

costed["precio_mxn"] = (
    costed["precio_mxn"]
    .round(4)
)


# ============================================================
# REMOVE ACCIDENTAL DUPLICATES
# ============================================================

costed = (
    costed
    .sort_values(
        [
            "recipe_id",
            "ingredient_position",
            "cadena",
        ]
    )
    .drop_duplicates(
        subset=[
            "recipe_id",
            "ingredient_position",
            "cadena",
        ],
        keep="first",
    )
)


# ============================================================
# INGREDIENT COST OUTPUT
# ============================================================

ingredient_costs = costed[
    [
        "recipe_id",
        "ingredient_position",
        "ingredient",
        "ingredient_raw",
        "canonical_ingredient",
        "profeco_category",
        "cadena",
        "producto_profeco",
        "normalized_quantity",
        "normalized_unit",
        "precio_mxn",
        "unidad_opcion_a",
        "cost_type",
        "cost_mxn",
    ]
].copy()


ingredient_costs.to_csv(
    INGREDIENT_COSTS_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# RECIPE TOTALS
# ============================================================

recipe_totals = (
    ingredient_costs
    .groupby(
        [
            "recipe_id",
            "cadena",
        ],
        as_index=False,
    )
    .agg(
        estimated_cost_mxn=(
            "cost_mxn",
            "sum",
        ),
        ingredients_costed=(
            "ingredient_position",
            "nunique",
        ),
    )
)


# Number of ingredients originally parsed per recipe
ingredient_counts = (
    quantities
    .groupby(
        "recipe_id",
        as_index=False,
    )
    .agg(
        total_ingredients=(
            "ingredient_position",
            "nunique",
        )
    )
)


recipe_totals = recipe_totals.merge(
    ingredient_counts,
    on="recipe_id",
    how="left",
)


recipe_totals[
    "ingredient_coverage_pct"
] = (
    recipe_totals[
        "ingredients_costed"
    ]
    /
    recipe_totals[
        "total_ingredients"
    ]
    * 100
).round(2)


recipes = recipes.rename(
    columns={
        "id": "recipe_id",
        "name": "recipe_name",
    }
)


recipe_totals = recipe_totals.merge(
    recipes,
    on="recipe_id",
    how="left",
)


recipe_totals[
    "estimated_cost_mxn"
] = (
    recipe_totals[
        "estimated_cost_mxn"
    ]
    .round(2)
)


# Cost per serving only if servings > 0
recipe_totals[
    "estimated_cost_per_serving_mxn"
] = np.where(
    pd.to_numeric(
        recipe_totals["servings"],
        errors="coerce",
    ) > 0,
    (
        recipe_totals[
            "estimated_cost_mxn"
        ]
        /
        pd.to_numeric(
            recipe_totals["servings"],
            errors="coerce",
        )
    ),
    np.nan,
)


recipe_totals[
    "estimated_cost_per_serving_mxn"
] = (
    recipe_totals[
        "estimated_cost_per_serving_mxn"
    ]
    .round(2)
)


# Reorder
recipe_totals = recipe_totals[
    [
        "recipe_id",
        "recipe_name",
        "cadena",
        "estimated_cost_mxn",
        "servings",
        "estimated_cost_per_serving_mxn",
        "ingredients_costed",
        "total_ingredients",
        "ingredient_coverage_pct",
        "serving_size",
    ]
]


recipe_totals.to_csv(
    RECIPE_COSTS_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 90)
print("RECIPE COST DATASET")
print("=" * 90)

print(
    f"\nIngredient-cost rows generated: "
    f"{len(ingredient_costs):,}"
)

print(
    f"Recipes with at least one priced ingredient: "
    f"{recipe_totals['recipe_id'].nunique():,}"
)

print(
    f"Recipe/chain combinations: "
    f"{len(recipe_totals):,}"
)


print("\n=== COST TYPES ===")

print(
    ingredient_costs[
        "cost_type"
    ]
    .value_counts()
    .to_string()
)


print("\n=== RECIPES BY CHAIN ===")

print(
    recipe_totals[
        "cadena"
    ]
    .value_counts()
    .to_string()
)


print("\n=== INGREDIENT COVERAGE ===")

print(
    recipe_totals[
        "ingredient_coverage_pct"
    ]
    .describe()
    .round(2)
    .to_string()
)


print("\nRecipes with >= 50% ingredient coverage:")

coverage_50 = recipe_totals[
    recipe_totals[
        "ingredient_coverage_pct"
    ] >= 50
]

print(
    f"{len(coverage_50):,} "
    f"recipe/chain combinations"
)


print("\n=== SAMPLE RECIPE COSTS ===")

print(
    recipe_totals[
        [
            "recipe_name",
            "cadena",
            "estimated_cost_mxn",
            "ingredients_costed",
            "total_ingredients",
            "ingredient_coverage_pct",
        ]
    ]
    .sort_values(
        "ingredient_coverage_pct",
        ascending=False,
    )
    .head(20)
    .to_string(index=False)
)


print("\n=== VALIDATION ===")

print(
    "Ingredient costs <= 0:",
    int(
        (
            ingredient_costs[
                "cost_mxn"
            ] <= 0
        ).sum()
    ),
)

print(
    "Duplicate ingredient/chain rows:",
    int(
        ingredient_costs.duplicated(
            subset=[
                "recipe_id",
                "ingredient_position",
                "cadena",
            ]
        ).sum()
    ),
)

print(
    "Null costs:",
    int(
        ingredient_costs[
            "cost_mxn"
        ].isna().sum()
    ),
)


print("\nSaved:")
print(INGREDIENT_COSTS_PATH)
print(RECIPE_COSTS_PATH)
