import pandas as pd
import ast

recipes = pd.read_csv(
    "raw_data/recipes.csv",
    usecols=[
        "RecipeId",
        "Name",
        "RecipeIngredientParts",
    ],
    nrows=5000,
)

def parse_ingredients(value):
    if pd.isna(value):
        return []

    value = str(value)

    # Food.com stores vectors like:
    # c("berries", "sugar", "lemon juice")
    if value.startswith('c('):
        value = value[2:-1]

    value = value.replace('"', "")

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


recipes["ingredients"] = recipes["RecipeIngredientParts"].apply(
    parse_ingredients
)

all_ingredients = (
    recipes["ingredients"]
    .explode()
    .dropna()
    .str.lower()
    .str.strip()
)

print("Unique ingredients:", all_ingredients.nunique())

print("\nMost common ingredients:")
print(all_ingredients.value_counts().head(100))
