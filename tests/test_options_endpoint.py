from fastapi.testclient import TestClient

from api.main import app
from api.services.options import (
    get_recommendation_options,
)


client = TestClient(app)


def test_options_service():
    options = get_recommendation_options()

    assert options.cadenas == [
        "Walmart",
        "Soriana",
        "Chedraui",
    ]

    assert options.restricciones == [
        "vegetariano",
        "vegano",
        "sin_gluten",
    ]

    assert options.personas_min == 1
    assert options.personas_max == 20


def test_options_endpoint():
    response = client.get(
        "/opciones"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["cadenas"] == [
        "Walmart",
        "Soriana",
        "Chedraui",
    ]

    assert data["restricciones"] == [
        "vegetariano",
        "vegano",
        "sin_gluten",
    ]

    assert data["personas_min"] == 1
    assert data["personas_max"] == 20
