from pathlib import Path

import pandas as pd

from api.schemas import RecommendationRequest
from api.services.recommendation import (
    load_recipe_prices,
    recommend,
)


REPORT_PATH = Path("reports/cost_audit.txt")

CHAINS = [
    "Walmart",
    "Soriana",
    "Chedraui",
]


def money(value: float) -> str:
    return f"${value:,.2f} MXN"


def audit_dataset(df: pd.DataFrame) -> list[str]:
    lines = []

    lines.append("========================================")
    lines.append("AUDITORÍA DE COSTOS ARMU")
    lines.append("========================================")
    lines.append("")

    lines.append("1. DATASET")
    lines.append("----------------------------------------")
    lines.append(f"Filas: {len(df):,}")
    lines.append(
        f"Recetas únicas: {df['id_receta'].nunique():,}"
    )
    lines.append("")

    recipe_prices = (
        df[
            [
                "id_receta",
                "nombre_receta",
                "cadena",
                "precio_total_receta_mxn",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    for chain in CHAINS:
        chain_df = recipe_prices[
            recipe_prices["cadena"].eq(chain)
        ].copy()

        prices = chain_df[
            "precio_total_receta_mxn"
        ].astype(float)

        lines.append(f"2. PRECIOS — {chain}")
        lines.append("----------------------------------------")
        lines.append(
            f"Recetas: {len(chain_df):,}"
        )
        lines.append(
            f"Mínimo: {money(prices.min())}"
        )
        lines.append(
            f"Mediana: {money(prices.median())}"
        )
        lines.append(
            f"Promedio: {money(prices.mean())}"
        )
        lines.append(
            f"Máximo: {money(prices.max())}"
        )

        low = chain_df[
            chain_df[
                "precio_total_receta_mxn"
            ] < 10
        ].sort_values(
            "precio_total_receta_mxn"
        )

        lines.append(
            f"Recetas debajo de $10: {len(low)}"
        )

        if not low.empty:
            lines.append("")
            lines.append(
                "10 recetas más baratas:"
            )

            for row in low.head(10).itertuples():
                lines.append(
                    f"- {row.nombre_receta} "
                    f"(id={row.id_receta}): "
                    f"{money(row.precio_total_receta_mxn)}"
                )

        lines.append("")

    return lines


def audit_consistency(df: pd.DataFrame) -> list[str]:
    lines = []

    lines.append("3. CONSISTENCIA INGREDIENTES VS TOTAL")
    lines.append("----------------------------------------")

    grouped = (
        df.groupby(
            [
                "id_receta",
                "nombre_receta",
                "cadena",
            ],
            as_index=False,
        )
        .agg(
            suma_ingredientes=(
                "costo_ingrediente_mxn",
                "sum",
            ),
            precio_total=(
                "precio_total_receta_mxn",
                "first",
            ),
        )
    )

    grouped["diferencia"] = (
        grouped["suma_ingredientes"]
        - grouped["precio_total"]
    ).abs()

    mismatches = grouped[
        grouped["diferencia"] > 0.10
    ].copy()

    lines.append(
        f"Combinaciones receta/cadena: "
        f"{len(grouped):,}"
    )

    lines.append(
        f"Diferencias mayores a $0.10: "
        f"{len(mismatches):,}"
    )

    if not mismatches.empty:
        lines.append("")
        lines.append(
            "Ejemplos con diferencias:"
        )

        for row in (
            mismatches
            .sort_values(
                "diferencia",
                ascending=False,
            )
            .head(10)
            .itertuples()
        ):
            lines.append(
                f"- {row.nombre_receta} / {row.cadena}: "
                f"ingredientes={money(row.suma_ingredientes)}, "
                f"total={money(row.precio_total)}, "
                f"diferencia={money(row.diferencia)}"
            )

    lines.append("")

    return lines


def audit_recommender() -> list[str]:
    lines = []

    lines.append("4. MENÚ GENERADO POR ARMU")
    lines.append("----------------------------------------")

    for chain in CHAINS:
        lines.append("")
        lines.append(f"CADENA: {chain}")

        for personas in [
            1,
            2,
            4,
            6,
        ]:
            response = recommend(
                RecommendationRequest(
                    gustos="",
                    presupuesto=None,
                    personas=personas,
                    cadena=chain,
                )
            )

            recipes = []

            for day, day_recipes in (
                response.menu_semanal.items()
            ):
                for recipe in day_recipes:
                    recipes.append(
                        (
                            day,
                            recipe.id,
                            recipe.name,
                        )
                    )

            lines.append("")
            lines.append(
                f"{personas} persona(s): "
                f"{money(response.carrito_final.costo_total)}"
            )

            for day, recipe_id, name in recipes:
                lines.append(
                    f"  - {day}: "
                    f"{name} "
                    f"(id={recipe_id})"
                )

    lines.append("")

    return lines


def audit_selected_recipe_costs(
    df: pd.DataFrame,
) -> list[str]:
    lines = []

    lines.append("5. DETALLE DEL MENÚ BASE DE WALMART")
    lines.append("----------------------------------------")

    response = recommend(
        RecommendationRequest(
            gustos="",
            presupuesto=None,
            personas=2,
            cadena="Walmart",
        )
    )

    selected_ids = []

    for day_recipes in (
        response.menu_semanal.values()
    ):
        for recipe in day_recipes:
            selected_ids.append(recipe.id)

    recipe_totals = (
        df[
            df["cadena"].eq("Walmart")
            & df["id_receta"].isin(
                selected_ids
            )
        ][
            [
                "id_receta",
                "nombre_receta",
                "precio_total_receta_mxn",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "precio_total_receta_mxn"
        )
    )

    calculated_total = float(
        recipe_totals[
            "precio_total_receta_mxn"
        ].sum()
    )

    for row in recipe_totals.itertuples():
        lines.append(
            f"- {row.nombre_receta} "
            f"(id={row.id_receta}): "
            f"{money(row.precio_total_receta_mxn)}"
        )

    lines.append("")
    lines.append(
        "Suma de precios de recetas: "
        + money(calculated_total)
    )

    lines.append(
        "Carrito reportado por API: "
        + money(
            response.carrito_final.costo_total
        )
    )

    difference = abs(
        calculated_total
        - response.carrito_final.costo_total
    )

    lines.append(
        "Diferencia: "
        + money(difference)
    )

    lines.append("")

    return lines


def main():
    df = load_recipe_prices()

    sections = []

    sections.extend(
        audit_dataset(df)
    )

    sections.extend(
        audit_consistency(df)
    )

    sections.extend(
        audit_recommender()
    )

    sections.extend(
        audit_selected_recipe_costs(df)
    )

    sections.append("6. INTERPRETACIÓN")
    sections.append("----------------------------------------")
    sections.append(
        "Este reporte no corrige precios automáticamente."
    )
    sections.append(
        "Su objetivo es detectar si los valores bajos "
        "provienen del dataset o de la lógica del recomendador."
    )
    sections.append("")
    sections.append(
        "Si la suma de ingredientes coincide con "
        "precio_total_receta_mxn, la API está respetando "
        "los costos almacenados."
    )
    sections.append("")
    sections.append(
        "Si los costos siguen siendo demasiado bajos, "
        "la siguiente revisión debe hacerse en las "
        "conversiones de cantidades y precios que generaron "
        "el dataset final."
    )

    report = "\n".join(sections)

    REPORT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print(report)
    print("")
    print(
        f"✅ reporte guardado en {REPORT_PATH}"
    )


if __name__ == "__main__":
    main()
