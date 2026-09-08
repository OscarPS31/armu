import streamlit as st

from armu.pipeline import NutriPlanMatcher


st.set_page_config(
    page_title="NutriPlan",
    page_icon="🥗",
    layout="centered",
)


@st.cache_resource
def load_matcher():
    return NutriPlanMatcher()


matcher = load_matcher()


st.title("🥗 NutriPlan")

st.write(
    "Convierte ingredientes de recetas en productos "
    "encontrados en PROFECO y estima su costo."
)


st.divider()


st.subheader("Ingresa tus ingredientes")


ingredients_text = st.text_area(
    "Escribe un ingrediente por línea",
    value=(
        "roasting chickens\n"
        "onions\n"
        "garlic cloves\n"
        "tomatoes\n"
        "olive oil"
    ),
    height=180,
)


if st.button(
    "Crear carrito",
    type="primary",
):

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
            "Buscando precios en PROFECO..."
        ):

            result = (
                matcher.build_shopping_cart(
                    ingredients
                )
            )


        st.success(
            "Carrito generado"
        )


        # ==============================================
        # SUMMARY
        # ==============================================

        col1, col2, col3 = st.columns(3)


        col1.metric(
            "Total estimado",
            f"${result['total']:.2f} MXN",
        )


        col2.metric(
            "Productos encontrados",
            result["matched_products"],
        )


        col3.metric(
            "Sin match",
            result["unmatched_products"],
        )


        # ==============================================
        # CART
        # ==============================================

        st.subheader(
            "🛒 Carrito"
        )


        if result["cart"]:

            cart_table = []


            for item in result["cart"]:

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
                            item[
                                "median_price"
                            ],

                        "Precio mínimo":
                            item[
                                "min_price"
                            ],

                        "Precio máximo":
                            item[
                                "max_price"
                            ],
                    }
                )


            st.dataframe(
                cart_table,
                use_container_width=True,
                hide_index=True,
            )


        # ==============================================
        # UNMATCHED
        # ==============================================

        if result["unmatched"]:

            st.subheader(
                "⚠️ Ingredientes sin match"
            )


            for item in result[
                "unmatched"
            ]:

                st.write(
                    "-",
                    item["ingredient"],
                )


        # ==============================================
        # DISCLAIMER
        # ==============================================

        st.info(
            "MVP: el costo representa el precio "
            "mediano de un producto o presentación "
            "PROFECO por ingrediente único. "
            "Todavía no calcula cantidades "
            "proporcionales por receta."
        )
