# Recommendation Pipeline

## Estado actual

La integración de recomendaciones reales ya está implementada y validada.

El endpoint:

POST /recomendacion

ya usa datos reales del proyecto.

## Flujo actual

Usuario
→ gustos + presupuesto + cadena
→ POST /recomendacion
→ api/services/recommendation.py
→ data/recipe_prices_complete_3chains.csv
→ ranking con TF-IDF
→ selección de hasta 7 recetas
→ cálculo de ingredientes
→ cálculo de costos
→ menú semanal + carrito + costo total

## Dataset principal

Archivo:

data/recipe_prices_complete_3chains.csv

Estado validado:

- 889 recetas
- 8,394 filas
- Walmart
- Soriana
- Chedraui

Este dataset contiene únicamente recetas completas para las 3 cadenas.

## Archivos importantes

### API

api/main.py
Inicializa FastAPI y registra el router.

api/routers/recipes.py
Expone POST /recomendacion.

api/schemas.py
Define los modelos de request y response.

### Motor de recomendación

api/services/recommendation.py

Responsabilidades:

- cargar el dataset final
- filtrar por cadena
- crear catálogo de recetas
- rankear por preferencias con TF-IDF
- respetar presupuesto
- seleccionar hasta 7 recetas
- construir menú semanal
- agregar ingredientes
- calcular carrito
- calcular costo total

### Tests

tests/test_real_recommendation.py

Ejecutar:

PYTHONPATH=. python -m pytest -q tests/test_real_recommendation.py

Estado validado:

4 passed

## IMPORTANTE: NO REHACER

Esta parte ya existe y funciona.

No volver a crear:

- matching de ingredientes desde cero
- sistema paralelo de precios
- otro CSV equivalente sin una razón técnica clara
- otro recomendador separado
- otro endpoint para resolver lo mismo
- lógica de precios dentro del frontend
- lógica de recomendación dentro de Streamlit

No volver a usar FAKE_MENU ni FAKE_CART para el flujo real de /recomendacion.

## Si necesitas modificar recomendaciones

Trabaja sobre:

api/services/recommendation.py

Antes y después de modificarlo, correr:

PYTHONPATH=. python -m pytest -q tests/test_real_recommendation.py

Los tests deben seguir pasando.

## Si trabajas en frontend

El frontend debe consumir POST /recomendacion.

No debe recalcular recomendaciones ni precios.

## Si trabajas en precios

El dataset final es:

data/recipe_prices_complete_3chains.csv

Scripts relacionados:

scripts/build_recipe_prices_kg_liter.py
scripts/build_complete_recipe_prices.py

## Limitaciones actuales

- El ranking usa TF-IDF sobre nombre e ingredientes.
- El parámetro personas todavía no escala cantidades.
- Las restricciones alimentarias todavía no están conectadas.
- El costo corresponde a las cantidades usadas en las recetas.
- El dataset final incluye 889 recetas completas.

## Próximos pasos

1. Conectar restricciones alimentarias.
2. Conectar tiempo máximo de preparación.
3. Escalar cantidades según personas.
4. Mejorar diversidad del menú.
5. Añadir tests HTTP.
6. Integrar frontend con /recomendacion.

## Regla del equipo

Antes de crear una solución nueva:

1. Revisar si ya existe.
2. Leer este documento.
3. Revisar los archivos relacionados.
4. Correr los tests.
5. Modificar lo existente antes de duplicarlo.


## Comparador de precios por receta

También existe el endpoint:

GET /comparar-precios/{id_receta}

Este endpoint compara exactamente la misma receta entre:

- Walmart
- Soriana
- Chedraui

Devuelve:

- precio total por cadena
- cadena más barata
- cadena más cara
- ahorro posible

Ejemplo conceptual:

Chicken Pasta

Walmart: 132.40 MXN
Soriana: 145.80 MXN
Chedraui: 127.90 MXN

Más barata: Chedraui
Ahorro: 17.90 MXN

Implementación:

api/services/price_comparison.py

Tests:

tests/test_price_comparison.py

Importante:

No recalcular estos precios en frontend.
El frontend debe consumir el endpoint de comparación.
