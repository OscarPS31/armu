"""
Weekly menu recommender for Armu / NutriPlan (simplified scope).

The user writes what they want to eat, picks dietary restrictions and a weekly
budget; we build a Monday–Sunday menu of distinct recipes that best match, and
report the weekly cost against the budget. Uses the per-recipe estimated cost.
No shopping cart, no supermarket choice, English only.
"""

from pathlib import Path

import pandas as pd

from armu.recommender import filter_by_restriction


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = PROJECT_ROOT / "data" / "recipes_priced.parquet"

DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def load_data():
    """Load the priced recipes dataset."""
    return pd.read_parquet(RECIPES_PATH)


def _rank_by_preference(df, user_text):
    """
    Order recipes by similarity to the user's text (TF-IDF + cosine).
    Adds a `similarity_score` column. Keeps original order when no text given.
    """
    if not user_text or not user_text.strip():
        df = df.copy()
        df["similarity_score"] = 0.0
        return df

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer(stop_words="english", max_features=40000)
    recipe_vectors = vectorizer.fit_transform(df["search_text"])
    user_vector = vectorizer.transform([user_text.lower()])

    scores = cosine_similarity(user_vector, recipe_vectors)[0]

    df = df.copy()
    df["similarity_score"] = scores
    return df.sort_values("similarity_score", ascending=False)

def select_menu_within_budget(
    ranked_df,
    budget,
    days=7,
    candidate_pool_size=20
):
    """
    Select the first combination of recipes that fits the budget.
    Candidates are already ranked by user preference.
    """
    from itertools import combinations

    candidates = (
        ranked_df
        .drop_duplicates(subset="name", keep="first")
        .dropna(subset=["estimated_cost"])
        .head(candidate_pool_size)
    )

    if len(candidates) < days:
        return None

    candidate_records = candidates.to_dict("records")

    for menu_tuple in combinations(candidate_records, days):

        total_cost = sum(
            recipe["estimated_cost"]
            for recipe in menu_tuple
        )

        if total_cost <= budget:
            return list(menu_tuple)

    return None


def generate_weekly_plan(
    user_text,
    restrictions,
    budget,
    recipes=None,
    days=7,
):
    """
    Build a Monday–Sunday menu.

    Args:
        user_text: free text describing what they want to eat (English).
        restrictions: list of diet restrictions (e.g. ["vegetarian"]).
        budget: weekly budget in MXN (compared to the sum of all recipes).
        recipes: optional preloaded dataframe (for caching).
        days: number of days to plan (default 7).

    Returns a dict with the menu, weekly total and budget status.
    """
    if recipes is None:
        recipes = load_data()

    # ---- diet restrictions (must always hold) ---------------------------
    pool = filter_by_restriction(recipes, restrictions)

    if pool.empty:
        return {
            "status": "NO_RECIPES",
            "menu": [],
            "total": 0.0,
            "budget": budget,
            "remaining": budget,
            "within_budget": True,
        }

    # ---- rank by preference, take up to `days` DISTINCT recipes ----------
    # Never clone a recipe to pad the week: show as many real, different
    # recipes as the diet allows, up to the number of days requested.
    ranked = _rank_by_preference(pool, user_text)
    # The source data has different recipes that share the same name; drop the
    # duplicate names so the week shows real variety, not the same title twice.
    ranked = ranked.drop_duplicates(subset="name", keep="first")
    available = len(ranked)
    chosen = select_menu_within_budget(
    ranked,
    budget,
    days,
    candidate_pool_size=20)
    incomplete = len(chosen) < days

    no_text_match = bool(
        user_text
        and user_text.strip()
        and all(row.get("similarity_score", 0) <= 0 for row in chosen)
    )

    menu = []
    for i, row in enumerate(chosen):
        menu.append(
            {
                "day": DAYS[i % len(DAYS)],
                "id": int(row["id"]),
                "name": row["name"],
                "cost": round(float(row["estimated_cost"]), 2),
                "cost_min": round(float(row["minimum_estimate"]), 2),
                "cost_max": round(float(row["maximum_estimate"]), 2),
                "ingredients": list(row["ingredients"]),
                "steps": list(row["steps"]),
                "servings": row.get("servings"),
            }
        )

    total = round(sum(item["cost"] for item in menu), 2)

    return {
        "status": "OK",
        "menu": menu,
        "total": total,
        "budget": budget,
        "remaining": round(budget - total, 2),
        "within_budget": total <= budget,
        "days_requested": days,
        "days_filled": len(menu),
        "available_recipes": available,
        "incomplete": incomplete,
        "no_text_match": no_text_match,
    }
