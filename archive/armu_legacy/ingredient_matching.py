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
    # --------------------------------------------------------
    # ENGLISH VARIANTS -> CANONICAL INTERNAL NAME
    # --------------------------------------------------------

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

    "roasting chicken": "chicken",
    "roasting chickens": "chicken",
    "chicken breast": "chicken",
    "chicken breasts": "chicken",

    # --------------------------------------------------------
    # SPANISH -> CANONICAL INTERNAL NAME
    # --------------------------------------------------------

    "sal": "salt",

    "azucar": "sugar",

    "mantequilla": "butter",
    "margarina": "margarine",

    "huevo": "egg",
    "huevos": "egg",

    "harina": "flour",

    "leche": "milk",

    "cebolla": "onion",
    "cebollas": "onion",

    "ajo": "garlic",
    "ajos": "garlic",

    "jitomate": "tomato",
    "jitomates": "tomato",
    "tomate": "tomato",
    "tomates": "tomato",

    "zanahoria": "carrot",
    "zanahorias": "carrot",

    "apio": "celery",

    "papa": "potatoes",
    "papas": "potatoes",
    "patata": "potatoes",
    "patatas": "potatoes",

    "calabaza": "zucchini",
    "calabacita": "zucchini",
    "calabacitas": "zucchini",

    "champinon": "mushroom",
    "champinones": "mushroom",
    "hongo": "mushroom",
    "hongos": "mushroom",

    "aceite de oliva": "olive oil",

    "vinagre": "vinegar",

    "salsa de soya": "soy sauce",
    "salsa de soja": "soy sauce",

    "mayonesa": "mayonnaise",

    "limon": "lemon",
    "limones": "lemon",

    "naranja": "orange",
    "naranjas": "orange",

    "manzana": "apples",
    "manzanas": "apples",

    "pollo": "chicken",
    "carne de pollo": "chicken",
    "carne pollo": "chicken",

    "res": "beef",
    "carne de res": "beef",
    "carne res": "beef",

    "tocino": "bacon",

    "arroz": "rice",

    "miel": "honey",

    "vainilla": "vanilla",

    "queso crema": "cream cheese",
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
    Convert an ingredient in English or Spanish
    to its canonical internal name.

    Examples:

        roast beef -> beef
        carne de res -> beef

        roasting chickens -> chicken
        pollo -> chicken

        onions -> onion
        cebolla -> onion
    """

    value = normalize_text(value)

    return INGREDIENT_ALIASES.get(
        value,
        value,
    )


def get_profeco_search_terms(ingredient):
    """
    Return PROFECO search terms associated
    with an ingredient.

    Examples:

        chicken -> ["carne pollo"]
        pollo -> ["carne pollo"]

        beef -> ["carne res"]
        carne de res -> ["carne res"]
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
    Return True when the ingredient currently
    has a PROFECO matching rule.
    """

    normalized = normalize_ingredient(
        ingredient
    )

    return normalized in INGREDIENT_RULES


def get_matching_info(ingredient):
    """
    Return basic bilingual matching information
    without querying PROFECO.
    """

    original = ingredient

    normalized = normalize_ingredient(
        ingredient
    )

    search_terms = get_profeco_search_terms(
        ingredient
    )

    return {
        "original": original,
        "normalized": normalized,
        "search_terms": search_terms,
        "supported": bool(search_terms),
    }
