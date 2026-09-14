from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_frontend_contract_end_to_end():
    options_response = client.get(
        "/opciones"
    )

    assert options_response.status_code == 200

    options = options_response.json()

    assert options["cadenas"] == [
        "Walmart",
        "Soriana",
        "Chedraui",
    ]

    assert options["restricciones"] == [
        "vegetariano",
        "vegano",
        "sin_gluten",
    ]

    assert options["personas_min"] == 1
    assert options["personas_max"] == 20

    recommendation_response = client.post(
        "/recomendacion",
        json={
            "gustos": "rice vegetables",
            "presupuesto": 1000,
            "personas": 2,
            "cadena": "Walmart",
            "restricciones": [
                "vegetariano",
            ],
        },
    )

    assert (
        recommendation_response.status_code
        == 200
    )

    recommendation = (
        recommendation_response.json()
    )

    assert "menu_semanal" in recommendation
    assert "carrito_final" in recommendation
    assert "mensaje" in recommendation

    recipe_ids = [
        recipe["id"]
        for recipes
        in recommendation[
            "menu_semanal"
        ].values()
        for recipe
        in recipes
    ]

    assert recipe_ids

    assert (
        recommendation[
            "carrito_final"
        ][
            "costo_total"
        ]
        <= 1000
    )

    recipe_id = recipe_ids[0]

    comparison_response = client.get(
        f"/comparar-precios/{recipe_id}"
    )

    assert (
        comparison_response.status_code
        == 200
    )

    comparison = (
        comparison_response.json()
    )

    assert (
        comparison["id_receta"]
        == recipe_id
    )

    assert comparison[
        "cadena_mas_barata"
    ] in {
        "Walmart",
        "Soriana",
        "Chedraui",
    }

    chains = {
        item["cadena"]
        for item
        in comparison["comparacion"]
    }

    assert chains == {
        "Walmart",
        "Soriana",
        "Chedraui",
    }


def test_frontend_rejects_invalid_people():
    response = client.post(
        "/recomendacion",
        json={
            "gustos": "",
            "personas": 0,
            "cadena": "Walmart",
            "restricciones": [],
        },
    )

    assert response.status_code == 422


def test_price_comparison_unknown_recipe_returns_404():
    response = client.get(
        "/comparar-precios/999999999"
    )

    assert response.status_code == 404
