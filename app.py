import streamlit as st

from armu.planner import generate_weekly_plan, load_data


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


recipes = get_data()


# Restriction key -> label shown to the user.
RESTRICTION_LABELS = {
    "vegetarian": "Vegetariano",
    "vegan": "Vegano",
    "gluten_free": "Sin gluten",
    "dairy_free": "Sin lácteos",
    "lactose_free": "Sin lactosa",
    "nut_free": "Sin frutos secos",
    "egg_free": "Sin huevo",
}

# Only offer restrictions that have enough recipes in the dataset.
MIN_RECIPES_PER_RESTRICTION = 10

USABLE_RESTRICTIONS = {
    key: label
    for key, label in RESTRICTION_LABELS.items()
    if int(recipes[f"is_{key}"].sum()) >= MIN_RECIPES_PER_RESTRICTION
}


# ============================================================
# HEADER
# ============================================================

st.title("🥗 Armu · NutriPlan")

st.write(
    "Dinos qué se te antoja, selecciona tus restricciones y define tu "
    "presupuesto semanal. Crearemos un menú de lunes a domingo para ti."
)

st.caption(
    f"{len(recipes):,} recetas con costo estimado (precios PROFECO, MXN)."
)

st.divider()


# ============================================================
# USER INPUTS
# ============================================================

st.subheader("¿Qué quieres comer?")

user_text = st.text_input(
    "Descríbelo con tus propias palabras",
    value="algo con pollo y verduras",
    placeholder="ej. una pasta ligera con queso o una sopa de res picante",
)

restriction_labels = st.multiselect(
    "Restricciones alimentarias",
    options=list(USABLE_RESTRICTIONS.values()),
    default=[],
    placeholder="Elige opciones",
)

label_to_key = {v: k for k, v in USABLE_RESTRICTIONS.items()}
restrictions = [label_to_key[label] for label in restriction_labels]

budget = st.number_input(
    "Presupuesto semanal (MXN)",
    min_value=0,
    value=800,
    step=50,
)


# ============================================================
# GENERATE WEEKLY MENU
# ============================================================

if st.button("🍽️ Crear mi menú semanal", type="primary", width="stretch"):

    with st.spinner("Creando tu menú..."):
        plan = generate_weekly_plan(
            user_text=user_text,
            restrictions=restrictions,
            budget=budget,
            recipes=recipes,
        )

    st.session_state["plan_actual"] = plan

if "plan_actual" in st.session_state:
    plan = st.session_state["plan_actual"]

    # --------------------------------------------------------
    # NO RECIPES
    # --------------------------------------------------------

    if plan["status"] == "NO_RECIPES":
        st.warning(
            "No hay recetas que coincidan con esas restricciones. Intenta quitar alguna."
        )
        st.stop()

    st.divider()

    if plan["no_text_match"]:
        st.warning(
            f"🔎 No encontramos «{user_text}» dentro de tus restricciones. "
            "Mostramos otras opciones compatibles. Intenta usar otras palabras."
        )

    if plan["incomplete"]:
        st.warning(
            f"⚠️ Only {plan['available_recipes']} recipe(s) match these "
            f"restrictions, so your menu has {plan['days_filled']} day(s) "
            "instead of 7. Remove a restriction for a full week."
        )

    # ========================================================
    # BUDGET SUMMARY
    # ========================================================

    st.subheader("Resumen")

    col1, col2, col3 = st.columns(3)
    col1.metric("Costo semanal", f"${plan['total']:.2f}")
    col2.metric("Presupuesto", f"${plan['budget']:.2f}")
    col3.metric(
        "Disponible",
        f"${plan['remaining']:.2f}",
        delta=None if plan["within_budget"] else "Sobre presupuesto",
        delta_color="normal" if plan["within_budget"] else "inverse",
    )

    if plan["within_budget"]:
        st.success(
            f"✅ Tu menú semanal está dentro del presupuesto. "
            f"Te quedan ${plan['remaining']:.2f} MXN disponibles."
        )
    else:
        st.error(
            f"⚠️ Tu menú supera el presupuesto por ${abs(plan['remaining']):.2f} MXN. "
            "Aumenta el presupuesto o ajusta tu búsqueda."
        )

    # ========================================================
    # WEEKLY MENU
    # ========================================================

    st.subheader("Tu menú semanal")

    DIAS = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }

    for item in plan["menu"]:
        with st.expander(
            f"**{DIAS.get(item['day'], item['day'])}** · {item['name']}  —  ${item['cost']:.2f} MXN"
        ):
            st.caption(
                f"Rango de costo estimado: ${item['cost_min']:.0f}–"
                f"{item['cost_max']:.0f} MXN"
            )

            st.markdown("**Ingredientes**")

            ingredientes_completos = "\n".join(
                f"- {ing}"
                for ing in item["ingredients"]
            )

            st.write(
                ingredientes_completos
            )

            if item["steps"]:
                st.markdown("**Preparación**")

                texto_preparacion = "\n".join(
                    f"{n}. {step}"
                    for n, step in enumerate(item["steps"], start=1)
                )

                preparacion_completa = "\n".join(
                    f"{n}. {step}"
                    for n, step in enumerate(item["steps"], start=1)
                )

                st.write(
                    preparacion_completa
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Armu · NutriPlan — Proyecto final de Le Wagon. "
    "Recetas: Food.com · Costos estimados: precios PROFECO."
)
