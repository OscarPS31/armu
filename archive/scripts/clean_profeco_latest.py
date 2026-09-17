import pandas as pd
import unicodedata


# ============================================================
# CONFIG
# ============================================================

INPUT_PATH = "data/QQP_2026/07-2026_Q2.csv"

OUTPUT_PATH = "data/profeco_clean.csv"


# ============================================================
# HELPERS
# ============================================================

def normalize_text(value):
    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    return " ".join(
        value.split()
    )


# ============================================================
# LOAD
# ============================================================

print("Loading PROFECO...")

df = pd.read_csv(
    INPUT_PATH,
    usecols=[
        "producto",
        "categoria",
        "precio",
        "presentacion",
        "cadena_comercial",
        "fecha_registro",
    ],
)

print(
    f"Original rows: {len(df):,}"
)


# ============================================================
# CLEAN PRICE
# ============================================================

df["precio"] = pd.to_numeric(
    df["precio"],
    errors="coerce",
)

before_price = len(df)

df = df[
    df["precio"].notna()
    &
    (df["precio"] > 0)
].copy()

print(
    "Removed null/zero prices:",
    f"{before_price - len(df):,}"
)


# ============================================================
# NORMALIZE PRODUCT
# ============================================================

df["producto_normalizado"] = (
    df["producto"]
    .apply(normalize_text)
)


# ============================================================
# REMOVE EMPTY PRODUCTS
# ============================================================

df = df[
    df["producto_normalizado"] != ""
].copy()


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before_duplicates = len(df)

df = df.drop_duplicates(
    subset=[
        "producto_normalizado",
        "precio",
        "presentacion",
        "cadena_comercial",
        "fecha_registro",
    ]
).copy()

print(
    "Duplicates removed:",
    f"{before_duplicates - len(df):,}"
)


# ============================================================
# DATE
# ============================================================

df["fecha_registro"] = pd.to_datetime(
    df["fecha_registro"],
    errors="coerce",
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 60)

print(
    "PROFECO CLEAN REPORT"
)

print("=" * 60)

print(
    f"Final rows: {len(df):,}"
)

print(
    f"Unique products: "
    f"{df['producto_normalizado'].nunique():,}"
)

print(
    f"Min price: "
    f"${df['precio'].min():.2f}"
)

print(
    f"Max price: "
    f"${df['precio'].max():.2f}"
)

print(
    f"Latest date: "
    f"{df['fecha_registro'].max()}"
)

print(
    f"Saved to: {OUTPUT_PATH}"
)

print(
    "\n=== SAMPLE ==="
)

print(
    df.head(10)
    .to_string(index=False)
)
