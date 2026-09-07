import pandas as pd
import unicodedata


# ============================================================
# 1. HELPERS
# ============================================================

def normalize_text(value):
    if pd.isna(value):
        return ""

    value = str(value).lower().strip()

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    return " ".join(value.split())


def parse_foodcom_vector(value):
    if pd.isna(value):
        return []

    value = str(value).strip()

    if value.startswith("c("):
        value = value[2:-1]

    value = value.replace('"', "")

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# 2. INGREDIENT NORMALIZATION
# ============================================================

ingredient_aliases = {
    "real vanilla": "vanilla",
    "pure vanilla": "vanilla",
    "vanilla extract": "vanilla",

    "garlic cloves": "garlic",
    "garlic clove": "garlic",

    "tomatoes": "tomato",
    "onions": "onion",
    "eggs": "egg",
    "lemons": "lemon",

    "unsalted butter": "butter",

    # NEW
    "roast beef": "beef",
}


def normalize_ingredient(value):
    value = normalize_text(value)

    return ingredient_aliases.get(
        value,
        value,
    )


# ============================================================
# 3. INGREDIENT -> PROFECO RULES
# ============================================================

ingredient_rules = {
    "salt": ["sal"],
    "sugar": ["azucar"],
    "butter": ["mantequilla"],
    "margarine": ["margarina"],

    "egg": ["huevo"],
    "flour": ["harina"],
    "milk": ["leche"],

    "onion": ["cebolla"],
    "garlic": ["ajo"],
    "tomato": ["jitomate"],

    "carrot": ["zanahoria"],
    "celery": ["apio"],
    "potatoes": ["papa"],
    "zucchini": ["calabaza"],

    "mushroom": ["champinones"],
    "mushrooms": ["champinones"],

    "olive oil": ["aceite de oliva"],
    "vinegar": ["vinagre"],
    "soy sauce": ["salsa de soya"],
    "mayonnaise": ["mayonesa"],

    "lemon": ["limon"],
    "orange": ["naranja"],
    "apples": ["manzana"],

    "chicken": ["carne pollo"],
    "beef": ["carne res"],
    "bacon": ["tocino"],

    "rice": ["arroz"],
    "honey": ["miel"],
    "vanilla": ["vainilla"],

    "cream cheese": ["queso crema"],
}


# ============================================================
# 4. LOAD RECIPES
# ============================================================

recipes = pd.read_csv(
    "raw_data/recipes.csv",
    usecols=[
        "RecipeId",
        "Name",
        "RecipeCategory",
        "RecipeIngredientParts",
        "Calories",
        "ProteinContent",
        "CarbohydrateContent",
        "FatContent",
        "AggregatedRating",
        "ReviewCount",
    ],
)


recipes["ingredients"] = (
    recipes["RecipeIngredientParts"]
    .apply(parse_foodcom_vector)
)


# ============================================================
# 5. LOAD PROFECO
# ============================================================

prices = pd.read_csv(
    "raw_data/07-2026_Q2.csv",
    usecols=[
        "producto",
        "presentacion",
        "categoria",
        "precio",
        "cadena_comercial",
        "estado",
        "municipio",
    ],
)


for column in [
    "producto",
    "presentacion",
    "categoria",
]:

    prices[f"{column}_normalized"] = (
        prices[column]
        .apply(normalize_text)
    )


prices["search_text"] = (
    prices["producto_normalized"]
    + " "
    + prices["presentacion_normalized"]
    + " "
    + prices["categoria_normalized"]
)


# ============================================================
# 6. PRICE MATCHING
# ============================================================

price_cache = {}


def find_price(ingredient):
    ingredient = normalize_ingredient(
        ingredient
    )

    if ingredient in price_cache:
        return price_cache[ingredient]

    if ingredient not in ingredient_rules:
        price_cache[ingredient] = None
        return None

    for term in ingredient_rules[ingredient]:

        term = normalize_text(term)

        matches = prices[
            prices["search_text"].str.contains(
                term,
                na=False,
                regex=False,
            )
        ]

        if matches.empty:
            continue

        result = {
            "ingredient": ingredient,
            "matched_term": term,
            "median_price":
                matches["precio"].median(),
        }

        price_cache[ingredient] = result

        return result

    price_cache[ingredient] = None

    return None


# ============================================================
# 7. RECIPE COVERAGE
# ============================================================

ignored_ingredients = {
    "water",
    "boiling water",
}


def recipe_coverage(ingredient_list):

    useful = []

    for ingredient in ingredient_list:

        ingredient = normalize_ingredient(
            ingredient
        )

        if ingredient in ignored_ingredients:
            continue

        useful.append(ingredient)

    if not useful:
        return 0.0

    matched = sum(
        ingredient in ingredient_rules
        for ingredient in useful
    )

    return matched / len(useful)


recipes["coverage"] = (
    recipes["ingredients"]
    .apply(recipe_coverage)
)


recipes["ingredient_count"] = (
    recipes["ingredients"]
    .apply(len)
)


# ============================================================
# 8. REMOVE CATEGORIES WE DON'T WANT
# ============================================================

excluded_categories = {
    "Dessert",
    "Pie",
    "Beverages",
    "Candy",
    "Bar Cookie",
    "Cookies",
    "Quick Breads",
}


recipes = recipes[
    ~recipes["RecipeCategory"]
    .isin(excluded_categories)
].copy()


# ============================================================
# 9. BASIC NUTRITION FILTER
# ============================================================

candidates = recipes[
    (recipes["coverage"] >= 0.70)
    &
    (recipes["ingredient_count"].between(4, 12))
    &
    (recipes["Calories"].between(250, 750))
    &
    (recipes["ProteinContent"] >= 10)
].copy()


# ============================================================
# 10. SCORING
# ============================================================

candidates["rating_safe"] = (
    candidates["AggregatedRating"]
    .fillna(0)
)


candidates["reviews_safe"] = (
    candidates["ReviewCount"]
    .fillna(0)
)


candidates["protein_score"] = (
    candidates["ProteinContent"]
    .clip(upper=50)
    / 50
)


candidates["rating_score"] = (
    candidates["rating_safe"]
    / 5
)


candidates["coverage_score"] = (
    candidates["coverage"]
)


candidates["score"] = (
    candidates["coverage_score"] * 0.40
    +
    candidates["protein_score"] * 0.35
    +
    candidates["rating_score"] * 0.25
)


# ============================================================
# 11. SELECT DIFFERENT CATEGORIES
# ============================================================

candidates = candidates.sort_values(
    by="score",
    ascending=False,
)


weekly_rows = []

used_categories = set()


for _, recipe in candidates.iterrows():

    category = recipe[
        "RecipeCategory"
    ]

    if category in used_categories:
        continue

    weekly_rows.append(
        recipe
    )

    used_categories.add(
        category
    )

    if len(weekly_rows) == 5:
        break


if len(weekly_rows) < 5:
    raise ValueError(
        "Could not find 5 diverse recipes."
    )


weekly_recipes = pd.DataFrame(
    weekly_rows
)


# ============================================================
# 12. UNIQUE INGREDIENTS
# ============================================================

all_ingredients = []


for _, recipe in weekly_recipes.iterrows():

    for ingredient in recipe["ingredients"]:

        ingredient = normalize_ingredient(
            ingredient
        )

        if ingredient in ignored_ingredients:
            continue

        all_ingredients.append(
            ingredient
        )


unique_ingredients = sorted(
    set(all_ingredients)
)


# ============================================================
# 13. SHOPPING CART
# ============================================================

cart_rows = []

cart_total = 0.0


for ingredient in unique_ingredients:

    price_info = find_price(
        ingredient
    )

    if price_info is None:

        cart_rows.append(
            {
                "ingredient": ingredient,
                "matched_term": None,
                "median_price": None,
                "status": "UNMATCHED",
            }
        )

        continue


    price = price_info[
        "median_price"
    ]

    cart_total += price


    cart_rows.append(
        {
            "ingredient":
                ingredient,

            "matched_term":
                price_info[
                    "matched_term"
                ],

            "median_price":
                price,

            "status":
                "MATCHED",
        }
    )


cart = pd.DataFrame(
    cart_rows
)


# ============================================================
# 14. BUDGET
# ============================================================

weekly_budget = 800.0

remaining = (
    weekly_budget
    - cart_total
)


# ============================================================
# 15. WEEKLY MENU OUTPUT
# ============================================================

print("\n" + "=" * 70)

print(
    "NUTRIPLAN — BALANCED WEEKLY MENU"
)

print("=" * 70)


print("\n=== WEEKLY MENU ===")


for index, (_, recipe) in enumerate(
    weekly_recipes.iterrows(),
    start=1,
):

    print(
        f"\n{index}. "
        f"{recipe['Name']}"
    )

    print(
        f"   Category: "
        f"{recipe['RecipeCategory']}"
    )

    print(
        f"   Calories: "
        f"{recipe['Calories']:.1f}"
    )

    print(
        f"   Protein: "
        f"{recipe['ProteinContent']:.1f} g"
    )

    print(
        f"   Coverage: "
        f"{recipe['coverage']:.1%}"
    )

    print(
        f"   Recommendation score: "
        f"{recipe['score']:.3f}"
    )


# ============================================================
# 16. SHOPPING CART OUTPUT
# ============================================================

print(
    "\n=== SHOPPING CART ==="
)


print(
    cart[
        [
            "ingredient",
            "matched_term",
            "median_price",
            "status",
        ]
    ]
    .to_string(
        index=False
    )
)


# ============================================================
# 17. SUMMARY
# ============================================================

matched = (
    cart["status"]
    .eq("MATCHED")
    .sum()
)


print(
    "\n=== SUMMARY ==="
)

print(
    f"Recipes selected: "
    f"{len(weekly_recipes)}"
)

print(
    f"Unique categories: "
    f"{weekly_recipes['RecipeCategory'].nunique()}"
)

print(
    f"Unique ingredients: "
    f"{len(cart)}"
)

print(
    f"Matched products: "
    f"{matched}/{len(cart)}"
)

print(
    f"Estimated cart total: "
    f"${cart_total:.2f} MXN"
)

print(
    f"Weekly budget: "
    f"${weekly_budget:.2f} MXN"
)

print(
    f"Remaining budget: "
    f"${remaining:.2f} MXN"
)


if remaining >= 0:

    print(
        "\n✅ WITHIN BUDGET"
    )

else:

    print(
        "\n❌ OVER BUDGET"
    )


# ============================================================
# 18. NUTRITION SUMMARY
# ============================================================

print(
    "\n=== NUTRITION SUMMARY ==="
)

print(
    f"Average calories: "
    f"{weekly_recipes['Calories'].mean():.1f}"
)

print(
    f"Average protein: "
    f"{weekly_recipes['ProteinContent'].mean():.1f} g"
)

print(
    f"Average carbs: "
    f"{weekly_recipes['CarbohydrateContent'].mean():.1f} g"
)

print(
    f"Average fat: "
    f"{weekly_recipes['FatContent'].mean():.1f} g"
)


# ============================================================
# 19. SAVE
# ============================================================

weekly_recipes[
    [
        "RecipeId",
        "Name",
        "RecipeCategory",
        "Calories",
        "ProteinContent",
        "CarbohydrateContent",
        "FatContent",
        "coverage",
        "score",
    ]
].to_csv(
    "notebooks/"
    "jose_balanced_weekly_menu.csv",
    index=False,
)


cart.to_csv(
    "notebooks/"
    "jose_balanced_weekly_cart.csv",
    index=False,
)


print(
    "\nFiles saved."
)
