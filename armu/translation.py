"""
Lightweight Spanish -> English translation for the user's free-text query.

Recipes (name, ingredients, tags) are in English, so a Spanish query would not
match anything under TF-IDF. We translate the query word by word using a food /
cooking dictionary. Unknown words pass through unchanged, so English queries
keep working too. Deterministic and offline (no LLM).
"""

from armu.ingredient_matching import normalize_text


# Spanish function words that carry no meaning for matching.
STOPWORDS_ES = {
    "algo", "con", "sin", "de", "del", "la", "el", "los", "las",
    "un", "una", "unos", "unas", "para", "que", "en", "o", "y", "a",
    "me", "quiero", "comer", "gusta", "algun", "alguna",
}


# Spanish -> English for the words a user is likely to type.
ES_EN = {
    # proteins
    "pollo": "chicken",
    "res": "beef",
    "carne": "beef",
    "cerdo": "pork",
    "pescado": "fish",
    "salmon": "salmon",
    "camaron": "shrimp",
    "camarones": "shrimp",
    "atun": "tuna",
    "tocino": "bacon",
    "jamon": "ham",
    "salchicha": "sausage",
    "pavo": "turkey",

    # vegetables
    "verdura": "vegetable",
    "verduras": "vegetable",
    "vegetales": "vegetable",
    "cebolla": "onion",
    "ajo": "garlic",
    "jitomate": "tomato",
    "tomate": "tomato",
    "papa": "potato",
    "papas": "potato",
    "zanahoria": "carrot",
    "champinon": "mushroom",
    "champinones": "mushroom",
    "hongos": "mushroom",
    "calabaza": "zucchini",
    "apio": "celery",
    "chicharo": "peas",
    "chicharos": "peas",
    "ejote": "green beans",
    "ejotes": "green beans",
    "lechuga": "lettuce",
    "espinaca": "spinach",
    "brocoli": "broccoli",
    "elote": "corn",
    "frijol": "beans",
    "frijoles": "beans",
    "chile": "chili",

    # carbs / grains
    "arroz": "rice",
    "pasta": "pasta",
    "pan": "bread",
    "harina": "flour",
    "avena": "oats",
    "tortilla": "tortilla",

    # dairy / eggs
    "queso": "cheese",
    "leche": "milk",
    "mantequilla": "butter",
    "crema": "cream",
    "huevo": "egg",
    "huevos": "egg",
    "yogur": "yogurt",
    "yogurt": "yogurt",

    # fruit
    "manzana": "apple",
    "platano": "banana",
    "naranja": "orange",
    "limon": "lemon",
    "fresa": "strawberry",
    "fresas": "strawberry",
    "pina": "pineapple",
    "papaya": "papaya",

    # dishes / preferences
    "sopa": "soup",
    "ensalada": "salad",
    "postre": "dessert",
    "dulce": "sweet",
    "picante": "spicy",
    "ligero": "light",
    "ligera": "light",
    "saludable": "healthy",
    "facil": "easy",
    "rapido": "quick",
    "rapida": "quick",
    "desayuno": "breakfast",
    "comida": "meal",
    "cena": "dinner",
    "guisado": "stew",

    # cuisines
    "mexicana": "mexican",
    "mexicano": "mexican",
    "italiana": "italian",
    "italiano": "italian",
    "china": "chinese",
    "chino": "chinese",
    "japonesa": "japanese",
    "tailandesa": "thai",
    "india": "indian",

    # cooking methods
    "horneado": "baked",
    "frito": "fried",
    "asado": "roasted",
    "hervido": "boiled",

    # pantry / misc
    "aceite": "oil",
    "azucar": "sugar",
    "miel": "honey",
    "chocolate": "chocolate",
    "vainilla": "vanilla",
    "nuez": "nuts",
    "nueces": "nuts",
    "almendra": "almonds",
    "almendras": "almonds",
}


def translate_query(text):
    """
    Translate a (possibly Spanish) query into English tokens for matching.

    - Normalizes text (lowercase, no accents).
    - Drops Spanish stopwords.
    - Maps known Spanish words to English; unknown words pass through.
    """
    if not text:
        return ""

    normalized = normalize_text(text)

    words = []
    for word in normalized.split():
        if word in STOPWORDS_ES:
            continue
        words.append(ES_EN.get(word, word))

    return " ".join(words)
