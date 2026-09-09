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
# PRESENTATION COLUMNS
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
# ROUNDING
#
# gram:
#   retain 4 decimals because values are small
#
# liter / piece / bunch:
#   2 decimals are sufficient for presentation
# ============================================================

gram_mask = (
    clean["unidad"] == "gramo"
)

clean.loc[
    gram_mask,
    "precio_promedio_mxn",
] = (
    clean.loc[
        gram_mask,
        "precio_promedio_mxn",
    ]
    .round(4)
)


other_mask = (
    clean["unidad"].isin(
        [
            "litro",
            "pieza",
            "manojo",
        ]
    )
)

clean.loc[
    other_mask,
    "precio_promedio_mxn",
] = (
    clean.loc[
        other_mask,
        "precio_promedio_mxn",
    ]
    .round(2)
)


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
            "unidad",
            "cadena",
            "producto_profeco",
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
    "Prices <= 0:",
    int(
        (
            clean["precio_promedio_mxn"]
            <= 0
        ).sum()
    ),
)

unexpected_units = sorted(
    set(clean["unidad"])
    - EXPECTED_UNITS
)

print(
    "Unexpected units:",
    unexpected_units,
)


# ============================================================
# ONION VALIDATION
# ============================================================

invalid_onion_bunch = clean[
    (clean["ingrediente"] == "onion")
    &
    (clean["unidad"] == "manojo")
]

print(
    "Invalid onion/manojo rows:",
    len(invalid_onion_bunch),
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
print("PRESENTATION CSV - FINAL")
print("=" * 80)

print(
    f"\nRows generated: "
    f"{len(clean):,}"
)


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


# ============================================================
# COVERAGE
# ============================================================

coverage = (
    clean.groupby(
        "ingrediente"
    )["cadena"]
    .nunique()
)

print("\nIngredient coverage:")

print(
    "Available in 3 chains:",
    int((coverage == 3).sum()),
)

print(
    "Available in 2 chains:",
    int((coverage == 2).sum()),
)

print(
    "Available in 1 chain:",
    int((coverage == 1).sum()),
)


# ============================================================
# ONION / GREEN ONION CHECK
# ============================================================

print("\n=== ONION VS GREEN ONION ===")

print(
    clean[
        clean["ingrediente"].isin(
            [
                "onion",
                "green onion",
            ]
        )
    ]
    .to_string(index=False)
)


# ============================================================
# PIEZA / MANOJO
# ============================================================

print("\n=== PIEZA / MANOJO ===")

print(
    clean[
        clean["unidad"].isin(
            [
                "pieza",
                "manojo",
            ]
        )
    ]
    .to_string(index=False)
)


# ============================================================
# SAMPLE
# ============================================================

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
    f"File size: "
    f"{size_mb:.3f} MB"
)
