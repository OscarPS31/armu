import re
from pathlib import Path

import pandas as pd


MAPPING_PATH = Path("data/ingredient_mapping_all.csv")
BACKUP_PATH = Path("data/ingredient_mapping_all_before_clam_recovery.csv")


SAFE_PATTERNS = [
    r"^clam$",
    r"^clams$",
    r"^fresh clam$",
    r"^fresh clams$",
    r"^frozen clam$",
    r"^frozen clams$",
    r"^raw clam$",
    r"^raw clams$",
    r"^live clam$",
    r"^live clams$",
    r"^whole clam$",
    r"^whole clams$",
    r"^chopped clam$",
    r"^chopped clams$",
    r"^minced clam$",
    r"^minced clams$",
    r"^cooked clam$",
    r"^cooked clams$",
    r"^shucked clam$",
    r"^shucked clams$",
    r"^small clam$",
    r"^small clams$",
    r"^chopped fresh clam$",
    r"^chopped fresh clams$",
    r"^clam chopped$",
    r"^clams chopped$",
    r"^clam minced$",
    r"^clams minced$",
    r"^clam chopped minced$",
    r"^clam meat$",
    r"^clam meats$",
    r"^minced sea clam$",
    r"^minced sea clams$",
    r"^raw maine clam$",
    r"^raw maine clams$",
    r"^shucked maine clam$",
    r"^shucked maine clams$",
    r"^pre cooked clam$",
    r"^pre cooked clams$",
    r"^pre-cooked clam$",
    r"^pre-cooked clams$",
    r"^hard shelled clam$",
    r"^hard shelled clams$",
]


def normalize(value):
    value = str(value).lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


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


ingredient_norm = (
    df["ingredient"]
    .fillna("")
    .map(normalize)
)


safe_regex = (
    "(?:"
    + "|".join(SAFE_PATTERNS)
    + ")"
)


mask = (
    ~df["has_profeco_price"]
    & ingredient_norm.str.match(
        safe_regex,
        na=False,
    )
)


recovered = df.loc[
    mask,
    [
        "ingredient",
        "occurrences",
    ],
].copy()


df.loc[
    mask,
    "canonical_ingredient",
] = "clam"

df.loc[
    mask,
    "profeco_category",
] = "Almeja"

df.loc[
    mask,
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


print("\n" + "=" * 80)
print("SAFE CLAM RECOVERY")
print("=" * 80)

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

    print("\n=== RECOVERED CLAM STRINGS ===")

    print(
        recovered
        .sort_values(
            "occurrences",
            ascending=False,
        )
        .to_string(index=False)
    )


print("\nSaved:")
print(MAPPING_PATH)
