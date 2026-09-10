from pathlib import Path

import requests
import streamlit as st

API_URL = "http://localhost:8000/recomendacion"
LOGO = Path(__file__).parent / "assets" / "armu_logo.png"

DIAS_ES = {
    "monday": "Lunes", "tuesday": "Martes", "wednesday": "Miércoles",
    "thursday": "Jueves", "friday": "Viernes",
    "saturday": "Sábado", "sunday": "Domingo",
}

st.set_page_config(page_title="Armu", page_icon="🍳", layout="wide")

st.markdown("""
<style>
/* ---------- form card ---------- */
[data-testid="stForm"] {
    background-color: #EFE8DA;
    border: 1px solid #DDD3BE;
    border-radius: 12px;
    padding: 1.5rem;
}

[data-testid="stForm"] input,
[data-testid="stForm"] textarea {
    background-color: #FBF8F1 !important;
    border: 1px solid #DDD3BE !important;
    border-radius: 8px !important;
}

/* ---------- bordered panels (results + cart) ---------- */
[data-testid="stVerticalBlock"][data-test-wrap] {
    background-color: #EFE8DA;
    border: 1px solid #DDD3BE;
    border-radius: 12px;
    padding: 1.5rem;
}

/* ---------- day expanders ---------- */
[data-testid="stExpander"] {
    border: none !important;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0 !important;
}

[data-testid="stExpander"] summary {
    background-color: #3F6B4E !important;
    padding: 0.5rem 1rem !important;
}

[data-testid="stExpander"] summary:hover {
    background-color: #33573F !important;
}

[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary svg {
    color: #FBF8F1 !important;
    fill: #FBF8F1 !important;
}

[data-testid="stExpanderDetails"] {
    background-color: #FBF8F1;
    padding: 1rem;
}

/* tighten the gap between stacked elements */
[data-testid="stVerticalBlock"] {
    gap: 0.35rem;
}

/* ---------- tabs ---------- */
[data-testid="stTab"][aria-selected="true"] p {
    color: #3F6B4E !important;
}

[data-testid="stTab"] .react-aria-SelectionIndicator {
    background-color: #3F6B4E !important;
}

/* ---------- shopping list table ---------- */
[data-testid="stTable"] thead th {
    color: #3F6B4E !important;
    font-weight: 600;
    background-color: #EFE8DA !important;
}
</style>
""", unsafe_allow_html=True)

if "data" not in st.session_state:
    st.session_state.data = None

#  logo
logo_l, logo_c, logo_r = st.columns([2, 1, 2])
logo_c.image(str(LOGO), use_container_width=True)

col_form, col_menu = st.columns([1, 2], gap="large")

# form
with col_form:
    with st.form("busqueda"):
        gustos = st.text_area(
            "¿Qué se te antoja?",
            placeholder="Tengo zanahoria, chícharos y espinaca. Vegano, nada de carne.",
            height=120,
        )
        presupuesto = st.number_input(
            "Presupuesto semanal (MXN)",
            min_value=0.0, value=500.0, step=50.0,
        )
        personas = st.number_input(
            "Personas", min_value=1, max_value=10, value=2,
        )
        enviar = st.form_submit_button(
            "Generar menú", type="primary", use_container_width=True,
        )

    if enviar:
        with st.spinner("Armando tu menú..."):
            try:
                r = requests.post(
                    API_URL,
                    json={
                        "gustos": gustos,
                        "presupuesto": presupuesto,
                        "personas": personas,
                    },
                    timeout=30,
                )
                r.raise_for_status()
                st.session_state.data = r.json()
            except requests.RequestException as e:
                st.session_state.data = None
                st.error(f"No se pudo conectar con la API: {e}")

data = st.session_state.data

# menu
with col_menu:
    with st.container(border=True):
        if data is None:
            st.markdown(
                "Describe lo que se te antoja y tu presupuesto. "
                "Armamos siete comidas y la lista del súper."
            )
        else:
            if data.get("mensaje"):
                st.warning(data["mensaje"])

            menu = data.get("menu_semanal", {})

            for dia_en, recetas in menu.items():
                dia = DIAS_ES.get(dia_en, dia_en)

                if not recetas:
                    with st.expander(f"**{dia}** — sin receta", expanded=False):
                        st.caption("No hubo receta para este día.")
                    continue

                titulo = recetas[0].get("name", "Sin nombre")

                with st.expander(f"**{dia}** · {titulo}", expanded=False):
                    for receta in recetas:
                        meta = []
                        if receta.get("servings"):
                            meta.append(f"{receta['servings']} porciones")
                        if receta.get("serving_size"):
                            meta.append(str(receta["serving_size"]))
                        if receta.get("is_vegan"):
                            meta.append("🌱 Vegano")
                        elif receta.get("is_vegetarian"):
                            meta.append("🥬 Vegetariano")
                        if receta.get("is_gluten_free"):
                            meta.append("🌾 Sin gluten")
                        if meta:
                            st.caption(" · ".join(meta))

                        tab_ing, tab_pasos = st.tabs(["Ingredientes", "Preparación"])

                        with tab_ing:
                            for ing in receta.get("ingredients", []):
                                st.markdown(f"- {str(ing).strip()}")

                        with tab_pasos:
                            for n, paso in enumerate(receta.get("steps", []), 1):
                                st.markdown(f"{n}. {paso}")

#  cart
if data is not None:
    carrito = data.get("carrito_final", {})

    st.divider()

    with st.container(border=True):
        st.subheader("Lista de compras")

        col_items, col_resumen = st.columns([2, 1], gap="large")

        with col_items:
            if carrito.get("items"):
                st.dataframe(
                    carrito["items"],
                    column_config={
                        "ingrediente": "Ingrediente",
                        "cantidad": "Cantidad",
                        "costo": st.column_config.NumberColumn("Costo", format="$%.2f"),
                    },
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("Sin productos en la lista.")

        with col_resumen:
            st.metric("Total", f"${carrito.get('costo_total', 0):,.2f}")
            if carrito.get("dentro_de_presupuesto", True):
                st.caption("✓ Dentro del presupuesto")
            else:
                st.error("Excede el presupuesto")

        sin_precio = carrito.get("ingredientes_sin_precio", [])
        no_incluidos = carrito.get("items_retirados", [])

        if sin_precio or no_incluidos:
            with st.expander("Notas sobre precios"):
                if sin_precio:
                    st.write("**Sin precio disponible:** " + ", ".join(sin_precio))
                if no_incluidos:
                    st.write("**No incluidos:** " + ", ".join(no_incluidos))
