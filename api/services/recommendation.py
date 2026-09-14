from functools import lru_cache
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
) -> pd.DataFrame:
    if budget is not None and budget <= 0:
        return ranked.iloc[0:0].copy()

    selected = []
    selected_ingredients = []
    running_total = 0.0

    for row in ranked.itertuples(index=False):
        recipe_cost = float(
            row.precio_total_receta_mxn
        )

        if budget is not None:
            if running_total + recipe_cost > budget:
                continue

        ingredients = list(
            getattr(
                row,
                "ingredientes",
                [],
            )
        )

        too_similar = any(
            ingredient_overlap(
                ingredients,
                previous,
            ) > MAX_INGREDIENT_OVERLAP
            for previous in selected_ingredients
        )

        if too_similar:
            continue

        selected.append(
            {
                "id_receta": int(row.id_receta),
                "nombre_receta": row.nombre_receta,
                "precio_total_receta_mxn": recipe_cost,
                "similarity_score": float(
                    row.similarity_score
                ),
            }
        )

        selected_ingredients.append(
            ingredients
        )

        running_total += recipe_cost

        if len(selected) == 7:
            break

    return pd.DataFrame(selected)


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

    ranked = rank_recipes(
        catalog,
        request.gustos,
    )

    selected = choose_weekly_recipes(
        ranked,
        request.presupuesto,
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
