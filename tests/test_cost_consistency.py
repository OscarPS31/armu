import pandas as pd

from api.services.recommendation import (
    load_recipe_prices,
)


def test_recipe_totals_match_ingredient_costs():
    df = load_recipe_prices()

    grouped = (
        df.groupby(
            [
                "id_receta",
                "cadena",
            ],
            as_index=False,
        )
        .agg(
            ingredient_total=(
                "costo_ingrediente_mxn",
                "sum",
            ),
            recipe_total=(
                "precio_total_receta_mxn",
                "first",
            ),
        )
    )

    grouped["difference"] = (
        grouped["ingredient_total"]
        - grouped["recipe_total"]
    ).abs()

    assert (
        grouped["difference"] <= 0.10
    ).all()


def test_no_negative_recipe_prices():
    df = load_recipe_prices()

    prices = (
        df[
            [
                "id_receta",
                "cadena",
                "precio_total_receta_mxn",
            ]
        ]
        .drop_duplicates()
    )

    assert (
        prices["precio_total_receta_mxn"] >= 0
    ).all()


def test_no_negative_ingredient_costs():
    df = load_recipe_prices()

    assert (
        df["costo_ingrediente_mxn"] >= 0
    ).all()


def test_all_complete_recipes_have_three_chains():
    df = load_recipe_prices()

    chain_counts = (
        df[
            [
                "id_receta",
                "cadena",
            ]
        ]
        .drop_duplicates()
        .groupby("id_receta")["cadena"]
        .nunique()
    )

    assert (chain_counts == 3).all()
