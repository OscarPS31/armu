from fastapi import APIRouter
from api.schemas import SearchRequest, SearchResponse
from api.services.search import search_recipes

router = APIRouter()

@router.post('/recipes/search', response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    return search_recipes(request)
