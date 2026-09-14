from fastapi import APIRouter, HTTPException

from api.schemas import (
    RecommendationRequest,
    RecommendationResponse,
)
from api.services.price_comparison import (
    compare_recipe_prices,
)
from api.services.recommendation import recommend


router = APIRouter()


@router.post(
    "/recomendacion",
    response_model=RecommendationResponse,
)
def recomendacion(
    request: RecommendationRequest,
) -> RecommendationResponse:
    return recommend(request)


@router.get("/comparar-precios/{id_receta}")
def comparar_precios(id_receta: int) -> dict:
    try:
        return compare_recipe_prices(id_receta)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
