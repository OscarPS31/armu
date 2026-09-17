import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INPUT_PATH = "data/profeco_clean.csv"
OUTPUT_PATH = "data/profeco_food.csv"


# ============================================================
# CATEGORÍAS IRRELEVANTES PARA RECETAS / INGREDIENTES
# ============================================================

EXCLUDED_CATEGORIES = {
    "Material Escolar",
    "Medicamentos",
    "Arts. para el Cuidado Personal",
    "Aparatos Eléctricos",
    "Detergentes y Productos Similares",
    "Accesorios Domésticos",
    "Aparatos Electrónicos",
    "Arts. de Esparcimiento (Juguetes)",
    "Arts. de Papel P/higiene Personal",
    "Artículos Deportivos",
    "Cigarrillos",
    "Utensilios Domésticos",
}


# ============================================================
# LOAD DATA
# ============================================================

print("Loading cleaned PROFECO dataset...")

df = pd.read_csv(
    INPUT_PATH
)

print(
    f"Rows before filtering: {len(df):,}"
)

print(
    f"Categories before filtering: "
    f"{df['categoria'].nunique():,}"
)


# ============================================================
# FILTER CATEGORIES
# ============================================================

filtered = df[
    ~df["categoria"].isin(
        EXCLUDED_CATEGORIES
    )
].copy()


# ============================================================
# REPORT REMOVED DATA
# ============================================================

removed = df[
    df["categoria"].isin(
        EXCLUDED_CATEGORIES
    )
].copy()


print(
    f"\nRows after filtering: {len(filtered):,}"
)

print(
    f"Rows removed: {len(removed):,}"
)

print(
    f"Categories after filtering: "
    f"{filtered['categoria'].nunique():,}"
)


print(
    "\n=== REMOVED CATEGORIES ==="
)

removed_summary = (
    removed["categoria"]
    .value_counts()
)

if removed_summary.empty:
    print("None")
else:
    print(
        removed_summary.to_string()
    )


# ============================================================
# VALIDATION
# ============================================================

print(
    "\n=== VALIDATION ==="
)

for category in sorted(
    EXCLUDED_CATEGORIES
):
    exists = (
        filtered["categoria"]
        == category
    ).any()

    print(
        f"{category}: {exists}"
    )


# ============================================================
# REMAINING CATEGORIES
# ============================================================

print(
    "\n=== REMAINING CATEGORIES ==="
)

remaining_categories = sorted(
    filtered[
        "categoria"
    ]
    .dropna()
    .unique()
)

for category in remaining_categories:
    print(
        category
    )


# ============================================================
# SAVE
# ============================================================

filtered.to_csv(
    OUTPUT_PATH,
    index=False
)


print(
    "\nSaved:"
)

print(
    OUTPUT_PATH
)
