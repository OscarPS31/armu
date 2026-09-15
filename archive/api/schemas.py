from pydantic import BaseModel

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
