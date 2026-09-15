import pandas as pd

print("\n=== RECIPES ===")
recipes = pd.read_csv(
    "raw_data/recipes.csv",
    usecols=[
        "RecipeId",
        "Name",
        "RecipeCategory",
        "Keywords",
        "RecipeIngredientParts",
        "AggregatedRating",
        "ReviewCount",
        "Calories",
        "CarbohydrateContent",
        "ProteinContent",
        "FatContent",
        "RecipeServings",
    ],
)

print("Shape:", recipes.shape)
print("\nMissing values:")
print(recipes.isna().sum().sort_values(ascending=False).head(15))

print("\nTop categories:")
print(recipes["RecipeCategory"].value_counts().head(20))

print("\nNutrition summary:")
print(
    recipes[
        [
            "Calories",
            "ProteinContent",
            "CarbohydrateContent",
            "FatContent",
        ]
    ].describe()
)


print("\n\n=== REVIEWS ===")
reviews = pd.read_csv(
    "raw_data/reviews.csv",
    usecols=["ReviewId", "RecipeId", "AuthorId", "Rating"],
)

print("Shape:", reviews.shape)
print("\nRatings:")
print(reviews["Rating"].value_counts().sort_index())

print("\nUnique users:", reviews["AuthorId"].nunique())
print("Unique recipes reviewed:", reviews["RecipeId"].nunique())


print("\n\n=== PROFECO PRICES ===")
prices = pd.read_csv(
    "raw_data/07-2026_Q2.csv",
    usecols=[
        "producto",
        "presentacion",
        "marca",
        "categoria",
        "precio",
        "cadena_comercial",
        "estado",
        "municipio",
    ],
)

print("Shape:", prices.shape)

print("\nUnique products:", prices["producto"].nunique())
print("Unique stores:", prices["cadena_comercial"].nunique())

print("\nTop product categories:")
print(prices["categoria"].value_counts().head(20))

print("\nPrice summary:")
print(prices["precio"].describe())

print("\nExample products:")
print(prices[["producto", "presentacion", "precio"]].head(30))
