import streamlit as st

from armu.pipeline import NutriPlanMatcher


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NutriPlan",
    page_icon="🥗",
    layout="centered",
)


# ============================================================
# LOAD MATCHER
# ============================================================

@st.cache_resource
def load_matcher():
    return NutriPlanMatcher()


matcher = load_matcher()


# ============================================================
# HEADER
# ============================================================

st.title("🥗 NutriPlan")

st.write(
    "Escribe ingredientes en español o inglés. "
    "NutriPlan los normaliza, los conecta con productos "
    "de PROFECO y estima el costo del carrito."
)

st.divider()


# ============================================================
# INGREDIENT INPUT
# ============================================================

st.subheader(
    "Ingresa tus ingredientes en español o inglés"
)

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
    placeholder=(
        "Ejemplo:\n"
        "pollo\n"
        "cebolla\n"
        "ajo\n"
        "jitomate"
    ),
)


# ============================================================
# CREATE CART
# ============================================================

if st.button(
    "🛒 Crear carrito",
    type="primary",
    width="stretch",
):

    ingredients = [
        ingredient.strip()
        for ingredient in ingredients_text.splitlines()
        if ingredient.strip()
    ]

    # --------------------------------------------------------
    # EMPTY INPUT
    # --------------------------------------------------------

    if not ingredients:

        st.warning(
            "Escribe al menos un ingrediente."
        )

    else:

        # ----------------------------------------------------
        # RUN MATCHING
        # ----------------------------------------------------

        with st.spinner(
            "Buscando productos y precios en PROFECO..."
        ):

            result = matcher.build_shopping_cart(
                ingredients
            )

        st.success(
            "✅ Carrito generado correctamente"
        )

        # ====================================================
        # SUMMARY
        # ====================================================

        st.subheader(
            "Resumen"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total estimado",
            f"${result['total']:.2f} MXN",
        )

        col2.metric(
            "Encontrados",
            result["matched_products"],
        )

        col3.metric(
            "Sin match",
            result["unmatched_products"],
        )

        # ====================================================
        # SHOPPING CART
        # ====================================================

        st.subheader(
            "🛒 Carrito estimado"
        )

        if result["cart"]:

            cart_table = []

            for item in result["cart"]:

                cart_table.append(
                    {
                        "Ingrediente original":
                            item["ingredient"],

                        "Ingrediente normalizado":
                            item["normalized"],

                        "Producto PROFECO":
                            item["matched_term"],

                        "Precio mediano (MXN)":
                            round(
                                item["median_price"],
                                2,
                            ),

                        "Precio mínimo (MXN)":
                            round(
                                item["min_price"],
                                2,
                            ),

                        "Precio máximo (MXN)":
                            round(
                                item["max_price"],
                                2,
                            ),

                        "Coincidencias PROFECO":
                            item["matches"],
                    }
                )

            st.dataframe(
                cart_table,
                width="stretch",
                hide_index=True,
            )

        # ====================================================
        # MATCH DETAILS
        # ====================================================

        st.subheader(
            "🔎 Matching"
        )

        for item in result["cart"]:

            st.write(
                f"**{item['ingredient']}**"
                f" → `{item['normalized']}`"
                f" → **{item['matched_term']}**"
                f" → ${item['median_price']:.2f} MXN"
            )

        # ====================================================
        # UNMATCHED INGREDIENTS
        # ====================================================

        if result["unmatched"]:

            st.subheader(
                "⚠️ Ingredientes sin match"
            )

            st.write(
                "Estos ingredientes todavía no tienen "
                "una regla de matching disponible:"
            )

            for item in result["unmatched"]:

                st.write(
                    f"- {item['ingredient']}"
                )

        # ====================================================
        # COVERAGE
        # ====================================================

        total_input = (
            result["matched_products"]
            + result["unmatched_products"]
        )

        if total_input > 0:

            coverage = (
                result["matched_products"]
                / total_input
                * 100
            )

        else:

            coverage = 0

        st.subheader(
            "📊 Cobertura"
        )

        st.progress(
            min(
                coverage / 100,
                1.0,
            )
        )

        st.write(
            f"{coverage:.1f}% de los ingredientes "
            "fueron encontrados."
        )

        # ====================================================
        # MVP EXPLANATION
        # ====================================================

        st.info(
            "MVP: el costo representa el precio mediano "
            "de una presentación o producto de PROFECO "
            "por ingrediente único. "
            "Todavía no calcula cantidades exactas "
            "consumidas por receta."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NutriPlan MVP — Matching bilingüe de ingredientes "
    "y estimación de precios con datos de PROFECO."
)
