import pandas as pd
import pytest

from api.schemas import RecommendationRequest
from api.services.recommendation import (
    filter_by_restrictions,
    normalize_restrictions,
    recipe_food_words,
    recommend,
)


def make_catalog():
    return pd.DataFrame(
        [
            {
                "id_receta": 1,
                "nombre_receta": "Chicken Rice",
                "ingredientes": [
                    "chicken",
                    "rice",
                    "onion",
                ],
                "precio_total_receta_mxn": 100.0,
                "search_text": "chicken rice onion",
            },
            {
                "id_receta": 2,
                "nombre_receta": "Vegetable Rice",
                "ingredientes": [
                    "rice",
                    "carrot",
                    "onion",
                ],
                "precio_total_receta_mxn": 80.0,
                "search_text": "vegetable rice carrot onion",
            },
            {
                "id_receta": 3,
                "nombre_receta": "Cheese Vegetable Rice",
                "ingredientes": [
                    "rice",
                    "cheese",
                    "carrot",
                ],
                "precio_total_receta_mxn": 90.0,
                "search_text": "cheese vegetable rice",
            },
            {
                "id_receta": 4,
                "nombre_receta": "Wheat Pasta",
                "ingredientes": [
                    "wheat",
                    "pasta",
                    "tomato",
                ],
                "precio_total_receta_mxn": 70.0,
                "search_text": "wheat pasta tomato",
            },
        ]
    )


def test_normalize_restrictions():
    assert normalize_restrictions(
        ["Vegetarian", "sin gluten"]
    ) == [
        "vegetariano",
        "sin_gluten",
    ]


def test_invalid_restriction():
    with pytest.raises(ValueError):
        normalize_restrictions(["keto"])


def test_food_tokenizer():
    words = recipe_food_words(
        "Chicken-Rice",
        ["green onion"],
    )

    assert "chicken" in words
    assert "rice" in words
    assert "onion" in words


def test_vegetarian_removes_meat():
    result = filter_by_restrictions(
        make_catalog(),
        ["vegetariano"],
    )

    names = result["nombre_receta"].tolist()

    assert "Chicken Rice" not in names
    assert "Vegetable Rice" in names
    assert "Cheese Vegetable Rice" in names


def test_vegan_removes_meat_and_dairy():
    result = filter_by_restrictions(
        make_catalog(),
        ["vegano"],
    )

    names = result["nombre_receta"].tolist()

    assert "Chicken Rice" not in names
    assert "Cheese Vegetable Rice" not in names
    assert "Vegetable Rice" in names


def test_gluten_free_removes_obvious_gluten():
    result = filter_by_restrictions(
        make_catalog(),
        ["sin_gluten"],
    )

    names = result["nombre_receta"].tolist()

    assert "Wheat Pasta" not in names
    assert "Vegetable Rice" in names


def test_real_vegetarian_menu_has_no_meat_terms():
    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=None,
            personas=2,
            cadena="Walmart",
            restricciones=["vegetariano"],
        )
    )

    forbidden = {
        "chicken",
        "beef",
        "pork",
        "tuna",
        "salmon",
        "fish",
        "shrimp",
        "turkey",
    }

    for recipes in response.menu_semanal.values():
        for recipe in recipes:
            words = recipe_food_words(
                recipe.name,
                recipe.ingredients,
            )

            assert not (
                words & forbidden
            )


def test_real_vegan_menu_has_no_obvious_animal_products():
    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=None,
            personas=2,
            cadena="Soriana",
            restricciones=["vegano"],
        )
    )

    forbidden = {
        "chicken",
        "beef",
        "pork",
        "fish",
        "tuna",
        "shrimp",
        "milk",
        "cheese",
        "egg",
        "eggs",
        "butter",
        "cream",
        "yogurt",
    }

    for recipes in response.menu_semanal.values():
        for recipe in recipes:
            words = recipe_food_words(
                recipe.name,
                recipe.ingredients,
            )

            assert not (
                words & forbidden
            )


def test_combined_vegan_gluten_free_request():
    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=1000,
            personas=2,
            cadena="Chedraui",
            restricciones=[
                "vegano",
                "sin_gluten",
            ],
        )
    )

    assert response.menu_semanal
    assert (
        response.carrito_final.costo_total
        <= 1000
    )
