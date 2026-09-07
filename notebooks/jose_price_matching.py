import pandas as pd


# ============================================================
# 1. LOAD RECIPES
# ============================================================

recipes = pd.read_csv(
    "raw_data/recipes.csv",
    usecols=[
        "RecipeId",
        "Name",
        "RecipeIngredientParts",
    ],
    nrows=5000,
)


def parse_ingredients(value):
    """
    Convert Food.com ingredient vectors like:

    c("salt", "butter", "onion")

    into a Python list.
    """

    if pd.isna(value):
        return []

    value = str(value)

    if value.startswith("c("):
        value = value[2:-1]

    value = value.replace('"', "")

    return [
        ingredient.strip().lower()
        for ingredient in value.split(",")
        if ingredient.strip()
    ]


recipes["ingredients"] = recipes[
    "RecipeIngredientParts"
].apply(parse_ingredients)


# ============================================================
# 2. GET MOST COMMON INGREDIENTS
# ============================================================

ingredients = (
    recipes["ingredients"]
    .explode()
    .dropna()
    .value_counts()
    .reset_index()
)

ingredients.columns = [
    "ingredient",
    "count",
]


print("\n=== MOST COMMON INGREDIENTS ===")

print(
    ingredients
    .head(30)
    .to_string(index=False)
)


# ============================================================
# 3. LOAD PROFECO PRICES
# ============================================================

prices = pd.read_csv(
    "raw_data/07-2026_Q2.csv",
    usecols=[
        "producto",
        "presentacion",
        "marca",
        "categoria",
        "precio",
        "cadena_comercial",
        "estado",
        "municipio",
    ],
)


# Normalize PROFECO product names
prices["producto_normalized"] = (
    prices["producto"]
    .astype(str)
    .str.lower()
    .str.strip()
)


# ============================================================
# 4. INGREDIENT TRANSLATION / NORMALIZATION MAP
# ============================================================

ingredient_map = {

    # --------------------------------------------------------
    # BASIC INGREDIENTS
    # --------------------------------------------------------

    "salt": "sal",

    "sugar": "azúcar",
    "brown sugar": "azúcar",
    "granulated sugar": "azúcar",
    "powdered sugar": "azúcar",
    "confectioners' sugar": "azúcar",
    "light brown sugar": "azúcar",

    "butter": "mantequilla",
    "unsalted butter": "mantequilla",

    "margarine": "margarina",

    "eggs": "huevo",
    "egg": "huevo",

    "flour": "harina",
    "all-purpose flour": "harina",
    "unbleached flour": "harina",

    "milk": "leche",
    "evaporated milk": "leche evaporada",
    "buttermilk": "leche",

    # --------------------------------------------------------
    # VEGETABLES
    # --------------------------------------------------------

    "onion": "cebolla",
    "onions": "cebolla",

    "green onion": "cebolla",
    "green onions": "cebolla",

    "garlic": "ajo",
    "garlic cloves": "ajo",
    "garlic clove": "ajo",
    "garlic powder": "ajo",

    "tomato": "jitomate",
    "tomatoes": "jitomate",
    "tomato sauce": "jitomate",
    "tomato paste": "jitomate",

    "celery": "apio",

    "carrot": "zanahoria",
    "carrots": "zanahoria",

    "green pepper": "chile",

    "zucchini": "calabaza",

    "mushrooms": "champiñones",
    "mushroom": "champiñones",

    "potatoes": "papa",

    "broccoli": "brócoli",

    "spinach": "espinacas",

    "cilantro": "cilantro",

    "parsley": "perejil",
    "fresh parsley": "perejil",

    # --------------------------------------------------------
    # HERBS / SPICES
    # --------------------------------------------------------

    "pepper": "pimienta",
    "black pepper": "pimienta",
    "white pepper": "pimienta",

    "cinnamon": "canela",

    "nutmeg": "nuez moscada",

    "paprika": "paprika",

    "ginger": "jengibre",

    "oregano": "orégano",

    "cumin": "comino",

    "cayenne pepper": "chile",
    "chili powder": "chile",

    "thyme": "tomillo",

    "basil": "albahaca",

    "bay leaf": "laurel",

    "clove": "clavo",

    "allspice": "pimienta",

    # --------------------------------------------------------
    # OILS / SAUCES
    # --------------------------------------------------------

    "olive oil": "aceite de oliva",

    "soy sauce": "salsa de soya",

    "worcestershire sauce": "salsa inglesa",

    "mayonnaise": "mayonesa",

    "vinegar": "vinagre",
    "cider vinegar": "vinagre",

    "tabasco sauce": "salsa",

    # --------------------------------------------------------
    # DAIRY
    # --------------------------------------------------------

    "sour cream": "crema",

    "cream cheese": "queso crema",

    "parmesan cheese": "queso parmesano",

    "cheddar cheese": "queso cheddar",

    "mozzarella cheese": "queso mozzarella",

    "heavy cream": "crema",

    # --------------------------------------------------------
    # FRUITS
    # --------------------------------------------------------

    "lemon": "limón",
    "lemons": "limón",

    "lemon juice": "limón",
    "fresh lemon juice": "limón",

    "lime juice": "limón",

    "orange": "naranja",
    "oranges": "naranja",

    "apples": "manzana",

    "strawberry": "fresa",
    "strawberries": "fresa",

    "raisins": "pasas",

    "coconut": "coco",

    "avocado": "aguacate",
    "avocados": "aguacate",

    # --------------------------------------------------------
    # NUTS
    # --------------------------------------------------------

    "pecans": "nuez",
    "walnuts": "nuez",

    # --------------------------------------------------------
    # PROTEINS
    # --------------------------------------------------------

    "chicken": "pollo",

    "bacon": "tocino",

    "beef": "carne",

    # --------------------------------------------------------
    # PANTRY
    # --------------------------------------------------------

    "rice": "arroz",

    "cornstarch": "fécula",

    "baking powder": "polvo para hornear",

    "baking soda": "bicarbonato",

    "vanilla": "vainilla",

    "vanilla extract": "vainilla",

    "honey": "miel",

    "dry mustard": "mostaza",

    "dijon mustard": "mostaza",

    "chicken broth": "caldo de pollo",
}


# ============================================================
# 5. MATCH INGREDIENTS WITH PROFECO PRODUCTS
# ============================================================

results = []

for ingredient, spanish_product in ingredient_map.items():

    matches = prices[
        prices["producto_normalized"].str.contains(
            spanish_product,
            case=False,
            na=False,
            regex=False,
        )
    ]

    if len(matches) > 0:

        results.append(
            {
                "ingredient": ingredient,
                "profeco_product": spanish_product,
                "matches": len(matches),
                "min_price": matches["precio"].min(),
                "median_price": matches["precio"].median(),
                "max_price": matches["precio"].max(),
            }
        )


results = pd.DataFrame(results)


# ============================================================
# 6. SHOW PRICE MATCHING RESULTS
# ============================================================

print("\n=== MATCHING RESULTS ===")

if len(results) > 0:

    print(
        results
        .sort_values(
            by="matches",
            ascending=False,
        )
        .to_string(index=False)
    )

else:

    print("No matches found.")


# ============================================================
# 7. TOP 100 INGREDIENT COVERAGE
# ============================================================

top_ingredients = ingredients.head(100).copy()

top_ingredients["mapped"] = (
    top_ingredients["ingredient"]
    .isin(ingredient_map.keys())
)


print("\n=== TOP 100 COVERAGE ===")

coverage_counts = (
    top_ingredients["mapped"]
    .value_counts()
)

print(coverage_counts)


mapped_count = top_ingredients["mapped"].sum()

coverage_percent = (
    mapped_count
    / len(top_ingredients)
    * 100
)


print(
    f"\nMapped ingredients: "
    f"{mapped_count}/100"
)

print(
    f"Coverage: "
    f"{coverage_percent:.1f}%"
)


# ============================================================
# 8. SHOW MAPPED INGREDIENTS
# ============================================================

print("\n=== MAPPED COMMON INGREDIENTS ===")

mapped = top_ingredients[
    top_ingredients["mapped"]
].copy()

mapped["profeco_product"] = (
    mapped["ingredient"]
    .map(ingredient_map)
)

print(
    mapped[
        [
            "ingredient",
            "profeco_product",
            "count",
        ]
    ]
    .to_string(index=False)
)


# ============================================================
# 9. SHOW INGREDIENTS THAT STILL NEED MATCHING
# ============================================================

print("\n=== UNMAPPED COMMON INGREDIENTS ===")

unmapped = top_ingredients[
    ~top_ingredients["mapped"]
]

print(
    unmapped[
        [
            "ingredient",
            "count",
        ]
    ]
    .to_string(index=False)
)


# ============================================================
# 10. SAVE RESULTS
# ============================================================

results.to_csv(
    "notebooks/jose_price_matching_results.csv",
    index=False,
)

top_ingredients.to_csv(
    "notebooks/jose_top100_ingredient_coverage.csv",
    index=False,
)


print("\n=== FILES CREATED ===")

print(
    "notebooks/"
    "jose_price_matching_results.csv"
)

print(
    "notebooks/"
    "jose_top100_ingredient_coverage.csv"
)
