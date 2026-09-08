from pydantic import BaseModel

class SearchRequest(BaseModel):
    pantry: list[str] = []
    wants: list[str] = []
    budget: float | None = None
    max_calories: float | None = None
    limit: int = 20

class IngredientLine(BaseModel):
    canonical_id: str
    name_es: str
    grams: float | None = None
    cost: float = 0.0
    in_pantry: bool = False
    is_free: bool = False
    priced: bool = True

class RecipeResult(BaseModel):
    recipe_id: int
    name: str
    calories: float | None = None
    servings: int | None = None
    total_cost: float
    missing_cost: float
    coverage: float
    ingredients: list[IngredientLine]

class SearchResponse(BaseModel):
    results: list[RecipeResult]
    total_found: int
