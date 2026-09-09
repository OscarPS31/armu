import pandas as pd
import unicodedata


# ============================================================
# CONFIG
# ============================================================

PROFECO_PATH = "data/profeco_clean.csv"

OUTPUT_PATH = "data/ingredient_prices.csv"

REPORT_PATH = "data/ingredient_prices_report.txt"


# ============================================================
# TOP 30 INGREDIENTS
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
# INGREDIENT -> PROFECO MAP
# ============================================================

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

    "water": [
        "Agua Sin Gas",
    ],

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

    "lemon juice": [
        "Limon",
    ],

    "baking powder": [
        "Polvo P/hornear",
    ],

    # Proxy: baking soda is not directly available
    "baking soda": [
        "Polvo P/hornear",
    ],

    # Proxy: closest hard Mexican cheese
    "parmesan cheese": [
        "Queso Cotija",
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

    "green onion": [
        "Cebolla",
    ],

    "cream cheese": [
        "Queso Crema",
        "Queso Doble Crema",
    ],

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

    # Proxy: closest available cheese
    "cheddar cheese": [
        "Queso Chihuahua",
    ],
}


# ============================================================
# MATCH TYPES
# ============================================================

MATCH_TYPE = {
    "water": "equivalent",
    "baking soda": "proxy",
    "parmesan cheese": "proxy",
    "green onion": "proxy",
    "garlic powder": "proxy",
    "cheddar cheese": "proxy",
    "lemon juice": "proxy",
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


df["producto_normalizado"] = (
    df["producto"]
    .apply(normalize_text)
)


# ============================================================
# BUILD OUTPUT
# ============================================================

rows = []

unmatched = []

match_report = []


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


    if selected_matches is None:

        unmatched.append(
            ingredient
        )

        continue


    median_price = (
        selected_matches["precio"]
        .median()
    )


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


    match_report.append(
        {
            "ingredient": ingredient,
            "profeco_category": selected_category,
            "match_type": MATCH_TYPE.get(
                ingredient,
                "exact",
            ),
        }
    )


# ============================================================
# FINAL DATAFRAME
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
# SAVE CSV
# ============================================================

ingredient_prices.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# MATCH QUALITY SUMMARY
# ============================================================

match_report_df = pd.DataFrame(
    match_report
)

exact_count = (
    match_report_df[
        "match_type"
    ]
    .eq("exact")
    .sum()
)

equivalent_count = (
    match_report_df[
        "match_type"
    ]
    .eq("equivalent")
    .sum()
)

proxy_count = (
    match_report_df[
        "match_type"
    ]
    .eq("proxy")
    .sum()
)


# ============================================================
# SAVE REPORT
# ============================================================

with open(
    REPORT_PATH,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "NutriPlan - Ingredient Prices Coverage Report\n"
    )

    f.write(
        "=============================================\n\n"
    )

    f.write(
        "Source:\n"
    )

    f.write(
        "PROFECO QQP 2026 - 07-2026_Q2.csv\n\n"
    )

    f.write(
        f"Top ingredients evaluated: {total}\n"
    )

    f.write(
        f"Ingredients with price: {covered}\n"
    )

    f.write(
        f"Coverage: {coverage:.1f}%\n\n"
    )

    f.write(
        "Match quality:\n"
    )

    f.write(
        f"- Exact: {exact_count}\n"
    )

    f.write(
        f"- Equivalent: {equivalent_count}\n"
    )

    f.write(
        f"- Proxy: {proxy_count}\n\n"
    )

    f.write(
        "Proxy/equivalent mappings:\n"
    )

    for item in match_report:

        if item["match_type"] != "exact":

            f.write(
                f"- {item['ingredient']} "
                f"-> {item['profeco_category']} "
                f"({item['match_type']})\n"
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
    "\n=== MATCH QUALITY ==="
)

print(
    f"Exact: {exact_count}"
)

print(
    f"Equivalent: {equivalent_count}"
)

print(
    f"Proxy: {proxy_count}"
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

print(
    REPORT_PATH
)
