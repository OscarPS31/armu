import os
import re

import pandas as pd

from armu.ingredient_matching import (
    INGREDIENT_RULES,
    normalize_text,
)


# ============================================================
# CONFIG
# ============================================================

SOURCE_PATH = "raw_data/07-2026_Q2.csv"

OUTPUT_PATH = "data/profeco_mvp.csv.gz"


# ============================================================
# LOAD DATA
# ============================================================

print("Loading full PROFECO dataset...")


prices = pd.read_csv(
    SOURCE_PATH,
    usecols=[
        "producto",
        "presentacion",
        "categoria",
        "precio",
        "cadena_comercial",
        "estado",
        "municipio",
    ],
)


print(
    f"Original rows: {len(prices):,}"
)


# ============================================================
# NORMALIZE SEARCH COLUMNS
# ============================================================

print(
    "Normalizing PROFECO text..."
)


for column in [
    "producto",
    "presentacion",
    "categoria",
]:

    prices[
        f"{column}_normalized"
    ] = (
        prices[column]
        .fillna("")
        .apply(normalize_text)
    )


prices["search_text"] = (
    prices["producto_normalized"]
    + " "
    + prices["presentacion_normalized"]
    + " "
    + prices["categoria_normalized"]
)


# ============================================================
# GET EVERY TERM USED BY OUR MATCHER
# ============================================================

search_terms = set()


for terms in INGREDIENT_RULES.values():

    for term in terms:

        search_terms.add(
            normalize_text(term)
        )


search_terms = sorted(
    search_terms
)


print(
    f"PROFECO search terms: "
    f"{len(search_terms)}"
)


# ============================================================
# FILTER ONLY RELEVANT PROFECO ROWS
# ============================================================

pattern = "|".join(
    re.escape(term)
    for term in search_terms
)


mask = (
    prices["search_text"]
    .str.contains(
        pattern,
        regex=True,
        na=False,
    )
)


profeco_mvp = (
    prices.loc[
        mask,
        [
            "producto",
            "presentacion",
            "categoria",
            "precio",
            "cadena_comercial",
            "estado",
            "municipio",
        ],
    ]
    .copy()
)


# ============================================================
# BASIC CLEANUP
# ============================================================

profeco_mvp["precio"] = (
    pd.to_numeric(
        profeco_mvp["precio"],
        errors="coerce",
    )
)


profeco_mvp = profeco_mvp[
    profeco_mvp["precio"].notna()
].copy()


profeco_mvp = profeco_mvp[
    profeco_mvp["precio"] > 0
].copy()


profeco_mvp = (
    profeco_mvp
    .drop_duplicates()
    .reset_index(drop=True)
)


# ============================================================
# SAVE COMPRESSED FILE
# ============================================================

os.makedirs(
    "data",
    exist_ok=True,
)


profeco_mvp.to_csv(
    OUTPUT_PATH,
    index=False,
    compression="gzip",
)


# ============================================================
# REPORT
# ============================================================

original_rows = len(prices)

mvp_rows = len(
    profeco_mvp
)


coverage = (
    mvp_rows
    / original_rows
    * 100
)


file_size_mb = (
    os.path.getsize(
        OUTPUT_PATH
    )
    / (1024 * 1024)
)


print("\n" + "=" * 60)

print(
    "NUTRIPLAN — PROFECO MVP DATASET"
)

print("=" * 60)


print(
    f"Original rows: "
    f"{original_rows:,}"
)


print(
    f"MVP rows: "
    f"{mvp_rows:,}"
)


print(
    f"Rows retained: "
    f"{coverage:.2f}%"
)


print(
    f"Compressed size: "
    f"{file_size_mb:.2f} MB"
)


print(
    f"Saved to: "
    f"{OUTPUT_PATH}"
)


print(
    "\n✅ PROFECO MVP dataset ready."
)
