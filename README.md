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

- **Recetas**: dataset de [Food.com](https://www.kaggle.com/datasets/realalexanderwei/food-com-recipes-with-ingredients-and-tags) (~20,500 recetas con ingredientes, pasos, tags de dieta y tiempo de preparación).
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

## 📁 Estructura del proyecto
