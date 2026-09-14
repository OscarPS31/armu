import pandas as pd
import pytest

from api.schemas import RecommendationRequest
from api.services.recommendation import (
    filter_recipe_quality,
    ingredient_overlap,
    load_recipe_prices,
    recommend,
)


def test_blocked_non_food_recipe():
    catalog = pd.DataFrame(
        [
            {
                "id_receta": 1,
                "nombre_receta": "Chicken Soup",
                "precio_total_receta_mxn": 50.0,
            },
            {
                "id_receta": 2,
                "nombre_receta": "Lemon Mint Elbow Bleach",
                "precio_total_receta_mxn": 2.0,
            },
        ]
    )

    result = filter_recipe_quality(
        catalog
    )

    assert (
        "Lemon Mint Elbow Bleach"
        not in result[
            "nombre_receta"
        ].tolist()
    )

    assert (
        "Chicken Soup"
        in result[
            "nombre_receta"
        ].tolist()
    )


def test_ingredient_overlap():
    overlap = ingredient_overlap(
        [
            "chicken",
            "onion",
            "tomato",
        ],
        [
            "chicken",
            "onion",
            "garlic",
        ],
    )

    assert overlap == pytest.approx(
        0.5
    )


def test_default_menu_does_not_include_bleach():
    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=None,
            personas=2,
            cadena="Walmart",
        )
    )

    names = [
        recipe.name.lower()
        for recipes
        in response.menu_semanal.values()
        for recipe
        in recipes
    ]

    assert all(
        "bleach" not in name
        for name in names
    )


def test_default_menu_not_only_cheapest_recipes():
    df = load_recipe_prices()

    walmart = (
        df[
            df["cadena"].eq(
                "Walmart"
            )
        ][
            [
                "id_receta",
                "precio_total_receta_mxn",
            ]
        ]
        .drop_duplicates()
    )

    median_price = float(
        walmart[
            "precio_total_receta_mxn"
        ].median()
    )

    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=None,
            personas=2,
            cadena="Walmart",
        )
    )

    selected_ids = {
        recipe.id
        for recipes
        in response.menu_semanal.values()
        for recipe
        in recipes
    }

    selected_prices = (
        walmart[
            walmart[
                "id_receta"
            ].isin(selected_ids)
        ][
            "precio_total_receta_mxn"
        ]
        .astype(float)
        .tolist()
    )

    assert selected_prices

    assert (
        sum(selected_prices)
        / len(selected_prices)
        > 10
    )

    assert any(
        price >= median_price * 0.5
        for price in selected_prices
    )


def test_menu_has_no_duplicate_recipe_ids():
    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=None,
            personas=2,
            cadena="Walmart",
        )
    )

    ids = [
        recipe.id
        for recipes
        in response.menu_semanal.values()
        for recipe
        in recipes
    ]

    assert len(ids) == len(
        set(ids)
    )
