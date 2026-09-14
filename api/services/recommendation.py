from functools import lru_cache
from html import unescape
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from api.schemas import (
    Cart,
    CartItem,
    Recipe,
    RecommendationRequest,
    RecommendationResponse,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PRICE_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "recipe_prices_complete_3chains.csv"
)

DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

VALID_CHAINS = {
    "walmart": "Walmart",
    "soriana": "Soriana",
    "chedraui": "Chedraui",
}

BASE_PERSONAS = 2

BLOCKED_RECIPE_TERMS = {
    "bleach",
    "cleaner",
    "cleaning",
    "laundry",
    "baby food",
}

NON_MAIN_TITLE_PATTERNS = (
    "replacement",
    "substitute",
    "seasoning",
    "marinade",
    "frosting",
    "icing",
)

NON_MAIN_ENDINGS = (
    " sauce",
    " dressing",
    " syrup",
    " rub",
    " dip",
    " spread",
    " frosting",
    " icing",
    " substitute",
    " replacement",
    " cream",
    " whip",
)

MAIN_MEAL_TERMS = {
    "chicken",
    "beef",
    "pork",
    "turkey",
    "fish",
    "salmon",
    "tuna",
    "shrimp",
    "seafood",
    "pasta",
    "spaghetti",
    "noodle",
    "rice",
    "beans",
    "chili",
    "curry",
    "stew",
    "soup",
    "casserole",
    "taco",
    "tacos",
    "enchilada",
    "burrito",
    "sandwich",
    "burger",
    "potato",
    "vegetable",
    "veggie",
    "lentil",
    "chickpea",
    "meatball",
    "lasagna",
}

MAX_INGREDIENT_OVERLAP = 0.75
MAX_CATEGORY_PER_DEFAULT_MENU = 2
MAX_CATEGORY_PER_PREFERENCE_MENU = 3
MAX_PREFERENCE_NAME_OVERLAP = 0.60

CATEGORY_TERMS = {
    "poultry": {
        "chicken",
        "turkey",
    },
    "fish": {
        "tuna",
        "salmon",
        "fish",
        "cod",
        "tilapia",
    },
    "seafood": {
        "shrimp",
        "prawn",
        "crab",
        "lobster",
        "seafood",
    },
    "beef": {
        "beef",
        "steak",
        "meatball",
    },
    "pork": {
        "pork",
        "bacon",
        "ham",
        "sausage",
    },
    "legumes": {
        "beans",
        "bean",
        "lentil",
        "lentils",
        "chickpea",
        "chickpeas",
    },
    "pasta": {
        "pasta",
        "spaghetti",
        "noodle",
        "noodles",
        "lasagna",
        "macaroni",
    },
    "rice": {
        "rice",
        "risotto",
    },
    "vegetarian": {
        "vegetable",
        "vegetables",
        "veggie",
        "tofu",
        "mushroom",
        "mushrooms",
    },
}


VALID_RESTRICTIONS = {
    "vegetariano": "vegetariano",
    "vegetarian": "vegetariano",
    "vegano": "vegano",
    "vegan": "vegano",
    "sin_gluten": "sin_gluten",
    "sin gluten": "sin_gluten",
    "gluten_free": "sin_gluten",
    "gluten-free": "sin_gluten",
}

MEAT_TERMS = {
    "beef",
    "steak",
    "chicken",
    "turkey",
    "pork",
    "ham",
    "bacon",
    "sausage",
    "fish",
    "tuna",
    "salmon",
    "cod",
    "tilapia",
    "shrimp",
    "prawn",
    "crab",
    "lobster",
    "seafood",
    "anchovy",
    "anchovies",
}

ANIMAL_PRODUCT_TERMS = MEAT_TERMS | {
    "egg",
    "eggs",
    "milk",
    "cheese",
    "cream",
    "butter",
    "yogurt",
    "yoghurt",
    "honey",
    "mayonnaise",
    "mayo",
}

GLUTEN_TERMS = {
    "wheat",
    "flour",
    "bread",
    "breadcrumbs",
    "pasta",
    "spaghetti",
    "noodle",
    "noodles",
    "macaroni",
    "lasagna",
    "couscous",
    "barley",
    "rye",
}


@lru_cache(maxsize=1)
def load_recipe_prices() -> pd.DataFrame:
    if not PRICE_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing dataset: {PRICE_DATA_PATH}"
        )

    df = pd.read_csv(
        PRICE_DATA_PATH,
        low_memory=False,
    )

    required_columns = {
        "id_receta",
        "nombre_receta",
        "ingrediente",
        "ingrediente_original",
        "cantidad",
        "unidad",
        "cadena",
        "costo_ingrediente_mxn",
        "precio_total_receta_mxn",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {sorted(missing)}"
        )

    df["id_receta"] = pd.to_numeric(
        df["id_receta"],
        errors="coerce",
    )

    df["cantidad"] = pd.to_numeric(
        df["cantidad"],
        errors="coerce",
    )

    df["costo_ingrediente_mxn"] = pd.to_numeric(
        df["costo_ingrediente_mxn"],
        errors="coerce",
    )

    df["precio_total_receta_mxn"] = pd.to_numeric(
        df["precio_total_receta_mxn"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "id_receta",
            "nombre_receta",
            "cadena",
            "costo_ingrediente_mxn",
            "precio_total_receta_mxn",
        ]
    ).copy()

    df["id_receta"] = df["id_receta"].astype(int)

    df["nombre_receta"] = (
        df["nombre_receta"]
        .astype(str)
        .map(unescape)
    )

    return df


def normalize_chain(value: str) -> str:
    key = str(value or "").strip().lower()

    if key not in VALID_CHAINS:
        raise ValueError(
            "Cadena no válida. Usa Walmart, Soriana o Chedraui."
        )

    return VALID_CHAINS[key]


def get_person_scale(personas: int) -> float:
    if personas < 1:
        raise ValueError(
            "El número de personas debe ser al menos 1."
        )

    return personas / BASE_PERSONAS


def build_recipe_catalog(
    df: pd.DataFrame,
    chain: str,
    personas: int = BASE_PERSONAS,
) -> pd.DataFrame:
    chain_df = df[
        df["cadena"].eq(chain)
    ].copy()

    catalog = (
        chain_df
        .groupby(
            [
                "id_receta",
                "nombre_receta",
            ],
            as_index=False,
        )
        .agg(
            ingredientes=(
                "ingrediente",
                lambda values: sorted(
                    {
                        str(value).strip()
                        for value in values
                        if pd.notna(value)
                        and str(value).strip()
                    }
                ),
            ),
            precio_total_receta_mxn=(
                "precio_total_receta_mxn",
                "first",
            ),
        )
    )

    scale = get_person_scale(personas)

    catalog["precio_total_receta_mxn"] = (
        catalog["precio_total_receta_mxn"]
        .astype(float)
        .mul(scale)
        .round(2)
    )

    catalog["search_text"] = (
        catalog["nombre_receta"]
        .fillna("")
        .astype(str)
        + " "
        + catalog["ingredientes"]
        .apply(lambda values: " ".join(values))
    ).str.lower()

    return catalog


def recipe_main_meal_score(
    name: str,
    ingredients: list[str],
) -> int:
    title = str(name or "").strip().lower()

    ingredient_text = " ".join(
        str(value).strip().lower()
        for value in ingredients
        if str(value).strip()
    )

    score = 0

    for term in MAIN_MEAL_TERMS:
        if term in title:
            score += 3
        elif term in ingredient_text:
            score += 1

    ingredient_count = len(
        {
            str(value).strip().lower()
            for value in ingredients
            if str(value).strip()
        }
    )

    if ingredient_count >= 5:
        score += 2
    elif ingredient_count >= 3:
        score += 1

    return score


def is_non_main_recipe(name: str) -> bool:
    title = str(name or "").strip().lower()

    if any(
        pattern in title
        for pattern in NON_MAIN_TITLE_PATTERNS
    ):
        return True

    return any(
        title.endswith(ending)
        for ending in NON_MAIN_ENDINGS
    )


def filter_recipe_quality(
    catalog: pd.DataFrame,
) -> pd.DataFrame:
    filtered = catalog.copy()

    blocked_pattern = "|".join(
        sorted(BLOCKED_RECIPE_TERMS)
    )

    if blocked_pattern:
        blocked = (
            filtered["nombre_receta"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(
                blocked_pattern,
                regex=True,
            )
        )

        filtered = filtered[
            ~blocked
        ].copy()

    non_main = filtered[
        "nombre_receta"
    ].apply(is_non_main_recipe)

    filtered = filtered[
        ~non_main
    ].copy()

    filtered["main_meal_score"] = filtered.apply(
        lambda row: recipe_main_meal_score(
            row["nombre_receta"],
            row["ingredientes"],
        ),
        axis=1,
    )

    return filtered


def normalize_restrictions(
    restrictions: list[str],
) -> list[str]:
    normalized = []

    for value in restrictions:
        key = str(value or "").strip().lower()

        if not key:
            continue

        if key not in VALID_RESTRICTIONS:
            raise ValueError(
                "Restricción no válida: "
                f"{value}. "
                "Usa vegetariano, vegano o sin_gluten."
            )

        canonical = VALID_RESTRICTIONS[key]

        if canonical not in normalized:
            normalized.append(canonical)

    return normalized


def tokenize_food_text(text: str) -> set[str]:
    cleaned = str(text or "").lower()

    for char in [
        "-",
        "/",
        ",",
        "(",
        ")",
        ".",
        ":",
        ";",
        "#",
        "&",
    ]:
        cleaned = cleaned.replace(char, " ")

    return set(cleaned.split())


def recipe_food_words(
    name: str,
    ingredients: list[str],
) -> set[str]:
    words = tokenize_food_text(name)

    for ingredient in ingredients:
        words |= tokenize_food_text(
            str(ingredient)
        )

    return words


def filter_by_restrictions(
    catalog: pd.DataFrame,
    restrictions: list[str],
) -> pd.DataFrame:
    normalized = normalize_restrictions(
        restrictions
    )

    if not normalized:
        return catalog.copy()

    keep_rows = []

    for _, row in catalog.iterrows():
        words = recipe_food_words(
            row["nombre_receta"],
            row["ingredientes"],
        )

        allowed = True

        if (
            "vegetariano" in normalized
            and words & MEAT_TERMS
        ):
            allowed = False

        if (
            "vegano" in normalized
            and words & ANIMAL_PRODUCT_TERMS
        ):
            allowed = False

        if (
            "sin_gluten" in normalized
            and words & GLUTEN_TERMS
        ):
            allowed = False

        keep_rows.append(allowed)

    return catalog.loc[
        keep_rows
    ].copy()


def rank_recipes(
    catalog: pd.DataFrame,
    user_text: str,
) -> pd.DataFrame:
    ranked = filter_recipe_quality(
        catalog
    )

    text = str(user_text or "").strip()

    if ranked.empty:
        return ranked

    if not text:
        ranked["similarity_score"] = 0.0

        median_price = float(
            ranked[
                "precio_total_receta_mxn"
            ].median()
        )

        ranked["default_quality_score"] = (
            ranked[
                "precio_total_receta_mxn"
            ]
            .sub(median_price)
            .abs()
        )

        return ranked.sort_values(
            [
                "main_meal_score",
                "default_quality_score",
                "precio_total_receta_mxn",
                "nombre_receta",
            ],
            ascending=[
                False,
                True,
                True,
                True,
            ],
        )

    vectorizer = TfidfVectorizer(
        strip_accents="unicode",
        lowercase=True,
    )

    recipe_vectors = vectorizer.fit_transform(
        ranked["search_text"]
    )

    user_vector = vectorizer.transform(
        [text]
    )

    ranked["similarity_score"] = cosine_similarity(
        user_vector,
        recipe_vectors,
    )[0]

    return ranked.sort_values(
        [
            "similarity_score",
            "precio_total_receta_mxn",
        ],
        ascending=[
            False,
            True,
        ],
    )


def recipe_category(
    name: str,
    ingredients: list[str],
) -> str:
    title = str(
        name or ""
    ).lower()

    ingredient_text = " ".join(
        str(value).lower()
        for value in ingredients
        if str(value).strip()
    )

    def tokenize(text: str) -> set[str]:
        cleaned = (
            text
            .replace("-", " ")
            .replace("/", " ")
            .replace("&", " ")
            .replace(",", " ")
            .replace("(", " ")
            .replace(")", " ")
        )

        return set(
            cleaned.split()
        )

    title_words = tokenize(
        title
    )

    ingredient_words = tokenize(
        ingredient_text
    )

    priority = [
        "poultry",
        "fish",
        "seafood",
        "beef",
        "pork",
        "legumes",
        "pasta",
        "rice",
        "vegetarian",
    ]

    # 1. El título manda.
    #
    # Ejemplo:
    # "Tuna Rice Casserole"
    # debe ser fish aunque tenga chicken broth
    # entre sus ingredientes.
    for category in priority:
        if (
            title_words
            & CATEGORY_TERMS[category]
        ):
            return category

    # 2. Si el título no informa la categoría,
    # usamos los ingredientes como fallback.
    for category in priority:
        if (
            ingredient_words
            & CATEGORY_TERMS[category]
        ):
            return category

    return "other"


def normalized_title_words(
    value: str,
) -> set[str]:
    text = str(value or "").lower()

    for char in [
        "-",
        "/",
        "&",
        ",",
        ".",
        "(",
        ")",
        "#",
        ":",
        ";",
    ]:
        text = text.replace(
            char,
            " ",
        )

    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "with",
        "of",
        "in",
        "for",
        "to",
        "easy",
        "best",
        "quick",
        "simple",
    }

    return {
        word
        for word in text.split()
        if word
        and word not in stopwords
    }


def title_overlap(
    first: str,
    second: str,
) -> float:
    first_words = normalized_title_words(
        first
    )

    second_words = normalized_title_words(
        second
    )

    if not first_words or not second_words:
        return 0.0

    intersection = len(
        first_words & second_words
    )

    union = len(
        first_words | second_words
    )

    return intersection / union


def ingredient_overlap(
    first: list[str],
    second: list[str],
) -> float:
    first_set = {
        str(value).strip().lower()
        for value in first
        if str(value).strip()
    }

    second_set = {
        str(value).strip().lower()
        for value in second
        if str(value).strip()
    }

    if not first_set or not second_set:
        return 0.0

    intersection = len(
        first_set & second_set
    )

    union = len(
        first_set | second_set
    )

    return intersection / union


def choose_weekly_recipes(
    ranked: pd.DataFrame,
    budget: float | None,
    diversify: bool = True,
    preference_mode: bool = False,
) -> pd.DataFrame:
    if budget is not None and budget <= 0:
        return ranked.iloc[0:0].copy()

    selected = []
    selected_ids = set()
    selected_ingredients = []
    selected_names = []
    category_counts = {}
    running_total = 0.0

    def try_add(
        row,
        enforce_category_limit: bool,
        enforce_preference_similarity: bool,
    ) -> bool:
        nonlocal running_total

        recipe_id = int(
            row.id_receta
        )

        if recipe_id in selected_ids:
            return False

        recipe_cost = float(
            row.precio_total_receta_mxn
        )

        if (
            budget is not None
            and running_total + recipe_cost > budget
        ):
            return False

        ingredients = list(
            getattr(
                row,
                "ingredientes",
                [],
            )
        )

        recipe_name = str(
            row.nombre_receta
        )

        too_similar_ingredients = any(
            ingredient_overlap(
                ingredients,
                previous,
            ) > MAX_INGREDIENT_OVERLAP
            for previous
            in selected_ingredients
        )

        if too_similar_ingredients:
            return False

        if (
            preference_mode
            and enforce_preference_similarity
        ):
            too_similar_name = any(
                title_overlap(
                    recipe_name,
                    previous_name,
                )
                > MAX_PREFERENCE_NAME_OVERLAP
                for previous_name
                in selected_names
            )

            if too_similar_name:
                return False

        category = recipe_category(
            recipe_name,
            ingredients,
        )

        category_limit = (
            MAX_CATEGORY_PER_PREFERENCE_MENU
            if preference_mode
            else MAX_CATEGORY_PER_DEFAULT_MENU
        )

        if (
            diversify
            and enforce_category_limit
            and category_counts.get(
                category,
                0,
            ) >= category_limit
        ):
            return False

        selected.append(
            {
                "id_receta": recipe_id,
                "nombre_receta": recipe_name,
                "precio_total_receta_mxn": recipe_cost,
                "similarity_score": float(
                    row.similarity_score
                ),
            }
        )

        selected_ids.add(
            recipe_id
        )

        selected_ingredients.append(
            ingredients
        )

        selected_names.append(
            recipe_name
        )

        category_counts[category] = (
            category_counts.get(
                category,
                0,
            )
            + 1
        )

        running_total += recipe_cost

        return True

    # Primera pasada:
    # respeta ranking + diversidad.
    for row in ranked.itertuples(
        index=False
    ):
        try_add(
            row,
            enforce_category_limit=True,
            enforce_preference_similarity=True,
        )

        if len(selected) == 7:
            break

    # Segunda pasada:
    # relajamos similitud de título,
    # pero conservamos límite de categoría.
    if len(selected) < 7:
        for row in ranked.itertuples(
            index=False
        ):
            try_add(
                row,
                enforce_category_limit=True,
                enforce_preference_similarity=False,
            )

            if len(selected) == 7:
                break

    # Tercera pasada:
    # fallback para completar el menú.
    if len(selected) < 7:
        for row in ranked.itertuples(
            index=False
        ):
            try_add(
                row,
                enforce_category_limit=False,
                enforce_preference_similarity=False,
            )

            if len(selected) == 7:
                break

    return pd.DataFrame(
        selected
    )


def make_recipe_model(
    recipe_id: int,
    df: pd.DataFrame,
    chain: str,
    personas: int,
) -> Recipe:
    rows = df[
        df["id_receta"].eq(recipe_id)
        & df["cadena"].eq(chain)
    ]

    if rows.empty:
        return Recipe(
            id=recipe_id,
            name="Receta no disponible",
            servings=personas,
        )

    ingredients = (
        rows["ingrediente_original"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    return Recipe(
        id=recipe_id,
        name=str(
            rows["nombre_receta"].iloc[0]
        ),
        servings=personas,
        ingredients=ingredients,
    )


def build_menu(
    selected: pd.DataFrame,
    df: pd.DataFrame,
    chain: str,
    personas: int,
) -> dict[str, list[Recipe]]:
    menu = {
        day: []
        for day in DAYS
    }

    if selected.empty:
        return menu

    for day, recipe_id in zip(
        DAYS,
        selected["id_receta"].tolist(),
    ):
        menu[day] = [
            make_recipe_model(
                int(recipe_id),
                df,
                chain,
                personas,
            )
        ]

    return menu


def build_cart(
    selected: pd.DataFrame,
    df: pd.DataFrame,
    chain: str,
    budget: float | None,
    personas: int,
) -> Cart:
    if selected.empty:
        return Cart()

    recipe_ids = selected[
        "id_receta"
    ].astype(int).tolist()

    rows = df[
        df["id_receta"].isin(recipe_ids)
        & df["cadena"].eq(chain)
    ].copy()

    scale = get_person_scale(personas)

    rows["cantidad_escalada"] = (
        rows["cantidad"]
        .astype(float)
        .mul(scale)
    )

    rows["costo_escalado"] = (
        rows["costo_ingrediente_mxn"]
        .astype(float)
        .mul(scale)
    )

    grouped = (
        rows
        .groupby(
            [
                "ingrediente",
                "unidad",
            ],
            as_index=False,
        )
        .agg(
            cantidad=(
                "cantidad_escalada",
                "sum",
            ),
            costo=(
                "costo_escalado",
                "sum",
            ),
        )
    )

    grouped["cantidad"] = grouped[
        "cantidad"
    ].round(4)

    grouped["costo"] = grouped[
        "costo"
    ].round(2)

    items = [
        CartItem(
            ingrediente=str(row.ingrediente),
            cantidad=float(row.cantidad),
            unidad=str(row.unidad),
            costo=float(row.costo),
        )
        for row in grouped.itertuples(
            index=False
        )
    ]

    total = round(
        float(
            grouped["costo"].sum()
        ),
        2,
    )

    return Cart(
        items=items,
        costo_total=total,
        dentro_de_presupuesto=(
            budget is None
            or total <= budget
        ),
    )


def recommend(
    request: RecommendationRequest,
) -> RecommendationResponse:
    df = load_recipe_prices()

    chain = normalize_chain(
        request.cadena
    )

    catalog = build_recipe_catalog(
        df,
        chain,
        request.personas,
    )

    catalog = filter_by_restrictions(
        catalog,
        request.restricciones,
    )

    ranked = rank_recipes(
        catalog,
        request.gustos,
    )

    has_preferences = bool(
        str(
            request.gustos or ""
        ).strip()
    )

    selected = choose_weekly_recipes(
        ranked,
        request.presupuesto,
        diversify=True,
        preference_mode=has_preferences,
    )

    menu = build_menu(
        selected,
        df,
        chain,
        request.personas,
    )

    cart = build_cart(
        selected,
        df,
        chain,
        request.presupuesto,
        request.personas,
    )

    if selected.empty:
        message = (
            f"No encontramos recetas completas en {chain} "
            f"para {request.personas} personas "
            "que cumplan el presupuesto."
        )

    elif len(selected) < 7:
        message = (
            f"Se encontraron {len(selected)} recetas en {chain} "
            f"para {request.personas} personas. "
            f"Costo estimado: ${cart.costo_total:.2f} MXN."
        )

    else:
        message = (
            f"Menú semanal generado con 7 recetas en {chain} "
            f"para {request.personas} personas. "
            f"Costo estimado: ${cart.costo_total:.2f} MXN."
        )

    return RecommendationResponse(
        menu_semanal=menu,
        carrito_final=cart,
        mensaje=message,
    )
