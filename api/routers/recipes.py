from fastapi import APIRouter
from api.schemas import SearchRequest, SearchResponse, RecommendationRequest, RecommendationResponse
from api.services.search import search_recipes
from api.services.recommendation import recommend


router = APIRouter()

@router.post('/recipes/search', response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    return search_recipes(request)

@router.post("/recomendacion", response_model=RecommendationResponse)
def recomendacion(request: RecommendationRequest) -> RecommendationResponse:
    return recommend(request)
