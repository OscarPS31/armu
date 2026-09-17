import re
from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/recipe_ingredients_quantities.csv")
BACKUP_PATH = Path("data/recipe_ingredients_quantities_before_edge_fix.csv")


df = pd.read_csv(INPUT_PATH, low_memory=False)

df.to_csv(
    BACKUP_PATH,
    index=False,
    encoding="utf-8-sig",
)


def parse_number(value):
    value = value.strip()

    if " " in value and "/" in value:
        whole, frac = value.split(maxsplit=1)
        num, den = frac.split("/")
        return float(whole) + float(num) / float(den)

    if "/" in value:
        num, den = value.split("/")
        return float(num) / float(den)

    return float(value)


number = r"\d+(?:\s+\d+/\d+|/\d+|\.\d+)?"


mass_pattern = re.compile(
    rf"\(({number})\s*(kg|kilograms?|g|grams?|lb|lbs|pounds?|oz|ounces?)\)",
    re.IGNORECASE,
)

volume_pattern = re.compile(
    rf"\(({number})\s*(ml|milliliters?|l|liters?|litres?)\)",
    re.IGNORECASE,
)


fixed_mass = 0
fixed_volume = 0
fixed_fake_g = 0


for idx, row in df.iterrows():

    text = str(row["ingredient_raw"])

    # ========================================================
    # Explicit parenthetical mass has priority
    #
    # 1/4 cup flour (30 g) -> 30 g
    # ========================================================

    mass_match = mass_pattern.search(text)

    if mass_match:

        quantity = parse_number(
            mass_match.group(1)
        )

        unit = mass_match.group(2).lower()

        if unit in {"kg", "kilogram", "kilograms"}:
            grams = quantity * 1000

        elif unit in {"g", "gram", "grams"}:
            grams = quantity

        elif unit in {"lb", "lbs", "pound", "pounds"}:
            grams = quantity * 453.59237

        elif unit in {"oz", "ounce", "ounces"}:
            grams = quantity * 28.349523125

        else:
            grams = None

        if grams is not None:

            df.at[idx, "normalized_quantity"] = round(
                grams,
                4,
            )

            df.at[idx, "normalized_unit"] = "gramo"
            df.at[idx, "conversion_type"] = "mass_exact"
            df.at[idx, "confidence"] = "high"

            fixed_mass += 1

            continue

    # ========================================================
    # Explicit parenthetical volume has priority
    #
    # 1/4 cup water (50 ml) -> 50 ml
    # ========================================================

    volume_match = volume_pattern.search(text)

    if volume_match:

        quantity = parse_number(
            volume_match.group(1)
        )

        unit = volume_match.group(2).lower()

        if unit in {
            "ml",
            "milliliter",
            "milliliters",
        }:
            milliliters = quantity

        elif unit in {
            "l",
            "liter",
            "liters",
            "litre",
            "litres",
        }:
            milliliters = quantity * 1000

        else:
            milliliters = None

        if milliliters is not None:

            df.at[idx, "normalized_quantity"] = round(
                milliliters,
                4,
            )

            df.at[idx, "normalized_unit"] = "mililitro"
            df.at[idx, "conversion_type"] = "volume_exact"
            df.at[idx, "confidence"] = "high"

            fixed_volume += 1

            continue

    # ========================================================
    # Fix false "gram" produced by e.g.
    #
    # Example:
    # 1/8 cup sugar-free syrup (e.g. Mrs. Butterworth)
    #
    # If there is no real g/gram measurement, restore cup.
    # ========================================================

    lower = text.lower()

    fake_gram = (
        row["normalized_unit"] == "gramo"
        and "e.g." in lower
        and not re.search(
            r"(?<![a-z.])"
            r"\d+(?:\s+\d+/\d+|/\d+|\.\d+)?"
            r"\s*(?:g|gram|grams)"
            r"\b",
            lower,
        )
    )

    if fake_gram:

        cup_match = re.match(
            rf"^\s*({number})\s*cups?\b",
            lower,
        )

        if cup_match:

            quantity = parse_number(
                cup_match.group(1)
            )

            df.at[idx, "quantity_min"] = quantity
            df.at[idx, "quantity_max"] = quantity
            df.at[idx, "quantity_estimate"] = quantity

            df.at[idx, "normalized_quantity"] = quantity
            df.at[idx, "normalized_unit"] = "cup"

            df.at[
                idx,
                "conversion_type",
            ] = "volume_needs_ingredient_density"

            df.at[idx, "confidence"] = "medium"

            fixed_fake_g += 1


df.to_csv(
    INPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


print("=" * 80)
print("RECIPE QUANTITY EDGE-CASE FIX")
print("=" * 80)

print(f"Parenthetical mass fixed: {fixed_mass:,}")
print(f"Parenthetical volume fixed: {fixed_volume:,}")
print(f"False e.g. grams fixed: {fixed_fake_g:,}")

print("\nSaved:")
print(INPUT_PATH)
