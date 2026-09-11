from pathlib import Path

import pandas as pd


INPUT_PATH = Path(
    "data/recipe_ingredients_quantities.csv"
)

OUTPUT_PATH = Path(
    "data/recipe_ingredients_quantities_clean.csv"
)


print("Loading parsed recipe quantities...")

df = pd.read_csv(
    INPUT_PATH,
    low_memory=False,
)


clean = df[
    [
        "recipe_id",
        "ingredient",
        "ingredient_raw",
        "quantity_estimate",
        "normalized_quantity",
        "normalized_unit",
        "conversion_type",
        "confidence",
    ]
].copy()


clean = clean.rename(
    columns={
        "recipe_id": "id_receta",
        "ingredient": "ingrediente",
        "ingredient_raw": "ingrediente_original",
        "quantity_estimate": "cantidad_original",
        "normalized_quantity": "cantidad_normalizada",
        "normalized_unit": "unidad_normalizada",
        "conversion_type": "tipo_conversion",
        "confidence": "confianza",
    }
)


# ============================================================
# UNIDADES
# ============================================================

unit_map = {
    "gramo": "gramo",
    "mililitro": "mililitro",
    "pieza": "pieza",
    "piece": "pieza",
    "cup": "taza",
    "tablespoon": "cucharada",
    "teaspoon": "cucharadita",
    "slice": "rebanada",
    "bunch": "manojo",
    "head": "pieza",
    "clove": "diente",
    "stalk": "tallo",
    "can": "lata",
    "package": "paquete",
    "pinch": "pizca",
    "dash": "toque",
    "glug": "chorrito",
}

clean["unidad_normalizada"] = (
    clean["unidad_normalizada"]
    .replace(unit_map)
)


# ============================================================
# TIPO DE CONVERSION
# ============================================================

conversion_map = {
    "mass_exact": "exacto_masa",
    "volume_exact": "exacto_volumen",
    "implicit_count": "conteo_aproximado",
    "count": "conteo_explicito",
    "volume_needs_ingredient_density": (
        "volumen_sin_conversion_a_gramos"
    ),
    "subjective": "subjetivo",
    "to_taste": "al_gusto",
    "unparsed": "sin_parsear",
}

clean["tipo_conversion"] = (
    clean["tipo_conversion"]
    .replace(conversion_map)
)


# ============================================================
# CONFIANZA
# ============================================================

confidence_map = {
    "high": "alta",
    "medium": "media",
    "low": "baja",
}

clean["confianza"] = (
    clean["confianza"]
    .replace(confidence_map)
)


# ============================================================
# LIMPIEZA
# ============================================================

clean["ingrediente"] = (
    clean["ingrediente"]
    .fillna("")
    .astype(str)
    .str.strip()
)

clean["ingrediente_original"] = (
    clean["ingrediente_original"]
    .fillna("")
    .astype(str)
    .str.strip()
)

clean["cantidad_original"] = pd.to_numeric(
    clean["cantidad_original"],
    errors="coerce",
).round(4)

clean["cantidad_normalizada"] = pd.to_numeric(
    clean["cantidad_normalizada"],
    errors="coerce",
).round(4)


before = len(clean)

clean = (
    clean
    .drop_duplicates()
    .reset_index(drop=True)
)

removed = before - len(clean)


# ============================================================
# SAVE
# ============================================================

clean.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


print("\n" + "=" * 90)
print("RECETAS - CANTIDADES HOMOLOGADAS")
print("=" * 90)

print(f"\nFilas: {len(clean):,}")
print(f"Duplicados eliminados: {removed:,}")

print("\n=== TIPOS DE CONVERSION ===")

print(
    clean["tipo_conversion"]
    .value_counts(dropna=False)
    .to_string()
)

print("\n=== CONFIANZA ===")

print(
    clean["confianza"]
    .value_counts(dropna=False)
    .to_string()
)

print("\n=== EJEMPLO ===")

print(
    clean[
        [
            "id_receta",
            "ingrediente",
            "ingrediente_original",
            "cantidad_original",
            "cantidad_normalizada",
            "unidad_normalizada",
            "tipo_conversion",
            "confianza",
        ]
    ]
    .head(25)
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_PATH)
