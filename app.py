import requests
import streamlit as st

API_URL = "http://localhost:8000/recomendacion"

st.set_page_config(page_title="Armu", page_icon="🍳", layout="wide")
st.title("Armu — menú semanal con presupuesto")

with st.form("busqueda"):
    gustos = st.text_area(
        "¿Qué se te antoja?",
        placeholder="Quiero 7 recetas diferentes. Tengo zanahoria, chícharos y espinaca. Vegano.",
    )
    col1, col2 = st.columns(2)
    presupuesto = col1.number_input("Presupuesto (MXN)", min_value=0.0, value=500.0, step=50.0)
    personas = col2.number_input("Personas", min_value=1, max_value=10, value=2)

    enviar = st.form_submit_button("Generar menú", type="primary")

if enviar:
    payload = {
        "gustos": gustos,
        "presupuesto": presupuesto,
        "personas": personas,
    }

    try:
        r = requests.post(API_URL, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        st.error(f"No se pudo conectar con la API: {e}")
        st.stop()

    if data.get("mensaje"):
        st.warning(data["mensaje"])

    DIAS_ES = {
        "monday": "Lunes", "tuesday": "Martes", "wednesday": "Miércoles",
        "thursday": "Jueves", "friday": "Viernes",
        "saturday": "Sábado", "sunday": "Domingo",
    }

    menu = data["menu_semanal"]

    st.subheader("Menú de la semana")

    for dia_en, recetas in menu.items():
        st.markdown(f"### {DIAS_ES.get(dia_en, dia_en)}")

        if not recetas:
            st.caption("Sin receta para este día")
            continue

        for receta in recetas:
            with st.container(border=True):
                st.markdown(f"**{receta['name']}**")

                meta = []
                if receta.get("servings"):
                    meta.append(f"{receta['servings']} porciones")
                if receta.get("serving_size"):
                    meta.append(receta["serving_size"])
                if meta:
                    st.caption(" · ".join(meta))

                chips = []
                if receta.get("is_vegan"):
                    chips.append("🌱 Vegano")
                elif receta.get("is_vegetarian"):
                    chips.append("🥬 Vegetariano")
                if receta.get("is_gluten_free"):
                    chips.append("🌾 Sin gluten")
                if chips:
                    st.caption(" ".join(chips))

                tab_ing, tab_pasos = st.tabs(["Ingredientes", "Preparación"])

                with tab_ing:
                    for ing in receta.get("ingredients", []):
                        st.markdown(f"- {ing.strip()}")

                with tab_pasos:
                    for i, paso in enumerate(receta.get("steps", []), 1):
                        st.markdown(f"{i}. {paso}")
    carrito = data["carrito_final"]

    st.divider()
    st.subheader("Lista de compras")

    col_items, col_resumen = st.columns([2, 1])

    with col_items:
        if carrito["items"]:
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
            st.caption("Sin productos en la lista")

    with col_resumen:
        st.metric("Total", f"${carrito['costo_total']:,.2f}")

        if carrito["dentro_de_presupuesto"]:
            st.success("Dentro del presupuesto")
        else:
            st.error("Excede el presupuesto")

    sin_precio = carrito.get("ingredientes_sin_precio", [])
    retirados = carrito.get("items_retirados", [])

    if sin_precio or retirados:
        with st.expander("Notas sobre precios"):
            if sin_precio:
                st.write("**Sin precio disponible:** " + ", ".join(sin_precio))
                st.caption("No se pudo estimar el costo de estos ingredientes.")
            if retirados:
                st.write("**Retirados:** " + ", ".join(retirados))
