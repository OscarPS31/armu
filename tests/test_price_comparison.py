from fastapi.testclient import TestClient

from api.main import app
from api.services.price_comparison import (
    compare_recipe_prices,
    load_price_data,
)


client = TestClient(app)


def get_example_recipe_id() -> int:
    df = load_price_data()

    return int(
        df["id_receta"].dropna().iloc[0]
    )


def test_compare_recipe_prices():
    recipe_id = get_example_recipe_id()

    result = compare_recipe_prices(recipe_id)

    assert result["id_receta"] == recipe_id
    assert result["nombre_receta"]
    assert len(result["comparacion"]) == 3

    chains = {
        item["cadena"]
        for item in result["comparacion"]
    }

    assert chains == {
        "Walmart",
        "Soriana",
        "Chedraui",
    }

    assert (
        result["precio_mas_barato_mxn"]
        <= result["precio_mas_caro_mxn"]
    )

    assert result["ahorro_mxn"] >= 0


def test_comparison_is_sorted():
    recipe_id = get_example_recipe_id()

    result = compare_recipe_prices(recipe_id)

    prices = [
        item["precio_total_mxn"]
        for item in result["comparacion"]
    ]

    assert prices == sorted(prices)


def test_price_comparison_endpoint():
    recipe_id = get_example_recipe_id()

    response = client.get(
        f"/comparar-precios/{recipe_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id_receta"] == recipe_id
    assert len(data["comparacion"]) == 3


def test_missing_recipe_returns_404():
    response = client.get(
        "/comparar-precios/999999999"
    )

    assert response.status_code == 404


def test_price_comparison_decodes_html_entities():
    result = compare_recipe_prices(
        362769
    )

    assert "&amp;" not in result[
        "nombre_receta"
    ]

    assert "&" in result[
        "nombre_receta"
    ]
