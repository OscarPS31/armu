import re
import unicodedata
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

FREQUENCIES_PATH = "data/ingredient_frequencies.csv"
OUTPUT_PATH = "data/ingredient_mapping_all.csv"


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value):
    if pd.isna(value):
        return ""

    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ============================================================
# MAPPING RULES
# ============================================================

RULES = [

    # --------------------------------------------------------
    # WATER
    # --------------------------------------------------------

    (
        r"\b(boiling water|cold water|warm water|hot water|water)\b",
        "water",
        "Agua Sin Gas",
    ),

    # --------------------------------------------------------
    # OILS / FATS
    # --------------------------------------------------------

    (
        r"\b(extra virgin olive oil|virgin olive oil|olive oil)\b",
        "olive oil",
        "Aceite de Oliva",
    ),

    (
        r"\b(vegetable oil|cooking oil|canola oil|corn oil|oil)\b",
        "vegetable oil",
        "Aceite",
    ),

    (
        r"\b(unsalted butter|salted butter|butter)\b",
        "butter",
        "Mantequilla",
    ),

    (
        r"\b(margarine|melted margarine)\b",
        "margarine",
        "Margarina",
    ),

    # --------------------------------------------------------
    # BASIC PANTRY
    # --------------------------------------------------------

    (
        r"\b(brown sugar|granulated sugar|powdered sugar|white sugar|sugar)\b",
        "sugar",
        "Azúcar",
    ),

    (
        r"\b(all purpose flour|all-purpose flour|plain flour|flour)\b",
        "flour",
        "Harina de Trigo",
    ),

    (
        r"\b(baking powder)\b",
        "baking powder",
        "Polvo P/hornear",
    ),

    (
        r"\b(vanilla extract|vanilla)\b",
        "vanilla",
        "Vainilla",
    ),

    (
        r"\b(cinnamon|ground cinnamon)\b",
        "cinnamon",
        "Canela",
    ),

    (
        r"\b(cumin|ground cumin)\b",
        "cumin",
        "Comino",
    ),

    (
        r"\b(oats|oatmeal|rolled oats)\b",
        "oats",
        "Avena",
    ),

    (
        r"\b(breadcrumbs|bread crumbs|dry breadcrumbs)\b",
        "breadcrumbs",
        "Empanizadores",
    ),

    (
        r"\b(cornstarch)\b",
        "cornstarch",
        "Harina de Maíz",
    ),

    (
        r"\b(rice|cooked rice)\b",
        "rice",
        "Arroz",
    ),

    (
        r"\b(macaroni)\b",
        "macaroni",
        "Pasta para Sopa",
    ),

    (
        r"\b(spaghetti)\b",
        "spaghetti",
        "Pasta para Sopa",
    ),

    (
        r"\b(pasta)\b",
        "pasta",
        "Pasta para Sopa",
    ),

    (
        r"\b(corn tortillas|corn tortilla)\b",
        "corn tortillas",
        "Tortilla de Maíz",
    ),

    (
        r"\b(cornmeal)\b",
        "cornmeal",
        "Harina de Maíz",
    ),

    (
        r"\b(french bread)\b",
        "french bread",
        "Pan Blanco Bolillo",
    ),

    # --------------------------------------------------------
    # SEASONINGS / SPICES
    # --------------------------------------------------------

    (
        r"\b(black pepper|ground black pepper|pepper)\b",
        "pepper",
        "Pimienta",
    ),

    (
        r"^salt$",
        "salt",
        "Sal Molida de Mesa",
    ),

    (
        r"\b(sea salt)\b",
        "sea salt",
        "Sal de Mar",
    ),

    (
        r"\b(dried oregano|oregano)\b",
        "oregano",
        "Orégano",
    ),

    (
        r"\b(dried thyme|thyme)\b",
        "thyme",
        "Tomillo",
    ),

    (
        r"\b(chili powder)\b",
        "chili powder",
        "Chile Seco",
    ),

    (
        r"\b(cayenne)\b",
        "cayenne",
        "Chile Seco",
    ),

    (
        r"\b(coriander)\b",
        "coriander",
        "Cilantro",
    ),

    (
        r"\b(sesame seeds|sesame seed)\b",
        "sesame seeds",
        "Ajonjolí",
    ),

    # Prevent "garlic cloves" from matching this rule.
    (
        r"^(whole |ground )?(clove|cloves)$",
        "cloves",
        "Clavo",
    ),

    # --------------------------------------------------------
    # VEGETABLES / LEGUMES
    # --------------------------------------------------------

    (
        r"\b(garlic clove|garlic cloves|garlic cloves minced|garlic|fresh garlic)\b",
        "garlic",
        "Ajo",
    ),

    (
        r"\b(garlic powder)\b",
        "garlic powder",
        "Ajo",
    ),

    (
        r"\b(green onion|green onions|spring onion|spring onions|scallions)\b",
        "green onion",
        "Cebolla",
    ),

    (
        r"\b(scallion|scallions)\b",
        "scallion",
        "Cebolla",
    ),

    (
        r"\b(shallot|shallots)\b",
        "shallot",
        "Cebolla",
    ),

    (
        r"\b(chopped onion|onions|onion)\b",
        "onion",
        "Cebolla",
    ),

    (
        r"\b(tomatoes|tomato|fresh tomatoes|chopped tomatoes)\b",
        "tomato",
        "Jitomate",
    ),

    (
        r"\b(carrots|carrot)\b",
        "carrot",
        "Zanahoria",
    ),

    (
        r"\b(celery)\b",
        "celery",
        "Apio",
    ),

    (
        r"\b(potatoes|potato)\b",
        "potato",
        "Papa",
    ),

    (
        r"\b(zucchini|zucchinis)\b",
        "zucchini",
        "Calabaza",
    ),

    (
        r"\b(pumpkin)\b",
        "pumpkin",
        "Calabaza",
    ),

    (
        r"\b(black beans|black bean)\b",
        "black beans",
        "Frijol",
    ),

    (
        r"\b(chickpeas|chickpea)\b",
        "chickpeas",
        "Garbanzo",
    ),

    (
        r"\b(mushrooms|mushroom)\b",
        "mushrooms",
        "Champiñones",
    ),

    (
        r"\b(cilantro|fresh cilantro)\b",
        "cilantro",
        "Cilantro",
    ),

    (
        r"\b(cucumber|cucumbers)\b",
        "cucumber",
        "Pepino",
    ),

    (
        r"\b(frozen peas|peas|pea)\b",
        "peas",
        "Chícharos",
    ),

    (
        r"\b(black olives|olives|olive)\b",
        "olives",
        "Aceituna",
    ),

    (
        r"\b(spinach)\b",
        "spinach",
        "Espinacas",
    ),

    (
        r"\b(green beans|green bean)\b",
        "green beans",
        "Ejote",
    ),

    (
        r"\b(cauliflower)\b",
        "cauliflower",
        "Coliflor",
    ),

    (
        r"\b(cabbage)\b",
        "cabbage",
        "Col",
    ),

    (
        r"\b(lettuce)\b",
        "lettuce",
        "Lechuga",
    ),

    (
        r"\b(broccoli florets|broccoli)\b",
        "broccoli",
        "Brócoli",
    ),

    (
        r"\b(frozen corn)\b",
        "corn",
        "Granos de Elote",
    ),

    (
        r"\b(whole kernel corn)\b",
        "whole kernel corn",
        "Granos de Elote",
    ),

    (
        r"\b(green chilies|green chiles)\b",
        "green chilies",
        "Chile Fresco",
    ),

    (
        r"\b(jalapeno|jalapeño)\b",
        "jalapeno",
        "Chile Fresco",
    ),

    (
        r"\b(artichoke hearts|artichoke)\b",
        "artichoke",
        "Alcachofa",
    ),

    # --------------------------------------------------------
    # FRUITS
    # --------------------------------------------------------

    (
        r"\b(fresh lemon juice|lemon juice|lemons|lemon)\b",
        "lemon",
        "Limón",
    ),

    (
        r"\b(lime juice|fresh lime juice|lime|limes)\b",
        "lime",
        "Limón",
    ),

    (
        r"\b(orange juice)\b",
        "orange juice",
        "Jugo de Fruta",
    ),

    (
        r"\b(raisins|raisin)\b",
        "raisins",
        "Pasa (Uva Pasa)",
    ),

    (
        r"\b(crushed pineapple|pineapple)\b",
        "pineapple",
        "Piña",
    ),

    (
        r"\b(bananas|banana)\b",
        "banana",
        "Plátano",
    ),

    (
        r"\b(apples|apple)\b",
        "apple",
        "Manzana",
    ),

    (
        r"\b(avocado|avocados)\b",
        "avocado",
        "Aguacate",
    ),

    (
        r"\b(strawberries|strawberry)\b",
        "strawberries",
        "Fresa",
    ),

    # --------------------------------------------------------
    # DAIRY
    # --------------------------------------------------------

    (
        r"\b(whole milk|skim milk|low fat milk|low-fat milk|milk)\b",
        "milk",
        "Leche Pasteurizada",
    ),

    (
        r"\b(sour cream|heavy cream|whipping cream|cream)\b",
        "cream",
        "Crema",
    ),

    (
        r"\b(cream cheese)\b",
        "cream cheese",
        "Queso Crema",
    ),

    (
        r"\b(plain yogurt|plain yoghurt)\b",
        "plain yogurt",
        "Yoghurt",
    ),

    # --------------------------------------------------------
    # EGGS
    # --------------------------------------------------------

    (
        r"\b(eggs|egg)\b",
        "egg",
        "Huevo",
    ),

    # --------------------------------------------------------
    # MEAT / SEAFOOD
    # --------------------------------------------------------

    (
        r"\b(ground beef|beef)\b",
        "beef",
        "Carne Res",
    ),

    (
        r"\b(chicken breast|chicken breasts|chicken thighs|chicken thigh|chicken)\b",
        "chicken",
        "Carne Pollo",
    ),

    (
        r"\b(bacon)\b",
        "bacon",
        "Tocino Ahumado",
    ),

    (
        r"\b(shrimp|shrimps)\b",
        "shrimp",
        "Camarón",
    ),

    (
        r"\b(crabmeat|crab meat)\b",
        "crabmeat",
        "Jaiba",
    ),

    (
        r"\b(ham)\b",
        "ham",
        "Jamón",
    ),

    (
        r"\b(ground pork)\b",
        "ground pork",
        "Carne Cerdo",
    ),

    (
        r"\b(pork tenderloin)\b",
        "pork tenderloin",
        "Carne Cerdo",
    ),

    (
        r"\b(pork chops|pork chop)\b",
        "pork chops",
        "Carne Cerdo",
    ),

    (
        r"\b(italian sausage)\b",
        "italian sausage",
        "Carne Cerdo",
    ),

    # --------------------------------------------------------
    # NUTS
    # --------------------------------------------------------

    (
        r"\b(chopped walnuts|walnuts|walnut)\b",
        "walnuts",
        "Nuez",
    ),

    (
        r"\b(sliced almonds|slivered almonds|almonds|almond)\b",
        "almonds",
        "Almendras",
    ),

    # --------------------------------------------------------
    # SAUCES / CONDIMENTS
    # --------------------------------------------------------

    (
        r"\b(worcestershire sauce)\b",
        "worcestershire sauce",
        "Salsa Inglesa",
    ),

    (
        r"\b(soy sauce)\b",
        "soy sauce",
        "Salsa de Soya",
    ),

    (
        r"\b(mayonnaise|mayo)\b",
        "mayonnaise",
        "Mayonesa",
    ),

    (
        r"\b(dijon mustard|yellow mustard|mustard)\b",
        "mustard",
        "Mostaza",
    ),

    (
        r"\b(ketchup|catsup)\b",
        "ketchup",
        "Salsa Catsup",
    ),

    (
        r"^(vinegar|white vinegar)$",
        "vinegar",
        "Vinagre",
    ),

    (
        r"\b(cider vinegar|apple cider vinegar)\b",
        "cider vinegar",
        "Vinagre",
    ),

    (
        r"^salsa$",
        "salsa",
        "Salsa Picante y Similares",
    ),

    (
        r"\b(tabasco sauce|hot sauce)\b",
        "hot sauce",
        "Salsa Picante y Similares",
    ),

    (
        r"\b(chili sauce)\b",
        "chili sauce",
        "Salsa Picante y Similares",
    ),

    # --------------------------------------------------------
    # SWEETENERS
    # --------------------------------------------------------

    (
        r"\b(honey)\b",
        "honey",
        "Miel de Abeja",
    ),

    # --------------------------------------------------------
    # ALCOHOL USED IN RECIPES
    # --------------------------------------------------------

    (
        r"\b(rum)\b",
        "rum",
        "Ron",
    ),

    (
        r"\b(brandy)\b",
        "brandy",
        "Brandy",
    ),
]


# ============================================================
# MATCH FUNCTION
# ============================================================

def map_ingredient(value):
    text = normalize_text(value)

    for pattern, canonical, profeco in RULES:
        if re.search(pattern, text):
            return canonical, profeco

    return None, None


# ============================================================
# LOAD COMPLETE FREQUENCY TABLE
# ============================================================

print("Loading complete ingredient universe...")

df = pd.read_csv(FREQUENCIES_PATH)

print(f"Unique ingredient strings: {len(df):,}")
print(f"Total occurrences: {df['occurrences'].sum():,}")


# ============================================================
# MAP ALL INGREDIENT STRINGS
# ============================================================

mapped = df["ingredient"].apply(map_ingredient)

df[
    [
        "canonical_ingredient",
        "profeco_category",
    ]
] = pd.DataFrame(
    mapped.tolist(),
    index=df.index,
)

df["has_profeco_price"] = (
    df["profeco_category"].notna()
)


# ============================================================
# COVERAGE
# ============================================================

total_unique = len(df)

mapped_unique = int(
    df["has_profeco_price"].sum()
)

total_occurrences = int(
    df["occurrences"].sum()
)

mapped_occurrences = int(
    df.loc[
        df["has_profeco_price"],
        "occurrences",
    ].sum()
)

unique_coverage = (
    mapped_unique
    / total_unique
    * 100
)

occurrence_coverage = (
    mapped_occurrences
    / total_occurrences
    * 100
)


# ============================================================
# SAVE COMPLETE MAPPING TABLE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# SUMMARY
# ============================================================

summary = (
    df[
        df["has_profeco_price"]
    ]
    .groupby(
        [
            "canonical_ingredient",
            "profeco_category",
        ],
        as_index=False,
    )
    ["occurrences"]
    .sum()
    .sort_values(
        "occurrences",
        ascending=False,
    )
)

summary["percentage"] = (
    summary["occurrences"]
    / total_occurrences
    * 100
)


# ============================================================
# MOST FREQUENT UNMATCHED
# ============================================================

unmatched = (
    df[
        ~df["has_profeco_price"]
    ]
    [
        [
            "ingredient",
            "occurrences",
        ]
    ]
    .sort_values(
        "occurrences",
        ascending=False,
    )
    .head(100)
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 70)
print("COMPLETE RECIPE INGREDIENT COVERAGE")
print("=" * 70)

print(
    f"Unique ingredient strings: "
    f"{total_unique:,}"
)

print(
    f"Mapped ingredient strings: "
    f"{mapped_unique:,}"
)

print(
    f"Unique-string coverage: "
    f"{unique_coverage:.2f}%"
)

print()

print(
    f"Total ingredient occurrences: "
    f"{total_occurrences:,}"
)

print(
    f"Mapped ingredient occurrences: "
    f"{mapped_occurrences:,}"
)

print(
    f"Occurrence coverage: "
    f"{occurrence_coverage:.2f}%"
)

print(
    "\n=== COVERAGE BY CANONICAL INGREDIENT ==="
)

print(
    summary.to_string(
        index=False
    )
)

print(
    "\n=== MOST FREQUENT UNMATCHED ==="
)

print(
    unmatched.to_string(
        index=False
    )
)

print("\nSaved:")
print(OUTPUT_PATH)
