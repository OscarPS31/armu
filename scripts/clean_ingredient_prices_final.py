import os
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INPUT_PATH = "data/ingredient_prices.csv"
OUTPUT_PATH = "data/ingredient_prices_clean.csv"


# ============================================================
# LOAD
# ============================================================

print("Loading ingredient prices...")

df = pd.read_csv(INPUT_PATH)

print(f"Original rows: {len(df):,}")


# ============================================================
# KEEP REQUIRED DATA
# ============================================================

df = df[
    [
        "ingredient",
        "profeco_category",
        "price",
        "unit",
        "store",
    ]
].copy()


# ============================================================
# CLEAN TEXT
# ============================================================

text_columns = [
    "ingredient",
    "profeco_category",
    "unit",
    "store",
]

for column in text_columns:
    df[column] = (
        df[column]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )


# ============================================================
# HUMAN-FRIENDLY INGREDIENT NAMES
#
# This is ONLY for the clean/share version.
# The original technical CSV remains unchanged.
# ============================================================

df["ingredient"] = (
    df["ingredient"]
    .str.replace("_", " ", regex=False)
    .str.title()
)


# ============================================================
# STANDARDIZE UNITS
# ============================================================

UNIT_MAP = {
    "kg": "kg",
    "litro": "litro",
    "pieza": "pieza",
    "manojo": "manojo",
}

df["unit"] = (
    df["unit"]
    .str.lower()
    .map(UNIT_MAP)
)


# ============================================================
# PRICE CLEANING
# ============================================================

df["price"] = pd.to_numeric(
    df["price"],
    errors="coerce",
)

df = df[
    df["price"].notna()
].copy()

df = df[
    df["price"] > 0
].copy()

df["price"] = df["price"].round(2)


# ============================================================
# REMOVE INVALID TEXT ROWS
# ============================================================

for column in [
    "ingredient",
    "profeco_category",
    "store",
]:
    df = df[
        df[column].notna()
        & (df[column] != "")
        & (df[column].str.lower() != "nan")
    ].copy()


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before_duplicates = len(df)

df = df.drop_duplicates().copy()

duplicates_removed = (
    before_duplicates - len(df)
)


# ============================================================
# SORT FOR HUMAN READABILITY
# ============================================================

df = df.sort_values(
    [
        "ingredient",
        "profeco_category",
        "store",
        "unit",
        "price",
    ],
    kind="stable",
).reset_index(drop=True)


# ============================================================
# RENAME COLUMNS FOR SHARE VERSION
# ============================================================

df = df.rename(
    columns={
        "ingredient": "ingrediente",
        "profeco_category": "producto_profeco",
        "price": "precio_mxn",
        "unit": "unidad",
        "store": "tienda",
    }
)


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

df = df[
    [
        "ingrediente",
        "producto_profeco",
        "precio_mxn",
        "unidad",
        "tienda",
    ]
]


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# REPORT
# ============================================================

size_mb = (
    os.path.getsize(OUTPUT_PATH)
    / 1024
    / 1024
)

print("\n" + "=" * 70)
print("CLEAN INGREDIENT PRICE DATASET")
print("=" * 70)

print(f"Final rows: {len(df):,}")
print(f"Duplicates removed: {duplicates_removed:,}")

print(
    f"Ingredients: "
    f"{df['ingrediente'].nunique():,}"
)

print(
    f"PROFECO products: "
    f"{df['producto_profeco'].nunique():,}"
)

print(
    f"Stores: "
    f"{df['tienda'].nunique():,}"
)

print("\nUnits:")
print(
    df["unidad"]
    .value_counts()
    .to_string()
)

print("\nNull values:")
print(
    df.isna()
    .sum()
    .to_string()
)

print("\nSample:")
print(
    df.head(20)
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_PATH)

print(
    f"File size: "
    f"{size_mb:.3f} MB"
)
