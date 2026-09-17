import pandas as pd

def get_ingredients_from_menu(
    menu_semanal,
    recipes_df
):
    recipe_ids = [
        recipe_id
        for daily_ids in menu_semanal.values()
        for recipe_id in daily_ids
    ]

    ingredients_list = []

    for recipe_id in recipe_ids:
        recipe_ingredients = (
            recipes_df.loc[
                recipes_df["id"] == recipe_id,
                ["ingredient", "quantity"]
            ]
            .dropna(subset=["ingredient"])
            .to_dict(orient="records")
        )

        ingredients_list.extend(recipe_ingredients)

    return ingredients_list

def aggregate_ingredients(ingredients_list):
    ingredients_df = pd.DataFrame(ingredients_list)

    ingredients_df["ingredient"] = (
        ingredients_df["ingredient"]
        .str.lower()
        .str.strip()
    )

    ingredients_df["quantity"] = pd.to_numeric(
        ingredients_df["quantity"],
        errors="coerce"
    )

    aggregated_ingredients = (
        ingredients_df
        .dropna(subset=["ingredient", "quantity"])
        .groupby(
            "ingredient",
            as_index=False
        )
        .agg(
            quantity=("quantity", "sum"),
            recipe_appearances=("ingredient", "size")
        )
    )

    return aggregated_ingredients

def calculate_cost(
    aggregated_ingredients,
    prices_df,
    selected_store
):
    ingredients = aggregated_ingredients.copy()
    prices = prices_df.copy()

    ingredients["ingredient"] = (
        ingredients["ingredient"]
        .str.lower()
        .str.strip()
    )

    prices["ingredient"] = (
        prices["ingredient"]
        .str.lower()
        .str.strip()
    )

    prices["price"] = pd.to_numeric(
        prices["price"],
        errors="coerce"
    )

    store_prices = prices.loc[
        prices["store"]
        .str.lower()
        .str.strip()
        .eq(selected_store.lower().strip())
        & prices["price"].notna()
        & (prices["price"] > 0)
    ].copy()

    store_prices = (
        store_prices
        .sort_values("price")
        .drop_duplicates(
            subset=["ingredient", "store"],
            keep="first"
        )
    )

    cart = ingredients.merge(
        store_prices[
            [
                "ingredient",
                "profeco_category",
                "price",
                "unit",
                "store"
            ]
        ],
        on="ingredient",
        how="left"
    )

    cart["cost"] = (
        cart["quantity"]
        * cart["price"]
    ).round(2)

    missing_ingredients = (
        cart.loc[
            cart["price"].isna(),
            "ingredient"
        ]
        .tolist()
    )

    total_cost = round(
        float(cart["cost"].sum()),
        2
    )

    return cart, total_cost, missing_ingredients