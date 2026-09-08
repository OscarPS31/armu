from api.schemas import RecipeResult, IngredientLine

from api.schemas import RecipeResult, IngredientLine

RECIPES = [
    # ejemplo todo cuesta
    RecipeResult(
        recipe_id=38271, name="Arroz con pollo",
        calories=612, servings=4,
        total_cost=66.75, missing_cost=66.40, coverage=1.0,
        ingredients=[
            IngredientLine(canonical_id="carne_pollo", name_es="Pollo", grams=500, cost=44.50),
            IngredientLine(canonical_id="arroz", name_es="Arroz", grams=300, cost=12.30),
            IngredientLine(canonical_id="jitomate", name_es="Jitomate", grams=240, cost=5.80),
            IngredientLine(canonical_id="cebolla", name_es="Cebolla", grams=110, cost=2.50),
            IngredientLine(canonical_id="aceite", name_es="Aceite", grams=30, cost=1.30),
            IngredientLine(canonical_id="sal", name_es="Sal", grams=5, cost=0.35, is_free=True),
        ],
    ),
    # muchas cosas en alacena
    RecipeResult(
        recipe_id=14903, name="Frijoles refritos",
        calories=284, servings=4,
        total_cost=22.80, missing_cost=3.15, coverage=1.0,
        ingredients=[
            IngredientLine(canonical_id="frijol", name_es="Frijol", grams=400, cost=16.80, in_pantry=True),
            IngredientLine(canonical_id="cebolla", name_es="Cebolla", grams=110, cost=2.50, in_pantry=True),
            IngredientLine(canonical_id="aceite", name_es="Aceite", grams=45, cost=1.95),
            IngredientLine(canonical_id="ajo", name_es="Ajo", grams=9, cost=1.20),
            IngredientLine(canonical_id="sal", name_es="Sal", grams=5, cost=0.35, is_free=True),
        ],
    ),
    # muchos is_free
    RecipeResult(
        recipe_id=52118, name="Pollo al horno con especias",
        calories=498, servings=4,
        total_cost=85.23, missing_cost=83.60, coverage=1.0,
        ingredients=[
            IngredientLine(canonical_id="carne_pollo", name_es="Pollo", grams=800, cost=71.20),
            IngredientLine(canonical_id="papa", name_es="Papa", grams=500, cost=9.50),
            IngredientLine(canonical_id="ajo", name_es="Ajo", grams=12, cost=1.60),
            IngredientLine(canonical_id="aceite", name_es="Aceite", grams=30, cost=1.30),
            IngredientLine(canonical_id="pimienta", name_es="Pimienta", grams=3, cost=0.68, is_free=True),
            IngredientLine(canonical_id="oregano", name_es="Orégano", grams=2, cost=0.45, is_free=True),
            IngredientLine(canonical_id="sal", name_es="Sal", grams=6, cost=0.42, is_free=True),
            IngredientLine(canonical_id="laurel", name_es="Hoja de laurel", grams=0.4, cost=0.08, is_free=True),
        ],
    ),
    # ingrediente sin precio (canela)
    RecipeResult(
        recipe_id=9440, name="Arroz con leche",
        calories=356, servings=6,
        total_cost=37.50, missing_cost=37.50, coverage=0.75,
        ingredients=[
            IngredientLine(canonical_id="leche", name_es="Leche", grams=1000, cost=24.50),
            IngredientLine(canonical_id="azucar", name_es="Azúcar", grams=150, cost=4.80),
            IngredientLine(canonical_id="arroz", name_es="Arroz", grams=200, cost=8.20),
            IngredientLine(canonical_id="canela", name_es="Canela", grams=3, cost=0.0, priced=False),
        ],
    ),
    # costo total muy alto
    RecipeResult(
        recipe_id=71265, name="Camarones al ajillo",
        calories=430, servings=4,
        total_cost=272.58, missing_cost=272.30, coverage=1.0,
        ingredients=[
            IngredientLine(canonical_id="camaron", name_es="Camarón", grams=600, cost=258.00),
            IngredientLine(canonical_id="limon", name_es="Limón", grams=120, cost=4.50),
            IngredientLine(canonical_id="ajo", name_es="Ajo", grams=30, cost=4.00),
            IngredientLine(canonical_id="chile_seco", name_es="Chile seco", grams=8, cost=3.20),
            IngredientLine(canonical_id="aceite", name_es="Aceite", grams=60, cost=2.60),
            IngredientLine(canonical_id="sal", name_es="Sal", grams=4, cost=0.28, is_free=True),
        ],
    ),
]
