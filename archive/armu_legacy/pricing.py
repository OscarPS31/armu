from pathlib import Path

import pandas as pd

from armu.ingredient_matching import (
    normalize_text,
    normalize_ingredient,
    get_profeco_search_terms,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PROFECO_PATH = (
    PROJECT_ROOT
    / "data"
    / "profeco_mvp.csv.gz"
)


# ============================================================
# LOAD PROFECO
# ============================================================

def load_profeco_prices(
    path=None,
):
    """
    Load and prepare the reduced PROFECO dataset.

    Uses a path relative to the project root so it works
    both locally and on Streamlit Community Cloud.
    """

    if path is None:
        path = DEFAULT_PROFECO_PATH

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"PROFECO dataset not found at: {path}"
        )

    prices = pd.read_csv(
        path,
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

    for column in [
        "producto",
        "presentacion",
        "categoria",
    ]:
        prices[f"{column}_normalized"] = (
            prices[column]
            .apply(normalize_text)
        )

    prices["search_text"] = (
        prices["producto_normalized"]
        + " "
        + prices["presentacion_normalized"]
        + " "
        + prices["categoria_normalized"]
    )

    return prices


# ============================================================
# PRICE MATCH
# ============================================================

def find_profeco_price(
    ingredient,
    prices,
):
    """
    Find a PROFECO match and price statistics
    for one recipe ingredient.
    """

    original = ingredient

    normalized = normalize_ingredient(
        ingredient
    )

    search_terms = get_profeco_search_terms(
        ingredient
    )

    if not search_terms:
        return {
            "ingredient": original,
            "normalized": normalized,
            "matched_term": None,
            "median_price": None,
            "min_price": None,
            "max_price": None,
            "matches": 0,
            "status": "UNSUPPORTED",
        }

    for term in search_terms:

        term_normalized = normalize_text(
            term
        )

        matches = prices[
            prices["search_text"]
            .str.contains(
                term_normalized,
                na=False,
                regex=False,
            )
        ]

        if matches.empty:
            continue

        return {
            "ingredient": original,
            "normalized": normalized,
            "matched_term": term,
            "median_price": float(
                matches["precio"].median()
            ),
            "min_price": float(
                matches["precio"].min()
            ),
            "max_price": float(
                matches["precio"].max()
            ),
            "matches": int(
                len(matches)
            ),
            "status": "MATCHED",
        }

    return {
        "ingredient": original,
        "normalized": normalized,
        "matched_term": None,
        "median_price": None,
        "min_price": None,
        "max_price": None,
        "matches": 0,
        "status": "NOT_FOUND",
    }
