import pandas as pd
import unicodedata


# ============================================================
# 1. NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Lowercase, remove accents and extra spaces.
    """
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
# 2. LOAD RECIPES
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


# ============================================================
# 3. LOAD PROFECO
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


# ============================================================
# 4. BUILD SEARCHABLE PROFECO TEXT
# ============================================================

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
# 5. INGREDIENT RULES
# ============================================================

# search_terms:
# Possible ways the ingredient may appear in PROFECO.
#
# match_type:
# exact    = very reliable
# synonym  = strong equivalent
# broad    = approximate/fallback

ingredient_rules = {

    # BASIC
    "salt": {
        "search_terms": ["sal"],
        "match_type": "exact",
    },

    "sugar": {
        "search_terms": ["azucar"],
        "match_type": "exact",
    },

    "brown sugar": {
        "search_terms": ["azucar"],
        "match_type": "synonym",
    },

    "granulated sugar": {
        "search_terms": ["azucar"],
        "match_type": "synonym",
    },

    "powdered sugar": {
        "search_terms": [
            "azucar glass",
            "azucar",
        ],
        "match_type": "synonym",
    },

    "confectioners' sugar": {
        "search_terms": [
            "azucar glass",
            "azucar",
        ],
        "match_type": "synonym",
    },

    "light brown sugar": {
        "search_terms": ["azucar"],
        "match_type": "synonym",
    },

    "butter": {
        "search_terms": ["mantequilla"],
        "match_type": "exact",
    },

    "unsalted butter": {
        "search_terms": [
            "mantequilla sin sal",
            "mantequilla",
        ],
        "match_type": "synonym",
    },

    "margarine": {
        "search_terms": ["margarina"],
        "match_type": "exact",
    },

    "egg": {
        "search_terms": ["huevo"],
        "match_type": "exact",
    },

    "eggs": {
        "search_terms": ["huevo"],
        "match_type": "exact",
    },

    "flour": {
        "search_terms": ["harina"],
        "match_type": "exact",
    },

    "all-purpose flour": {
        "search_terms": ["harina"],
        "match_type": "synonym",
    },

    "unbleached flour": {
        "search_terms": ["harina"],
        "match_type": "synonym",
    },

    "milk": {
        "search_terms": ["leche"],
        "match_type": "exact",
    },

    "evaporated milk": {
        "search_terms": ["leche evaporada"],
        "match_type": "exact",
    },

    # VEGETABLES
    "onion": {
        "search_terms": ["cebolla"],
        "match_type": "exact",
    },

    "onions": {
        "search_terms": ["cebolla"],
        "match_type": "exact",
    },

    "green onion": {
        "search_terms": [
            "cebolla cambray",
            "cebolla",
        ],
        "match_type": "broad",
    },

    "green onions": {
        "search_terms": [
            "cebolla cambray",
            "cebolla",
        ],
        "match_type": "broad",
    },

    "garlic": {
        "search_terms": ["ajo"],
        "match_type": "exact",
    },

    "garlic clove": {
        "search_terms": ["ajo"],
        "match_type": "synonym",
    },

    "garlic cloves": {
        "search_terms": ["ajo"],
        "match_type": "synonym",
    },

    "garlic powder": {
        "search_terms": [
            "ajo en polvo",
            "ajo",
        ],
        "match_type": "broad",
    },

    "tomato": {
        "search_terms": [
            "jitomate",
        ],
        "match_type": "exact",
    },

    "tomatoes": {
        "search_terms": [
            "jitomate",
        ],
        "match_type": "exact",
    },

    "tomato paste": {
        "search_terms": [
            "pure de tomate",
        ],
        "match_type": "synonym",
    },

    "tomato sauce": {
        "search_terms": [
            "pure de tomate",
            "salsa de tomate",
        ],
        "match_type": "synonym",
    },

    "celery": {
        "search_terms": ["apio"],
        "match_type": "exact",
    },

    "carrot": {
        "search_terms": ["zanahoria"],
        "match_type": "exact",
    },

    "carrots": {
        "search_terms": ["zanahoria"],
        "match_type": "exact",
    },

    "potatoes": {
        "search_terms": ["papa"],
        "match_type": "exact",
    },

    "zucchini": {
        "search_terms": ["calabaza"],
        "match_type": "synonym",
    },

    "mushroom": {
        "search_terms": ["champinones"],
        "match_type": "exact",
    },

    "mushrooms": {
        "search_terms": ["champinones"],
        "match_type": "exact",
    },

    # HERBS / SPICES
    "pepper": {
        "search_terms": ["pimienta"],
        "match_type": "broad",
    },

    "black pepper": {
        "search_terms": ["pimienta negra"],
        "match_type": "exact",
    },

    "white pepper": {
        "search_terms": ["pimienta blanca"],
        "match_type": "exact",
    },

    "cinnamon": {
        "search_terms": ["canela"],
        "match_type": "exact",
    },

    "oregano": {
        "search_terms": ["oregano"],
        "match_type": "exact",
    },

    "cumin": {
        "search_terms": ["comino"],
        "match_type": "exact",
    },

    "thyme": {
        "search_terms": ["tomillo"],
        "match_type": "exact",
    },

    "bay leaf": {
        "search_terms": ["laurel"],
        "match_type": "synonym",
    },

    "clove": {
        "search_terms": ["clavo"],
        "match_type": "exact",
    },

    "green pepper": {
        "search_terms": [
            "chile poblano",
            "chile fresco",
        ],
        "match_type": "broad",
    },

    "cayenne pepper": {
        "search_terms": ["chile"],
        "match_type": "broad",
    },

    "chili powder": {
        "search_terms": ["chile"],
        "match_type": "broad",
    },

    # OILS / SAUCES
    "olive oil": {
        "search_terms": ["aceite de oliva"],
        "match_type": "exact",
    },

    "soy sauce": {
        "search_terms": ["salsa de soya"],
        "match_type": "exact",
    },

    "worcestershire sauce": {
        "search_terms": ["salsa inglesa"],
        "match_type": "synonym",
    },

    "mayonnaise": {
        "search_terms": ["mayonesa"],
        "match_type": "exact",
    },

    "vinegar": {
        "search_terms": ["vinagre"],
        "match_type": "exact",
    },

    "cider vinegar": {
        "search_terms": [
            "vinagre de manzana",
            "vinagre",
        ],
        "match_type": "broad",
    },

    # DAIRY
    "sour cream": {
        "search_terms": ["crema"],
        "match_type": "broad",
    },

    "cream cheese": {
        "search_terms": ["queso crema"],
        "match_type": "exact",
    },

    "heavy cream": {
        "search_terms": [
            "crema batida",
            "crema",
        ],
        "match_type": "broad",
    },

    # FRUIT
    "lemon": {
        "search_terms": ["limon"],
        "match_type": "exact",
    },

    "lemons": {
        "search_terms": ["limon"],
        "match_type": "exact",
    },

    "lemon juice": {
        "search_terms": ["limon"],
        "match_type": "broad",
    },

    "fresh lemon juice": {
        "search_terms": ["limon"],
        "match_type": "broad",
    },

    "lime juice": {
        "search_terms": ["limon"],
        "match_type": "synonym",
    },

    "orange": {
        "search_terms": ["naranja"],
        "match_type": "exact",
    },

    "apples": {
        "search_terms": ["manzana"],
        "match_type": "exact",
    },

    "raisins": {
        "search_terms": ["pasas"],
        "match_type": "exact",
    },

    "coconut": {
        "search_terms": ["coco"],
        "match_type": "exact",
    },

    # NUTS
    "pecans": {
        "search_terms": ["nuez"],
        "match_type": "broad",
    },

    "walnuts": {
        "search_terms": ["nuez"],
        "match_type": "broad",
    },

    # PROTEINS
    "chicken": {
        "search_terms": [
            "carne pollo",
        ],
        "match_type": "exact",
    },

    "beef": {
        "search_terms": [
            "carne res",
        ],
        "match_type": "exact",
    },

    "bacon": {
        "search_terms": ["tocino"],
        "match_type": "exact",
    },

    # PANTRY
    "rice": {
        "search_terms": ["arroz"],
        "match_type": "exact",
    },

    "baking powder": {
        "search_terms": [
            "polvo p/hornear",
            "polvo para hornear",
        ],
        "match_type": "exact",
    },

    "vanilla": {
        "search_terms": ["vainilla"],
        "match_type": "exact",
    },

    "vanilla extract": {
        "search_terms": ["vainilla"],
        "match_type": "synonym",
    },

    "honey": {
        "search_terms": ["miel"],
        "match_type": "exact",
    },

    "dijon mustard": {
        "search_terms": ["mostaza"],
        "match_type": "synonym",
    },
}


# ============================================================
# 6. CONFIDENCE
# ============================================================

confidence_scores = {
    "exact": 1.0,
    "synonym": 0.9,
    "broad": 0.5,
}


# ============================================================
# 7. MATCH FUNCTION
# ============================================================

def find_profeco_match(rule):

    search_terms = rule["search_terms"]

    for term in search_terms:

        normalized_term = normalize_text(term)

        mask = prices[
            "search_text"
        ].str.contains(
            normalized_term,
            na=False,
            regex=False,
        )

        matches = prices[mask]

        if not matches.empty:
            return matches, term

    return pd.DataFrame(), None


# ============================================================
# 8. RUN MATCHING
# ============================================================

results = []


for ingredient, rule in ingredient_rules.items():

    matches, matched_term = (
        find_profeco_match(rule)
    )

    if matches.empty:
        continue

    match_type = rule["match_type"]

    results.append(
        {
            "ingredient": ingredient,
            "matched_term": matched_term,
            "match_type": match_type,
            "confidence":
                confidence_scores[match_type],
            "matches": len(matches),
            "min_price":
                matches["precio"].min(),
            "median_price":
                matches["precio"].median(),
            "max_price":
                matches["precio"].max(),
        }
    )


results = pd.DataFrame(results)


# ============================================================
# 9. TOP 100
# ============================================================

top100 = ingredients.head(100).copy()


top100["in_dictionary"] = (
    top100["ingredient"]
    .isin(ingredient_rules.keys())
)


matched_set = (
    set(results["ingredient"])
    if not results.empty
    else set()
)


top100["profeco_match"] = (
    top100["ingredient"]
    .isin(matched_set)
)


# ============================================================
# 10. COVERAGE
# ============================================================

dictionary_count = (
    top100["in_dictionary"].sum()
)

real_count = (
    top100["profeco_match"].sum()
)


dictionary_coverage = (
    dictionary_count / 100 * 100
)

real_coverage = (
    real_count / 100 * 100
)


print("\n=== MATCHER V2 ===")

print(
    f"Dictionary coverage: "
    f"{dictionary_count}/100 "
    f"({dictionary_coverage:.1f}%)"
)

print(
    f"Real PROFECO coverage: "
    f"{real_count}/100 "
    f"({real_coverage:.1f}%)"
)


# ============================================================
# 11. CONFIDENCE
# ============================================================

top100 = top100.merge(
    results[
        [
            "ingredient",
            "match_type",
            "confidence",
            "median_price",
            "matched_term",
        ]
    ],
    on="ingredient",
    how="left",
)


top100["confidence"] = (
    top100["confidence"]
    .fillna(0)
)


average_confidence = (
    top100["confidence"].mean()
)


print(
    f"\nAverage confidence: "
    f"{average_confidence:.2f}"
)


# ============================================================
# 12. MATCH TYPE DISTRIBUTION
# ============================================================

print(
    "\n=== MATCH TYPE DISTRIBUTION ==="
)

print(
    top100["match_type"]
    .fillna("unmatched")
    .value_counts()
)


# ============================================================
# 13. SUCCESSFUL MATCHES
# ============================================================

print(
    "\n=== SUCCESSFUL MATCHES ==="
)

successful = (
    top100[
        top100["profeco_match"]
    ]
    .sort_values(
        [
            "confidence",
            "count",
        ],
        ascending=False,
    )
)

print(
    successful[
        [
            "ingredient",
            "matched_term",
            "count",
            "match_type",
            "confidence",
            "median_price",
        ]
    ]
    .to_string(index=False)
)


# ============================================================
# 14. FAILED MATCHES
# ============================================================

print(
    "\n=== STILL UNMATCHED ==="
)

failed = top100[
    ~top100["profeco_match"]
]

print(
    failed[
        [
            "ingredient",
            "count",
        ]
    ]
    .to_string(index=False)
)


# ============================================================
# 15. SAVE
# ============================================================

results.to_csv(
    "notebooks/"
    "jose_price_matching_v2_results.csv",
    index=False,
)

top100.to_csv(
    "notebooks/"
    "jose_top100_matching_v2.csv",
    index=False,
)


print(
    "\n=== FILES SAVED ==="
)

print(
    "notebooks/"
    "jose_price_matching_v2_results.csv"
)

print(
    "notebooks/"
    "jose_top100_matching_v2.csv"
)
