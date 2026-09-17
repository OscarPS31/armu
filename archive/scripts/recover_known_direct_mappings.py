import re
from pathlib import Path

import pandas as pd


MAPPING_PATH = Path("data/ingredient_mapping_all.csv")
BACKUP_PATH = Path(
    "data/ingredient_mapping_all_before_direct_recovery_v2.csv"
)


# ============================================================
# SAFE DIRECT PROFECO RULES
# ============================================================

RULES = [
    {
        "pattern": r"\bbaking soda\b",
        "canonical": "baking soda",
        "profeco": "Bicarbonato",
        "exclude": [],
    },
    {
        "pattern": r"\bnutmeg\b",
        "canonical": "nutmeg",
        "profeco": "Nuez Moscada",
        "exclude": [],
    },
    {
        "pattern": r"\bpaprika\b",
        "canonical": "paprika",
        "profeco": "Paprika",
        "exclude": [],
    },
    {
        "pattern": r"\bparmesan(?: cheese)?\b",
        "canonical": "parmesan cheese",
        "profeco": "Queso Parmesano",
        "exclude": [],
    },

    # Ginger: avoid drinks, syrups, sauces, etc.
    {
        "pattern": r"\bginger(?:root)?\b",
        "canonical": "ginger",
        "profeco": "Jengibre",
        "exclude": [
            r"\bginger ale\b",
            r"\bginger beer\b",
            r"\bginger soda\b",
            r"\bginger syrup\b",
            r"\bginger juice\b",
            r"\bginger sauce\b",
            r"\bginger paste\b",
            r"\bginger preserves\b",
            r"\bginger marmalade\b",
            r"\bginger candy\b",
        ],
    },

    {
        "pattern": r"\bparsley\b",
        "canonical": "parsley",
        "profeco": "Perejil",
        "exclude": [],
    },
    {
        "pattern": r"\bbasil\b",
        "canonical": "basil",
        "profeco": "Albahaca",
        "exclude": [
            r"\bbasil pesto\b",
            r"\bpesto\b",
        ],
    },
    {
        "pattern": r"\bcheddar cheese\b",
        "canonical": "cheddar cheese",
        "profeco": "Queso Cheddar",
        "exclude": [
            r"\bcheddar cheese sauce\b",
            r"\bcheddar cheese soup\b",
            r"\bcheddar cheese spread\b",
        ],
    },

    # Pecans: actual nut forms only, not pie/filling/flavor.
    {
        "pattern": r"\bpecans?\b",
        "canonical": "pecan",
        "profeco": "Nuez",
        "exclude": [
            r"\bpecan pie\b",
            r"\bpecan filling\b",
            r"\bpecan flavor\b",
            r"\bpecan syrup\b",
        ],
    },

    # Coconut: exclude derived products.
    {
        "pattern": r"\bcoconut\b",
        "canonical": "coconut",
        "profeco": "Coco",
        "exclude": [
            r"\bcoconut milk\b",
            r"\bcoconut cream\b",
            r"\bcream of coconut\b",
            r"\bcoconut oil\b",
            r"\bcoconut water\b",
            r"\bcoconut extract\b",
            r"\bcoconut flour\b",
            r"\bcoconut sugar\b",
            r"\bcoconut syrup\b",
            r"\bcoconut rum\b",
            r"\bcoconut liqueur\b",
        ],
    },

    {
        "pattern": r"^chickens?$",
        "canonical": "chicken",
        "profeco": "Carne Pollo",
        "exclude": [],
    },
]


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


df.to_csv(
    BACKUP_PATH,
    index=False,
    encoding="utf-8-sig",
)

print(f"Backup saved: {BACKUP_PATH}")


before_strings = int(
    df["has_profeco_price"].sum()
)

before_occurrences = int(
    df.loc[
        df["has_profeco_price"],
        "occurrences",
    ].sum()
)


ingredient_text = (
    df["ingredient"]
    .fillna("")
    .astype(str)
    .str.lower()
    .str.strip()
)


recovered_records = []


for rule in RULES:

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

    indices = df.index[mask]

    for idx in indices:

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


df.to_csv(
    MAPPING_PATH,
    index=False,
    encoding="utf-8-sig",
)


after_strings = int(
    df["has_profeco_price"].sum()
)

after_occurrences = int(
    df.loc[
        df["has_profeco_price"],
        "occurrences",
    ].sum()
)


recovered = pd.DataFrame(
    recovered_records
)


print("\n" + "=" * 90)
print("KNOWN DIRECT PROFECO RECOVERY V2")
print("=" * 90)

print(
    "\nRecovered ingredient strings:",
    f"{after_strings - before_strings:,}",
)

print(
    "Recovered occurrences:",
    f"{after_occurrences - before_occurrences:,}",
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


if not recovered.empty:

    print(
        "\n=== RECOVERED BY CANONICAL INGREDIENT ==="
    )

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

    print(summary.to_string(index=False))


    print(
        "\n=== CHECK EXCLUDED FALSE POSITIVES ==="
    )

    checks = [
        "ginger ale",
        "ginger beer",
        "coconut milk",
        "coconut cream",
        "coconut oil",
        "coconut water",
        "basil pesto",
        "cheddar cheese sauce",
        "pecan pie",
    ]

    for term in checks:

        rows = df[
            df["ingredient"]
            .fillna("")
            .str.lower()
            .str.contains(
                term,
                regex=False,
            )
        ]

        wrongly_mapped = rows[
            rows["has_profeco_price"]
            & rows["canonical_ingredient"].isin(
                [
                    "ginger",
                    "coconut",
                    "basil",
                    "cheddar cheese",
                    "pecan",
                ]
            )
        ]

        print(
            f"{term}: "
            f"{len(wrongly_mapped)} suspicious mapped rows"
        )


print("\nSaved:")
print(MAPPING_PATH)
