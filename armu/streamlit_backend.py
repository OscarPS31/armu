from __future__ import annotations

from typing import Any

from api.schemas import RecommendationRequest
from api.services.options import get_recommendation_options
from api.services.price_comparison import compare_recipe_prices
from api.services.recommendation import recommend


def model_to_dict(model: Any) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


def get_streamlit_options() -> dict:
    options = get_recommendation_options()

    return model_to_dict(options)


def generate_streamlit_plan(
    gustos: str,
    presupuesto: float | None,
    personas: int,
    cadena: str,
    restricciones: list[str] | None = None,
) -> dict:
    request = RecommendationRequest(
        gustos=gustos,
        presupuesto=presupuesto,
        personas=personas,
        cadena=cadena,
        restricciones=restricciones or [],
    )

    response = recommend(request)

    return model_to_dict(response)


def compare_recipe_for_streamlit(
    recipe_id: int,
) -> dict:
    return compare_recipe_prices(
        recipe_id
    )
