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
    "vegetarian": "Vegetarian",
    "vegan": "Vegan",
    "gluten_free": "Gluten free",
    "dairy_free": "Dairy free",
    "lactose_free": "Lactose free",
    "nut_free": "Nut free",
    "egg_free": "Egg free",
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
    "Tell us what you feel like eating, set your restrictions and your weekly "
    "budget, and we'll build a Monday–Sunday menu that fits you best."
)

st.caption(
    f"{len(recipes):,} recipes with an estimated cost (PROFECO prices, MXN)."
)

st.divider()


# ============================================================
# USER INPUTS
# ============================================================

st.subheader("¿Qué quieres comer?")

user_text = st.text_input(
    "Descríbelo con tus propias palabras",
    value="algo con pollo y verduras",
    placeholder="e.g. a light pasta with cheese, or a spicy beef soup",
)

restriction_labels = st.multiselect(
    "Restricciones alimentarias",
    options=list(USABLE_RESTRICTIONS.values()),
    default=[],
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

    # --------------------------------------------------------
    # NO RECIPES
    # --------------------------------------------------------

    if plan["status"] == "NO_RECIPES":
        st.warning(
            "No recipes match those restrictions. Try removing one."
        )
        st.stop()

    st.divider()

    if plan["no_text_match"]:
        st.warning(
            f"🔎 Nothing matches «{user_text}» within your restrictions. "
            "Showing other options that do fit — try different words."
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
        delta=None if plan["within_budget"] else "Over budget",
        delta_color="normal" if plan["within_budget"] else "inverse",
    )

    if plan["within_budget"]:
        st.success(
            f"✅ Tu menú semanal fits the budget. "
            f"You have ${plan['remaining']:.2f} MXN left."
        )
    else:
        st.error(
            f"⚠️ Your menu is ${abs(plan['remaining']):.2f} MXN over budget. "
            "Raise the budget or adjust your search."
        )

    # ========================================================
    # WEEKLY MENU
    # ========================================================

    st.subheader("Tu menú semanal")

    for item in plan["menu"]:
        with st.expander(
            f"**{item['day']}** · {item['name']}  —  ${item['cost']:.2f} MXN"
        ):
            st.caption(
                f"Rango de costo estimado: ${item['cost_min']:.0f}–"
                f"{item['cost_max']:.0f} MXN"
            )

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


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Armu · NutriPlan — Le Wagon final project. "
    "Recipes: Food.com · Cost estimates: PROFECO prices."
)
