from fastapi import APIRouter
from api.schemas import RecommendationRequest, RecommendationResponse
from api.services.recommendation import recommend


router = APIRouter()

@router.post("/recomendacion", response_model=RecommendationResponse)
def recomendacion(request: RecommendationRequest) -> RecommendationResponse:
    return recommend(request)
