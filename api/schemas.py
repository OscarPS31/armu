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
    cost: float
    in_pantry: bool = False
    is_free: bool = False
    priced: bool = True

class RecipeResult(BaseModel):
    recipe_id: int
    name: str
    calories: float | None = None
    servings: int | None = None
    total_cost: float #precio que cuesta la receta completa
    missing_cost: float #precio que se va a gastar el cliente (descontar cuando in_pantry/is_free = True)
    coverage: float
    ingredients: list[IngredientLine]

class SearchResponse(BaseModel):
    results: list[RecipeResult]
    total_found: int
