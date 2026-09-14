from functools import lru_cache
from html import unescape
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PRICE_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "recipe_prices_complete_3chains.csv"
)

CHAINS = [
    "Walmart",
    "Soriana",
    "Chedraui",
]


@lru_cache(maxsize=1)
def load_price_data() -> pd.DataFrame:
    if not PRICE_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing dataset: {PRICE_DATA_PATH}"
        )

    df = pd.read_csv(
        PRICE_DATA_PATH,
        low_memory=False,
    )

    required_columns = {
        "id_receta",
        "nombre_receta",
        "cadena",
        "precio_total_receta_mxn",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    return df


def compare_recipe_prices(recipe_id: int) -> dict:
    df = load_price_data()

    recipe_df = df[
        df["id_receta"] == recipe_id
    ].copy()

    if recipe_df.empty:
        raise ValueError(
            f"Recipe id {recipe_id} not found"
        )

    recipe_name = unescape(
        str(
            recipe_df["nombre_receta"].iloc[0]
        )
    )

    prices = (
        recipe_df[
            [
                "cadena",
                "precio_total_receta_mxn",
            ]
        ]
        .drop_duplicates()
        .groupby(
            "cadena",
            as_index=False,
        )["precio_total_receta_mxn"]
        .first()
    )

    comparison = []

    for chain in CHAINS:
        chain_row = prices[
            prices["cadena"] == chain
        ]

        if chain_row.empty:
            continue

        price = float(
            chain_row[
                "precio_total_receta_mxn"
            ].iloc[0]
        )

        comparison.append(
            {
                "cadena": chain,
                "precio_total_mxn": round(
                    price,
                    2,
                ),
            }
        )

    if not comparison:
        raise ValueError(
            f"No prices found for recipe id {recipe_id}"
        )

    comparison = sorted(
        comparison,
        key=lambda item: item[
            "precio_total_mxn"
        ],
    )

    cheapest = comparison[0]
    most_expensive = comparison[-1]

    savings = round(
        most_expensive["precio_total_mxn"]
        - cheapest["precio_total_mxn"],
        2,
    )

    return {
        "id_receta": int(recipe_id),
        "nombre_receta": recipe_name,
        "comparacion": comparison,
        "cadena_mas_barata": cheapest["cadena"],
        "precio_mas_barato_mxn": cheapest[
            "precio_total_mxn"
        ],
        "cadena_mas_cara": most_expensive["cadena"],
        "precio_mas_caro_mxn": most_expensive[
            "precio_total_mxn"
        ],
        "ahorro_mxn": savings,
    }
