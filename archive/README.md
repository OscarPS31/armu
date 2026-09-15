# Archivo (código no usado por la app)

Esta carpeta guarda trabajo previo del proyecto que **no se usa en la app actual**
(`app.py`). Se conserva como referencia y por si alguien quiere retomarlo.

La app en producción solo usa: `app.py`, `armu/planner.py`, `armu/recommender.py`,
`data/recipes_priced.parquet` y `scripts/build_demo_dataset.py`.

Contenido de este archivo:

- `armu_legacy/` — versión anterior del backend (matching de ingredientes,
  precios y carrito por cadena): `pricing.py`, `pipeline.py`, `ingredient_matching.py`.
- `api/` — intento de API con FastAPI (no conectado a la app).
- `scripts/` — scripts de limpieza y construcción de datos de etapas anteriores.
- `data/` — datasets intermedios/antiguos (precios PROFECO, ingredientes, etc.).
- `notebooks/` — notebooks y scripts de exploración del equipo.
- `docs/` — reportes generados durante la exploración.
- `misc/` — `frente_c.py`, `ROADMAP_NUTRIPLAN.txt` y CSVs sueltos.
