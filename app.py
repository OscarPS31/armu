import streamlit as st

from armu.pipeline import NutriPlanMatcher
from armu.streamlit_backend import (
    compare_recipe_for_streamlit,
    generate_streamlit_plan,
    get_streamlit_options,
)


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="NutriPlan",
    page_icon="🥗",
    layout="wide",
)


DAY_NAMES = {
    "monday": "Lunes",
    "tuesday": "Martes",
    "wednesday": "Miércoles",
    "thursday": "Jueves",
    "friday": "Viernes",
    "saturday": "Sábado",
    "sunday": "Domingo",
}


RESTRICTION_NAMES = {
    "vegetariano": "Vegetariano",
    "vegano": "Vegano",
    "sin_gluten": "Sin gluten",
}


# ============================================================
# CACHED RESOURCES
# ============================================================

@st.cache_resource
def load_matcher():
    return NutriPlanMatcher()


@st.cache_data(show_spinner=False)
def load_recommendation_options():
    return get_streamlit_options()


# ============================================================
# HEADER
# ============================================================

st.title("🥗 NutriPlan")

st.write(
    "Planea tu semana, ajusta tu presupuesto y compara "
    "precios entre supermercados."
)

st.divider()


# ============================================================
# TABS
# ============================================================

plan_tab, manual_tab = st.tabs(
    [
        "🍽️ Plan semanal",
        "🛒 Carrito por ingredientes",
    ]
)


# ============================================================
# WEEKLY PLAN
# ============================================================

with plan_tab:

    st.header(
        "Plan semanal personalizado"
    )

    st.write(
        "Elige tus preferencias y NutriPlan generará "
        "7 recetas con un carrito estimado."
    )

    options = load_recommendation_options()

    left, right = st.columns(2)

    with left:

        gustos = st.text_input(
            "¿Qué se te antoja?",
            value="chicken vegetables",
            placeholder=(
                "Ejemplo: pollo, pasta, arroz, verduras..."
            ),
        )

        presupuesto = st.number_input(
            "Presupuesto semanal (MXN)",
            min_value=50.0,
            value=1200.0,
            step=50.0,
        )

        personas = st.number_input(
            "Número de personas",
            min_value=int(
                options["personas_min"]
            ),
            max_value=int(
                options["personas_max"]
            ),
            value=2,
            step=1,
        )

    with right:

        cadena = st.selectbox(
            "Supermercado principal",
            options["cadenas"],
        )

        restricciones = st.multiselect(
            "Restricciones alimentarias",
            options["restricciones"],
            format_func=lambda value: (
                RESTRICTION_NAMES.get(
                    value,
                    value,
                )
            ),
        )

        st.info(
            "Las restricciones son filtros heurísticos "
            "del MVP y no sustituyen validación médica "
            "para alergias o celiaquía."
        )

    generate_clicked = st.button(
        "✨ Generar menú semanal",
        type="primary",
        width="stretch",
        key="generate_weekly_menu",
    )

    if generate_clicked:

        try:

            with st.spinner(
                "Buscando recetas y calculando precios..."
            ):

                recommendation = (
                    generate_streamlit_plan(
                        gustos=gustos,
                        presupuesto=float(
                            presupuesto
                        ),
                        personas=int(
                            personas
                        ),
                        cadena=cadena,
                        restricciones=restricciones,
                    )
                )

            st.session_state[
                "weekly_recommendation"
            ] = recommendation

            st.session_state[
                "price_comparison"
            ] = None

            st.success(
                "✅ Menú semanal generado"
            )

        except Exception as exc:

            st.error(
                f"No se pudo generar el menú: {exc}"
            )

    recommendation = st.session_state.get(
        "weekly_recommendation"
    )

    if recommendation:

        st.divider()

        cart = recommendation[
            "carrito_final"
        ]

        menu = recommendation[
            "menu_semanal"
        ]

        recipe_count = sum(
            len(recipes)
            for recipes
            in menu.values()
        )

        st.subheader(
            "Resumen"
        )

        metric_1, metric_2, metric_3, metric_4 = (
            st.columns(4)
        )

        metric_1.metric(
            "Costo estimado",
            (
                f"${cart['costo_total']:.2f} MXN"
            ),
        )

        metric_2.metric(
            "Recetas",
            recipe_count,
        )

        metric_3.metric(
            "Ingredientes",
            len(
                cart["items"]
            ),
        )

        metric_4.metric(
            "Presupuesto",
            (
                "✅ Dentro"
                if cart[
                    "dentro_de_presupuesto"
                ]
                else "⚠️ Excedido"
            ),
        )

        if recommendation.get(
            "mensaje"
        ):
            st.caption(
                recommendation["mensaje"]
            )

        st.divider()

        st.header(
            "📅 Tu menú semanal"
        )

        for day, recipes in menu.items():

            day_name = DAY_NAMES.get(
                day,
                day.title(),
            )

            st.subheader(
                day_name
            )

            for recipe in recipes:

                with st.expander(
                    f"🍽️ {recipe['name']}",
                    expanded=True,
                ):

                    serving_text = (
                        recipe.get(
                            "servings"
                        )
                    )

                    if serving_text:
                        st.caption(
                            f"Porciones: {serving_text}"
                        )

                    ingredients = recipe.get(
                        "ingredients",
                        [],
                    )

                    if ingredients:

                        st.write(
                            "**Ingredientes:**"
                        )

                        for ingredient in ingredients:
                            st.write(
                                f"- {ingredient}"
                            )

                    compare_clicked = st.button(
                        "💰 Comparar supermercados",
                        key=(
                            "compare_recipe_"
                            f"{recipe['id']}"
                        ),
                    )

                    if compare_clicked:

                        try:

                            st.session_state[
                                "price_comparison"
                            ] = (
                                compare_recipe_for_streamlit(
                                    int(
                                        recipe["id"]
                                    )
                                )
                            )

                        except Exception as exc:

                            st.error(
                                "No se pudo comparar "
                                f"la receta: {exc}"
                            )

        comparison = st.session_state.get(
            "price_comparison"
        )

        if comparison:

            st.divider()

            st.header(
                "💰 Comparación de supermercados"
            )

            st.subheader(
                comparison[
                    "nombre_receta"
                ]
            )

            comparison_rows = [
                {
                    "Supermercado":
                        item["cadena"],
                    "Precio estimado (MXN)":
                        item[
                            "precio_total_mxn"
                        ],
                }
                for item
                in comparison[
                    "comparacion"
                ]
            ]

            st.dataframe(
                comparison_rows,
                width="stretch",
                hide_index=True,
            )

            comp_1, comp_2, comp_3 = (
                st.columns(3)
            )

            comp_1.metric(
                "Más barato",
                comparison[
                    "cadena_mas_barata"
                ],
            )

            comp_2.metric(
                "Precio",
                (
                    "$"
                    f"{comparison['precio_mas_barato_mxn']:.2f}"
                    " MXN"
                ),
            )

            comp_3.metric(
                "Ahorro máximo",
                (
                    "$"
                    f"{comparison['ahorro_mxn']:.2f}"
                    " MXN"
                ),
            )

        st.divider()

        st.header(
            "🛒 Carrito estimado"
        )

        cart_rows = []

        for item in cart[
            "items"
        ]:

            cart_rows.append(
                {
                    "Ingrediente":
                        item[
                            "ingrediente"
                        ],
                    "Cantidad":
                        round(
                            item[
                                "cantidad"
                            ],
                            2,
                        ),
                    "Unidad":
                        item.get(
                            "unidad"
                        )
                        or "",
                    "Costo (MXN)":
                        round(
                            item[
                                "costo"
                            ],
                            2,
                        ),
                }
            )

        if cart_rows:

            st.dataframe(
                cart_rows,
                width="stretch",
                hide_index=True,
            )

        else:

            st.info(
                "El carrito no contiene items."
            )

        st.metric(
            "Total estimado del carrito",
            f"${cart['costo_total']:.2f} MXN",
        )

        st.caption(
            "Los costos son proporcionales a la cantidad "
            "utilizada por receta; no necesariamente "
            "representan comprar el paquete comercial completo."
        )


# ============================================================
# LEGACY MANUAL CART
# ============================================================

with manual_tab:

    st.header(
        "Carrito por ingredientes"
    )

    st.write(
        "Esta vista conserva el flujo original de NutriPlan: "
        "escribe ingredientes y busca productos PROFECO."
    )

    matcher = load_matcher()

    ingredients_text = st.text_area(
        "Escribe un ingrediente por línea",
        value=(
            "pollo\n"
            "cebolla\n"
            "ajo\n"
            "jitomate\n"
            "aceite de oliva"
        ),
        height=180,
        key="manual_ingredients",
    )

    manual_clicked = st.button(
        "🛒 Crear carrito manual",
        type="primary",
        width="stretch",
        key="manual_cart_button",
    )

    if manual_clicked:

        ingredients = [
            ingredient.strip()
            for ingredient
            in ingredients_text.splitlines()
            if ingredient.strip()
        ]

        if not ingredients:

            st.warning(
                "Escribe al menos un ingrediente."
            )

        else:

            with st.spinner(
                "Buscando productos y precios en PROFECO..."
            ):

                result = (
                    matcher.build_shopping_cart(
                        ingredients
                    )
                )

            st.success(
                "✅ Carrito generado correctamente"
            )

            col1, col2, col3 = (
                st.columns(3)
            )

            col1.metric(
                "Total estimado",
                f"${result['total']:.2f} MXN",
            )

            col2.metric(
                "Encontrados",
                result[
                    "matched_products"
                ],
            )

            col3.metric(
                "Sin match",
                result[
                    "unmatched_products"
                ],
            )

            if result[
                "cart"
            ]:

                cart_table = []

                for item in result[
                    "cart"
                ]:

                    cart_table.append(
                        {
                            "Ingrediente":
                                item[
                                    "ingredient"
                                ],
                            "Normalizado":
                                item[
                                    "normalized"
                                ],
                            "Producto PROFECO":
                                item[
                                    "matched_term"
                                ],
                            "Precio mediano":
                                round(
                                    item[
                                        "median_price"
                                    ],
                                    2,
                                ),
                        }
                    )

                st.dataframe(
                    cart_table,
                    width="stretch",
                    hide_index=True,
                )

            if result[
                "unmatched"
            ]:

                st.warning(
                    "Hay ingredientes sin match."
                )

                for item in result[
                    "unmatched"
                ]:
                    st.write(
                        f"- {item['ingredient']}"
                    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NutriPlan MVP — recomendaciones, carrito y "
    "comparación de precios con datos reales."
)
