from scripts.demo_mvp import run_demo


def test_demo_runs_end_to_end():
    result = run_demo(
        gustos="chicken vegetables",
        presupuesto=1200,
        personas=2,
        cadena="Walmart",
        restricciones=[],
    )

    assert result[
        "opciones"
    ][
        "cadenas"
    ] == [
        "Walmart",
        "Soriana",
        "Chedraui",
    ]

    assert result[
        "menu"
    ]

    assert result[
        "comparacion_primera_receta"
    ] is not None


def test_demo_preserves_input_configuration():
    result = run_demo(
        gustos="rice vegetables",
        presupuesto=None,
        personas=4,
        cadena="Chedraui",
        restricciones=[],
    )

    assert result[
        "input"
    ][
        "personas"
    ] == 4

    assert result[
        "input"
    ][
        "cadena"
    ] == "Chedraui"

    assert len(
        result[
            "menu"
        ]
    ) == 7


def test_demo_accepts_dietary_restriction():
    result = run_demo(
        gustos="vegetables beans",
        presupuesto=1000,
        personas=2,
        cadena="Soriana",
        restricciones=[
            "vegetariano",
        ],
    )

    assert result[
        "input"
    ][
        "restricciones"
    ] == [
        "vegetariano"
    ]

    assert result[
        "menu"
    ]

    assert (
        result[
            "carrito"
        ][
            "costo_total"
        ]
        <= 1000
    )
