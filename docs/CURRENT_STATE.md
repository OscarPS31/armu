# CURRENT STATE

## ✅ YA ESTÁ HECHO

- Recomendador real conectado a datos reales
- 889 recetas completas
- 8,394 filas en dataset final
- Walmart
- Soriana
- Chedraui
- Ranking de recetas con TF-IDF
- Presupuesto
- Carrito con cantidades y costos
- Comparador de precios por receta
- Cadena más barata
- Cálculo de ahorro
- Escalado por número de personas
- 13 tests pasando
- Endpoint POST /recomendacion
- Endpoint GET /comparar-precios/{id_receta}

## 🚧 ESTAMOS TRABAJANDO EN

- Auditoría de costos del menú
- Verificar que los costos bajos sean correctos
- Mejorar claridad del flujo para frontend

## ⏳ FALTA

- Restricciones alimentarias
- Tiempo máximo de preparación
- Mejorar diversidad del menú
- Integración final con frontend
- Demo final completa

## ⛔ NO VOLVER A HACER

No crear otra implementación paralela de:

- matching de ingredientes
- pipeline de precios
- recomendador
- comparador de supermercados
- dataset final equivalente
- carrito calculado desde frontend

Antes de crear algo nuevo, revisar primero si ya existe.

## 📍 DÓNDE ESTÁ CADA COSA

### Recomendador

api/services/recommendation.py

### Comparador de precios

api/services/price_comparison.py

### Endpoints

api/routers/recipes.py

### Schemas

api/schemas.py

### Dataset final

data/recipe_prices_complete_3chains.csv

### Tests

tests/test_real_recommendation.py
tests/test_price_comparison.py
tests/test_people_scaling.py

### Documentación técnica

docs/RECOMMENDATION_PIPELINE.md

## 🧪 CÓMO VERIFICAR QUE TODO SIGUE FUNCIONANDO

Ejecutar:

PYTHONPATH=. python -m pytest -q \
tests/test_real_recommendation.py \
tests/test_price_comparison.py \
tests/test_people_scaling.py

Resultado esperado:

13 passed

## REGLA DEL EQUIPO

Antes de modificar algo:

1. Revisar CURRENT_STATE.md
2. Revisar RECOMMENDATION_PIPELINE.md
3. Leer el archivo que ya implementa esa función
4. Correr los tests
5. Modificar lo existente
6. No duplicar lógica
