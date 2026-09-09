import os
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INPUT_PATH = "data/ingredient_prices.csv"
OUTPUT_PATH = "data/ingredient_prices_top3_chains.csv"


# ============================================================
# CHAIN GROUPS
# ============================================================

CHAIN_MAP = {
    # Soriana
    "Hipermercado Soriana": "Soriana",
    "Mega Soriana": "Soriana",
    "Soriana Super": "Soriana",

    # Chedraui
    "Chedraui": "Chedraui",
    "Super Chedraui": "Chedraui",
    "Chedraui Selecto": "Chedraui",

    # Walmart
    "Wal-mart": "Walmart",
    "Wal-mart Express": "Walmart",
}

CHAIN_ORDER = [
    "Soriana",
    "Chedraui",
    "Walmart",
]


# ============================================================
# STRICT EXCLUSIONS
#
# Weak / approximate mappings that we do not want in the
# clean comparison.
# ============================================================

EXCLUDED_INGREDIENTS = {
    "shallot",
    "pumpkin",
    "cayenne",
    "chili powder",
}


# ============================================================
# TRUE ALIASES
#
# Only merge names that genuinely represent the same ingredient.
# ============================================================

ALIAS_GROUPS = {
    "cilantro": "cilantro",
    "coriander": "cilantro",

    "green onion": "green onion",
    "scallion": "green onion",
}

DISPLAY_ALIASES = {
    "cilantro": "cilantro, coriander",
    "green onion": "green onion, scallion",
}


# ============================================================
# LIQUID INGREDIENTS
#
# These ingredients use LITRO as their official comparison unit.
#
# Everything else uses GRAMO.
# ============================================================

LIQUID_INGREDIENTS = {
    "water",
    "milk",
    "olive oil",
    "vegetable oil",
    "orange juice",
    "vinegar",
    "cider vinegar",
    "soy sauce",
    "worcestershire sauce",
    "hot sauce",
    "chili sauce",
    "rum",
    "brandy",
}


# ============================================================
# LOAD
# ============================================================

print("Loading technical ingredient price dataset...")

df = pd.read_csv(INPUT_PATH)

print(f"Original rows: {len(df):,}")
print(f"Original stores: {df['store'].nunique():,}")
print(f"Original ingredients: {df['ingredient'].nunique():,}")


# ============================================================
# FILTER TOP 3 CHAINS
# ============================================================

top3 = df[
    df["store"].isin(CHAIN_MAP.keys())
].copy()

top3["cadena"] = (
    top3["store"]
    .map(CHAIN_MAP)
)

print("\nRows belonging to selected chains:")
print(f"{len(top3):,}")


# ============================================================
# REMOVE WEAK MAPPINGS
# ============================================================

before_strict = len(top3)

top3 = top3[
    ~top3["ingredient"].isin(
        EXCLUDED_INGREDIENTS
    )
].copy()

print("\nRows removed by strict mapping rules:")
print(f"{before_strict - len(top3):,}")


# ============================================================
# KEEP ONLY SAFE SOURCE UNITS
#
# kg    -> can be converted safely to grams
# litro -> stays as liters
#
# pieza/manojo are removed because no trustworthy weight
# conversion is available.
# ============================================================

before_safe_units = len(top3)

top3 = top3[
    top3["unit"].isin(
        [
            "kg",
            "litro",
        ]
    )
].copy()

print("\nRows removed because source unit is not safely comparable:")
print(f"{before_safe_units - len(top3):,}")


# ============================================================
# TRUE ALIAS NORMALIZATION
# ============================================================

top3["ingrediente"] = (
    top3["ingredient"]
    .map(ALIAS_GROUPS)
    .fillna(top3["ingredient"])
)

top3["ingredientes_relacionados"] = (
    top3["ingrediente"]
    .map(DISPLAY_ALIASES)
    .fillna(top3["ingrediente"])
)


# ============================================================
# DEFINE OFFICIAL UNIT PER INGREDIENT
#
# Liquid ingredient -> litro
# Other ingredient  -> gramo
# ============================================================

top3["unidad_objetivo"] = top3[
    "ingrediente"
].apply(
    lambda ingredient:
        "litro"
        if ingredient in LIQUID_INGREDIENTS
        else "gramo"
)


# ============================================================
# SELECT ONLY SOURCE ROWS THAT MATCH OFFICIAL UNIT
#
# liquid:
#     source must already be litro
#
# solid:
#     source must be kg, later converted to gram price
# ============================================================

liquid_mask = (
    (top3["unidad_objetivo"] == "litro")
    &
    (top3["unit"] == "litro")
)

solid_mask = (
    (top3["unidad_objetivo"] == "gramo")
    &
    (top3["unit"] == "kg")
)

before_preferred_units = len(top3)

top3 = top3[
    liquid_mask | solid_mask
].copy()

print("\nRows removed because they do not match the ingredient's official unit:")
print(f"{before_preferred_units - len(top3):,}")


# ============================================================
# PRICE HOMOLOGATION
#
# kg -> MXN per gram
# litro -> MXN per liter
# ============================================================

top3["precio_homologado_mxn"] = top3["price"]


kg_mask = (
    top3["unit"] == "kg"
)

top3.loc[
    kg_mask,
    "precio_homologado_mxn",
] = (
    top3.loc[
        kg_mask,
        "price",
    ]
    / 1000
)


liter_mask = (
    top3["unit"] == "litro"
)

top3.loc[
    liter_mask,
    "precio_homologado_mxn",
] = top3.loc[
    liter_mask,
    "price",
]


top3["unidad"] = (
    top3["unidad_objetivo"]
)


# ============================================================
# REMOVE TRUE-ALIAS DUPLICATION
#
# Example:
#
# cilantro + coriander
#
# should not count the same commercial price twice.
# ============================================================

price_observations = (
    top3[
        [
            "cadena",
            "store",
            "ingrediente",
            "ingredientes_relacionados",
            "profeco_category",
            "precio_homologado_mxn",
            "unidad",
        ]
    ]
    .drop_duplicates()
    .copy()
)

print("\nRows after removing true-alias duplication:")
print(f"{len(price_observations):,}")


# ============================================================
# MEAN BY CHAIN
#
# One row per:
#
# chain
# + ingredient
# + PROFECO product
# + official unit
# ============================================================

result = (
    price_observations
    .groupby(
        [
            "cadena",
            "ingrediente",
            "ingredientes_relacionados",
            "profeco_category",
            "unidad",
        ],
        as_index=False,
    )
    .agg(
        precio_promedio_mxn=(
            "precio_homologado_mxn",
            "mean",
        ),

        formatos_con_precio=(
            "store",
            "nunique",
        ),
    )
)


# ============================================================
# ROUND
#
# Per-gram prices need 4 decimals.
# Liter values can also safely keep 4 decimals.
# ============================================================

result["precio_promedio_mxn"] = (
    result["precio_promedio_mxn"]
    .round(4)
)


# ============================================================
# RENAME PROFECO COLUMN
# ============================================================

result = result.rename(
    columns={
        "profeco_category": "producto_profeco",
    }
)


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

result = result[
    [
        "cadena",
        "ingrediente",
        "producto_profeco",
        "ingredientes_relacionados",
        "precio_promedio_mxn",
        "unidad",
        "formatos_con_precio",
    ]
]


# ============================================================
# SORT
# ============================================================

result["cadena"] = pd.Categorical(
    result["cadena"],
    categories=CHAIN_ORDER,
    ordered=True,
)

result = (
    result
    .sort_values(
        [
            "cadena",
            "ingrediente",
            "producto_profeco",
        ]
    )
    .reset_index(drop=True)
)

result["cadena"] = (
    result["cadena"]
    .astype(str)
)


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 80)
print("TOP 3 CHAINS - FINAL STRICT HOMOLOGATED DATASET")
print("=" * 80)

print(f"\nRows generated: {len(result):,}")


print("\nIngredients by chain:")

print(
    result.groupby(
        "cadena",
        observed=True,
    )["ingrediente"]
    .nunique()
    .reindex(CHAIN_ORDER)
    .to_string()
)


print("\nPROFECO products by chain:")

print(
    result.groupby(
        "cadena",
        observed=True,
    )["producto_profeco"]
    .nunique()
    .reindex(CHAIN_ORDER)
    .to_string()
)


print("\nUnits:")

print(
    result["unidad"]
    .value_counts()
    .to_string()
)


# ============================================================
# CHECK THAT EACH INGREDIENT HAS ONLY ONE UNIT
# ============================================================

unit_count = (
    result.groupby(
        "ingrediente"
    )["unidad"]
    .nunique()
)

multiple_units = unit_count[
    unit_count > 1
]

print("\nIngredients with more than one unit:")

if multiple_units.empty:
    print("0 ✅")
else:
    print(multiple_units.to_string())


# ============================================================
# COMMON COMPARABLE INGREDIENTS
# ============================================================

common = (
    result.groupby(
        [
            "ingrediente",
            "producto_profeco",
            "unidad",
        ],
        observed=True,
    )["cadena"]
    .nunique()
    .reset_index(
        name="chains_available"
    )
)

common = common[
    common["chains_available"] == 3
]

print(
    "\nComparable ingredient/product/unit combinations "
    "available in all 3 chains:"
)

print(f"{len(common):,}")


# ============================================================
# LIQUID CHECK
# ============================================================

print("\n=== LIQUID CHECK ===")

liquid_check = result[
    result["unidad"] == "litro"
]

print(
    liquid_check[
        [
            "cadena",
            "ingrediente",
            "producto_profeco",
            "precio_promedio_mxn",
            "unidad",
        ]
    ]
    .head(40)
    .to_string(index=False)
)


# ============================================================
# SOLID CHECK
# ============================================================

print("\n=== SOLID CHECK ===")

solid_check = result[
    result["unidad"] == "gramo"
]

print(
    solid_check[
        [
            "cadena",
            "ingrediente",
            "producto_profeco",
            "precio_promedio_mxn",
            "unidad",
        ]
    ]
    .head(30)
    .to_string(index=False)
)


# ============================================================
# IMPORTANT INGREDIENT CHECK
# ============================================================

important_ingredients = [
    "onion",
    "zucchini",
    "ground pork",
    "pork tenderloin",
    "pork chops",
    "italian sausage",
    "water",
    "milk",
    "olive oil",
    "vegetable oil",
    "hot sauce",
    "chili sauce",
    "cream",
    "honey",
]

important = result[
    result["ingrediente"].isin(
        important_ingredients
    )
]

print("\n=== FINAL IMPORTANT CHECK ===")

print(
    important.to_string(
        index=False
    )
)


# ============================================================
# VALIDATION
# ============================================================

print("\n=== VALIDATION ===")

print(
    "Null values:",
    int(result.isna().sum().sum()),
)

print(
    "Duplicate rows:",
    int(result.duplicated().sum()),
)

print(
    "Prices <= 0:",
    int(
        (
            result["precio_promedio_mxn"]
            <= 0
        ).sum()
    ),
)

print(
    "Unexpected units:",
    sorted(
        set(result["unidad"])
        - {
            "gramo",
            "litro",
        }
    ),
)

print(
    "Excluded weak mappings still present:",
    sorted(
        set(result["ingrediente"])
        & EXCLUDED_INGREDIENTS
    ),
)


# ============================================================
# FILE SIZE
# ============================================================

size_mb = (
    os.path.getsize(OUTPUT_PATH)
    / 1024
    / 1024
)

print("\nSaved:")
print(OUTPUT_PATH)

print(
    f"File size: "
    f"{size_mb:.3f} MB"
)
