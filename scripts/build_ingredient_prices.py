import pandas as pd
import unicodedata


# ============================================================
# CONFIG
# ============================================================

PROFECO_PATH = "data/profeco_clean.csv"

OUTPUT_PATH = "data/ingredient_prices.csv"


# ============================================================
# TOP 30 INGREDIENTS FROM RECIPES
# ============================================================

TOP_INGREDIENTS = [
    "salt",
    "sugar",
    "butter",
    "egg",
    "garlic",
    "onion",
    "flour",
    "water",
    "olive oil",
    "milk",
    "vanilla",
    "pepper",
    "lemon juice",
    "baking powder",
    "baking soda",
    "parmesan cheese",
    "carrot",
    "cinnamon",
    "black pepper",
    "sour cream",
    "tomato",
    "margarine",
    "green onion",
    "cream cheese",
    "garlic powder",
    "celery",
    "honey",
    "soy sauce",
    "mayonnaise",
    "cheddar cheese",
]


# ============================================================
# INGREDIENT -> PROFECO PRODUCT CANDIDATES
# ============================================================

# Multiple candidates are allowed.
# The script will use the first product that actually exists
# in the latest PROFECO dataset.

INGREDIENT_TO_PROFECO = {
    "salt": [
        "Sal Molida de Mesa",
        "Sal de Mar",
    ],

    "sugar": [
        "Azucar",
    ],

    "butter": [
        "Mantequilla",
    ],

    "egg": [
        "Huevo",
    ],

    "garlic": [
        "Ajo",
    ],

    "onion": [
        "Cebolla",
    ],

    "flour": [
        "Harina de Trigo",
    ],

    # Water is intentionally not forced to an unrelated product.
    "water": [],

    "olive oil": [
        "Aceite de Oliva",
        "Aceite",
    ],

    "milk": [
        "Leche Pasteurizada",
        "Leche Ultrapasteurizada",
    ],

    "vanilla": [
        "Vainilla",
    ],

    "pepper": [
        "Pimienta",
    ],

    # Closest available basic ingredient.
    "lemon juice": [
        "Limon",
    ],

    "baking powder": [
        "Polvo P/hornear",
    ],

    "baking soda": [
        "Bicarbonato de Sodio",
    ],

    "parmesan cheese": [
        "Queso Parmesano",
    ],

    "carrot": [
        "Zanahoria",
    ],

    "cinnamon": [
        "Canela",
    ],

    "black pepper": [
        "Pimienta",
    ],

    "sour cream": [
        "Crema",
    ],

    "tomato": [
        "Jitomate",
        "Tomate",
    ],

    "margarine": [
        "Margarina",
    ],

    # Approximation: PROFECO may not distinguish green onion.
    "green onion": [
        "Cebolla",
    ],

    "cream cheese": [
        "Queso Crema",
        "Queso Doble Crema",
    ],

    # Approximation to the fresh ingredient if powder is unavailable.
    "garlic powder": [
        "Ajo",
    ],

    "celery": [
        "Apio",
    ],

    "honey": [
        "Miel de Abeja",
    ],

    "soy sauce": [
        "Salsa de Soya",
    ],

    "mayonnaise": [
        "Mayonesa",
    ],

    "cheddar cheese": [
        "Queso Cheddar",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def normalize_text(value):
    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    return " ".join(
        value.split()
    )


def infer_unit(presentation):
    """
    Convert PROFECO presentation text into a simplified unit.

    This is intentionally conservative.
    """

    text = normalize_text(
        presentation
    )

    if "kg" in text:
        return "kg"

    if (
        "litro" in text
        or " lt" in f" {text}"
        or text.startswith("lt")
    ):
        return "litro"

    if "ml" in text:
        return "ml"

    if (
        "pieza" in text
        or "pza" in text
    ):
        return "pieza"

    if "docena" in text:
        return "docena"

    if "manojo" in text:
        return "manojo"

    if (
        "gr" in text
        or "gramo" in text
    ):
        return "g"

    return "presentacion"


# ============================================================
# LOAD PROFECO
# ============================================================

print("Loading clean PROFECO dataset...")

df = pd.read_csv(
    PROFECO_PATH
)

print(
    f"Rows loaded: {len(df):,}"
)


# ============================================================
# NORMALIZE PRODUCT NAMES
# ============================================================

df["producto_normalizado"] = (
    df["producto"]
    .apply(normalize_text)
)


# ============================================================
# FIND ONE PROFECO MATCH PER INGREDIENT
# ============================================================

rows = []

unmatched = []


for ingredient in TOP_INGREDIENTS:

    candidate_products = (
        INGREDIENT_TO_PROFECO.get(
            ingredient,
            [],
        )
    )

    selected_matches = None
    selected_category = None


    for product in candidate_products:

        product_normalized = (
            normalize_text(product)
        )

        matches = df[
            df["producto_normalizado"]
            == product_normalized
        ].copy()


        if not matches.empty:

            selected_matches = matches
            selected_category = (
                matches.iloc[0]["producto"]
            )

            break


    # --------------------------------------------------------
    # NO MATCH
    # --------------------------------------------------------

    if selected_matches is None:

        unmatched.append(
            ingredient
        )

        continue


    # --------------------------------------------------------
    # ROBUST PRICE
    # --------------------------------------------------------

    median_price = (
        selected_matches["precio"]
        .median()
    )


    # Find an actual row closest to the median so that
    # store + presentation correspond to a real observation.
    selected_matches[
        "distance_to_median"
    ] = (
        selected_matches["precio"]
        - median_price
    ).abs()


    representative = (
        selected_matches
        .sort_values(
            "distance_to_median"
        )
        .iloc[0]
    )


    unit = infer_unit(
        representative[
            "presentacion"
        ]
    )


    store = representative[
        "cadena_comercial"
    ]


    rows.append(
        {
            "ingredient":
                ingredient,

            "profeco_category":
                selected_category,

            "price":
                round(
                    float(median_price),
                    2,
                ),

            "unit":
                unit,

            "store":
                store,
        }
    )


# ============================================================
# BUILD FINAL DATAFRAME
# ============================================================

ingredient_prices = pd.DataFrame(
    rows,
    columns=[
        "ingredient",
        "profeco_category",
        "price",
        "unit",
        "store",
    ],
)


# ============================================================
# COVERAGE
# ============================================================

total = len(
    TOP_INGREDIENTS
)

covered = len(
    ingredient_prices
)

coverage = (
    covered
    / total
    * 100
)


# ============================================================
# SAVE
# ============================================================

ingredient_prices.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print(
    "\n" + "=" * 65
)

print(
    "NUTRIPLAN — INGREDIENT PRICES"
)

print(
    "=" * 65
)

print(
    f"Top ingredients evaluated: "
    f"{total}"
)

print(
    f"Ingredients with PROFECO price: "
    f"{covered}"
)

print(
    f"Coverage: "
    f"{coverage:.1f}%"
)

print(
    f"Missing ingredients: "
    f"{len(unmatched)}"
)


print(
    "\n=== UNMATCHED INGREDIENTS ==="
)

if unmatched:

    for ingredient in unmatched:
        print(
            "-",
            ingredient,
        )

else:

    print(
        "None"
    )


print(
    "\n=== FINAL DATASET ==="
)

print(
    ingredient_prices
    .to_string(
        index=False
    )
)


print(
    "\n=== OUTPUT ==="
)

print(
    OUTPUT_PATH
)
