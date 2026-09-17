import os
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INPUT_PATH = "data/ingredient_prices_top3_chains.csv"
OUTPUT_PATH = "data/ingredient_prices_top3_chains_clean.csv"

CHAIN_ORDER = [
    "Soriana",
    "Chedraui",
    "Walmart",
]

EXPECTED_UNITS = {
    "gramo",
    "litro",
    "pieza",
    "manojo",
}


# ============================================================
# LOAD
# ============================================================

print("Loading validated top-3 chain dataset...")

df = pd.read_csv(INPUT_PATH)

print(f"Input rows: {len(df):,}")


# ============================================================
# BASE COLUMNS
# ============================================================

clean = df[
    [
        "cadena",
        "ingrediente",
        "producto_profeco",
        "precio_promedio_mxn",
        "unidad",
    ]
].copy()


# ============================================================
# CLEAN TEXT
# ============================================================

for column in [
    "cadena",
    "ingrediente",
    "producto_profeco",
    "unidad",
]:
    clean[column] = (
        clean[column]
        .astype(str)
        .str.strip()
    )


# ============================================================
# OPTION A
#
# Keep the current normalized price:
#
# gram   -> MXN / gram
# liter  -> MXN / liter
# piece  -> MXN / piece
# bunch  -> MXN / bunch
# ============================================================

clean["precio_opcion_a_mxn"] = (
    clean["precio_promedio_mxn"]
)

clean["unidad_opcion_a"] = (
    clean["unidad"]
)


# ============================================================
# OPTION B
#
# gram:
#     convert price per gram back to a
#     1000-gram commercial reference
#
# liter / piece / bunch:
#     price remains unchanged
# ============================================================

clean["precio_opcion_b_mxn"] = (
    clean["precio_promedio_mxn"]
)

clean["unidad_opcion_b"] = (
    clean["unidad"]
)


gram_mask = (
    clean["unidad"] == "gramo"
)

clean.loc[
    gram_mask,
    "precio_opcion_b_mxn",
] = (
    clean.loc[
        gram_mask,
        "precio_promedio_mxn",
    ]
    * 1000
)

clean.loc[
    gram_mask,
    "unidad_opcion_b",
] = "1000 gramos"


# ============================================================
# ROUNDING
# ============================================================

clean["precio_opcion_a_mxn"] = (
    clean["precio_opcion_a_mxn"]
    .round(4)
)

clean["precio_opcion_b_mxn"] = (
    clean["precio_opcion_b_mxn"]
    .round(2)
)


# ============================================================
# FINAL COLUMNS
# ============================================================

clean = clean[
    [
        "cadena",
        "ingrediente",
        "producto_profeco",
        "precio_opcion_a_mxn",
        "unidad_opcion_a",
        "precio_opcion_b_mxn",
        "unidad_opcion_b",
    ]
]


# ============================================================
# SORT
# ============================================================

clean["cadena"] = pd.Categorical(
    clean["cadena"],
    categories=CHAIN_ORDER,
    ordered=True,
)

clean = (
    clean
    .sort_values(
        [
            "ingrediente",
            "unidad_opcion_a",
            "cadena",
        ]
    )
    .reset_index(drop=True)
)

clean["cadena"] = (
    clean["cadena"]
    .astype(str)
)


# ============================================================
# VALIDATION
# ============================================================

print("\n=== VALIDATION ===")

print(
    "Null values:",
    int(clean.isna().sum().sum()),
)

print(
    "Duplicate rows:",
    int(clean.duplicated().sum()),
)

print(
    "Prices A <= 0:",
    int(
        (
            clean["precio_opcion_a_mxn"] <= 0
        ).sum()
    ),
)

print(
    "Prices B <= 0:",
    int(
        (
            clean["precio_opcion_b_mxn"] <= 0
        ).sum()
    ),
)

unexpected_units = sorted(
    set(clean["unidad_opcion_a"])
    - EXPECTED_UNITS
)

print(
    "Unexpected option A units:",
    unexpected_units,
)


# ============================================================
# SAVE
# ============================================================

clean.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("PRESENTATION CSV - OPTION A VS OPTION B")
print("=" * 80)

print(f"\nRows generated: {len(clean):,}")


print("\n=== SAMPLE ===")

print(
    clean.head(30)
    .to_string(index=False)
)


print("\n=== GRAM EXAMPLE ===")

print(
    clean[
        clean["unidad_opcion_a"] == "gramo"
    ]
    .head(15)
    .to_string(index=False)
)


print("\n=== OTHER UNITS ===")

print(
    clean[
        clean["unidad_opcion_a"].isin(
            [
                "litro",
                "pieza",
                "manojo",
            ]
        )
    ]
    .head(20)
    .to_string(index=False)
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
