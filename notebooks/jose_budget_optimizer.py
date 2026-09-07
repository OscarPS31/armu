import pandas as pd
import unicodedata


# ============================================================
# 1. CONFIG
# ============================================================

WEEKLY_BUDGET = 800.0
RECIPES_NEEDED = 5


# ============================================================
# 2. HELPERS
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
# 3. INGREDIENT NORMALIZATION
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

    "roast beef": "beef",
}


def normalize_ingredient(value):
    value = normalize_text(value)

    return ingredient_aliases.get(
        value,
        value,
    )


# ============================================================
# 4. INGREDIENT -> PROFECO RULES
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
# 5. IGNORED / FORBIDDEN INGREDIENTS
# ============================================================

ignored_ingredients = {
    "water",
    "boiling water",
}


forbidden_ingredients = {
    "beer",
    "wine",
    "white wine",
    "red wine",
    "dry white wine",
    "brandy",
    "rum",
    "vodka",
    "whiskey",
    "whisky",
    "bourbon",
    "sherry",
    "marsala",
    "liqueur",
    "tequila",
    "cognac",
    "vermouth",
}


def has_forbidden_ingredient(ingredient_list):
    normalized = {
        normalize_ingredient(x)
        for x in ingredient_list
    }

    return any(
        ingredient in forbidden_ingredients
        for ingredient in normalized
    )


# ============================================================
# 6. LOAD RECIPES
# ============================================================

print("Loading recipes...")

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
# 7. LOAD PROFECO
# ============================================================

print("Loading PROFECO prices...")

prices = pd.read_csv(
    "raw_data/07-2026_Q2.csv",
    usecols=[
        "producto",
        "presentacion",
        "categoria",
        "precio",
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
# 8. PRECOMPUTE INGREDIENT PRICES
# ============================================================

print("Calculating ingredient prices...")


ingredient_prices = {}


for ingredient, search_terms in ingredient_rules.items():

    found_price = None
    found_term = None

    for term in search_terms:

        normalized_term = normalize_text(
            term
        )

        matches = prices[
            prices["search_text"]
            .str.contains(
                normalized_term,
                na=False,
                regex=False,
            )
        ]

        if matches.empty:
            continue

        found_price = (
            matches["precio"]
            .median()
        )

        found_term = term

        break


    if found_price is not None:

        ingredient_prices[
            ingredient
        ] = {
            "price": found_price,
            "matched_term": found_term,
        }


print(
    f"Priced ingredients: "
    f"{len(ingredient_prices)}"
)


# ============================================================
# 9. NORMALIZE RECIPE INGREDIENTS
# ============================================================

def normalize_recipe_ingredients(
    ingredient_list,
):

    output = []

    for ingredient in ingredient_list:

        ingredient = normalize_ingredient(
            ingredient
        )

        if ingredient in ignored_ingredients:
            continue

        output.append(
            ingredient
        )

    return list(set(output))


recipes["normalized_ingredients"] = (
    recipes["ingredients"]
    .apply(
        normalize_recipe_ingredients
    )
)


recipes["has_forbidden_ingredient"] = (
    recipes["ingredients"]
    .apply(has_forbidden_ingredient)
)


# ============================================================
# 10. COVERAGE
# ============================================================

def calculate_coverage(
    ingredient_list,
):

    if not ingredient_list:
        return 0.0

    matched = sum(
        ingredient in ingredient_prices
        for ingredient in ingredient_list
    )

    return (
        matched
        / len(ingredient_list)
    )


recipes["coverage"] = (
    recipes[
        "normalized_ingredients"
    ]
    .apply(calculate_coverage)
)


recipes["ingredient_count"] = (
    recipes[
        "normalized_ingredients"
    ]
    .apply(len)
)


# ============================================================
# 11. EXCLUDED CATEGORIES
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


# ============================================================
# 12. FILTER RECIPES
# ============================================================

candidates = recipes[
    ~recipes["RecipeCategory"]
    .isin(excluded_categories)
].copy()


candidates = candidates[
    (candidates["coverage"] >= 0.70)
    &
    (
        candidates[
            "ingredient_count"
        ].between(4, 12)
    )
    &
    (
        candidates[
            "Calories"
        ].between(250, 750)
    )
    &
    (
        candidates[
            "ProteinContent"
        ] >= 10
    )
    &
    (
        candidates[
            "has_forbidden_ingredient"
        ] == False
    )
].copy()


print(
    f"Candidates after filtering: "
    f"{len(candidates)}"
)


# ============================================================
# 13. CATEGORY QUALITY SCORE
# ============================================================

preferred_categories = {
    "Chicken": 1.0,
    "Meat": 1.0,
    "Pork": 1.0,
    "Seafood": 1.0,
    "Fish": 1.0,
    "One Dish Meal": 1.0,

    "Vegetable": 0.9,
    "Stew": 0.9,
    "Chowders": 0.85,

    "Lunch/Snacks": 0.8,
    "Breakfast": 0.75,

    "Very Low Carbs": 0.8,
}


candidates["category_score"] = (
    candidates["RecipeCategory"]
    .map(preferred_categories)
    .fillna(0.6)
)


# ============================================================
# 14. NUTRITION / RATING SCORE
# ============================================================

candidates["rating_safe"] = (
    candidates[
        "AggregatedRating"
    ]
    .fillna(0)
)


candidates["protein_score"] = (
    candidates[
        "ProteinContent"
    ]
    .clip(
        lower=0,
        upper=50,
    )
    / 50
)


candidates["rating_score"] = (
    candidates[
        "rating_safe"
    ]
    .clip(
        lower=0,
        upper=5,
    )
    / 5
)


candidates["coverage_score"] = (
    candidates["coverage"]
)


# ============================================================
# 15. BALANCED RECOMMENDATION SCORE
# ============================================================

candidates["score"] = (
    candidates["coverage_score"] * 0.30
    +
    candidates["protein_score"] * 0.30
    +
    candidates["rating_score"] * 0.20
    +
    candidates["category_score"] * 0.20
)


# ============================================================
# 16. LIMIT SEARCH SPACE
# ============================================================

candidates = (
    candidates
    .sort_values(
        by="score",
        ascending=False,
    )
)


# Keep best 5 per category
candidates = (
    candidates
    .groupby(
        "RecipeCategory",
        group_keys=False,
    )
    .head(5)
)


# Keep strongest 15 categories
best_categories = (
    candidates
    .groupby(
        "RecipeCategory"
    )["score"]
    .max()
    .sort_values(
        ascending=False
    )
    .head(15)
    .index
)


candidates = candidates[
    candidates[
        "RecipeCategory"
    ].isin(best_categories)
].copy()


print(
    f"Candidate recipes for optimizer: "
    f"{len(candidates)}"
)


# ============================================================
# 17. COST FUNCTION
# ============================================================

def ingredient_set_cost(
    ingredients,
):

    total = 0.0

    for ingredient in ingredients:

        info = ingredient_prices.get(
            ingredient
        )

        if info is None:
            continue

        total += info["price"]

    return total


# ============================================================
# 18. GREEDY BUDGET OPTIMIZER
# ============================================================

print(
    "Optimizing weekly menu..."
)


selected_recipes = []

selected_categories = set()

current_ingredients = set()

current_cost = 0.0


for _, recipe in candidates.iterrows():

    if (
        len(selected_recipes)
        >= RECIPES_NEEDED
    ):
        break


    category = recipe[
        "RecipeCategory"
    ]


    if category in selected_categories:
        continue


    recipe_ingredients = set(
        recipe[
            "normalized_ingredients"
        ]
    )


    proposed_ingredients = (
        current_ingredients
        | recipe_ingredients
    )


    proposed_cost = (
        ingredient_set_cost(
            proposed_ingredients
        )
    )


    if proposed_cost > WEEKLY_BUDGET:
        continue


    selected_recipes.append(
        recipe
    )


    selected_categories.add(
        category
    )


    current_ingredients = (
        proposed_ingredients
    )


    current_cost = (
        proposed_cost
    )


# ============================================================
# 19. FALLBACK
# ============================================================

if len(selected_recipes) < RECIPES_NEEDED:

    print(
        "Running fallback search..."
    )


    fallback_candidates = (
        candidates
        .sort_values(
            by=[
                "category_score",
                "coverage",
                "score",
            ],
            ascending=False,
        )
    )


    for _, recipe in (
        fallback_candidates
        .iterrows()
    ):

        if (
            len(selected_recipes)
            >= RECIPES_NEEDED
        ):
            break


        category = recipe[
            "RecipeCategory"
        ]


        if category in selected_categories:
            continue


        recipe_ingredients = set(
            recipe[
                "normalized_ingredients"
            ]
        )


        proposed_ingredients = (
            current_ingredients
            | recipe_ingredients
        )


        proposed_cost = (
            ingredient_set_cost(
                proposed_ingredients
            )
        )


        if proposed_cost > WEEKLY_BUDGET:
            continue


        selected_recipes.append(
            recipe
        )


        selected_categories.add(
            category
        )


        current_ingredients = (
            proposed_ingredients
        )


        current_cost = (
            proposed_cost
        )


# ============================================================
# 20. VALIDATE
# ============================================================

if (
    len(selected_recipes)
    < RECIPES_NEEDED
):

    raise ValueError(
        "Could not find 5 recipes "
        "under the current budget."
    )


weekly_recipes = pd.DataFrame(
    selected_recipes
)


# ============================================================
# 21. BUILD FINAL CART
# ============================================================

cart_rows = []


for ingredient in sorted(
    current_ingredients
):

    info = ingredient_prices.get(
        ingredient
    )


    if info is None:

        cart_rows.append(
            {
                "ingredient":
                    ingredient,

                "matched_term":
                    None,

                "median_price":
                    None,

                "status":
                    "UNMATCHED",
            }
        )

        continue


    cart_rows.append(
        {
            "ingredient":
                ingredient,

            "matched_term":
                info[
                    "matched_term"
                ],

            "median_price":
                info["price"],

            "status":
                "MATCHED",
        }
    )


cart = pd.DataFrame(
    cart_rows
)


remaining_budget = (
    WEEKLY_BUDGET
    - current_cost
)


# ============================================================
# 22. OUTPUT MENU
# ============================================================

print("\n" + "=" * 70)

print(
    "NUTRIPLAN — CLEAN BUDGET OPTIMIZER"
)

print("=" * 70)


print(
    "\n=== WEEKLY MENU ==="
)


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
        f"   Category quality: "
        f"{recipe['category_score']:.2f}"
    )

    print(
        f"   Score: "
        f"{recipe['score']:.3f}"
    )


# ============================================================
# 23. OUTPUT CART
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
# 24. SUMMARY
# ============================================================

matched_count = (
    cart["status"]
    .eq("MATCHED")
    .sum()
)


menu_score = (
    weekly_recipes[
        "score"
    ]
    .sum()
)


print(
    "\n=== OPTIMIZATION SUMMARY ==="
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
    f"Matched products: "
    f"{matched_count}/{len(cart)}"
)


print(
    f"Menu score: "
    f"{menu_score:.3f}"
)


print(
    f"Estimated cart total: "
    f"${current_cost:.2f} MXN"
)


print(
    f"Weekly budget: "
    f"${WEEKLY_BUDGET:.2f} MXN"
)


print(
    f"Remaining budget: "
    f"${remaining_budget:.2f} MXN"
)


if current_cost <= WEEKLY_BUDGET:

    print(
        "\n✅ MENU SELECTED WITHIN BUDGET"
    )

else:

    print(
        "\n❌ MENU OVER BUDGET"
    )


# ============================================================
# 25. NUTRITION SUMMARY
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
# 26. QUALITY CHECK
# ============================================================

print(
    "\n=== QUALITY CHECK ==="
)


forbidden_found = []


for _, recipe in weekly_recipes.iterrows():

    recipe_forbidden = [
        ingredient
        for ingredient
        in recipe[
            "normalized_ingredients"
        ]
        if ingredient
        in forbidden_ingredients
    ]


    if recipe_forbidden:

        forbidden_found.append(
            {
                "recipe":
                    recipe["Name"],

                "ingredients":
                    recipe_forbidden,
            }
        )


if not forbidden_found:

    print(
        "✅ No forbidden alcohol ingredients found."
    )

else:

    print(
        "❌ Forbidden ingredients detected:"
    )

    print(
        forbidden_found
    )


# ============================================================
# 27. SAVE
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
        "category_score",
        "score",
    ]
].to_csv(
    "notebooks/"
    "jose_clean_budget_menu.csv",
    index=False,
)


cart.to_csv(
    "notebooks/"
    "jose_clean_budget_cart.csv",
    index=False,
)


print(
    "\n=== FILES SAVED ==="
)

print(
    "notebooks/"
    "jose_clean_budget_menu.csv"
)

print(
    "notebooks/"
    "jose_clean_budget_cart.csv"
)
