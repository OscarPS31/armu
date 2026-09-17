from pathlib import Path

import pandas as pd


QUANTITIES_PATH = Path(
    "data/recipe_ingredients_quantities_clean.csv"
)

PRICES_PATH = Path(
    "data/recipe_prices_kg_liter.csv"
)

OUTPUT_PATH = Path(
    "data/recipe_prices_complete_3chains.csv"
)

CHAINS = [
    "Walmart",
    "Soriana",
    "Chedraui",
]


print("Loading original recipe ingredients...")

quantities = pd.read_csv(
    QUANTITIES_PATH,
    low_memory=False,
)

print("Loading priced recipe dataset...")

priced = pd.read_csv(
    PRICES_PATH,
    low_memory=False,
)


# ============================================================
# SOURCE INGREDIENT KEY
#
# We use the original recipe ingredient identity.
# This lets us know how many ingredients the recipe truly needs.
# ============================================================

quantities["source_key"] = (
    quantities["ingrediente"]
    .fillna("")
    .astype(str)
    .str.lower()
    .str.strip()
    + "|||"
    + quantities["ingrediente_original"]
    .fillna("")
    .astype(str)
    .str.lower()
    .str.strip()
)


priced["source_key"] = (
    priced["ingrediente"]
    .fillna("")
    .astype(str)
    .str.lower()
    .str.strip()
    + "|||"
    + priced["ingrediente_original"]
    .fillna("")
    .astype(str)
    .str.lower()
    .str.strip()
)


# ============================================================
# HOW MANY INGREDIENTS DOES EACH RECIPE REQUIRE?
# ============================================================

required = (
    quantities[
        [
            "id_receta",
            "source_key",
        ]
    ]
    .drop_duplicates()
    .groupby(
        "id_receta",
        as_index=False,
    )
    .agg(
        ingredientes_requeridos=(
            "source_key",
            "nunique",
        )
    )
)


print(
    "Recipes in source:",
    f"{required['id_receta'].nunique():,}",
)


# ============================================================
# HOW MANY INGREDIENTS HAVE A VALID PRICE IN EACH CHAIN?
# ============================================================

available = (
    priced[
        [
            "id_receta",
            "cadena",
            "source_key",
        ]
    ]
    .drop_duplicates()
    .groupby(
        [
            "id_receta",
            "cadena",
        ],
        as_index=False,
    )
    .agg(
        ingredientes_con_precio=(
            "source_key",
            "nunique",
        )
    )
)


coverage = available.merge(
    required,
    on="id_receta",
    how="left",
)


coverage["receta_completa_en_cadena"] = (
    coverage["ingredientes_con_precio"]
    == coverage["ingredientes_requeridos"]
)


# ============================================================
# RECIPE MUST BE COMPLETE IN ALL 3 CHAINS
# ============================================================

complete_by_recipe = (
    coverage
    .groupby(
        "id_receta",
        as_index=False,
    )
    .agg(
        cadenas_presentes=(
            "cadena",
            "nunique",
        ),
        cadenas_completas=(
            "receta_completa_en_cadena",
            "sum",
        ),
    )
)


valid_recipe_ids = complete_by_recipe[
    (
        complete_by_recipe["cadenas_presentes"]
        == len(CHAINS)
    )
    &
    (
        complete_by_recipe["cadenas_completas"]
        == len(CHAINS)
    )
]["id_receta"]


# ============================================================
# KEEP ONLY COMPLETE RECIPES
# ============================================================

final = priced[
    priced["id_receta"].isin(
        valid_recipe_ids
    )
].copy()


# ============================================================
# ADD REQUIRED INGREDIENT COUNT
# ============================================================

final = final.merge(
    required,
    on="id_receta",
    how="left",
)


# ============================================================
# RECOMPUTE TRUE TOTAL
# ============================================================

totals = (
    final
    .groupby(
        [
            "id_receta",
            "cadena",
        ],
        as_index=False,
    )
    .agg(
        precio_total_receta_mxn_new=(
            "costo_ingrediente_mxn",
            "sum",
        ),
        ingredientes_con_precio_new=(
            "source_key",
            "nunique",
        ),
    )
)


totals[
    "precio_total_receta_mxn_new"
] = (
    totals[
        "precio_total_receta_mxn_new"
    ]
    .round(2)
)


final = final.drop(
    columns=[
        "precio_total_receta_mxn",
        "ingredientes_con_precio",
    ],
    errors="ignore",
)


final = final.merge(
    totals,
    on=[
        "id_receta",
        "cadena",
    ],
    how="left",
)


final = final.rename(
    columns={
        "precio_total_receta_mxn_new":
            "precio_total_receta_mxn",

        "ingredientes_con_precio_new":
            "ingredientes_con_precio",
    }
)


# ============================================================
# VALIDATION
# ============================================================

validation = (
    final[
        [
            "id_receta",
            "cadena",
            "ingredientes_requeridos",
            "ingredientes_con_precio",
        ]
    ]
    .drop_duplicates()
)


incomplete = validation[
    validation["ingredientes_requeridos"]
    != validation["ingredientes_con_precio"]
]


chain_count = (
    final[
        [
            "id_receta",
            "cadena",
        ]
    ]
    .drop_duplicates()
    .groupby(
        "id_receta"
    )["cadena"]
    .nunique()
)


invalid_chain_count = int(
    (chain_count != 3).sum()
)


# ============================================================
# CLEAN OUTPUT
# ============================================================

final = final.drop(
    columns=[
        "source_key",
    ],
    errors="ignore",
)


final = final.sort_values(
    [
        "id_receta",
        "cadena",
        "ingrediente",
    ]
).reset_index(
    drop=True
)


final.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 90)
print("COMPLETE RECIPE PRICE DATASET")
print("=" * 90)

print(
    "\nRecipes before strict filter:",
    f"{priced['id_receta'].nunique():,}",
)

print(
    "Complete recipes:",
    f"{final['id_receta'].nunique():,}",
)

print(
    "Recipes removed:",
    f"{priced['id_receta'].nunique() - final['id_receta'].nunique():,}",
)

print(
    "Final rows:",
    f"{len(final):,}",
)


print("\n=== CHAINS ===")

print(
    final["cadena"]
    .value_counts()
    .to_string()
)


print("\n=== COMPLETENESS VALIDATION ===")

print(
    "Incomplete recipe/chain groups:",
    len(incomplete),
)

print(
    "Recipes without exactly 3 chains:",
    invalid_chain_count,
)

print(
    "Null prices:",
    int(
        final[
            "precio_kg_litro_mxn"
        ]
        .isna()
        .sum()
    ),
)

print(
    "Null ingredient costs:",
    int(
        final[
            "costo_ingrediente_mxn"
        ]
        .isna()
        .sum()
    ),
)


print("\n=== SAMPLE COMPLETE RECIPES ===")

sample_ids = (
    final["id_receta"]
    .drop_duplicates()
    .head(3)
)

sample = final[
    final["id_receta"].isin(
        sample_ids
    )
][
    [
        "nombre_receta",
        "ingrediente",
        "cantidad",
        "unidad",
        "cadena",
        "precio_kg_litro_mxn",
        "costo_ingrediente_mxn",
        "precio_total_receta_mxn",
        "ingredientes_requeridos",
        "ingredientes_con_precio",
    ]
]

print(
    sample.to_string(
        index=False
    )
)


print("\nSaved:")
print(OUTPUT_PATH)
