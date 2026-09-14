import pandas as pd
import streamlit as st

from armu.planner import CHAINS, generate_weekly_plan, load_data


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Armu · NutriPlan",
    page_icon="🥗",
    layout="centered",
)


# ============================================================
# DATA
# ============================================================

@st.cache_data
def get_data():
    return load_data()


recipes, costs = get_data()


# Restriction key -> label shown to the user.
RESTRICTION_LABELS = {
    "vegetarian": "Vegetariano",
    "vegan": "Vegano",
    "gluten_free": "Sin gluten",
    "dairy_free": "Sin lácteos",
    "lactose_free": "Sin lactosa",
    "nut_free": "Sin nueces",
    "egg_free": "Sin huevo",
}


# ============================================================
# HEADER
# ============================================================

st.title("🥗 Armu · NutriPlan")

st.write(
    "Genera un **menú semanal** según tus preferencias y arma el "
    "**carrito de súper** con precios reales de PROFECO, cuidando tu presupuesto."
)

st.caption(
    f"Demo sobre {len(recipes)} recetas con costo completo en "
    "Walmart, Soriana y Chedraui."
)

st.divider()


# ============================================================
# USER INPUTS
# ============================================================

st.subheader("1 · Tus preferencias")

user_text = st.text_input(
    "¿Qué quieres comer esta semana?",
    value="algo con pollo y verduras",
    placeholder="ej. algo ligero con pollo, o pasta y queso",
)

restriction_labels = st.multiselect(
    "Restricciones alimentarias",
    options=list(RESTRICTION_LABELS.values()),
    default=[],
)

# Map the chosen labels back to the internal keys the recommender expects.
label_to_key = {v: k for k, v in RESTRICTION_LABELS.items()}
restrictions = [label_to_key[label] for label in restriction_labels]

col_a, col_b = st.columns(2)

with col_a:
    max_time = st.radio(
        "Tiempo máximo para cocinar",
        options=[15, 30, 60],
        index=1,
        format_func=lambda m: f"{m} min",
        horizontal=True,
    )

with col_b:
    chain = st.selectbox(
        "Supermercado",
        options=CHAINS,
        index=0,
    )

budget = st.number_input(
    "Presupuesto semanal (MXN)",
    min_value=0,
    value=800,
    step=50,
)


# ============================================================
# GENERATE PLAN
# ============================================================

if st.button("🍽️ Generar mi plan semanal", type="primary", width="stretch"):

    with st.spinner("Armando tu menú y carrito..."):
        plan = generate_weekly_plan(
            restrictions=restrictions,
            max_time=max_time,
            user_text=user_text,
            budget=budget,
            chain=chain,
            recipes=recipes,
            costs=costs,
        )

    # --------------------------------------------------------
    # NO RECIPES
    # --------------------------------------------------------

    if plan["status"] == "NO_RECIPES":
        st.warning(
            "Ninguna receta cumple con esas restricciones y tiempo. "
            "Intenta quitar alguna restricción o subir el tiempo disponible."
        )
        st.stop()

    st.divider()

    # ========================================================
    # BUDGET SUMMARY
    # ========================================================

    st.subheader("2 · Resumen")

    col1, col2, col3 = st.columns(3)
    col1.metric("Carrito estimado", f"${plan['total']:.2f}")
    col2.metric("Presupuesto", f"${plan['budget']:.2f}")
    col3.metric(
        "Restante",
        f"${plan['remaining']:.2f}",
        delta=None if plan["within_budget"] else "Excedido",
        delta_color="normal" if plan["within_budget"] else "inverse",
    )

    if plan["within_budget"]:
        st.success(
            f"✅ El menú cabe en tu presupuesto en {chain}. "
            f"Te sobran ${plan['remaining']:.2f} MXN."
        )
    else:
        st.error(
            f"⚠️ El menú se pasa por ${abs(plan['remaining']):.2f} MXN en {chain}. "
            "Prueba otro supermercado o sube el presupuesto."
        )

    # ========================================================
    # WEEKLY MENU
    # ========================================================

    st.subheader("3 · Tu menú semanal")

    for item in plan["menu"]:
        with st.expander(
            f"**{item['day']}** · {item['name']}  —  ${item['cost']:.2f} MXN"
        ):
            st.markdown("**Ingredientes**")
            st.write("\n".join(f"- {ing}" for ing in item["ingredients"]))

            if item["steps"]:
                st.markdown("**Preparación**")
                st.write(
                    "\n".join(
                        f"{n}. {step}"
                        for n, step in enumerate(item["steps"], start=1)
                    )
                )

    # ========================================================
    # SHOPPING LIST
    # ========================================================

    st.subheader(f"4 · Carrito de súper ({chain})")

    if plan["shopping_list"]:
        shopping_table = [
            {
                "Ingrediente": row["ingredient"],
                "Producto PROFECO": row["profeco_product"],
                "Cantidad (g)": round(row["quantity_g"], 0),
                "Costo (MXN)": round(row["cost_mxn"], 2),
            }
            for row in plan["shopping_list"]
        ]
        st.dataframe(
            shopping_table,
            width="stretch",
            hide_index=True,
        )

    # ========================================================
    # CHAIN COMPARISON
    # ========================================================

    st.subheader("5 · Comparación entre supermercados")

    comparison = pd.DataFrame(
        {
            "Supermercado": list(plan["chain_totals"].keys()),
            "Costo total (MXN)": list(plan["chain_totals"].values()),
        }
    ).sort_values("Costo total (MXN)")

    cheapest = comparison.iloc[0]

    st.dataframe(comparison, width="stretch", hide_index=True)

    st.info(
        f"🏆 El más barato para este menú es **{cheapest['Supermercado']}** "
        f"con ${cheapest['Costo total (MXN)']:.2f} MXN."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Armu · NutriPlan — Proyecto final Le Wagon. "
    "Datos: recetas de Food.com + precios de PROFECO (Walmart, Soriana, Chedraui)."
)
