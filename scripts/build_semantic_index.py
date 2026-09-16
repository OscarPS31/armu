from pathlib import Path

import numpy as np

from armu.planner import load_data
from armu.semantic_recommender import load_model


OUTPUT = Path("data/recipe_embeddings.npy")
IDS_OUTPUT = Path("data/recipe_embedding_ids.npy")


def main():
    recipes = load_data()

    texts = []

    for _, row in recipes.iterrows():
        ingredients = " ".join(map(str, row["ingredients"]))
        texts.append(
            f"{row['name']} {ingredients}".lower()
        )

    print(f"📚 Recetas: {len(recipes)}")
    print("🧠 Creando índice semántico...")

    model = load_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=64,
    )

    # float16 reduce aproximadamente a la mitad el tamaño.
    embeddings = np.asarray(
        embeddings,
        dtype=np.float16,
    )

    ids = recipes["id"].to_numpy(
        dtype=np.int64,
    )

    np.save(OUTPUT, embeddings)
    np.save(IDS_OUTPUT, ids)

    print("\n✅ Índice creado")
    print("Shape:", embeddings.shape)
    print("Embeddings:", OUTPUT)
    print("IDs:", IDS_OUTPUT)


if __name__ == "__main__":
    main()
