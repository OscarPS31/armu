from armu.streamlit_backend import (
    compare_recipe_for_streamlit,
    generate_streamlit_plan,
    get_streamlit_options,
)


def test_streamlit_options():
    options = get_streamlit_options()

    assert options["cadenas"] == [
        "Walmart",
        "Soriana",
        "Chedraui",
    ]

    assert options["personas_min"] == 1
    assert options["personas_max"] == 20


def test_streamlit_generates_weekly_plan():
    result = generate_streamlit_plan(
        gustos="chicken vegetables",
        presupuesto=1200,
        personas=2,
        cadena="Walmart",
        restricciones=[],
    )

    recipes = [
        recipe
        for day_recipes
        in result[
            "menu_semanal"
        ].values()
        for recipe
        in day_recipes
    ]

    assert len(recipes) == 7

    assert (
        result[
            "carrito_final"
        ][
            "costo_total"
        ]
        <= 1200
    )


def test_streamlit_comparison_from_generated_recipe():
    result = generate_streamlit_plan(
        gustos="chicken vegetables",
        presupuesto=1200,
        personas=2,
        cadena="Walmart",
        restricciones=[],
    )

    recipe = next(
        recipe
        for recipes
        in result[
            "menu_semanal"
        ].values()
        for recipe
        in recipes
    )

    comparison = (
        compare_recipe_for_streamlit(
            recipe["id"]
        )
    )

    chains = {
        row["cadena"]
        for row
        in comparison[
            "comparacion"
        ]
    }

    assert chains == {
        "Walmart",
        "Soriana",
        "Chedraui",
    }
