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


def build_recipe_catalog(
    df: pd.DataFrame,
    chain: str,
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

    catalog["search_text"] = (
        catalog["nombre_receta"]
        .fillna("")
        .astype(str)
        + " "
        + catalog["ingredientes"]
        .apply(lambda values: " ".join(values))
    ).str.lower()

    return catalog


def rank_recipes(
    catalog: pd.DataFrame,
    user_text: str,
) -> pd.DataFrame:
    ranked = catalog.copy()
    text = str(user_text or "").strip()

    if not text:
        ranked["similarity_score"] = 0.0

        return ranked.sort_values(
            [
                "precio_total_receta_mxn",
                "nombre_receta",
            ],
            ascending=[
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


def choose_weekly_recipes(
    ranked: pd.DataFrame,
    budget: float | None,
) -> pd.DataFrame:
    if budget is not None and budget <= 0:
        return ranked.iloc[0:0].copy()

    selected = []
    running_total = 0.0

    for row in ranked.itertuples(index=False):
        recipe_cost = float(
            row.precio_total_receta_mxn
        )

        if budget is not None:
            if running_total + recipe_cost > budget:
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

        running_total += recipe_cost

        if len(selected) == 7:
            break

    return pd.DataFrame(selected)


def make_recipe_model(
    recipe_id: int,
    df: pd.DataFrame,
    chain: str,
) -> Recipe:
    rows = df[
        df["id_receta"].eq(recipe_id)
        & df["cadena"].eq(chain)
    ]

    if rows.empty:
        return Recipe(
            id=recipe_id,
            name="Receta no disponible",
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
        ingredients=ingredients,
    )


def build_menu(
    selected: pd.DataFrame,
    df: pd.DataFrame,
    chain: str,
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
            )
        ]

    return menu


def build_cart(
    selected: pd.DataFrame,
    df: pd.DataFrame,
    chain: str,
    budget: float | None,
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
                "cantidad",
                "sum",
            ),
            costo=(
                "costo_ingrediente_mxn",
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
    )

    cart = build_cart(
        selected,
        df,
        chain,
        request.presupuesto,
    )

    if selected.empty:
        message = (
            f"No encontramos recetas completas en {chain} "
            "que cumplan el presupuesto."
        )

    elif len(selected) < 7:
        message = (
            f"Se encontraron {len(selected)} recetas en {chain}. "
            f"Costo estimado: ${cart.costo_total:.2f} MXN."
        )

    else:
        message = (
            f"Menú semanal generado con 7 recetas en {chain}. "
            f"Costo estimado: ${cart.costo_total:.2f} MXN."
        )

    return RecommendationResponse(
        menu_semanal=menu,
        carrito_final=cart,
        mensaje=message,
    )
