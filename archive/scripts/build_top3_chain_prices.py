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
    "Hipermercado Soriana": "Soriana",
    "Mega Soriana": "Soriana",
    "Soriana Super": "Soriana",

    "Chedraui": "Chedraui",
    "Super Chedraui": "Chedraui",
    "Chedraui Selecto": "Chedraui",

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
# ============================================================

EXCLUDED_INGREDIENTS = {
    "shallot",
    "pumpkin",
    "cayenne",
    "chili powder",
}


# ============================================================
# TRUE ALIASES
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
# VALID SOURCE UNITS
# ============================================================

VALID_UNITS = {
    "kg",
    "litro",
    "pieza",
    "manojo",
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

top3["cadena"] = top3["store"].map(CHAIN_MAP)

print("\nRows belonging to selected chains:")
print(f"{len(top3):,}")


# ============================================================
# REMOVE WEAK MAPPINGS
# ============================================================

before_strict = len(top3)

top3 = top3[
    ~top3["ingredient"].isin(EXCLUDED_INGREDIENTS)
].copy()

print("\nRows removed by strict mapping rules:")
print(f"{before_strict - len(top3):,}")


# ============================================================
# KEEP VALID UNITS
# ============================================================

before_units = len(top3)

top3 = top3[
    top3["unit"].isin(VALID_UNITS)
].copy()

print("\nRows removed because unit is unsupported:")
print(f"{before_units - len(top3):,}")


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
# TARGETED SEMANTIC CLEANUP
#
# Cebolla sold by bunch corresponds to green onion / scallion,
# not regular onion.
#
# Keep:
#   onion       -> kg -> gram
#   green onion -> bunch
#
# Remove only:
#   onion -> bunch
# ============================================================

before_onion_cleanup = len(top3)

bad_onion_bunch = (
    (top3["ingrediente"] == "onion")
    &
    (top3["unit"] == "manojo")
)

top3 = top3[
    ~bad_onion_bunch
].copy()

print("\nRows removed by onion/bunch semantic cleanup:")
print(f"{before_onion_cleanup - len(top3):,}")


# ============================================================
# UNIT HOMOLOGATION
#
# kg     -> gram
# litro  -> liter
# pieza  -> piece
# manojo -> bunch
# ============================================================

top3["precio_homologado_mxn"] = (
    top3["price"].astype(float)
)

top3["unidad"] = top3["unit"]


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

top3.loc[
    kg_mask,
    "unidad",
] = "gramo"


# ============================================================
# REMOVE TRUE-ALIAS DUPLICATION
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
# CHAIN MEAN
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
# ============================================================

result["precio_promedio_mxn"] = (
    result["precio_promedio_mxn"]
    .round(4)
)


# ============================================================
# RENAME
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
            "unidad",
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
print("TOP 3 CHAINS - FINAL HOMOLOGATED DATASET")
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


print("\nUnits:")

print(
    result["unidad"]
    .value_counts()
    .to_string()
)


# ============================================================
# INGREDIENT COVERAGE
# ============================================================

coverage = (
    result.groupby(
        "ingrediente",
        observed=True,
    )["cadena"]
    .nunique()
)

print("\nIngredient coverage:")

print(
    f"Available in 3 chains: "
    f"{int((coverage == 3).sum()):,}"
)

print(
    f"Available in 2 chains: "
    f"{int((coverage == 2).sum()):,}"
)

print(
    f"Available in 1 chain: "
    f"{int((coverage == 1).sum()):,}"
)


# ============================================================
# ONION CHECK
# ============================================================

print("\n=== ONION CHECK ===")

onion_check = result[
    result["ingrediente"].isin(
        [
            "onion",
            "green onion",
        ]
    )
]

print(
    onion_check[
        [
            "cadena",
            "ingrediente",
            "producto_profeco",
            "precio_promedio_mxn",
            "unidad",
        ]
    ]
    .to_string(index=False)
)


# ============================================================
# PIEZA / MANOJO CHECK
# ============================================================

print("\n=== PIEZA / MANOJO SAMPLE ===")

native_units = result[
    result["unidad"].isin(
        [
            "pieza",
            "manojo",
        ]
    )
]

print(
    native_units.head(40)
    .to_string(index=False)
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
            result["precio_promedio_mxn"] <= 0
        ).sum()
    ),
)

expected_units = {
    "gramo",
    "litro",
    "pieza",
    "manojo",
}

print(
    "Unexpected units:",
    sorted(
        set(result["unidad"])
        - expected_units
    ),
)

print(
    "Excluded weak mappings still present:",
    sorted(
        set(result["ingrediente"])
        & EXCLUDED_INGREDIENTS
    ),
)

bad_final_onion = result[
    (result["ingrediente"] == "onion")
    &
    (result["unidad"] == "manojo")
]

print(
    "Invalid onion/manojo rows:",
    len(bad_final_onion),
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
    f"File size: {size_mb:.3f} MB"
)
