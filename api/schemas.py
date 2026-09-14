from pydantic import BaseModel, Field


class Recipe(BaseModel):
    id: int
    name: str
    servings: int | None = None
    serving_size: str | None = None
    ingredients: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_vegan: bool = False
    is_vegetarian: bool = False
    is_gluten_free: bool = False


class CartItem(BaseModel):
    ingrediente: str
    cantidad: float
    unidad: str | None = None
    costo: float


class Cart(BaseModel):
    items: list[CartItem] = Field(default_factory=list)
    costo_total: float = 0.0
    dentro_de_presupuesto: bool = True
    ingredientes_sin_precio: list[str] = Field(default_factory=list)
    items_retirados: list[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    gustos: str = ""
    presupuesto: float | None = None
    personas: int = 2
    cadena: str = "Walmart"


class RecommendationResponse(BaseModel):
    menu_semanal: dict[str, list[Recipe]]
    carrito_final: Cart
    mensaje: str | None = None
