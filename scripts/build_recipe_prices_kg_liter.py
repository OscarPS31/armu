from pathlib import Path

import numpy as np
import pandas as pd


QUANTITIES_PATH = Path(
    "data/recipe_ingredients_quantities_clean.csv"
)

MAPPING_PATH = Path(
    "data/ingredient_mapping_all.csv"
)

PRICES_PATH = Path(
    "data/ingredient_prices_top3_chains_clean.csv"
)

RECIPES_PATH = Path(
    "data/Kaggle/recipes_ingredients.csv"
)

OUTPUT_PATH = Path(
    "data/recipe_prices_kg_liter.csv"
)


# ============================================================
# CONVERSIONS
# ============================================================

LITERS_PER_UNIT = {
    "taza": 0.236588,
    "cucharada": 0.0147868,
    "cucharadita": 0.00492892,
}

LIQUIDS = {
    "water",
    "milk",
    "cream",
    "olive oil",
    "vegetable oil",
    "canola oil",
    "corn oil",
    "sesame oil",
    "vinegar",
    "cider vinegar",
    "white vinegar",
    "lemon juice",
    "lime juice",
    "orange juice",
    "tomato juice",
    "soy sauce",
    "chili sauce",
    "hot sauce",
    "brandy",
    "rum",
    "wine",
}

GRAMS_PER_CUP = {
    "all-purpose flour": 120,
    "flour": 120,
    "plain flour": 120,
    "cornstarch": 128,
    "sugar": 200,
    "brown sugar": 220,
    "powdered sugar": 120,
    "rice": 185,
    "oats": 90,
    "butter": 227,
    "margarine": 227,
    "peanut butter": 258,
    "almonds": 143,
    "pecan": 109,
    "walnuts": 117,
    "black beans": 172,
    "kidney beans": 177,
    "pinto beans": 171,
    "white beans": 179,
    "parmesan cheese": 100,
    "cheddar cheese": 113,
    "mozzarella cheese": 112,
    "spinach": 30,
    "cilantro": 16,
    "parsley": 60,
    "onion": 160,
    "green onion": 100,
    "tomato": 180,
    "carrot": 128,
    "corn": 165,
    "peas": 160,
    "mushrooms": 70,
    "avocado": 150,
    "coconut": 80,
}

GRAMS_PER_PIECE = {
    "egg": 50,
    "apple": 182,
    "banana": 118,
    "orange": 131,
    "lemon": 58,
    "lime": 67,
    "avocado": 150,
    "onion": 110,
    "red onion": 110,
    "green pepper": 120,
    "bell pepper": 120,
    "tomato": 123,
    "potato": 173,
    "sweet potato": 130,
    "carrot": 61,
    "zucchini": 196,
    "cucumber": 200,
    "eggplant": 458,
    "cauliflower": 575,
    "lettuce": 539,
    "artichoke": 128,
    "garlic": 3,
}

GRAMS_PER_BUNCH = {
    "cilantro": 100,
    "green onion": 100,
    "radish": 250,
    "spinach": 250,
    "parsley": 100,
}

GRAMS_PER_SLICE = {
    "bacon": 8,
    "bread": 25,
    "french bread": 30,
    "cheddar cheese": 20,
    "mozzarella cheese": 20,
}


# ============================================================
# HELPERS
# ============================================================

def norm(series):
    return (
        series
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )


# ============================================================
# LOAD
# ============================================================

print("Loading recipe quantities...")
q = pd.read_csv(
    QUANTITIES_PATH,
    low_memory=False,
)

print("Loading ingredient mapping...")
mapping = pd.read_csv(
    MAPPING_PATH,
    low_memory=False,
)

print("Loading clean PROFECO prices...")
prices = pd.read_csv(
    PRICES_PATH,
    low_memory=False,
)

print("Loading recipe names...")
recipes = pd.read_csv(
    RECIPES_PATH,
    usecols=["id", "name"],
    low_memory=False,
)


# ============================================================
# INGREDIENT MAPPING
# ============================================================

q["ingredient_key"] = norm(
    q["ingrediente"]
)

mapping["ingredient_key"] = norm(
    mapping["ingredient"]
)

mapping = (
    mapping[
        mapping["has_profeco_price"] == True
    ][
        [
            "ingredient_key",
            "canonical_ingredient",
        ]
    ]
    .dropna()
    .drop_duplicates("ingredient_key")
)

q = q.merge(
    mapping,
    on="ingredient_key",
    how="left",
)

q["canonical_key"] = norm(
    q["canonical_ingredient"]
)


# ============================================================
# ALIASES
# ============================================================

q["canonical_key"] = q["canonical_key"].replace(
    {
        "coriander": "cilantro",
        "scallion": "green onion",
    }
)


# ============================================================
# RECIPE NAMES
# ============================================================

recipes = recipes.rename(
    columns={
        "id": "id_receta",
        "name": "nombre_receta",
    }
)

q = q.merge(
    recipes,
    on="id_receta",
    how="left",
)


# ============================================================
# QUANTITY -> GRAMS / LITERS
# ============================================================

def convert_quantity(row):

    canonical = str(
        row["canonical_key"]
    ).strip()

    unit = row["unidad_normalizada"]

    amount = pd.to_numeric(
        row["cantidad_normalizada"],
        errors="coerce",
    )

    if pd.isna(amount) or amount <= 0:
        return pd.Series(
            [np.nan, None, "sin_conversion"]
        )

    # already grams
    if unit == "gramo":
        return pd.Series(
            [amount, "gramos", "directa"]
        )

    # ml -> liters
    if unit == "mililitro":
        return pd.Series(
            [amount / 1000, "litros", "directa"]
        )

    # cups / spoons
    if unit in LITERS_PER_UNIT:

        liters = (
            amount
            * LITERS_PER_UNIT[unit]
        )

        if canonical in LIQUIDS:
            return pd.Series(
                [
                    liters,
                    "litros",
                    "volumen",
                ]
            )

        if canonical in GRAMS_PER_CUP:

            cup_fraction = (
                liters
                / LITERS_PER_UNIT["taza"]
            )

            grams = (
                cup_fraction
                * GRAMS_PER_CUP[canonical]
            )

            return pd.Series(
                [
                    grams,
                    "gramos",
                    "densidad_aproximada",
                ]
            )

    # pieces -> grams
    if (
        unit == "pieza"
        and canonical in GRAMS_PER_PIECE
    ):

        return pd.Series(
            [
                amount * GRAMS_PER_PIECE[canonical],
                "gramos",
                "peso_por_pieza_aproximado",
            ]
        )

    # garlic cloves
    if (
        unit == "diente"
        and canonical == "garlic"
    ):

        return pd.Series(
            [
                amount * 3,
                "gramos",
                "peso_por_diente_aproximado",
            ]
        )

    # bunch -> grams
    if (
        unit == "manojo"
        and canonical in GRAMS_PER_BUNCH
    ):

        return pd.Series(
            [
                amount * GRAMS_PER_BUNCH[canonical],
                "gramos",
                "peso_por_manojo_aproximado",
            ]
        )

    # slices -> grams
    if (
        unit == "rebanada"
        and canonical in GRAMS_PER_SLICE
    ):

        return pd.Series(
            [
                amount * GRAMS_PER_SLICE[canonical],
                "gramos",
                "peso_por_rebanada_aproximado",
            ]
        )

    return pd.Series(
        [np.nan, None, "sin_conversion"]
    )


q[
    [
        "cantidad",
        "unidad",
        "tipo_conversion",
    ]
] = q.apply(
    convert_quantity,
    axis=1,
)


q = q[
    q["unidad"].isin(
        ["gramos", "litros"]
    )
].copy()


# ============================================================
# REMOVE KNOWN BAD SEMANTIC MAPPINGS
# ============================================================

ingredient_text = norm(
    q["ingrediente"]
)

canon = q["canonical_key"]

bad = (
    (
        ingredient_text.str.contains(
            "water chestnut",
            regex=False,
        )
        & canon.eq("water")
    )
    |
    (
        ingredient_text.str.contains(
            "vinegar",
            regex=False,
        )
        & canon.eq("rice")
    )
    |
    (
        ingredient_text.str.contains(
            r"tomato (?:sauce|paste|juice|puree)",
            regex=True,
            na=False,
        )
        & canon.eq("tomato")
    )
    |
    (
        ingredient_text.str.contains(
            "ketchup",
            regex=False,
        )
        & canon.eq("tomato")
    )
    |
    (
        ingredient_text.str.contains(
            "peanut butter",
            regex=False,
        )
        & canon.eq("butter")
    )
    |
    (
        ingredient_text.str.contains(
            "cream cheese",
            regex=False,
        )
        & canon.eq("cream")
    )
    |
    (
        ingredient_text.str.contains(
            r"(?:beef|chicken|turkey|pork) (?:broth|stock)",
            regex=True,
            na=False,
        )
        & canon.isin(
            [
                "beef",
                "chicken",
                "turkey",
                "pork",
            ]
        )
    )
    |
    (
        ingredient_text.str.contains(
            "onion powder",
            regex=False,
        )
        & canon.eq("onion")
    )
    |
    (
        ingredient_text.str.contains(
            "garlic powder",
            regex=False,
        )
        & canon.eq("garlic")
    )
    |
    (
        ingredient_text.str.contains(
            r"(?:lemon|lime|orange) (?:juice|zest)",
            regex=True,
            na=False,
        )
        & canon.isin(
            ["lemon", "lime", "orange"]
        )
    )
)

# Additional conservative semantic exclusions
bad = bad | (
    # onion soup mix is not fresh onion
    (
        ingredient_text.str.contains(
            "onion soup mix",
            regex=False,
        )
        & canon.eq("onion")
    )
    |
    # fruit juices are not whole fruit
    (
        ingredient_text.str.contains(
            "juice",
            regex=False,
        )
        & canon.isin(
            [
                "apple",
                "pineapple",
                "lemon",
                "lime",
                "orange",
                "grapefruit",
            ]
        )
    )
    |
    # sodas / beverages are not fresh fruit
    (
        ingredient_text.str.contains(
            r"\\b(?:beverage|soda|soft drink)\\b",
            regex=True,
            na=False,
        )
        & canon.isin(
            [
                "apple",
                "pineapple",
                "lemon",
                "lime",
                "orange",
                "grapefruit",
            ]
        )
    )
    |
    # sherbet / sorbet are not fresh fruit
    (
        ingredient_text.str.contains(
            r"\\b(?:sherbet|sorbet)\\b",
            regex=True,
            na=False,
        )
        & canon.isin(
            [
                "apple",
                "pineapple",
                "lemon",
                "lime",
                "orange",
                "grapefruit",
            ]
        )
    )
)

q = q.loc[~bad].copy()


# ============================================================
# PREPARE PRICE TABLE
#
# IMPORTANT:
#
# solids -> ONLY option B / 1000 gramos
# liquids -> ONLY option A / litro
#
# pieza/manojo are NOT converted to kg.
# ============================================================

prices["canonical_key"] = norm(
    prices["ingrediente"]
)

prices["canonical_key"] = (
    prices["canonical_key"]
    .replace(
        {
            "coriander": "cilantro",
            "scallion": "green onion",
        }
    )
)


# ------------------------------------------------------------
# SOLID PRICE: MXN / 1000 GRAMS
# ------------------------------------------------------------

solid_prices = prices[
    prices["unidad_opcion_b"]
    .astype(str)
    .str.lower()
    .str.strip()
    .eq("1000 gramos")
].copy()

solid_prices["precio_kg_litro_mxn"] = (
    pd.to_numeric(
        solid_prices["precio_opcion_b_mxn"],
        errors="coerce",
    )
)

solid_prices["unidad_precio"] = "kg"

solid_prices = solid_prices[
    [
        "cadena",
        "canonical_key",
        "producto_profeco",
        "precio_kg_litro_mxn",
        "unidad_precio",
    ]
]


# ------------------------------------------------------------
# LIQUID PRICE: MXN / LITER
# ------------------------------------------------------------

liquid_prices = prices[
    prices["unidad_opcion_a"]
    .astype(str)
    .str.lower()
    .str.strip()
    .eq("litro")
].copy()

liquid_prices["precio_kg_litro_mxn"] = (
    pd.to_numeric(
        liquid_prices["precio_opcion_a_mxn"],
        errors="coerce",
    )
)

liquid_prices["unidad_precio"] = "litro"

liquid_prices = liquid_prices[
    [
        "cadena",
        "canonical_key",
        "producto_profeco",
        "precio_kg_litro_mxn",
        "unidad_precio",
    ]
]


price_table = pd.concat(
    [
        solid_prices,
        liquid_prices,
    ],
    ignore_index=True,
)


price_table = price_table[
    price_table["precio_kg_litro_mxn"].notna()
    & (
        price_table["precio_kg_litro_mxn"] > 0
    )
].copy()


# ============================================================
# JOIN RECIPE + PRICE
# ============================================================

df = q.merge(
    price_table,
    on="canonical_key",
    how="inner",
)


# ============================================================
# MATCH UNITS STRICTLY
# ============================================================

compatible = (
    (
        (df["unidad"] == "gramos")
        & (df["unidad_precio"] == "kg")
    )
    |
    (
        (df["unidad"] == "litros")
        & (df["unidad_precio"] == "litro")
    )
)

df = df.loc[
    compatible
].copy()


# ============================================================
# REMOVE EXACT DUPLICATE INGREDIENT ROWS
# ============================================================

duplicate_cols = [
    "id_receta",
    "ingrediente",
    "ingrediente_original",
    "canonical_key",
    "cantidad",
    "unidad",
    "cadena",
    "producto_profeco",
    "precio_kg_litro_mxn",
    "unidad_precio",
]

before_dedupe = len(df)

df = df.drop_duplicates(
    subset=duplicate_cols,
    keep="first",
).copy()

print(
    "Exact duplicate ingredient-price rows removed:",
    f"{before_dedupe - len(df):,}",
)


# ============================================================
# COST
# ============================================================

df["costo_ingrediente_mxn"] = np.where(
    df["unidad"].eq("gramos"),

    (
        df["cantidad"]
        / 1000
        * df["precio_kg_litro_mxn"]
    ),

    (
        df["cantidad"]
        * df["precio_kg_litro_mxn"]
    ),
)


# ============================================================
# CLEAN NUMBERS
# ============================================================

df["cantidad"] = (
    df["cantidad"]
    .round(4)
)

df["precio_kg_litro_mxn"] = (
    df["precio_kg_litro_mxn"]
    .round(2)
)

df["costo_ingrediente_mxn"] = (
    df["costo_ingrediente_mxn"]
    .round(2)
)

df = df[
    df["costo_ingrediente_mxn"] > 0
].copy()


# ============================================================
# TOTAL PER RECIPE / CHAIN
# ============================================================

totals = (
    df.groupby(
        [
            "id_receta",
            "cadena",
        ],
        as_index=False,
    )
    .agg(
        precio_total_receta_mxn=(
            "costo_ingrediente_mxn",
            "sum",
        ),
        ingredientes_con_precio=(
            "ingrediente",
            "count",
        ),
    )
)

totals["precio_total_receta_mxn"] = (
    totals["precio_total_receta_mxn"]
    .round(2)
)

df = df.merge(
    totals,
    on=[
        "id_receta",
        "cadena",
    ],
    how="left",
)


# ============================================================
# FINAL
# ============================================================

final = df[
    [
        "id_receta",
        "nombre_receta",
        "ingrediente",
        "ingrediente_original",
        "canonical_ingredient",
        "cantidad",
        "unidad",
        "cadena",
        "producto_profeco",
        "precio_kg_litro_mxn",
        "unidad_precio",
        "costo_ingrediente_mxn",
        "precio_total_receta_mxn",
        "ingredientes_con_precio",
        "tipo_conversion",
    ]
].copy()

final = final.rename(
    columns={
        "canonical_ingredient":
        "ingrediente_homologado",
    }
)

final = final.sort_values(
    [
        "id_receta",
        "cadena",
        "ingrediente",
    ]
).reset_index(drop=True)


final.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 90)
print("FINAL RECIPE + CORRECT PROFECO PRICE DATASET")
print("=" * 90)

print(
    "\nRows:",
    f"{len(final):,}",
)

print(
    "Recipes:",
    f"{final['id_receta'].nunique():,}",
)

print("\n=== RECIPE UNITS ===")
print(
    final["unidad"]
    .value_counts()
    .to_string()
)

print("\n=== PRICE UNITS ===")
print(
    final["unidad_precio"]
    .value_counts()
    .to_string()
)

print("\n=== CHAINS ===")
print(
    final["cadena"]
    .value_counts()
    .to_string()
)

print("\n=== PRICE SAMPLE ===")

print(
    final[
        [
            "nombre_receta",
            "ingrediente",
            "cantidad",
            "unidad",
            "cadena",
            "precio_kg_litro_mxn",
            "unidad_precio",
            "costo_ingrediente_mxn",
            "precio_total_receta_mxn",
        ]
    ]
    .head(30)
    .to_string(index=False)
)

print("\n=== VALIDATION ===")

print(
    "Unexpected recipe units:",
    int(
        (
            ~final["unidad"]
            .isin(["gramos", "litros"])
        ).sum()
    ),
)

print(
    "Unexpected price units:",
    int(
        (
            ~final["unidad_precio"]
            .isin(["kg", "litro"])
        ).sum()
    ),
)

print(
    "Null prices:",
    int(
        final["precio_kg_litro_mxn"]
        .isna()
        .sum()
    ),
)

print(
    "Price <= 0:",
    int(
        (
            final["precio_kg_litro_mxn"]
            <= 0
        ).sum()
    ),
)

print(
    "Cost <= 0:",
    int(
        (
            final["costo_ingrediente_mxn"]
            <= 0
        ).sum()
    ),
)

print(
    "Piece/bunch price rows:",
    int(
        final["unidad_precio"]
        .isin(["pieza", "manojo"])
        .sum()
    ),
)

print("\nSaved:")
print(OUTPUT_PATH)
