from collections import Counter

from api.schemas import RecommendationRequest
from api.services.recommendation import (
    load_recipe_prices,
    recipe_category,
    recommend,
)


def flatten_menu(response):
    return [
        recipe
        for recipes
        in response.menu_semanal.values()
        for recipe
        in recipes
    ]


def test_html_entities_are_decoded():
    df = load_recipe_prices()

    names = (
        df["nombre_receta"]
        .astype(str)
        .tolist()
    )

    assert all(
        "&amp;" not in name
        for name in names
    )


def test_recipe_categories():
    assert (
        recipe_category(
            "Chicken Pasta",
            [
                "chicken",
                "pasta",
                "tomato",
            ],
        )
        == "poultry"
    )

    assert (
        recipe_category(
            "Tuna Rice Casserole",
            [
                "tuna",
                "rice",
            ],
        )
        == "fish"
    )

    assert (
        recipe_category(
            "Beef Stew",
            [
                "beef",
                "potato",
            ],
        )
        == "beef"
    )


def test_default_menu_has_category_diversity():
    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=None,
            personas=2,
            cadena="Walmart",
        )
    )

    recipes = flatten_menu(
        response
    )

    assert len(recipes) == 7

    categories = [
        recipe_category(
            recipe.name,
            recipe.ingredients,
        )
        for recipe in recipes
    ]

    counts = Counter(
        categories
    )

    assert len(counts) >= 4

    assert max(
        counts.values()
    ) <= 2


def test_explicit_preferences_still_work():
    response = recommend(
        RecommendationRequest(
            gustos="chicken",
            presupuesto=None,
            personas=2,
            cadena="Walmart",
        )
    )

    recipes = flatten_menu(
        response
    )

    text = " ".join(
        (
            recipe.name
            + " "
            + " ".join(
                recipe.ingredients
            )
        ).lower()
        for recipe in recipes
    )

    assert "chicken" in text


def test_default_menu_names_are_clean():
    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=None,
            personas=2,
            cadena="Walmart",
        )
    )

    recipes = flatten_menu(
        response
    )

    assert all(
        "&amp;" not in recipe.name
        for recipe in recipes
    )
