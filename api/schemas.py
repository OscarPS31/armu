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


class Recipe(BaseModel):
    id: int
    name: str
    servings: int | None = None
    serving_size: str | None = None
    ingredients: list[str] = []
    steps: list[str] = []
    tags: list[str] = []
    is_vegan: bool = False
    is_vegetarian: bool = False
    is_gluten_free: bool = False


class CartItem(BaseModel):
    ingrediente: str
    cantidad: float
    costo: float


class Cart(BaseModel):
    items: list[CartItem] = []
    costo_total: float = 0.0
    dentro_de_presupuesto: bool = True
    ingredientes_sin_precio: list[str] = []
    items_retirados: list[str] = []


class RecommendationRequest(BaseModel):
    gustos: str = ""
    presupuesto: float | None = None
    personas: int = 2


class RecommendationResponse(BaseModel):
    menu_semanal: dict[str, list[Recipe]]
    carrito_final: Cart
    mensaje: str | None = None
