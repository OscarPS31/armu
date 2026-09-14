import pandas as pd
import pytest

from api.schemas import RecommendationRequest
from api.services.recommendation import (
    filter_recipe_quality,
    ingredient_overlap,
    is_non_main_recipe,
    load_recipe_prices,
    recipe_main_meal_score,
    recommend,
)


def test_blocked_non_food_recipe():
    catalog = pd.DataFrame(
        [
            {
                "id_receta": 1,
                "nombre_receta": "Chicken Soup",
                "ingredientes": [
                    "chicken",
                    "onion",
                    "carrot",
                ],
                "precio_total_receta_mxn": 50.0,
            },
            {
                "id_receta": 2,
                "nombre_receta": "Lemon Mint Elbow Bleach",
                "ingredientes": [
                    "lemon",
                    "mint",
                ],
                "precio_total_receta_mxn": 2.0,
            },
        ]
    )

    result = filter_recipe_quality(
        catalog
    )

    names = result[
        "nombre_receta"
    ].tolist()

    assert "Lemon Mint Elbow Bleach" not in names
    assert "Chicken Soup" in names


def test_replacement_and_substitute_are_not_main_meals():
    assert is_non_main_recipe(
        "Powdered Sugar Replacement"
    )

    assert is_non_main_recipe(
        "Confectioners Sugar Substitute"
    )


def test_standalone_sauce_is_not_main_meal():
    assert is_non_main_recipe(
        "Classic Tomato Sauce"
    )


def test_main_meal_score_favors_real_meal():
    chicken_score = recipe_main_meal_score(
        "Chicken Rice Casserole",
        [
            "chicken",
            "rice",
            "onion",
            "carrot",
            "garlic",
        ],
    )

    sugar_score = recipe_main_meal_score(
        "Sugar Mix",
        [
            "sugar",
            "water",
        ],
    )

    assert chicken_score > sugar_score


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


def test_default_menu_does_not_include_blocked_terms():
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

    assert all(
        "replacement" not in name
        for name in names
    )

    assert all(
        "substitute" not in name
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


def test_default_menu_has_main_meal_candidates():
    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=None,
            personas=2,
            cadena="Walmart",
        )
    )

    recipes = [
        recipe
        for daily
        in response.menu_semanal.values()
        for recipe
        in daily
    ]

    assert recipes

    scores = [
        recipe_main_meal_score(
            recipe.name,
            recipe.ingredients,
        )
        for recipe in recipes
    ]

    assert max(scores) > 0
