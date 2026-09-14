from api.schemas import RecommendationRequest
from api.services.recommendation import (
    DAYS,
    load_recipe_prices,
    normalize_chain,
    recommend,
)


def test_dataset_loads():
    df = load_recipe_prices()

    assert not df.empty
    assert df["id_receta"].nunique() > 0

    assert {
        "Walmart",
        "Soriana",
        "Chedraui",
    }.issubset(
        set(df["cadena"].unique())
    )


def test_chain_normalization():
    assert normalize_chain("walmart") == "Walmart"
    assert normalize_chain("SORiana") == "Soriana"
    assert normalize_chain("chedraui") == "Chedraui"


def test_real_recommendation():
    request = RecommendationRequest(
        gustos="chicken tomato onion",
        presupuesto=800,
        personas=2,
        cadena="Walmart",
    )

    response = recommend(request)

    assert set(
        response.menu_semanal.keys()
    ) == set(DAYS)

    assert (
        response.carrito_final.costo_total
        <= 800
    )


def test_three_chains_work():
    for chain in [
        "Walmart",
        "Soriana",
        "Chedraui",
    ]:
        response = recommend(
            RecommendationRequest(
                gustos="chicken",
                presupuesto=800,
                cadena=chain,
            )
        )

        assert (
            response.carrito_final.costo_total
            <= 800
        )
