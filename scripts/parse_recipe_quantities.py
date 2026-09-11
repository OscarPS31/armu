import ast
import re
from fractions import Fraction
from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/Kaggle/recipes_ingredients.csv")
OUTPUT_PATH = Path("data/recipe_ingredients_quantities.csv")


# ============================================================
# HELPERS
# ============================================================

UNICODE_FRACTIONS = {
    "½": "1/2",
    "⅓": "1/3",
    "⅔": "2/3",
    "¼": "1/4",
    "¾": "3/4",
    "⅕": "1/5",
    "⅖": "2/5",
    "⅗": "3/5",
    "⅘": "4/5",
    "⅙": "1/6",
    "⅚": "5/6",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8",
}


def parse_list(value):
    if pd.isna(value):
        return []

    try:
        result = ast.literal_eval(value)
        return result if isinstance(result, list) else []
    except Exception:
        return []


def clean_text(value):
    text = str(value).lower().strip()

    for old, new in UNICODE_FRACTIONS.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text


def parse_single_number(text):
    text = text.strip()

    # Mixed number: 1 1/2
    match = re.fullmatch(
        r"(\d+)\s+(\d+)/(\d+)",
        text,
    )

    if match:
        whole = float(match.group(1))
        fraction = float(
            Fraction(
                int(match.group(2)),
                int(match.group(3)),
            )
        )
        return whole + fraction

    # Fraction
    match = re.fullmatch(
        r"(\d+)/(\d+)",
        text,
    )

    if match:
        return float(
            Fraction(
                int(match.group(1)),
                int(match.group(2)),
            )
        )

    # Decimal / integer
    try:
        return float(text)
    except Exception:
        return None


def parse_quantity(text):
    """
    Returns:
        quantity_min
        quantity_max
        quantity_estimate
        quantity_text
    """

    text = clean_text(text)

    # Range:
    # 1-2
    # 1 - 2
    # 1/2-1
    # 12 -14
    range_match = re.match(
        r"^\s*"
        r"(\d+(?:\s+\d+/\d+|/\d+|\.\d+)?)"
        r"\s*-\s*"
        r"(\d+(?:\s+\d+/\d+|/\d+|\.\d+)?)"
        r"\b",
        text,
    )

    if range_match:
        left = parse_single_number(
            range_match.group(1)
        )
        right = parse_single_number(
            range_match.group(2)
        )

        if left is not None and right is not None:
            return (
                left,
                right,
                (left + right) / 2,
                range_match.group(0).strip(),
            )

    # Single mixed number / fraction / decimal / integer
    number_match = re.match(
        r"^\s*"
        r"("
        r"\d+\s+\d+/\d+"
        r"|"
        r"\d+/\d+"
        r"|"
        r"\d+(?:\.\d+)?"
        r")",
        text,
    )

    if number_match:
        value = parse_single_number(
            number_match.group(1)
        )

        if value is not None:
            return (
                value,
                value,
                value,
                number_match.group(1),
            )

    return (
        None,
        None,
        None,
        None,
    )


# ============================================================
# UNIT DETECTION
# ============================================================

UNIT_PATTERNS = [
    (
        "kilogram",
        r"\b(?:kg|kilogram|kilograms)\b",
    ),
    (
        "gram",
        r"\b(?:g|gr|gram|grams)\b",
    ),
    (
        "fluid_ounce",
        r"\b(?:fluid ounce|fluid ounces|fl oz)\b",
    ),
    (
        "ounce",
        r"\b(?:oz|ounce|ounces)\b",
    ),
    (
        "pound",
        r"\b(?:lb|lbs|pound|pounds)\b",
    ),
    (
        "milliliter",
        r"\b(?:ml|milliliter|milliliters)\b",
    ),
    (
        "liter",
        r"\b(?:l|liter|liters|litre|litres)\b",
    ),
    (
        "cup",
        r"\b(?:cup|cups)\b",
    ),
    (
        "tablespoon",
        r"\b(?:tbsp|tablespoon|tablespoons|table spoon|table spoons)\b",
    ),
    (
        "teaspoon",
        r"\b(?:tsp|teaspoon|teaspoons)\b",
    ),
    (
        "piece",
        r"\b(?:piece|pieces)\b",
    ),
    (
        "slice",
        r"\b(?:slice|slices)\b",
    ),
    (
        "bunch",
        r"\b(?:bunch|bunches)\b",
    ),
    (
        "head",
        r"\b(?:head|heads)\b",
    ),
    (
        "clove",
        r"\b(?:clove|cloves)\b",
    ),
    (
        "stalk",
        r"\b(?:stalk|stalks)\b",
    ),
    (
        "can",
        r"\b(?:can|cans)\b",
    ),
    (
        "package",
        r"\b(?:package|packages|pkg|pkgs)\b",
    ),
    (
        "pinch",
        r"\b(?:pinch|pinches)\b",
    ),
    (
        "dash",
        r"\b(?:dash|dashes)\b",
    ),
]


def detect_unit(text):
    text = clean_text(text)

    for unit, pattern in UNIT_PATTERNS:
        if re.search(pattern, text):
            return unit

    return None


# ============================================================
# PACKAGE WEIGHT
# ============================================================

PACKAGE_PATTERN = re.compile(
    r"^\s*"
    r"(?P<count>\d+(?:\s+\d+/\d+|/\d+|\.\d+)?)"
    r"\s*"
    r"\("
    r"\s*"
    r"(?P<size>\d+(?:\s+\d+/\d+|/\d+|\.\d+)?)"
    r"\s*"
    r"(?P<unit>"
    r"kg|kilograms?|"
    r"g|grams?|"
    r"lb|lbs|pounds?|"
    r"oz|ounces?"
    r")"
    r"\s*"
    r"\)",
    flags=re.IGNORECASE,
)


def parse_package_weight(text):
    text = clean_text(text)

    match = PACKAGE_PATTERN.search(text)

    if not match:
        return None

    count = parse_single_number(
        match.group("count")
    )

    size = parse_single_number(
        match.group("size")
    )

    unit = match.group("unit").lower()

    if count is None or size is None:
        return None

    total = count * size

    if unit in {
        "kg",
        "kilogram",
        "kilograms",
    }:
        grams = total * 1000

    elif unit in {
        "g",
        "gram",
        "grams",
    }:
        grams = total

    elif unit in {
        "lb",
        "lbs",
        "pound",
        "pounds",
    }:
        grams = total * 453.59237

    elif unit in {
        "oz",
        "ounce",
        "ounces",
    }:
        grams = total * 28.349523125

    else:
        return None

    return {
        "package_count": count,
        "package_size": size,
        "package_unit": unit,
        "normalized_quantity": grams,
        "normalized_unit": "gramo",
        "conversion_type": "package_mass_exact",
        "confidence": "high",
    }


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_quantity(
    ingredient,
    raw_text,
):
    text = clean_text(raw_text)

    result = {
        "quantity_min": None,
        "quantity_max": None,
        "quantity_estimate": None,
        "unit_original": None,
        "normalized_quantity": None,
        "normalized_unit": None,
        "conversion_type": "unparsed",
        "confidence": "low",
    }

    # --------------------------------------------------------
    # Subjective quantities
    # --------------------------------------------------------

    if re.search(
        r"\bto taste\b",
        text,
    ):
        result.update(
            {
                "conversion_type": "to_taste",
                "confidence": "low",
            }
        )
        return result

    if re.search(
        r"\b(?:pinch|pinches)\b",
        text,
    ):
        qmin, qmax, qest, _ = parse_quantity(
            text
        )

        result.update(
            {
                "quantity_min": qmin,
                "quantity_max": qmax,
                "quantity_estimate": qest,
                "unit_original": "pinch",
                "normalized_unit": "pinch",
                "conversion_type": "subjective",
                "confidence": "low",
            }
        )

        return result

    if re.search(
        r"\b(?:dash|dashes)\b",
        text,
    ):
        qmin, qmax, qest, _ = parse_quantity(
            text
        )

        result.update(
            {
                "quantity_min": qmin,
                "quantity_max": qmax,
                "quantity_estimate": qest,
                "unit_original": "dash",
                "normalized_unit": "dash",
                "conversion_type": "subjective",
                "confidence": "low",
            }
        )

        return result

    if re.search(
        r"\bglug\b",
        text,
    ):
        result.update(
            {
                "unit_original": "glug",
                "normalized_unit": "glug",
                "conversion_type": "subjective",
                "confidence": "low",
            }
        )

        return result

    # --------------------------------------------------------
    # Package with explicit mass
    #
    # 2 (14 ounce) cans black beans
    # 1 (8 ounce) package cream cheese
    # --------------------------------------------------------

    package = parse_package_weight(
        text
    )

    if package:
        result.update(package)
        return result

    # --------------------------------------------------------
    # General quantity
    # --------------------------------------------------------

    qmin, qmax, qest, _ = parse_quantity(
        text
    )

    unit = detect_unit(text)

    result["quantity_min"] = qmin
    result["quantity_max"] = qmax
    result["quantity_estimate"] = qest
    result["unit_original"] = unit

    # --------------------------------------------------------
    # Exact mass
    # --------------------------------------------------------

    if (
        qest is not None
        and unit == "gram"
    ):
        result.update(
            {
                "normalized_quantity": qest,
                "normalized_unit": "gramo",
                "conversion_type": "mass_exact",
                "confidence": "high",
            }
        )

        return result

    if (
        qest is not None
        and unit == "kilogram"
    ):
        result.update(
            {
                "normalized_quantity": qest * 1000,
                "normalized_unit": "gramo",
                "conversion_type": "mass_exact",
                "confidence": "high",
            }
        )

        return result

    if (
        qest is not None
        and unit == "pound"
    ):
        result.update(
            {
                "normalized_quantity": (
                    qest * 453.59237
                ),
                "normalized_unit": "gramo",
                "conversion_type": "mass_exact",
                "confidence": "high",
            }
        )

        return result

    if (
        qest is not None
        and unit == "ounce"
    ):
        result.update(
            {
                "normalized_quantity": (
                    qest * 28.349523125
                ),
                "normalized_unit": "gramo",
                "conversion_type": "mass_exact",
                "confidence": "high",
            }
        )

        return result

    # --------------------------------------------------------
    # Explicit liquid measures
    # --------------------------------------------------------

    if (
        qest is not None
        and unit == "milliliter"
    ):
        result.update(
            {
                "normalized_quantity": qest,
                "normalized_unit": "mililitro",
                "conversion_type": "volume_exact",
                "confidence": "high",
            }
        )

        return result

    if (
        qest is not None
        and unit == "liter"
    ):
        result.update(
            {
                "normalized_quantity": qest * 1000,
                "normalized_unit": "mililitro",
                "conversion_type": "volume_exact",
                "confidence": "high",
            }
        )

        return result

    if (
        qest is not None
        and unit == "fluid_ounce"
    ):
        result.update(
            {
                "normalized_quantity": (
                    qest * 29.5735295625
                ),
                "normalized_unit": "mililitro",
                "conversion_type": "volume_exact",
                "confidence": "high",
            }
        )

        return result

    # --------------------------------------------------------
    # Recipe volume measurements
    #
    # We preserve them instead of pretending a cup of flour
    # weighs the same as a cup of oil.
    # --------------------------------------------------------

    if (
        qest is not None
        and unit in {
            "cup",
            "tablespoon",
            "teaspoon",
        }
    ):
        result.update(
            {
                "normalized_quantity": qest,
                "normalized_unit": unit,
                "conversion_type": (
                    "volume_needs_ingredient_density"
                ),
                "confidence": "medium",
            }
        )

        return result

    # --------------------------------------------------------
    # Countable units
    # --------------------------------------------------------

    if (
        qest is not None
        and unit in {
            "piece",
            "slice",
            "bunch",
            "head",
            "clove",
            "stalk",
            "can",
            "package",
        }
    ):
        result.update(
            {
                "normalized_quantity": qest,
                "normalized_unit": unit,
                "conversion_type": "count",
                "confidence": "medium",
            }
        )

        return result

    # --------------------------------------------------------
    # Quantity but no written unit
    #
    # Example:
    # 4 pork chops
    # 2 avocados
    # 1 banana
    #
    # Treat as count/piece for now.
    # --------------------------------------------------------

    if (
        qest is not None
        and unit is None
    ):
        result.update(
            {
                "normalized_quantity": qest,
                "normalized_unit": "pieza",
                "conversion_type": "implicit_count",
                "confidence": "medium",
            }
        )

        return result

    return result


# ============================================================
# PROCESS DATASET
# ============================================================

print("Loading recipes...")

df = pd.read_csv(
    INPUT_PATH,
    usecols=[
        "id",
        "ingredients",
        "ingredients_raw",
    ],
)

records = []

recipes_aligned = 0
recipes_skipped = 0


for _, row in df.iterrows():

    ingredients = parse_list(
        row["ingredients"]
    )

    raw = parse_list(
        row["ingredients_raw"]
    )

    if (
        not ingredients
        or not raw
        or len(ingredients) != len(raw)
    ):
        recipes_skipped += 1
        continue

    recipes_aligned += 1

    for position, (
        ingredient,
        raw_text,
    ) in enumerate(
        zip(
            ingredients,
            raw,
        )
    ):

        parsed = normalize_quantity(
            ingredient,
            raw_text,
        )

        records.append(
            {
                "recipe_id": row["id"],
                "ingredient_position": position,
                "ingredient": ingredient,
                "ingredient_raw": raw_text,
                **parsed,
            }
        )


result = pd.DataFrame(records)


# ============================================================
# ROUND
# ============================================================

for column in [
    "quantity_min",
    "quantity_max",
    "quantity_estimate",
    "normalized_quantity",
]:
    result[column] = (
        pd.to_numeric(
            result[column],
            errors="coerce",
        )
        .round(4)
    )


# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 90)
print("RECIPE QUANTITY PARSER")
print("=" * 90)

print(
    f"\nRecipes aligned: "
    f"{recipes_aligned:,}"
)

print(
    f"Recipes skipped because lists differ: "
    f"{recipes_skipped:,}"
)

print(
    f"Ingredient rows generated: "
    f"{len(result):,}"
)


print("\n=== CONVERSION TYPES ===")

print(
    result[
        "conversion_type"
    ]
    .value_counts()
    .to_string()
)


print("\n=== CONFIDENCE ===")

print(
    result[
        "confidence"
    ]
    .value_counts()
    .to_string()
)


print("\n=== NORMALIZED UNIT ===")

print(
    result[
        "normalized_unit"
    ]
    .value_counts(
        dropna=False
    )
    .head(20)
    .to_string()
)


print("\n=== SAMPLE EXACT MASS ===")

print(
    result[
        result["conversion_type"].isin(
            [
                "mass_exact",
                "package_mass_exact",
            ]
        )
    ][
        [
            "ingredient",
            "ingredient_raw",
            "normalized_quantity",
            "normalized_unit",
            "conversion_type",
        ]
    ]
    .head(20)
    .to_string(index=False)
)


print("\n=== SAMPLE IMPLICIT COUNT ===")

print(
    result[
        result[
            "conversion_type"
        ] == "implicit_count"
    ][
        [
            "ingredient",
            "ingredient_raw",
            "normalized_quantity",
            "normalized_unit",
        ]
    ]
    .head(20)
    .to_string(index=False)
)


print("\n=== SAMPLE SUBJECTIVE ===")

print(
    result[
        result[
            "conversion_type"
        ].isin(
            [
                "subjective",
                "to_taste",
            ]
        )
    ][
        [
            "ingredient",
            "ingredient_raw",
            "quantity_estimate",
            "normalized_unit",
            "conversion_type",
        ]
    ]
    .head(20)
    .to_string(index=False)
)


print("\nSaved:")
print(OUTPUT_PATH)
