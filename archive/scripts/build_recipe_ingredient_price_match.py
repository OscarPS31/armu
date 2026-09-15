from pathlib import Path

import pandas as pd


RECIPES_PATH = Path(
    "data/recipe_ingredients_quantities_clean.csv"
)

PRICES_PATH = Path(
    "data/ingredient_prices_top3_chains_clean.csv"
)

OUTPUT_PATH = Path(
    "data/recipe_ingredients_with_prices.csv"
)


print("Loading clean recipe quantities...")
recipes = pd.read_csv(
    RECIPES_PATH,
    low_memory=False,
)

print("Loading clean top-3 prices...")
prices = pd.read_csv(
    PRICES_PATH,
    low_memory=False,
)


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_recipe_cols = {
    "id_receta",
    "ingrediente",
    "ingrediente_original",
    "cantidad_normalizada",
    "unidad_normalizada",
    "tipo_conversion",
    "confianza",
}

required_price_cols = {
    "cadena",
    "ingrediente",
    "producto_profeco",
    "precio_opcion_a_mxn",
    "unidad_opcion_a",
    "precio_opcion_b_mxn",
    "unidad_opcion_b",
}


missing_recipe = required_recipe_cols - set(recipes.columns)
missing_price = required_price_cols - set(prices.columns)

if missing_recipe:
    raise ValueError(
        f"Missing recipe columns: {sorted(missing_recipe)}"
    )

if missing_price:
    raise ValueError(
        f"Missing price columns: {sorted(missing_price)}"
    )


# ============================================================
# NORMALIZE MATCH KEY
# ============================================================

def normalize_key(series):
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


recipes["ingrediente_key"] = normalize_key(
    recipes["ingrediente"]
)

prices["ingrediente_key"] = normalize_key(
    prices["ingrediente"]
)


# ============================================================
# PREPARE PRICE TABLE
# ============================================================

price_table = prices[
    [
        "cadena",
        "ingrediente_key",
        "ingrediente",
        "producto_profeco",
        "precio_opcion_a_mxn",
        "unidad_opcion_a",
        "precio_opcion_b_mxn",
        "unidad_opcion_b",
    ]
].copy()


price_table = price_table.rename(
    columns={
        "ingrediente": "ingrediente_precio",
        "precio_opcion_a_mxn": "precio_mxn",
        "unidad_opcion_a": "unidad_precio",
        "precio_opcion_b_mxn": "precio_1000_mxn",
        "unidad_opcion_b": "unidad_precio_1000",
    }
)


# ============================================================
# MATCH
# ============================================================

matched = recipes.merge(
    price_table,
    on="ingrediente_key",
    how="left",
)


# ============================================================
# MATCH STATUS
# ============================================================

matched["match_status"] = "sin_precio"

matched.loc[
    matched["cadena"].notna(),
    "match_status",
] = "precio_disponible"


# ============================================================
# UNIT COMPATIBILITY
#
# This does NOT calculate cost.
# It only tells us whether quantity unit and price unit
# are directly compatible.
# ============================================================

def compatibility(row):
    quantity_unit = row["unidad_normalizada"]
    price_unit = row["unidad_precio"]

    if pd.isna(price_unit):
        return "sin_precio"

    if pd.isna(quantity_unit):
        return "cantidad_sin_unidad"

    # Directly compatible
    direct = {
        ("gramo", "gramo"),
        ("pieza", "pieza"),
        ("manojo", "manojo"),
    }

    if (quantity_unit, price_unit) in direct:
        return "compatible"

    # Recipe quantity in ml, price in liter
    if (
        quantity_unit == "mililitro"
        and price_unit == "litro"
    ):
        return "compatible_conversion"

    # Cups / spoons require density or volume conversion
    if quantity_unit in {
        "taza",
        "cucharada",
        "cucharadita",
    }:
        return "requiere_conversion"

    # Subjective units
    if quantity_unit in {
        "pizca",
        "toque",
        "chorrito",
    }:
        return "subjetivo"

    return "unidad_no_compatible"


matched["compatibilidad_unidad"] = (
    matched.apply(
        compatibility,
        axis=1,
    )
)


# ============================================================
# CLEAN OUTPUT
# ============================================================

output = matched[
    [
        "id_receta",
        "ingrediente",
        "ingrediente_original",
        "cantidad_original",
        "cantidad_normalizada",
        "unidad_normalizada",
        "tipo_conversion",
        "confianza",
        "cadena",
        "producto_profeco",
        "precio_mxn",
        "unidad_precio",
        "precio_1000_mxn",
        "unidad_precio_1000",
        "match_status",
        "compatibilidad_unidad",
    ]
].copy()


# ============================================================
# SORT
# ============================================================

output = output.sort_values(
    [
        "id_receta",
        "ingrediente",
        "cadena",
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
print("RECIPE INGREDIENT + PRICE MATCH")
print("=" * 90)

print(f"\nRows generated: {len(output):,}")

print(
    "Unique recipes:",
    f"{output['id_receta'].nunique():,}",
)

print(
    "Unique recipe ingredients:",
    f"{output['ingrediente'].nunique():,}",
)


print("\n=== MATCH STATUS ===")

print(
    output[
        "match_status"
    ]
    .value_counts(
        dropna=False
    )
    .to_string()
)


print("\n=== UNIT COMPATIBILITY ===")

print(
    output[
        "compatibilidad_unidad"
    ]
    .value_counts(
        dropna=False
    )
    .to_string()
)


# ============================================================
# UNIQUE SOURCE-ROW MATCH COVERAGE
#
# Because matched ingredients can produce one row per chain,
# calculate coverage on original recipe ingredient rows too.
# ============================================================

base_cols = [
    "id_receta",
    "ingrediente",
    "ingrediente_original",
]

source_rows = (
    output[
        base_cols + [
            "match_status",
        ]
    ]
    .groupby(
        base_cols,
        dropna=False,
        as_index=False,
    )
    .agg(
        has_price=(
            "match_status",
            lambda x: (
                x == "precio_disponible"
            ).any(),
        )
    )
)

source_with_price = int(
    source_rows["has_price"].sum()
)

source_total = len(source_rows)

coverage = (
    source_with_price
    / source_total
    * 100
    if source_total
    else 0
)

print("\n=== SOURCE INGREDIENT COVERAGE ===")

print(
    f"Source ingredient rows: "
    f"{source_total:,}"
)

print(
    f"Rows with at least one chain price: "
    f"{source_with_price:,}"
)

print(
    f"Coverage: {coverage:.2f}%"
)


print("\n=== MATCHED SAMPLE ===")

sample = output[
    output[
        "match_status"
    ] == "precio_disponible"
][
    [
        "id_receta",
        "ingrediente",
        "cantidad_normalizada",
        "unidad_normalizada",
        "cadena",
        "producto_profeco",
        "precio_mxn",
        "unidad_precio",
        "compatibilidad_unidad",
    ]
].head(30)

print(
    sample.to_string(
        index=False
    )
)


print("\n=== VALIDATION ===")

print(
    "Duplicate full rows:",
    int(
        output.duplicated().sum()
    ),
)

print(
    "Matched rows with null price:",
    int(
        (
            (
                output["match_status"]
                == "precio_disponible"
            )
            & output[
                "precio_mxn"
            ].isna()
        ).sum()
    ),
)


print("\nSaved:")
print(OUTPUT_PATH)
