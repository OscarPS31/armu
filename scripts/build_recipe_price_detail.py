from pathlib import Path

import numpy as np
import pandas as pd


QUANTITIES_PATH = Path(
    "data/recipe_ingredients_quantities_clean.csv"
)

PRICES_PATH = Path(
    "data/ingredient_prices_top3_chains_clean.csv"
)

RECIPES_PATH = Path(
    "data/Kaggle/recipes_ingredients.csv"
)

OUTPUT_PATH = Path(
    "data/recipe_price_detail.csv"
)


print("Loading clean recipe quantities...")

quantities = pd.read_csv(
    QUANTITIES_PATH,
    low_memory=False,
)

print("Loading prices...")

prices = pd.read_csv(
    PRICES_PATH,
    low_memory=False,
)

print("Loading recipe names...")

recipes = pd.read_csv(
    RECIPES_PATH,
    usecols=[
        "id",
        "name",
        "servings",
    ],
    low_memory=False,
)


# ============================================================
# NORMALIZE KEYS
# ============================================================

def key(series):
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


quantities["ingrediente_key"] = key(
    quantities["ingrediente"]
)

prices["ingrediente_key"] = key(
    prices["ingrediente"]
)


# ============================================================
# PREPARE PRICES
# ============================================================

price_table = prices[
    [
        "cadena",
        "ingrediente_key",
        "producto_profeco",
        "precio_opcion_a_mxn",
        "unidad_opcion_a",
    ]
].copy()

price_table = price_table.rename(
    columns={
        "precio_opcion_a_mxn": "precio_individual_mxn",
        "unidad_opcion_a": "unidad_precio",
    }
)


# ============================================================
# MATCH
# ============================================================

df = quantities.merge(
    price_table,
    on="ingrediente_key",
    how="left",
)


# ============================================================
# COST PER INGREDIENT
# ============================================================

df["costo_ingrediente_mxn"] = np.nan
df["match_precio"] = "sin_precio"


# ------------------------------------------------------------
# GRAMS
# ------------------------------------------------------------

mask = (
    df["cantidad_normalizada"].notna()
    & (df["unidad_normalizada"] == "gramo")
    & (df["unidad_precio"] == "gramo")
)

df.loc[
    mask,
    "costo_ingrediente_mxn",
] = (
    df.loc[
        mask,
        "cantidad_normalizada",
    ]
    *
    df.loc[
        mask,
        "precio_individual_mxn",
    ]
)

df.loc[
    mask,
    "match_precio",
] = "compatible"


# ------------------------------------------------------------
# MILLILITERS -> PRICE PER LITER
# ------------------------------------------------------------

mask = (
    df["cantidad_normalizada"].notna()
    & (df["unidad_normalizada"] == "mililitro")
    & (df["unidad_precio"] == "litro")
)

df.loc[
    mask,
    "costo_ingrediente_mxn",
] = (
    df.loc[
        mask,
        "cantidad_normalizada",
    ]
    / 1000
    *
    df.loc[
        mask,
        "precio_individual_mxn",
    ]
)

df.loc[
    mask,
    "match_precio",
] = "compatible"


# ------------------------------------------------------------
# PIECES
# ------------------------------------------------------------

mask = (
    df["cantidad_normalizada"].notna()
    & (df["unidad_normalizada"] == "pieza")
    & (df["unidad_precio"] == "pieza")
)

df.loc[
    mask,
    "costo_ingrediente_mxn",
] = (
    df.loc[
        mask,
        "cantidad_normalizada",
    ]
    *
    df.loc[
        mask,
        "precio_individual_mxn",
    ]
)

df.loc[
    mask,
    "match_precio",
] = "compatible"


# ------------------------------------------------------------
# BUNCHES
# ------------------------------------------------------------

mask = (
    df["cantidad_normalizada"].notna()
    & (df["unidad_normalizada"] == "manojo")
    & (df["unidad_precio"] == "manojo")
)

df.loc[
    mask,
    "costo_ingrediente_mxn",
] = (
    df.loc[
        mask,
        "cantidad_normalizada",
    ]
    *
    df.loc[
        mask,
        "precio_individual_mxn",
    ]
)

df.loc[
    mask,
    "match_precio",
] = "compatible"


# ============================================================
# ROUND
# ============================================================

df["precio_individual_mxn"] = (
    pd.to_numeric(
        df["precio_individual_mxn"],
        errors="coerce",
    )
    .round(4)
)

df["costo_ingrediente_mxn"] = (
    pd.to_numeric(
        df["costo_ingrediente_mxn"],
        errors="coerce",
    )
    .round(2)
)


# ============================================================
# TOTAL PER RECIPE + CHAIN
# ============================================================

totals = (
    df[
        df["costo_ingrediente_mxn"].notna()
    ]
    .groupby(
        [
            "id_receta",
            "cadena",
        ],
        as_index=False,
    )
    .agg(
        precio_total_receta_mxn=(
            "costo_ingrediente_mxn",
            "sum",
        ),
        ingredientes_con_precio=(
            "ingrediente",
            "count",
        ),
    )
)

totals["precio_total_receta_mxn"] = (
    totals["precio_total_receta_mxn"]
    .round(2)
)


# ============================================================
# ATTACH TOTAL TO EACH INGREDIENT ROW
# ============================================================

df = df.merge(
    totals,
    on=[
        "id_receta",
        "cadena",
    ],
    how="left",
)


# ============================================================
# ADD RECIPE NAME
# ============================================================

recipes = recipes.rename(
    columns={
        "id": "id_receta",
        "name": "nombre_receta",
    }
)

df = df.merge(
    recipes,
    on="id_receta",
    how="left",
)


# ============================================================
# FINAL OUTPUT
# ============================================================

output = df[
    [
        "id_receta",
        "nombre_receta",
        "ingrediente",
        "ingrediente_original",
        "cantidad_normalizada",
        "unidad_normalizada",
        "cadena",
        "producto_profeco",
        "precio_individual_mxn",
        "unidad_precio",
        "costo_ingrediente_mxn",
        "precio_total_receta_mxn",
        "ingredientes_con_precio",
        "servings",
        "match_precio",
        "confianza",
    ]
].copy()


output = output.sort_values(
    [
        "id_receta",
        "cadena",
        "ingrediente",
    ],
    na_position="last",
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

output.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 90)
print("RECIPE PRICE DETAIL")
print("=" * 90)

print(
    f"\nRows generated: {len(output):,}"
)

print(
    "Recipes:",
    f"{output['id_receta'].nunique():,}",
)

print(
    "Recipes with calculated total:",
    f"{output.loc[output['precio_total_receta_mxn'].notna(), 'id_receta'].nunique():,}",
)


print("\n=== MATCH ===")

print(
    output["match_precio"]
    .value_counts(dropna=False)
    .to_string()
)


print("\n=== SAMPLE COMPLETE RECIPE ===")

complete_ids = (
    output[
        output["precio_total_receta_mxn"].notna()
    ]["id_receta"]
    .drop_duplicates()
)

if len(complete_ids):

    sample_id = complete_ids.iloc[0]

    sample = output[
        output["id_receta"] == sample_id
    ][
        [
            "id_receta",
            "nombre_receta",
            "ingrediente",
            "cantidad_normalizada",
            "unidad_normalizada",
            "cadena",
            "precio_individual_mxn",
            "costo_ingrediente_mxn",
            "precio_total_receta_mxn",
        ]
    ]

    print(
        sample.to_string(
            index=False
        )
    )


print("\n=== VALIDATION ===")

print(
    "Negative costs:",
    int(
        (
            output["costo_ingrediente_mxn"]
            .dropna()
            < 0
        ).sum()
    ),
)

print(
    "Negative totals:",
    int(
        (
            output["precio_total_receta_mxn"]
            .dropna()
            < 0
        ).sum()
    ),
)


print("\nSaved:")
print(OUTPUT_PATH)
