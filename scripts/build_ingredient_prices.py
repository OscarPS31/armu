import os
import re
import unicodedata

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

PROFECO_PATH = "data/profeco_food.csv"
MAPPING_PATH = "data/ingredient_mapping_all.csv"
OUTPUT_PATH = "data/ingredient_prices.csv"

OUTPUT_COLUMNS = [
    "ingredient",
    "profeco_category",
    "price",
    "unit",
    "store",
]


# ============================================================
# TEXT NORMALIZATION
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

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# ============================================================
# SPECIFIC PRESENTATION FILTERS
#
# These prevent mappings such as "ground pork" from using
# prices for every possible pork presentation.
# ============================================================

PRESENTATION_RULES = {

    "cornstarch": {
        "include": [
            "fecula",
        ],
    },

    "cider vinegar": {
        "include": [
            "manzana",
        ],
    },

    "black beans": {
        "include": [
            "negro",
        ],
    },

    "orange juice": {
        "include": [
            "naranja",
        ],
    },

    "ground pork": {
        "include": [
            "molida",
            "pulpa molida",
        ],
    },

    "pork tenderloin": {
        "include": [
            "lomo",
            "cana de lomo",
        ],
    },

    "pork chops": {
        "include": [
            "chuleta",
        ],
    },

    "italian sausage": {
        "include": [
            "longaniza",
        ],
    },

    "jalapeno": {
        "include": [
            "jalapeno",
            "cuaresmeno",
        ],
    },

    "spaghetti": {
        "include": [
            "spaghetti",
            "espaguetti",
        ],
    },

    "macaroni": {
        "include": [
            "codo",
        ],
    },

    "plain yogurt": {
        "include": [
            "natural",
        ],
    },

    "green onion": {
        "include": [
            "cambray",
        ],
    },

    "scallion": {
        "include": [
            "cambray",
        ],
    },

    # Cornmeal is not the same as cornstarch.
    # We explicitly remove "fécula" presentations here.
    "cornmeal": {
        "exclude": [
            "fecula",
        ],
    },
}


# ============================================================
# PRESENTATION FILTER
# ============================================================

def apply_presentation_filter(
    df,
    canonical_ingredient,
):
    rule = PRESENTATION_RULES.get(
        canonical_ingredient
    )

    if rule is None:
        return df

    result = df.copy()

    presentation = (
        result["presentacion_normalizada"]
        .fillna("")
    )

    include_terms = rule.get(
        "include",
        [],
    )

    exclude_terms = rule.get(
        "exclude",
        [],
    )

    if include_terms:

        include_mask = pd.Series(
            False,
            index=result.index,
        )

        for term in include_terms:
            include_mask |= (
                presentation.str.contains(
                    normalize_text(term),
                    regex=False,
                    na=False,
                )
            )

        result = result[
            include_mask
        ].copy()

        presentation = (
            result["presentacion_normalizada"]
            .fillna("")
        )

    if exclude_terms:

        exclude_mask = pd.Series(
            False,
            index=result.index,
        )

        for term in exclude_terms:
            exclude_mask |= (
                presentation.str.contains(
                    normalize_text(term),
                    regex=False,
                    na=False,
                )
            )

        result = result[
            ~exclude_mask
        ].copy()

    return result


# ============================================================
# UNIT / QUANTITY PARSER
#
# Returns:
#   normalized_price
#   normalized_unit
#
# Examples:
#
#   500 Gr. at $50
#       -> $100 / kg
#
#   750 Ml. at $60
#       -> $80 / litro
#
#   Paquete C/12 at $48
#       -> $4 / pieza
#
#   Pieza at $10
#       -> $10 / pieza
#
# ============================================================

def normalize_price_unit(
    presentation,
    price,
):
    if pd.isna(price):
        return None, None

    try:
        price = float(price)
    except (TypeError, ValueError):
        return None, None

    if price <= 0:
        return None, None

    text = normalize_text(
        presentation
    )

    if not text:
        return None, None

    # --------------------------------------------------------
    # KG
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*kg\b",
        text,
    )

    if match:
        quantity = float(
            match.group(1).replace(",", ".")
        )

        if quantity > 0:
            return (
                price / quantity,
                "kg",
            )

    # --------------------------------------------------------
    # GRAMS -> KG
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(?:gr|g)\.?\b",
        text,
    )

    if match:
        grams = float(
            match.group(1).replace(",", ".")
        )

        if grams > 0:
            return (
                price * 1000 / grams,
                "kg",
            )

    # --------------------------------------------------------
    # LITERS
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(?:lt|lts|litro|litros|l)\.?\b",
        text,
    )

    if match:
        liters = float(
            match.group(1).replace(",", ".")
        )

        if liters > 0:
            return (
                price / liters,
                "litro",
            )

    # --------------------------------------------------------
    # ML -> LITER
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*ml\b",
        text,
    )

    if match:
        ml = float(
            match.group(1).replace(",", ".")
        )

        if ml > 0:
            return (
                price * 1000 / ml,
                "litro",
            )

    # --------------------------------------------------------
    # MULTI-PACK COUNT
    #
    # Examples:
    # C/12
    # C / 18
    # --------------------------------------------------------

    match = re.search(
        r"\bc\s*/\s*(\d+)\b",
        text,
    )

    if match:
        pieces = int(
            match.group(1)
        )

        if pieces > 0:
            return (
                price / pieces,
                "pieza",
            )

    # --------------------------------------------------------
    # PIECES / PIEZA
    # --------------------------------------------------------

    match = re.search(
        r"(\d+)\s*piezas?\b",
        text,
    )

    if match:
        pieces = int(
            match.group(1)
        )

        if pieces > 0:
            return (
                price / pieces,
                "pieza",
            )

    if re.search(
        r"\bpieza\b",
        text,
    ):
        return (
            price,
            "pieza",
        )

    # --------------------------------------------------------
    # MANOJO
    # --------------------------------------------------------

    if re.search(
        r"\bmanojo\b",
        text,
    ):
        return (
            price,
            "manojo",
        )

    # --------------------------------------------------------
    # NO SAFE NORMALIZATION
    # --------------------------------------------------------

    return None, None


# ============================================================
# LOAD DATA
# ============================================================

print(
    "Loading filtered PROFECO data..."
)

profeco = pd.read_csv(
    PROFECO_PATH
)

print(
    f"PROFECO rows: "
    f"{len(profeco):,}"
)


print(
    "\nLoading ingredient mapping..."
)

mapping = pd.read_csv(
    MAPPING_PATH
)

mapping = mapping[
    mapping["has_profeco_price"] == True
].copy()

mapping = (
    mapping[
        [
            "canonical_ingredient",
            "profeco_category",
        ]
    ]
    .dropna()
    .drop_duplicates()
)

print(
    f"Unique canonical mappings: "
    f"{len(mapping):,}"
)


# ============================================================
# PREPARE PROFECO
# ============================================================

profeco["producto_normalizado_match"] = (
    profeco["producto"]
    .map(normalize_text)
)

profeco["presentacion_normalizada"] = (
    profeco["presentacion"]
    .map(normalize_text)
)

profeco["precio"] = pd.to_numeric(
    profeco["precio"],
    errors="coerce",
)

profeco = profeco[
    profeco["precio"].notna()
].copy()

profeco = profeco[
    profeco["precio"] > 0
].copy()


# ============================================================
# STORE NAME
# ============================================================

if "cadena_comercial" in profeco.columns:

    profeco["store_final"] = (
        profeco["cadena_comercial"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

else:
    profeco["store_final"] = ""


if "nombre_comercial" in profeco.columns:

    fallback_store = (
        profeco["nombre_comercial"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    empty_store = (
        profeco["store_final"] == ""
    )

    profeco.loc[
        empty_store,
        "store_final",
    ] = fallback_store[
        empty_store
    ]


profeco.loc[
    profeco["store_final"] == "",
    "store_final",
] = "Unknown"


# ============================================================
# BUILD PRICE TABLE
# ============================================================

all_rows = []

no_profeco_rows = []
no_presentation_rows = []
no_normalizable_rows = []


print(
    "\nBuilding normalized ingredient prices..."
)


for _, mapping_row in mapping.iterrows():

    canonical = str(
        mapping_row[
            "canonical_ingredient"
        ]
    )

    profeco_product = str(
        mapping_row[
            "profeco_category"
        ]
    )

    target_product = normalize_text(
        profeco_product
    )

    subset = profeco[
        profeco[
            "producto_normalizado_match"
        ]
        == target_product
    ].copy()

    # --------------------------------------------------------
    # Product not found
    # --------------------------------------------------------

    if subset.empty:
        no_profeco_rows.append(
            (
                canonical,
                profeco_product,
            )
        )
        continue

    # --------------------------------------------------------
    # Apply ingredient-specific presentation filters
    # --------------------------------------------------------

    filtered_subset = (
        apply_presentation_filter(
            subset,
            canonical,
        )
    )

    if filtered_subset.empty:
        no_presentation_rows.append(
            (
                canonical,
                profeco_product,
            )
        )
        continue

    normalized_records = []

    # --------------------------------------------------------
    # Normalize every price observation
    # --------------------------------------------------------

    for _, row in filtered_subset.iterrows():

        normalized_price, unit = (
            normalize_price_unit(
                row.get(
                    "presentacion"
                ),
                row.get(
                    "precio"
                ),
            )
        )

        if (
            normalized_price is None
            or unit is None
        ):
            continue

        normalized_records.append(
            {
                "ingredient": canonical,
                "profeco_category": profeco_product,
                "price": normalized_price,
                "unit": unit,
                "store": row[
                    "store_final"
                ],
            }
        )

    if not normalized_records:
        no_normalizable_rows.append(
            (
                canonical,
                profeco_product,
            )
        )
        continue

    all_rows.extend(
        normalized_records
    )


# ============================================================
# DATAFRAME
# ============================================================

if not all_rows:

    raise RuntimeError(
        "No normalized ingredient prices were generated."
    )


result = pd.DataFrame(
    all_rows
)


# ============================================================
# REMOVE IMPOSSIBLE / EXTREME VALUES
#
# Conservative sanity check only.
# We do not aggressively remove legitimate expensive foods.
# ============================================================

result = result[
    result["price"].notna()
].copy()

result = result[
    result["price"] > 0
].copy()


# ============================================================
# AGGREGATE
#
# We use median because PROFECO contains multiple observations
# by date/location and median is more robust than mean.
# ============================================================

result = (
    result
    .groupby(
        [
            "ingredient",
            "profeco_category",
            "unit",
            "store",
        ],
        as_index=False,
    )
    ["price"]
    .median()
)


# ============================================================
# ROUND PRICES
# ============================================================

result["price"] = (
    result["price"]
    .round(2)
)


# ============================================================
# ORDER
# ============================================================

result = result[
    OUTPUT_COLUMNS
].sort_values(
    [
        "ingredient",
        "store",
        "unit",
    ]
).reset_index(
    drop=True
)


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print(
    "\n" + "=" * 70
)

print(
    "INGREDIENT PRICE DATASET COMPLETE"
)

print(
    "=" * 70
)

print(
    f"Rows generated: "
    f"{len(result):,}"
)

print(
    f"Ingredients with prices: "
    f"{result['ingredient'].nunique():,}"
)

print(
    f"PROFECO products used: "
    f"{result['profeco_category'].nunique():,}"
)

print(
    f"Stores: "
    f"{result['store'].nunique():,}"
)

print(
    "\nUnits:"
)

print(
    result[
        "unit"
    ]
    .value_counts()
    .to_string()
)

print(
    "\n=== SAMPLE ==="
)

print(
    result.head(30).to_string(
        index=False
    )
)


# ============================================================
# MAPPINGS WITHOUT USABLE PRICES
# ============================================================

if no_profeco_rows:

    print(
        "\n=== PRODUCT NOT FOUND IN PROFECO ==="
    )

    for canonical, product in no_profeco_rows:
        print(
            f"{canonical} -> {product}"
        )


if no_presentation_rows:

    print(
        "\n=== NO MATCHING PRESENTATION ==="
    )

    for canonical, product in no_presentation_rows:
        print(
            f"{canonical} -> {product}"
        )


if no_normalizable_rows:

    print(
        "\n=== PRICE PRESENTATION COULD NOT BE NORMALIZED ==="
    )

    for canonical, product in no_normalizable_rows:
        print(
            f"{canonical} -> {product}"
        )


# ============================================================
# FILE SIZE
# ============================================================

size_bytes = os.path.getsize(
    OUTPUT_PATH
)

size_mb = (
    size_bytes
    / 1024
    / 1024
)

print(
    "\nSaved:"
)

print(
    OUTPUT_PATH
)

print(
    f"File size: "
    f"{size_mb:.2f} MB"
)

print(
    "\nRequired columns:"
)

print(
    list(result.columns)
)
