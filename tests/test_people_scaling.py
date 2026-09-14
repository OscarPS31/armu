import pytest
from pydantic import ValidationError

from api.schemas import RecommendationRequest
from api.services.recommendation import (
    build_recipe_catalog,
    get_person_scale,
    load_recipe_prices,
    normalize_chain,
    recommend,
)


def test_person_scale():
    assert get_person_scale(1) == 0.5
    assert get_person_scale(2) == 1.0
    assert get_person_scale(4) == 2.0
    assert get_person_scale(6) == 3.0


def test_invalid_people_rejected():
    with pytest.raises(ValidationError):
        RecommendationRequest(
            personas=0
        )


def test_recipe_catalog_scales_cost():
    df = load_recipe_prices()
    chain = normalize_chain("Walmart")

    catalog_2 = build_recipe_catalog(
        df,
        chain,
        personas=2,
    )

    catalog_4 = build_recipe_catalog(
        df,
        chain,
        personas=4,
    )

    merged = catalog_2[
        [
            "id_receta",
            "precio_total_receta_mxn",
        ]
    ].merge(
        catalog_4[
            [
                "id_receta",
                "precio_total_receta_mxn",
            ]
        ],
        on="id_receta",
        suffixes=(
            "_2",
            "_4",
        ),
    )

    row = merged.iloc[0]

    assert row[
        "precio_total_receta_mxn_4"
    ] == pytest.approx(
        row[
            "precio_total_receta_mxn_2"
        ] * 2,
        abs=0.02,
    )


def test_cart_scales_with_people():
    request_2 = RecommendationRequest(
        gustos="",
        presupuesto=None,
        personas=2,
        cadena="Walmart",
    )

    request_4 = RecommendationRequest(
        gustos="",
        presupuesto=None,
        personas=4,
        cadena="Walmart",
    )

    response_2 = recommend(request_2)
    response_4 = recommend(request_4)

    assert response_2.carrito_final.costo_total > 0

    assert (
        response_4.carrito_final.costo_total
        == pytest.approx(
            response_2.carrito_final.costo_total * 2,
            abs=0.10,
        )
    )


def test_menu_reports_requested_servings():
    response = recommend(
        RecommendationRequest(
            gustos="chicken",
            presupuesto=1000,
            personas=4,
            cadena="Soriana",
        )
    )

    recipes = [
        recipe
        for recipes_for_day
        in response.menu_semanal.values()
        for recipe
        in recipes_for_day
    ]

    assert recipes

    assert all(
        recipe.servings == 4
        for recipe in recipes
    )
