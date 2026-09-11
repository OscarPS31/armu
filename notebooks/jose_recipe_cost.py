import pandas as pd
import unicodedata


# ============================================================
# 1. TEXT NORMALIZATION
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


# ============================================================
# 2. PARSE FOOD.COM VECTOR
# ============================================================

def parse_foodcom_vector(value):
    """
    Convert:
    c("2", "1/2", "1")

    into:
    ["2", "1/2", "1"]
    """

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

    "milk": ["leche"],
    "egg": ["huevo"],
    "sugar": ["azucar"],
    "salt": ["sal"],
    "vanilla": ["vainilla"],
    "butter": ["mantequilla"],

    "flour": ["harina"],
    "onion": ["cebolla"],
    "garlic": ["ajo"],
    "tomato": ["jitomate"],
    "carrot": ["zanahoria"],
    "celery": ["apio"],

    "potatoes": ["papa"],
    "rice": ["arroz"],

    "chicken": ["carne pollo"],
    "beef": ["carne res"],
    "bacon": ["tocino"],

    "olive oil": ["aceite de oliva"],
    "vinegar": ["vinagre"],
    "soy sauce": ["salsa de soya"],
    "mayonnaise": ["mayonesa"],

    "lemon": ["limon"],
    "orange": ["naranja"],
    "apples": ["manzana"],
}


# ============================================================
# 5. LOAD RECIPES
# ============================================================

recipes = pd.read_csv(
    "raw_data/recipes.csv",
    usecols=[
        "RecipeId",
        "Name",
        "RecipeIngredientQuantities",
        "RecipeIngredientParts",
        "Calories",
        "ProteinContent",
        "CarbohydrateContent",
        "FatContent",
    ],
)


# ============================================================
# 6. LOAD PROFECO
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
# 7. PROFECO PRICE MATCH
# ============================================================

def find_price(ingredient):

    ingredient = normalize_ingredient(
        ingredient
    )

    if ingredient not in ingredient_rules:
        return None

    for term in ingredient_rules[ingredient]:

        term = normalize_text(term)

        matches = prices[
            prices["search_text"]
            .str.contains(
                term,
                na=False,
                regex=False,
            )
        ]

        if matches.empty:
            continue

        return {
            "matched_term": term,
            "median_price":
                matches["precio"].median(),
            "min_price":
                matches["precio"].min(),
            "max_price":
                matches["precio"].max(),
            "matches":
                len(matches),
        }

    return None


# ============================================================
# 8. SELECT RECIPE 80
# ============================================================

recipe = recipes[
    recipes["RecipeId"] == 80
].iloc[0]


raw_ingredients = parse_foodcom_vector(
    recipe["RecipeIngredientParts"]
)

raw_quantities = parse_foodcom_vector(
    recipe["RecipeIngredientQuantities"]
)


# ============================================================
# 9. DATA QUALITY CHECK
# ============================================================

print("\n=== DATA QUALITY CHECK ===")

print(
    f"Ingredients found: "
    f"{len(raw_ingredients)}"
)

print(
    f"Quantities found: "
    f"{len(raw_quantities)}"
)


if len(raw_ingredients) != len(raw_quantities):

    print(
        "\nWARNING:"
        " ingredient and quantity lengths "
        "do not match."
    )

    print(
        "Only aligned values will be used."
    )


# Use only safely aligned positions
safe_length = min(
    len(raw_ingredients),
    len(raw_quantities),
)


ingredients = raw_ingredients[
    :safe_length
]

quantities = raw_quantities[
    :safe_length
]


# ============================================================
# 10. BUILD RECIPE TABLE
# ============================================================

rows = []

cart_total = 0


for ingredient, quantity in zip(
    ingredients,
    quantities,
):

    normalized = normalize_ingredient(
        ingredient
    )

    price_info = find_price(
        normalized
    )

    if price_info is None:

        rows.append(
            {
                "original_ingredient":
                    ingredient,

                "normalized_ingredient":
                    normalized,

                "quantity":
                    quantity,

                "matched_term":
                    None,

                "median_package_price":
                    None,

                "status":
                    "UNMATCHED",
            }
        )

        continue


    cart_total += (
        price_info["median_price"]
    )


    rows.append(
        {
            "original_ingredient":
                ingredient,

            "normalized_ingredient":
                normalized,

            "quantity":
                quantity,

            "matched_term":
                price_info[
                    "matched_term"
                ],

            "median_package_price":
                price_info[
                    "median_price"
                ],

            "status":
                "MATCHED",
        }
    )


result = pd.DataFrame(rows)


# ============================================================
# 11. REPORT
# ============================================================

print("\n" + "=" * 70)

print(
    "NUTRIPLAN — RECIPE COST PIPELINE"
)

print("=" * 70)


print(
    f"\nRecipe: "
    f"{recipe['Name']}"
)

print(
    f"Recipe ID: "
    f"{recipe['RecipeId']}"
)


print("\n=== INGREDIENT ALIGNMENT ===")

print(
    result.to_string(
        index=False
    )
)


matched = (
    result["status"]
    .eq("MATCHED")
    .sum()
)


print("\n=== SUMMARY ===")

print(
    f"Matched: "
    f"{matched}/{len(result)}"
)

print(
    f"Estimated shopping cart: "
    f"${cart_total:.2f} MXN"
)


print(
    "\nNOTE:"
)

print(
    "This represents the approximate "
    "cost of purchasing one package "
    "of every matched ingredient."
)

print(
    "The recipe dataset does not provide "
    "enough unit information here to "
    "calculate the exact proportional "
    "consumed cost reliably."
)


# ============================================================
# 12. EXTRA QUANTITIES
# ============================================================

if len(raw_quantities) > safe_length:

    print(
        "\n=== EXTRA UNALIGNED QUANTITIES ==="
    )

    print(
        raw_quantities[
            safe_length:
        ]
    )


# ============================================================
# 13. SAVE
# ============================================================

output = (
    "notebooks/"
    "jose_recipe_cost_result.csv"
)

result.to_csv(
    output,
    index=False,
)

print(
    f"\nSaved: {output}"
)
