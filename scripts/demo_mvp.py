import argparse
import json
import sys
import warnings
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
)

from fastapi.testclient import TestClient

from api.main import app


def run_demo(
    gustos: str = "chicken vegetables",
    presupuesto: float | None = 1200,
    personas: int = 2,
    cadena: str = "Walmart",
    restricciones: list[str] | None = None,
) -> dict:
    restricciones = restricciones or []

    client = TestClient(
        app
    )

    options_response = client.get(
        "/opciones"
    )

    if options_response.status_code != 200:
        raise RuntimeError(
            "No se pudieron obtener las opciones."
        )

    options = options_response.json()

    payload = {
        "gustos": gustos,
        "presupuesto": presupuesto,
        "personas": personas,
        "cadena": cadena,
        "restricciones": restricciones,
    }

    recommendation_response = client.post(
        "/recomendacion",
        json=payload,
    )

    if recommendation_response.status_code != 200:
        raise RuntimeError(
            "Falló POST /recomendacion: "
            f"{recommendation_response.status_code} "
            f"{recommendation_response.text}"
        )

    recommendation = (
        recommendation_response.json()
    )

    menu_rows = []

    for day, recipes in (
        recommendation[
            "menu_semanal"
        ].items()
    ):
        for recipe in recipes:
            menu_rows.append(
                {
                    "dia": day,
                    "id": recipe["id"],
                    "nombre": recipe["name"],
                    "personas": recipe[
                        "servings"
                    ],
                }
            )

    comparison = None

    if menu_rows:
        recipe_id = menu_rows[0][
            "id"
        ]

        comparison_response = client.get(
            f"/comparar-precios/{recipe_id}"
        )

        if (
            comparison_response.status_code
            == 200
        ):
            comparison = (
                comparison_response.json()
            )

    return {
        "input": payload,
        "opciones": options,
        "menu": menu_rows,
        "carrito": recommendation[
            "carrito_final"
        ],
        "mensaje": recommendation[
            "mensaje"
        ],
        "comparacion_primera_receta": comparison,
    }


def print_demo(
    result: dict,
) -> None:
    print("")
    print(
        "========================================"
    )
    print(
        "        ARMU — DEMO BACKEND MVP"
    )
    print(
        "========================================"
    )

    payload = result[
        "input"
    ]

    print("")
    print("CONFIGURACIÓN")
    print("-------------")

    print(
        "Supermercado:",
        payload["cadena"],
    )

    print(
        "Personas:",
        payload["personas"],
    )

    print(
        "Presupuesto:",
        (
            f"${payload['presupuesto']:.2f} MXN"
            if payload["presupuesto"] is not None
            else "Sin límite"
        ),
    )

    print(
        "Gustos:",
        payload["gustos"] or "Sin preferencia",
    )

    print(
        "Restricciones:",
        (
            ", ".join(
                payload[
                    "restricciones"
                ]
            )
            or "Ninguna"
        ),
    )

    print("")
    print("MENÚ SEMANAL")
    print("------------")

    if not result["menu"]:
        print(
            "No se encontraron recetas."
        )

    for row in result[
        "menu"
    ]:
        print(
            f"{row['dia']:10} -> "
            f"{row['nombre']} "
            f"(id={row['id']})"
        )

    cart = result[
        "carrito"
    ]

    print("")
    print("CARRITO")
    print("-------")

    print(
        "Costo estimado:",
        f"${cart['costo_total']:.2f} MXN",
    )

    print(
        "Dentro del presupuesto:",
        (
            "Sí"
            if cart[
                "dentro_de_presupuesto"
            ]
            else "No"
        ),
    )

    print(
        "Ingredientes agregados:",
        len(
            cart[
                "items"
            ]
        ),
    )

    print("")
    print("COMPARACIÓN DE SUPERMERCADOS")
    print("----------------------------")

    comparison = result[
        "comparacion_primera_receta"
    ]

    if comparison is None:
        print(
            "No disponible."
        )

    else:
        print(
            "Receta:",
            comparison[
                "nombre_receta"
            ],
        )

        for item in comparison[
            "comparacion"
        ]:
            print(
                f"{item['cadena']:10} "
                f"${item['precio_total_mxn']:.2f}"
            )

        print("")
        print(
            "Más barato:",
            comparison[
                "cadena_mas_barata"
            ],
            f"${comparison['precio_mas_barato_mxn']:.2f}",
        )

        print(
            "Ahorro máximo:",
            f"${comparison['ahorro_mxn']:.2f} MXN",
        )

    print("")
    print("MENSAJE DEL BACKEND")
    print("-------------------")

    print(
        result[
            "mensaje"
        ]
    )

    print("")
    print(
        "========================================"
    )
    print(
        "             DEMO COMPLETA"
    )
    print(
        "========================================"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Demo end-to-end del backend ARMU"
        )
    )

    parser.add_argument(
        "--gustos",
        default="chicken vegetables",
    )

    parser.add_argument(
        "--presupuesto",
        type=float,
        default=1200,
    )

    parser.add_argument(
        "--personas",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--cadena",
        default="Walmart",
    )

    parser.add_argument(
        "--restriccion",
        action="append",
        default=[],
        help=(
            "Puede repetirse. Ejemplo: "
            "--restriccion vegetariano"
        ),
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime la demo como JSON.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    result = run_demo(
        gustos=args.gustos,
        presupuesto=args.presupuesto,
        personas=args.personas,
        cadena=args.cadena,
        restricciones=args.restriccion,
    )

    if args.json:
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

    else:
        print_demo(
            result
        )


if __name__ == "__main__":
    main()
