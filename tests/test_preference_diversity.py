from collections import Counter

from api.schemas import RecommendationRequest
from api.services.recommendation import (
    normalized_title_words,
    recipe_category,
    recommend,
    title_overlap,
)


def flatten_menu(response):
    return [
        recipe
        for recipes
        in response.menu_semanal.values()
        for recipe
        in recipes
    ]


def test_title_overlap_detects_similar_names():
    overlap = title_overlap(
        "Fluffy White Rice",
        "White Rice",
    )

    assert overlap > 0.5


def test_title_overlap_separates_different_meals():
    overlap = title_overlap(
        "Vegetable Rice",
        "Black Bean Sweet Potato Burgers",
    )

    assert overlap < 0.5


def test_title_normalization_removes_stopwords():
    words = normalized_title_words(
        "The Best Easy Rice"
    )

    assert "the" not in words
    assert "best" not in words
    assert "easy" not in words
    assert "rice" in words


def test_preference_menu_avoids_baby_food():
    response = recommend(
        RecommendationRequest(
            gustos="rice vegetables",
            presupuesto=1000,
            personas=2,
            cadena="Walmart",
            restricciones=[
                "vegetariano",
            ],
        )
    )

    names = [
        recipe.name.lower()
        for recipe
        in flatten_menu(response)
    ]

    assert all(
        "baby food" not in name
        for name in names
    )


def test_preference_menu_keeps_user_interest():
    response = recommend(
        RecommendationRequest(
            gustos="rice vegetables",
            presupuesto=1000,
            personas=2,
            cadena="Walmart",
            restricciones=[
                "vegetariano",
            ],
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

    assert (
        "rice" in text
        or "vegetable" in text
        or "vegetables" in text
    )


def test_preference_menu_has_some_category_diversity():
    response = recommend(
        RecommendationRequest(
            gustos="rice vegetables",
            presupuesto=1000,
            personas=2,
            cadena="Walmart",
            restricciones=[
                "vegetariano",
            ],
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

    assert len(counts) >= 3
    assert max(counts.values()) <= 3
