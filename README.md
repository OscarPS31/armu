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

El demo corre sobre `data/recipes_priced.parquet` (ya incluido en el repo). El
usuario escribe qué quiere comer, elige restricciones alimentarias y un
presupuesto por receta, y la app devuelve las **recetas que mejor le quedan
dentro de su presupuesto**, con su costo estimado, ingredientes y pasos.

Los datos se regeneran (requiere `raw_data/`, no versionado) con:

```bash
python scripts/build_demo_dataset.py
```

## 🧱 Cómo está armado

- `app.py` — interfaz Streamlit (demo).
- `armu/planner.py` — filtra por dieta y presupuesto, y rankea por preferencia (TF-IDF).
- `armu/recommender.py` — filtros por restricción/tiempo (utilidades base).
- `scripts/build_demo_dataset.py` — construye `data/recipes_priced.parquet`.

El demo se apoya en **~51,000 recetas con costo estimado de alta confianza**
(`recipes_with_estimated_cost.csv`, en MXN con precios de PROFECO), producto del
pipeline de limpieza, matching y estimación de costos del equipo.

## 🔭 Trabajo futuro (para quien quiera mejorar la app)

El MVP se cierra a propósito con un alcance acotado. Pendientes conocidos:

- **Carrito de súper por cadena**: sumar ingredientes de varias recetas y
  comparar el costo entre supermercados (Walmart, Soriana, Chedraui).
- **Menú semanal**: pasar de "recetas sueltas" a un plan de varios días con
  optimización de presupuesto.
- **Traducción al español** de ingredientes y pasos (hoy en inglés).
- **Más recetas**: incluir estimaciones de confianza media para ampliar el
  catálogo (hoy solo alta confianza).
- **Flags de dieta**: re-derivarlos desde los ingredientes; algunos vienen
  incompletos del dataset original.

## 📁 Estructura del proyecto
