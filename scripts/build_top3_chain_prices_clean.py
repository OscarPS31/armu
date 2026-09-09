import os
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INPUT_PATH = "data/ingredient_prices_top3_chains.csv"
OUTPUT_PATH = "data/ingredient_prices_top3_chains_clean.csv"


# ============================================================
# LOAD
# ============================================================

print("Loading validated top-3 chain dataset...")

df = pd.read_csv(INPUT_PATH)

print(f"Input rows: {len(df):,}")


# ============================================================
# SELECT PRESENTATION COLUMNS
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
# FRIENDLIER DISPLAY
# ============================================================

clean["cadena"] = clean["cadena"].str.strip()
clean["ingrediente"] = clean["ingrediente"].str.strip()
clean["producto_profeco"] = clean["producto_profeco"].str.strip()
clean["unidad"] = clean["unidad"].str.strip()


# ============================================================
# ROUNDING
#
# Gram prices need 4 decimals.
# Liter prices are easier to read with 2 decimals.
# ============================================================

gram_mask = clean["unidad"] == "gramo"
liter_mask = clean["unidad"] == "litro"

clean.loc[
    gram_mask,
    "precio_promedio_mxn"
] = clean.loc[
    gram_mask,
    "precio_promedio_mxn"
].round(4)

clean.loc[
    liter_mask,
    "precio_promedio_mxn"
] = clean.loc[
    liter_mask,
    "precio_promedio_mxn"
].round(2)


# ============================================================
# SORT
# ============================================================

CHAIN_ORDER = [
    "Soriana",
    "Chedraui",
    "Walmart",
]

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
            "cadena",
            "producto_profeco",
        ]
    )
    .reset_index(drop=True)
)

clean["cadena"] = clean["cadena"].astype(str)


# ============================================================
# VALIDATION
# ============================================================

print("\n=== VALIDATION ===")

print(
    "Null values:",
    int(clean.isna().sum().sum())
)

print(
    "Duplicate rows:",
    int(clean.duplicated().sum())
)

print(
    "Prices <= 0:",
    int(
        (
            clean["precio_promedio_mxn"] <= 0
        ).sum()
    )
)

print(
    "Unexpected units:",
    sorted(
        set(clean["unidad"])
        - {
            "gramo",
            "litro",
        }
    )
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
print("PRESENTATION CSV")
print("=" * 80)

print(f"\nRows generated: {len(clean):,}")

print("\nRows by chain:")
print(
    clean["cadena"]
    .value_counts()
    .reindex(CHAIN_ORDER)
    .to_string()
)

print("\nUnique ingredients:")
print(
    clean["ingrediente"]
    .nunique()
)

print("\nUnits:")
print(
    clean["unidad"]
    .value_counts()
    .to_string()
)

print("\n=== SAMPLE ===")

print(
    clean.head(30)
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
