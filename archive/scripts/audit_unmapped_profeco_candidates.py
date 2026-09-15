import re
import unicodedata
from pathlib import Path

import pandas as pd


MAPPING_PATH = Path("data/ingredient_mapping_all.csv")
PROFECO_PATH = Path("data/profeco_food.csv")
OUTPUT_PATH = Path("data/unmapped_profeco_candidates.csv")


def normalize_text(value: str) -> str:
    value = str(value).lower().strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


TRANSLATIONS = {
    "salmon": ["salmon"],
    "tuna": ["atun"],
    "asparagus": ["esparrago", "esparragos"],
    "eggplant": ["berenjena"],
    "kidney beans": ["frijol"],
    "black beans": ["frijol"],
    "pinto beans": ["frijol"],
    "white beans": ["frijol"],
    "green beans": ["ejote", "ejotes"],
    "peas": ["chicharo", "chicharos"],
    "spinach": ["espinaca"],
    "lettuce": ["lechuga"],
    "cauliflower": ["coliflor"],
    "broccoli": ["brocoli"],
    "cabbage": ["col", "repollo"],
    "cucumber": ["pepino"],
    "radish": ["rabano", "rabanos"],
    "beet": ["betabel"],
    "beets": ["betabel"],
    "turnip": ["nabo"],
    "sweet potato": ["camote"],
    "yam": ["camote"],
    "corn": ["maiz"],
    "shrimp": ["camaron"],
    "crab": ["jaiba", "cangrejo"],
    "crabmeat": ["jaiba", "cangrejo"],
    "clam": ["almeja"],
    "clams": ["almeja"],
    "oyster": ["ostion"],
    "oysters": ["ostion"],
    "squid": ["calamar"],
    "octopus": ["pulpo"],
    "trout": ["trucha"],
    "cod": ["bacalao"],
    "sardine": ["sardina"],
    "sardines": ["sardina"],
    "anchovy": ["anchoveta", "anchoa"],
    "anchovies": ["anchoveta", "anchoa"],
    "pork": ["carne cerdo"],
    "ground pork": ["carne cerdo"],
    "pork chops": ["carne cerdo"],
    "pork tenderloin": ["carne cerdo"],
    "ham": ["jamon"],
    "turkey": ["pavo"],
    "ground turkey": ["pavo"],
    "lamb": ["carne borrego", "cordero"],
    "duck": ["pato"],
    "mozzarella": ["queso mozzarella"],
    "mozzarella cheese": ["queso mozzarella"],
    "cottage cheese": ["queso cottage"],
    "ricotta": ["queso ricotta"],
    "feta": ["queso feta"],
    "blue cheese": ["queso azul"],
    "swiss cheese": ["queso suizo"],
    "cheddar cheese": ["queso cheddar"],
    "parmesan cheese": ["queso parmesano"],
    "goat cheese": ["queso cabra"],
    "cream cheese": ["queso crema"],
}


print("Loading mapping...")

mapping = pd.read_csv(MAPPING_PATH)

required_mapping_columns = {
    "ingredient",
    "occurrences",
    "canonical_ingredient",
    "profeco_category",
    "has_profeco_price",
}

missing_mapping = required_mapping_columns - set(mapping.columns)

if missing_mapping:
    raise ValueError(
        f"Missing mapping columns: {sorted(missing_mapping)}"
    )


unmapped = mapping[
    mapping["has_profeco_price"] == False
].copy()

print(f"Unmapped ingredient strings: {len(unmapped):,}")
print(
    "Unmapped occurrences:",
    f"{unmapped['occurrences'].sum():,}",
)


print("\nLoading PROFECO food dataset...")

profeco = pd.read_csv(PROFECO_PATH)

required_profeco_columns = {
    "producto",
    "categoria",
}

missing_profeco = required_profeco_columns - set(profeco.columns)

if missing_profeco:
    raise ValueError(
        f"Missing PROFECO columns: {sorted(missing_profeco)}"
    )


profeco = (
    profeco[
        [
            "producto",
            "categoria",
        ]
    ]
    .dropna()
    .drop_duplicates()
    .copy()
)

profeco["producto_norm"] = (
    profeco["producto"]
    .map(normalize_text)
)

profeco["categoria_norm"] = (
    profeco["categoria"]
    .map(normalize_text)
)


records = []


for _, row in unmapped.iterrows():

    ingredient = str(
        row["ingredient"]
    ).strip()

    ingredient_norm = normalize_text(
        ingredient
    )

    occurrences = int(
        row["occurrences"]
    )

    matches_found = []


    for english_key, spanish_terms in TRANSLATIONS.items():

        english_norm = normalize_text(
            english_key
        )

        if not re.search(
            rf"\b{re.escape(english_norm)}\b",
            ingredient_norm,
        ):
            continue


        for spanish_term in spanish_terms:

            spanish_norm = normalize_text(
                spanish_term
            )

            candidate_matches = profeco[
                profeco["producto_norm"].str.contains(
                    rf"\b{re.escape(spanish_norm)}\b",
                    regex=True,
                    na=False,
                )
            ]

            if candidate_matches.empty:
                continue


            for _, candidate in candidate_matches.iterrows():

                producto = candidate["producto"]
                categoria = candidate["categoria"]

                confidence = "review"

                if english_key in {
                    "salmon",
                    "tuna",
                    "asparagus",
                    "eggplant",
                    "spinach",
                    "lettuce",
                    "cauliflower",
                    "broccoli",
                    "cucumber",
                    "shrimp",
                    "crab",
                    "crabmeat",
                    "clam",
                    "clams",
                    "oyster",
                    "oysters",
                    "squid",
                    "octopus",
                    "trout",
                    "cod",
                    "sardine",
                    "sardines",
                }:
                    confidence = "high"

                if english_key in {
                    "kidney beans",
                    "black beans",
                    "pinto beans",
                    "white beans",
                    "green beans",
                    "peas",
                    "pork",
                    "ground pork",
                    "pork chops",
                    "pork tenderloin",
                    "turkey",
                    "lamb",
                    "duck",
                }:
                    confidence = "review"


                matches_found.append(
                    {
                        "ingredient": ingredient,
                        "occurrences": occurrences,
                        "matched_keyword": english_key,
                        "possible_profeco_product": producto,
                        "profeco_category": categoria,
                        "confidence": confidence,
                    }
                )


    records.extend(matches_found)


result = pd.DataFrame(records)


if result.empty:
    print("\nNo candidates found.")
    raise SystemExit(0)


result = (
    result
    .drop_duplicates()
    .sort_values(
        [
            "occurrences",
            "ingredient",
            "possible_profeco_product",
        ],
        ascending=[
            False,
            True,
            True,
        ],
    )
    .reset_index(drop=True)
)


result.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)


print("\n" + "=" * 80)
print("UNMAPPED PROFECO CANDIDATES")
print("=" * 80)

print(
    "\nCandidate rows:",
    f"{len(result):,}",
)

print(
    "Unique recipe ingredients:",
    f"{result['ingredient'].nunique():,}",
)

print(
    "Recoverable occurrences represented:",
    f"{result.drop_duplicates('ingredient')['occurrences'].sum():,}",
)


print("\n=== HIGH CONFIDENCE ===")

high = result[
    result["confidence"] == "high"
]

if high.empty:
    print("None")
else:
    print(
        high.head(100)
        .to_string(index=False)
    )


print("\n=== REVIEW ===")

review = result[
    result["confidence"] == "review"
]

if review.empty:
    print("None")
else:
    print(
        review.head(100)
        .to_string(index=False)
    )


print("\n=== TOP INGREDIENTS TO RECOVER ===")

summary = (
    result
    .groupby(
        [
            "ingredient",
            "confidence",
        ],
        as_index=False,
    )
    .agg(
        occurrences=(
            "occurrences",
            "max",
        ),
        possible_products=(
            "possible_profeco_product",
            "nunique",
        ),
    )
    .sort_values(
        "occurrences",
        ascending=False,
    )
)

print(
    summary.head(50)
    .to_string(index=False)
)


print("\nSaved:")
print(OUTPUT_PATH)
