"""
Build data/recipes_priced.parquet from the team's exported CSV
(data/recipes_51k_eng.csv), which has English column names and all recipe steps.

The CSV stores `steps` as a list-like string with UNESCAPED double quotes
(e.g. `10"` inches), which breaks strict parsing for ~22% of recipes. We use a
tolerant reader that recovers those steps instead of dropping them.

Run:

    python scripts/build_parquet_from_csv.py
"""

import ast
import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "recipes_51k_eng.csv"
OUT_PATH = PROJECT_ROOT / "data" / "recipes_priced.parquet"

FLAG_COLUMNS = [
    "is_vegan",
    "is_vegetarian",
    "is_gluten_free",
    "is_dairy_free",
    "is_lactose_free",
    "is_nut_free",
    "is_egg_free",
    "quick_15min",
    "quick_30min",
    "quick_60min",
]


def split_pipe(value):
    """Ingredients / tags are stored pipe-joined: 'a | b | c'."""
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def read_steps(value):
    """
    Read a recipe's steps, recovering the ones whose quotes were not escaped.

    1) Try a strict parse (works for ~78%).
    2) On failure, split on the real separator between steps ('", "') instead
       of trusting every quote, then trim stray quotes from the edges.
    """
    s = str(value).strip()

    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
    except Exception:
        pass

    if s.startswith("["):
        s = s[1:]
    if s.endswith("]"):
        s = s[:-1]

    parts = re.split(r'",\s*"', s)
    return [p.strip().strip('"').strip() for p in parts if p.strip().strip('"').strip()]


def to_bool(series):
    """Flags come as 'True'/'False' strings; normalize to real booleans."""
    return series.astype(str).str.strip().str.lower().isin(["true", "1"])


def build_search_text(row):
    name = str(row.get("name") or "")
    ingredients = " ".join(str(i) for i in row["ingredients"])
    tags = " ".join(str(t) for t in row["tags"])
    return f"{name} {ingredients} {tags}".lower()


def main():
    print("Loading CSV...")
    df = pd.read_csv(CSV_PATH)
    print(f"  {len(df)} rows")

    df = df.drop_duplicates(subset="id", keep="first")
    print(f"  {len(df)} unique recipes")

    df["ingredients"] = df["ingredients"].apply(split_pipe)
    df["tags"] = df["tags"].apply(split_pipe)
    df["steps"] = df["steps"].apply(read_steps)

    for col in FLAG_COLUMNS:
        df[col] = to_bool(df[col])

    for col in ["estimated_cost", "minimum_estimate", "maximum_estimate"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    df["search_text"] = df.apply(build_search_text, axis=1)

    columns = [
        "id",
        "name",
        "ingredients",
        "steps",
        "servings",
        "tags",
        *FLAG_COLUMNS,
        "search_text",
        "estimated_cost",
        "minimum_estimate",
        "maximum_estimate",
        "confidence",
    ]
    out = df[columns]

    empty_steps = (out["steps"].apply(len) == 0).sum()
    print(f"  recipes with recovered steps: {(out['steps'].apply(len) > 0).sum()}")
    print(f"  recipes still without steps : {empty_steps}")

    out.to_parquet(OUT_PATH, index=False)
    print(f"  wrote {OUT_PATH.name} ({len(out)} recipes)")
    print("Done.")


if __name__ == "__main__":
    main()
