import ast
import re
from collections import Counter
from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/Kaggle/recipes_ingredients.csv")


def parse_list(value):
    if pd.isna(value):
        return []

    try:
        parsed = ast.literal_eval(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


df = pd.read_csv(
    INPUT_PATH,
    usecols=["id", "ingredients", "ingredients_raw"],
)


unit_patterns = {
    "gram": r"\b(?:g|gr|gram|grams)\b",
    "kilogram": r"\b(?:kg|kilogram|kilograms)\b",
    "ounce": r"\b(?:oz|ounce|ounces)\b",
    "pound": r"\b(?:lb|lbs|pound|pounds)\b",
    "cup": r"\b(?:cup|cups)\b",
    "tablespoon": r"\b(?:tbsp|tablespoon|tablespoons)\b",
    "teaspoon": r"\b(?:tsp|teaspoon|teaspoons)\b",
    "piece": r"\b(?:piece|pieces)\b",
    "slice": r"\b(?:slice|slices)\b",
    "can": r"\b(?:can|cans)\b",
    "package": r"\b(?:package|packages|pkg)\b",
    "pinch": r"\b(?:pinch|pinches)\b",
    "dash": r"\b(?:dash|dashes)\b",
    "to_taste": r"\bto taste\b",
}


unit_counts = Counter()
examples = {key: [] for key in unit_patterns}
unclassified = []


total_rows = 0
aligned_rows = 0
ingredient_pairs = 0


for _, row in df.iterrows():

    ingredients = parse_list(row["ingredients"])
    raw = parse_list(row["ingredients_raw"])

    total_rows += 1

    if len(ingredients) != len(raw):
        continue

    aligned_rows += 1

    for ingredient, raw_text in zip(ingredients, raw):

        ingredient_pairs += 1

        text = str(raw_text).lower().strip()

        found = False

        for unit_name, pattern in unit_patterns.items():

            if re.search(pattern, text):

                unit_counts[unit_name] += 1
                found = True

                if len(examples[unit_name]) < 8:
                    examples[unit_name].append(
                        (
                            ingredient,
                            raw_text,
                        )
                    )

        if not found and len(unclassified) < 50:
            unclassified.append(
                (
                    ingredient,
                    raw_text,
                )
            )


print("=" * 90)
print("RECIPE QUANTITY AUDIT")
print("=" * 90)

print(f"\nRecipes: {total_rows:,}")
print(f"Recipes with aligned ingredient lists: {aligned_rows:,}")
print(f"Ingredient/raw pairs: {ingredient_pairs:,}")


print("\n=== UNIT COUNTS ===")

for unit, count in unit_counts.most_common():
    print(f"{unit:15} {count:,}")


print("\n=== EXAMPLES ===")

for unit in unit_patterns:

    print(f"\n--- {unit.upper()} ---")

    if not examples[unit]:
        print("NO EXAMPLES")
        continue

    for ingredient, raw_text in examples[unit]:
        print(
            f"{ingredient:<30} -> {raw_text}"
        )


print("\n=== UNCLASSIFIED SAMPLE ===")

for ingredient, raw_text in unclassified:
    print(
        f"{ingredient:<30} -> {raw_text}"
    )
