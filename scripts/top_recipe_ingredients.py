import ast
import re
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

RECIPES_PATH = "raw_data/recipes.csv"

TOP_N = 30


# ============================================================
# PARSER
# ============================================================

def parse_foodcom_vector(value):
    """
    Convert:
        c("milk", "eggs", "sugar")
    into:
        ["milk", "eggs", "sugar"]
    """

    if pd.isna(value):
        return []

    value = str(value).strip()

    if not value.startswith("c("):
        return []

    inner = value[2:-1]

    try:
        parsed = ast.literal_eval(
            "[" + inner + "]"
        )

        return [
            str(item).strip().lower()
            for item in parsed
            if str(item).strip()
        ]

    except Exception:

        items = re.findall(
            r'"([^"]+)"',
            inner,
        )

        return [
            item.strip().lower()
            for item in items
            if item.strip()
        ]


# ============================================================
# BASIC NORMALIZATION
# ============================================================

ALIASES = {
    "eggs": "egg",
    "onions": "onion",
    "tomatoes": "tomato",
    "carrots": "carrot",
    "lemons": "lemon",

    "garlic cloves": "garlic",
    "garlic clove": "garlic",

    "unsalted butter": "butter",

    "granulated sugar": "sugar",
    "brown sugar": "sugar",
    "powdered sugar": "sugar",
    "confectioners' sugar": "sugar",

    "all-purpose flour": "flour",
    "unbleached flour": "flour",

    "vanilla extract": "vanilla",

    "fresh lemon juice": "lemon juice",

    "green onions": "green onion",

    "button mushrooms": "mushrooms",
}


def normalize_ingredient(value):

    value = str(value).strip().lower()

    return ALIASES.get(
        value,
        value,
    )


# ============================================================
# LOAD
# ============================================================

print("Loading recipes...")

df = pd.read_csv(
    RECIPES_PATH,
    usecols=[
        "RecipeIngredientParts",
    ],
)


print(
    f"Recipes loaded: {len(df):,}"
)


# ============================================================
# PARSE
# ============================================================

print(
    "Parsing ingredients..."
)

df["ingredients"] = (
    df["RecipeIngredientParts"]
    .apply(parse_foodcom_vector)
)


# ============================================================
# EXPLODE + NORMALIZE
# ============================================================

ingredients = (
    df["ingredients"]
    .explode()
    .dropna()
    .astype(str)
    .str.strip()
    .str.lower()
)


ingredients = (
    ingredients
    .apply(normalize_ingredient)
)


# ============================================================
# COUNTS
# ============================================================

counts = (
    ingredients
    .value_counts()
)


print(
    "\n=== TOP 30 INGREDIENTS ===\n"
)


for index, (
    ingredient,
    count,
) in enumerate(
    counts.head(TOP_N).items(),
    start=1,
):

    print(
        f"{index:02d}. "
        f"{ingredient:<25} "
        f"{count:,}"
    )


print(
    "\n=== TOTAL UNIQUE INGREDIENTS ==="
)

print(
    counts.index.nunique()
)
