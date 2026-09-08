from api.fixtures import RECIPES
from api.schemas import SearchRequest, SearchResponse

def search_recipes(request: SearchRequest) -> SearchResponse:
    total_found = len(RECIPES)
    total_shown = RECIPES[:request.limit]
    return SearchResponse(results=total_shown, total_found=total_found)
