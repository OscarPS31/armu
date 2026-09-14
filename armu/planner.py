"""
End-to-end weekly plan for the NutriPlan / Armu demo.

Takes the user's preferences and returns a weekly menu, a shopping list and
the estimated cart cost per supermarket chain, using the self-contained demo
dataset (889 fully-priced recipes).
"""

from pathlib import Path

import pandas as pd

from armu.recommender import filter_by_restriction, filter_by_time
from armu.translation import translate_query


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RECIPES_PATH = PROJECT_ROOT / "data" / "demo_recipes.parquet"
COSTS_PATH = PROJECT_ROOT / "data" / "demo_ingredient_costs.parquet"

CHAINS = ["Walmart", "Soriana", "Chedraui"]

DAYS_ES = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


def load_data():
    """Load the demo recipes and ingredient-cost tables."""
    recipes = pd.read_parquet(RECIPES_PATH)
    costs = pd.read_parquet(COSTS_PATH)
    return recipes, costs


def _rank_by_preference(df, user_text):
    """
    Order recipes by similarity to the user's free text using TF-IDF +
    cosine similarity. Falls back to the original order when no text is given.
    """
    if not user_text or not user_text.strip():
        return df.reset_index(drop=True)

    # Recipes are in English; translate the (possibly Spanish) query first.
    query = translate_query(user_text)
    if not query.strip():
        return df.reset_index(drop=True)

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer()
    recipe_vectors = vectorizer.fit_transform(df["search_text"])
    user_vector = vectorizer.transform([query])

    scores = cosine_similarity(user_vector, recipe_vectors)[0]

    df = df.copy()
    df["similarity_score"] = scores
    return df.sort_values("similarity_score", ascending=False)


def _shopping_list(costs, recipe_ids, chain):
    """
    Aggregate all ingredients of the chosen recipes into one shopping list
    for a given chain.
    """
    subset = costs[
        (costs["id"].isin(recipe_ids))
        & (costs["chain"] == chain)
    ]

    grouped = (
        subset.groupby(["ingredient", "profeco_product"], as_index=False)
        .agg(
            quantity_g=("quantity", "sum"),
            cost_mxn=("cost_mxn", "sum"),
        )
        .sort_values("cost_mxn", ascending=False)
    )

    return grouped.to_dict("records")


def generate_weekly_plan(
    restrictions,
    max_time,
    user_text,
    budget,
    chain,
    recipes=None,
    costs=None,
    days=7,
):
    """
    Build a full weekly plan.

    Args:
        restrictions: list of diet restrictions (e.g. ["vegetarian"]).
        max_time: 15, 30 or 60 (minutes available to cook).
        user_text: free text describing what the user wants to eat.
        budget: weekly budget in MXN.
        chain: one of CHAINS, the supermarket to cost the cart against.
        recipes, costs: optional preloaded dataframes (for caching).
        days: number of meals to plan (default 7).

    Returns a dict with the menu, shopping list, totals and budget status.
    """
    if recipes is None or costs is None:
        recipes, costs = load_data()

    # ---- filter by restriction + time -----------------------------------
    filtered = filter_by_restriction(recipes, restrictions)
    filtered = filter_by_time(filtered, max_time)

    if filtered.empty:
        return {
            "status": "NO_RECIPES",
            "menu": [],
            "shopping_list": [],
            "total": 0.0,
            "budget": budget,
            "remaining": budget,
            "within_budget": True,
            "chain": chain,
            "chain_totals": {},
        }

    # ---- rank by preference and pick the top N --------------------------
    ranked = _rank_by_preference(filtered, user_text)
    selected = ranked.head(days)

    cost_col = f"cost_{chain.lower()}"

    menu = []
    for i, (_, row) in enumerate(selected.iterrows()):
        menu.append(
            {
                "day": DAYS_ES[i % len(DAYS_ES)],
                "id": int(row["id"]),
                "name": row["name"],
                "cost": round(float(row[cost_col]), 2),
                "ingredients": list(row["ingredients"]),
                "steps": list(row["steps"]),
                "quick_15min": bool(row["quick_15min"]),
                "quick_30min": bool(row["quick_30min"]),
                "quick_60min": bool(row["quick_60min"]),
            }
        )

    recipe_ids = [item["id"] for item in menu]

    total = round(sum(item["cost"] for item in menu), 2)

    # ---- cart total for every chain (for comparison) --------------------
    chain_totals = {}
    for c in CHAINS:
        col = f"cost_{c.lower()}"
        chain_totals[c] = round(
            float(selected[col].sum()),
            2,
        )

    shopping_list = _shopping_list(costs, recipe_ids, chain)

    return {
        "status": "OK",
        "menu": menu,
        "shopping_list": shopping_list,
        "total": total,
        "budget": budget,
        "remaining": round(budget - total, 2),
        "within_budget": total <= budget,
        "chain": chain,
        "chain_totals": chain_totals,
    }
