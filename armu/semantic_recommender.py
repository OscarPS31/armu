import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer, util


SEMANTIC_INDEX_PATH = Path("data/recipe_embeddings.npy")
SEMANTIC_IDS_PATH = Path("data/recipe_embedding_ids.npy")


@lru_cache(maxsize=1)
def load_semantic_index():
    embeddings = np.load(
        SEMANTIC_INDEX_PATH,
        mmap_mode="r",
    )

    ids = np.load(
        SEMANTIC_IDS_PATH,
        mmap_mode="r",
    )

    id_to_position = {
        int(recipe_id): position
        for position, recipe_id in enumerate(ids)
    }

    return embeddings, id_to_position


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


DISH_TYPES = {
    "sopa": ["soup", "stew", "chowder", "bisque"],
    "pasta": [
        "pasta",
        "spaghetti",
        "linguine",
        "macaroni",
        "noodle",
        "noodles",
        "fettuccine",
        "lasagna",
    ],
    "postre": [
        "dessert",
        "cake",
        "brownie",
        "cookie",
        "cookies",
        "mousse",
        "pie",
        "pudding",
        "cheesecake",
        "tart",
    ],
}


INGREDIENT_CONCEPTS = {
    "pollo": ["chicken"],
    "res": ["beef", "steak", "ground beef"],
    "verduras": [
        "vegetable",
        "vegetables",
        "broccoli",
        "carrot",
        "carrots",
        "zucchini",
        "pepper",
        "peppers",
        "green bean",
        "green beans",
    ],
    "queso": [
        "cheese",
        "cheddar",
        "mozzarella",
        "parmesan",
        "romano",
    ],
    "chocolate": ["chocolate", "cocoa"],
}


SOFT_CONCEPTS = {
    "picante": [
        "spicy",
        "chili",
        "chile",
        "jalapeno",
        "jalapeño",
        "cayenne",
        "hot pepper",
    ],
    "cremosa": [
        "cream",
        "creamy",
        "alfredo",
    ],
}


@lru_cache(maxsize=1)
def load_model():
    return SentenceTransformer(MODEL_NAME)


def _has_term(text, term):
    return bool(
        re.search(
            rf"(?<!\w){re.escape(term.lower())}(?!\w)",
            str(text).lower(),
        )
    )


def _contains_any(text, terms):
    return any(_has_term(text, term) for term in terms)


def _detect(query, concepts):
    return [
        concept
        for concept in concepts
        if _has_term(query, concept)
    ]


def _recipe_text(row):
    ingredients = " ".join(map(str, row["ingredients"]))
    return f"{row['name']} {ingredients}".lower()


def prefilter_candidates(recipes, query):
    dish_concepts = _detect(query, DISH_TYPES)
    ingredient_concepts = _detect(query, INGREDIENT_CONCEPTS)
    soft_concepts = _detect(query, SOFT_CONCEPTS)

    names = recipes["name"].astype(str).str.lower()

    texts = (
        names
        + " "
        + recipes["ingredients"].map(
            lambda values: " ".join(map(str, values)).lower()
        )
    )

    mask = np.ones(len(recipes), dtype=bool)
    bonus = np.zeros(len(recipes), dtype=np.float32)

    def pattern_for(terms):
        escaped = [
            re.escape(term.lower())
            for term in terms
        ]

        return (
            r"(?<!\w)(?:"
            + "|".join(escaped)
            + r")(?!\w)"
        )

    # Tipo de platillo: debe aparecer en el nombre.
    for concept in dish_concepts:
        hit = names.str.contains(
            pattern_for(DISH_TYPES[concept]),
            regex=True,
            na=False,
        ).to_numpy()

        mask &= hit

    # Ingredientes/conceptos principales:
    # pueden aparecer en nombre o ingredientes.
    for concept in ingredient_concepts:
        hit = texts.str.contains(
            pattern_for(INGREDIENT_CONCEPTS[concept]),
            regex=True,
            na=False,
        ).to_numpy()

        mask &= hit

    # Modificadores como "picante" o "cremosa"
    # dan bonificación.
    for concept in soft_concepts:
        hit = texts.str.contains(
            pattern_for(SOFT_CONCEPTS[concept]),
            regex=True,
            na=False,
        ).to_numpy()

        bonus += hit.astype(np.float32) * 0.10

    positions = np.flatnonzero(mask)

    return [
        (
            recipes.index[pos],
            texts.iloc[pos],
            float(bonus[pos]),
        )
        for pos in positions
    ]


def semantic_search(recipes, query, model=None, top_k=7):
    if model is None:
        model = load_model()

    candidates = prefilter_candidates(recipes, query)

    # Si hay suficientes candidatos que cumplen los modificadores
    # (por ejemplo "picante" o "cremosa"), priorizamos solo esos.
    preferred = [
        item for item in candidates
        if item[2] > 0
    ]

    preferred_threshold = min(top_k, 7)

    if len(preferred) >= preferred_threshold:
        candidates = preferred

    if not candidates:
        candidates = [
            (idx, _recipe_text(row), 0.0)
            for idx, row in recipes.iterrows()
        ]

    indices = [item[0] for item in candidates]

    bonuses = np.array(
        [item[2] for item in candidates],
        dtype=np.float32,
    )

    # Usamos embeddings precalculados de las 50,496 recetas.
    semantic_index, id_to_position = load_semantic_index()

    positions = [
        id_to_position[int(recipes.loc[idx, "id"])]
        for idx in indices
    ]

    recipe_embeddings = np.asarray(
        semantic_index[positions],
        dtype=np.float32,
    )

    recipe_embeddings = np.nan_to_num(
        recipe_embeddings,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype=np.float32,
    )

    query_embedding = np.nan_to_num(
        query_embedding,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    recipe_embeddings = np.nan_to_num(
        recipe_embeddings,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    scores = np.sum(
        recipe_embeddings * query_embedding,
        axis=1,
        dtype=np.float32,
    )
    scores = scores + bonuses

    order = np.argsort(scores)[::-1][:top_k]

    result = recipes.loc[
        [indices[i] for i in order]
    ].copy()

    result["semantic_score"] = [
        float(scores[i])
        for i in order
    ]

    return result
