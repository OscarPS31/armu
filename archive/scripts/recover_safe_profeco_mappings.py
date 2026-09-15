import re
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

MAPPING_PATH = Path("data/ingredient_mapping_all.csv")
BACKUP_PATH = Path("data/ingredient_mapping_all_before_recovery.csv")


# ============================================================
# SAFE RECOVERY RULES
# ============================================================
#
# IMPORTANT:
# These rules intentionally avoid ambiguous families such as:
#
# - corn / corn syrup / corn flakes
# - clam juice / clam broth
# - pork sausage / generic sausage
# - mozzarella / cottage cheese without direct PROFECO product
#
# We only recover mappings we can defend semantically.
# ============================================================

RULES = [
    # --------------------------------------------------------
    # SALMON
    # --------------------------------------------------------
    {
        "pattern": r"\bsalmon\b",
        "canonical": "salmon",
        "profeco": "Salmón",
        "exclude": [
            r"\bsalmonella\b",
            r"\bsalmon seasoning\b",
            r"\bsalmon magic\b",
        ],
    },

    # --------------------------------------------------------
    # TUNA
    # --------------------------------------------------------
    {
        "pattern": r"\btuna\b",
        "canonical": "tuna",
        "profeco": "Atún",
        "exclude": [],
    },

    # --------------------------------------------------------
    # SQUID
    # --------------------------------------------------------
    {
        "pattern": r"\bsquid\b",
        "canonical": "squid",
        "profeco": "Calamar",
        "exclude": [],
    },

    # --------------------------------------------------------
    # OCTOPUS
    # --------------------------------------------------------
    {
        "pattern": r"\boctopus\b",
        "canonical": "octopus",
        "profeco": "Pulpo",
        "exclude": [],
    },

    # --------------------------------------------------------
    # TROUT
    # --------------------------------------------------------
    {
        "pattern": r"\btrout\b",
        "canonical": "trout",
        "profeco": "Trucha",
        "exclude": [
            # Avoid mixed fish alternatives.
            r"\bsalmon\b",
        ],
    },

    # --------------------------------------------------------
    # SARDINES
    # --------------------------------------------------------
    {
        "pattern": r"\bsardines?\b",
        "canonical": "sardine",
        "profeco": "Sardina",
        "exclude": [],
    },

    # --------------------------------------------------------
    # CRAB / CRABMEAT
    # --------------------------------------------------------
    {
        "pattern": r"\bcrabmeat\b|\bcrab meat\b|\bcrab\b",
        "canonical": "crabmeat",
        "profeco": "Jaiba",
        "exclude": [
            r"\bimitation crab\b",
            r"\bsurimi\b",
        ],
    },

    # --------------------------------------------------------
    # KIDNEY BEANS
    # --------------------------------------------------------
    {
        "pattern": r"\b(?:red\s+)?kidney beans\b",
        "canonical": "kidney beans",
        "profeco": "Frijol",
        "exclude": [
            r"\bpork\b",
        ],
    },

    # --------------------------------------------------------
    # PINTO BEANS
    # --------------------------------------------------------
    {
        "pattern": r"\bpinto beans\b",
        "canonical": "pinto beans",
        "profeco": "Frijol",
        "exclude": [
            r"\bpork\b",
        ],
    },

    # --------------------------------------------------------
    # WHITE BEANS
    # --------------------------------------------------------
    {
        "pattern": r"\bwhite beans\b",
        "canonical": "white beans",
        "profeco": "Frijol",
        "exclude": [
            r"\bpork\b",
        ],
    },

    # --------------------------------------------------------
    # TURKEY
    # --------------------------------------------------------
    {
        "pattern": r"\bground turkey\b",
        "canonical": "ground turkey",
        "profeco": "Carne Pavo",
        "exclude": [
            r"\bsausage\b",
            r"\bdeli\b",
            r"\bham\b",
        ],
    },

    {
        "pattern": r"\bturkey breast\b",
        "canonical": "turkey",
        "profeco": "Carne Pavo",
        "exclude": [
            r"\bdeli\b",
            r"\bsmoked\b",
            r"\bham\b",
            r"\bsliced\b",
        ],
    },

    {
        "pattern": r"^(?:fresh\s+)?turkey$",
        "canonical": "turkey",
        "profeco": "Carne Pavo",
        "exclude": [],
    },

    # --------------------------------------------------------
    # RADISH
    # --------------------------------------------------------
    {
        "pattern": r"\bradishes?\b",
        "canonical": "radish",
        "profeco": "Rábano",
        "exclude": [],
    },

    # --------------------------------------------------------
    # BEET
    # --------------------------------------------------------
    {
        "pattern": r"\bbeets?\b",
        "canonical": "beet",
        "profeco": "Betabel",
        "exclude": [],
    },
]


# ============================================================
# LOAD
# ============================================================

print("Loading ingredient mapping...")

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


# ============================================================
# BACKUP
# ============================================================

df.to_csv(
    BACKUP_PATH,
    index=False,
    encoding="utf-8-sig",
)

print(f"Backup saved: {BACKUP_PATH}")


# ============================================================
# ORIGINAL METRICS
# ============================================================

before_strings = int(
    df["has_profeco_price"].sum()
)

before_occurrences = int(
    df.loc[
        df["has_profeco_price"],
        "occurrences",
    ].sum()
)


# ============================================================
# RECOVER
# ============================================================

recovered_records = []


for rule in RULES:

    ingredient_text = (
        df["ingredient"]
        .fillna("")
        .astype(str)
        .str.lower()
    )

    mask = (
        ~df["has_profeco_price"]
        & ingredient_text.str.contains(
            rule["pattern"],
            regex=True,
            na=False,
        )
    )

    for exclude_pattern in rule["exclude"]:
        mask &= ~ingredient_text.str.contains(
            exclude_pattern,
            regex=True,
            na=False,
        )

    matched_indices = df.index[mask]

    for idx in matched_indices:

        recovered_records.append(
            {
                "ingredient": df.at[idx, "ingredient"],
                "occurrences": int(
                    df.at[idx, "occurrences"]
                ),
                "canonical_ingredient": rule["canonical"],
                "profeco_category": rule["profeco"],
            }
        )

        df.at[
            idx,
            "canonical_ingredient",
        ] = rule["canonical"]

        df.at[
            idx,
            "profeco_category",
        ] = rule["profeco"]

        df.at[
            idx,
            "has_profeco_price",
        ] = True


# ============================================================
# METRICS
# ============================================================

after_strings = int(
    df["has_profeco_price"].sum()
)

after_occurrences = int(
    df.loc[
        df["has_profeco_price"],
        "occurrences",
    ].sum()
)

recovered_strings = (
    after_strings - before_strings
)

recovered_occurrences = (
    after_occurrences - before_occurrences
)


# ============================================================
# VALIDATE
# ============================================================

if df[
    df["has_profeco_price"]
][
    [
        "canonical_ingredient",
        "profeco_category",
    ]
].isna().any().any():

    raise ValueError(
        "Recovered mapping contains missing canonical/category values."
    )


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    MAPPING_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# REPORT
# ============================================================

recovered = pd.DataFrame(
    recovered_records
)

print("\n" + "=" * 80)
print("SAFE PROFECO MAPPING RECOVERY")
print("=" * 80)

print(
    f"\nRecovered ingredient strings: "
    f"{recovered_strings:,}"
)

print(
    f"Recovered occurrences: "
    f"{recovered_occurrences:,}"
)

print(
    f"\nMapped strings before: "
    f"{before_strings:,}"
)

print(
    f"Mapped strings after: "
    f"{after_strings:,}"
)

print(
    f"\nMapped occurrences before: "
    f"{before_occurrences:,}"
)

print(
    f"Mapped occurrences after: "
    f"{after_occurrences:,}"
)


if not recovered.empty:

    print("\n=== RECOVERED BY CANONICAL INGREDIENT ===")

    summary = (
        recovered
        .groupby(
            [
                "canonical_ingredient",
                "profeco_category",
            ],
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

    print(
        summary.to_string(index=False)
    )


    print("\n=== TOP RECOVERED STRINGS ===")

    print(
        recovered
        .sort_values(
            "occurrences",
            ascending=False,
        )
        .head(50)
        .to_string(index=False)
    )


print("\nSaved:")
print(MAPPING_PATH)
