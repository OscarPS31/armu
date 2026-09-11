from pathlib import Path

import pandas as pd


MAPPING_PATH = Path("data/ingredient_mapping_all.csv")
BACKUP_PATH = Path(
    "data/ingredient_mapping_all_before_coconut_cleanup.csv"
)


print("Loading mapping...")

df = pd.read_csv(MAPPING_PATH)

required = {
    "ingredient",
    "occurrences",
    "canonical_ingredient",
    "profeco_category",
    "has_profeco_price",
}

missing = required - set(df.columns)

if missing:
    raise ValueError(
        f"Missing columns: {sorted(missing)}"
    )


# ------------------------------------------------------------
# Backup
# ------------------------------------------------------------

df.to_csv(
    BACKUP_PATH,
    index=False,
    encoding="utf-8-sig",
)

print(f"Backup saved: {BACKUP_PATH}")


# ------------------------------------------------------------
# Metrics before
# ------------------------------------------------------------

before_strings = int(
    df["has_profeco_price"].sum()
)

before_occurrences = int(
    df.loc[
        df["has_profeco_price"],
        "occurrences",
    ].sum()
)


# ------------------------------------------------------------
# Normalize ingredient text
# ------------------------------------------------------------

ingredient = (
    df["ingredient"]
    .fillna("")
    .astype(str)
    .str.lower()
    .str.strip()
)


# ------------------------------------------------------------
# Coconut-derived products that must NOT use generic
# dairy/coconut/water/rice/etc. PROFECO prices
# ------------------------------------------------------------

derived_mask = (
    ingredient.str.contains(
        r"\bcoconut[\s-]*milk\b",
        regex=True,
        na=False,
    )
    |
    ingredient.str.contains(
        r"\bcoconut[\s-]*cream\b",
        regex=True,
        na=False,
    )
    |
    ingredient.str.contains(
        r"\bcream of coconut\b",
        regex=True,
        na=False,
    )
)


mapped_mask = (
    derived_mask
    & df["has_profeco_price"]
)


removed = df.loc[
    mapped_mask,
    [
        "ingredient",
        "occurrences",
        "canonical_ingredient",
        "profeco_category",
    ],
].copy()


# ------------------------------------------------------------
# Remove unsupported price mapping
# ------------------------------------------------------------

df.loc[
    mapped_mask,
    "canonical_ingredient",
] = pd.NA

df.loc[
    mapped_mask,
    "profeco_category",
] = pd.NA

df.loc[
    mapped_mask,
    "has_profeco_price",
] = False


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

df.to_csv(
    MAPPING_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ------------------------------------------------------------
# Metrics after
# ------------------------------------------------------------

after_strings = int(
    df["has_profeco_price"].sum()
)

after_occurrences = int(
    df.loc[
        df["has_profeco_price"],
        "occurrences",
    ].sum()
)


print("\n" + "=" * 90)
print("COCONUT DERIVED PRODUCT CLEANUP")
print("=" * 90)

print(
    "\nMappings removed:",
    f"{before_strings - after_strings:,}",
)

print(
    "Occurrences removed:",
    f"{before_occurrences - after_occurrences:,}",
)

print(
    "\nMapped strings before:",
    f"{before_strings:,}",
)

print(
    "Mapped strings after:",
    f"{after_strings:,}",
)

print(
    "\nMapped occurrences before:",
    f"{before_occurrences:,}",
)

print(
    "Mapped occurrences after:",
    f"{after_occurrences:,}",
)


if not removed.empty:

    print("\n=== REMOVED BY OLD MAPPING ===")

    summary = (
        removed
        .groupby(
            [
                "canonical_ingredient",
                "profeco_category",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            ingredient_strings=(
                "ingredient",
                "nunique",
            ),
            occurrences=(
                "occurrences",
                "sum",
            ),
        )
        .sort_values(
            "occurrences",
            ascending=False,
        )
    )

    print(summary.to_string(index=False))


    print("\n=== TOP REMOVED STRINGS ===")

    print(
        removed
        .sort_values(
            "occurrences",
            ascending=False,
        )
        .head(50)
        .to_string(index=False)
    )


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

remaining_bad = df[
    df["has_profeco_price"]
    & (
        df["ingredient"]
        .fillna("")
        .str.lower()
        .str.contains(
            r"\bcoconut[\s-]*milk\b"
            r"|\bcoconut[\s-]*cream\b"
            r"|\bcream of coconut\b",
            regex=True,
            na=False,
        )
    )
]

print(
    "\nRemaining mapped coconut-derived rows:",
    len(remaining_bad),
)


# Pecan check using a TRUE word-boundary expression,
# not the previous substring bug.
pecan_pie = df[
    df["ingredient"]
    .fillna("")
    .str.lower()
    .str.contains(
        r"\bpecan pie\b",
        regex=True,
        na=False,
    )
    & df["has_profeco_price"]
]

print(
    "Actual mapped 'pecan pie' rows:",
    len(pecan_pie),
)

print("\nSaved:")
print(MAPPING_PATH)
