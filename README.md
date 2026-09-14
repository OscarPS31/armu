# 🥗 Armu

App de nutrición personalizada con optimización de presupuesto de supermercado. Proyecto final del bootcamp de Data Science & IA de Le Wagon.

## 🎯 Problema

Planear un menú semanal que se ajuste a los gustos, restricciones alimentarias y objetivos de salud de una persona —y que además no se pase del presupuesto disponible para el súper— es un proceso manual y tedioso.

## 💡 Solución

Armu genera un menú semanal personalizado según las preferencias del usuario (restricciones alimentarias, objetivo, tiempo disponible para cocinar) y arma automáticamente el carrito de supermercado optimizado para no exceder el presupuesto indicado.

## 🧩 Cómo funciona

1. El usuario ingresa sus preferencias: restricciones (vegano, vegetariano, sin gluten, sin lácteos, sin nueces, etc.), tiempo disponible y presupuesto semanal.
2. El sistema filtra y recomienda recetas que cumplen esas condiciones.
3. Se arma un carrito de compras optimizado según el presupuesto disponible.
4. El usuario ve su menú semanal + lista de compras en una interfaz simple.

## 📊 Datos

- **Recetas**: dataset de [Food.com](https://www.kaggle.com/datasets/realalexanderwei/food-com-recipes-with-ingredients-and-tags) (~500,436 recetas con ingredientes, pasos, tags de dieta y tiempo de preparación).
- **Precios de supermercado**: [Quién es Quién en los Precios (PROFECO)](https://datos.profeco.gob.mx/datos_abiertos/qqp.php).

## 🛠️ Stack técnico

- Python (pandas, numpy, scikit-learn)
- Jupyter / JupyterLab para exploración
- _(front-end / demo: por definir — ej. Streamlit)_

## 🚀 Setup local

```bash
git clone git@github.com:OscarPS31/armu.git
cd armu
pyenv virtualenv 3.10.6 armu
pyenv local armu
pip install --upgrade pip
pip install -r requirements.txt
```

## ▶️ Correr el demo

```bash
streamlit run app.py
```

El demo funciona de punta a punta sobre `data/demo_recipes.parquet` y
`data/demo_ingredient_costs.parquet` (ya incluidos en el repo). El usuario
ingresa preferencias, restricciones, tiempo y presupuesto, y la app devuelve:

1. Un **menú semanal** personalizado.
2. El **costo de cada receta** y el **carrito total** vs. el presupuesto.
3. La **lista de compras** con el producto PROFECO y el costo por ingrediente.
4. La **comparación de precio** entre Walmart, Soriana y Chedraui.

Los datasets de demo se regeneran (requiere `raw_data/`, no versionado) con:

```bash
python scripts/build_demo_dataset.py
```

## 🧱 Cómo está armado

- `app.py` — interfaz Streamlit (demo).
- `armu/planner.py` — orquesta menú + carrito + presupuesto por cadena.
- `armu/recommender.py` — filtros por dieta/tiempo y ranking por preferencia (TF-IDF).
- `scripts/build_demo_dataset.py` — construye los datasets de demo.

El demo se apoya en **889 recetas con costo completo** (cantidad convertida a
gramos, ingrediente homologado y precio proporcional real de PROFECO en 3
cadenas), producto del pipeline de limpieza y matching del equipo.

## 🔭 Trabajo futuro (para quien quiera mejorar la app)

El MVP se cierra a propósito con un alcance acotado. Pendientes conocidos:

- **Ampliar el catálogo PROFECO**: hoy son ~75 productos de comida, lo que
  limita cuántas recetas quedan 100% cubiertas (889 de ~500k). Ampliar el
  catálogo desde el PROFECO crudo subiría la cobertura.
- **Más recetas**: al crecer el catálogo, relajar el filtro de "receta
  completamente costeable" para ofrecer más variedad.
- **Optimización de presupuesto**: hoy se seleccionan por preferencia y se
  reporta el costo; un siguiente paso es elegir el menú optimizando dentro
  del presupuesto desde el inicio.
- **Limpieza de nombres de receta**: filtrar artefactos del dataset de
  Food.com que no son comidas (ej. papillas, suplementos).

## 📁 Estructura del proyecto
