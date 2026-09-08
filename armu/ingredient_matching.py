import pandas as pd
import unicodedata


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Normalize text for matching:
    - lowercase
    - strip spaces
    - remove accents
    - collapse repeated whitespace
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
# INGREDIENT ALIASES
# ============================================================

INGREDIENT_ALIASES = {
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

    # Current known cleanup
    "roasting chickens": "chicken",
}


# ============================================================
# INGREDIENT -> PROFECO SEARCH TERMS
# ============================================================

INGREDIENT_RULES = {
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
# PUBLIC FUNCTIONS
# ============================================================

def normalize_ingredient(value):
    """
    Convert an ingredient to its canonical internal name.

    Example:
        roast beef -> beef
        eggs -> egg
        roasting chickens -> chicken
    """
    value = normalize_text(value)

    return INGREDIENT_ALIASES.get(
        value,
        value,
    )


def get_profeco_search_terms(ingredient):
    """
    Return the PROFECO terms associated with an ingredient.

    Example:
        chicken -> ["carne pollo"]
        beef -> ["carne res"]
    """
    normalized = normalize_ingredient(
        ingredient
    )

    return INGREDIENT_RULES.get(
        normalized,
        [],
    )


def ingredient_is_supported(ingredient):
    """
    Return True when the ingredient currently has
    a PROFECO matching rule.
    """
    normalized = normalize_ingredient(
        ingredient
    )

    return normalized in INGREDIENT_RULES


def get_matching_info(ingredient):
    """
    Return basic ingredient matching information
    without loading PROFECO yet.
    """

    original = ingredient

    normalized = normalize_ingredient(
        ingredient
    )

    search_terms = (
        get_profeco_search_terms(
            ingredient
        )
    )

    return {
        "original": original,
        "normalized": normalized,
        "search_terms": search_terms,
        "supported": bool(search_terms),
    }
