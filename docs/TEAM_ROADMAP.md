# TEAM ROADMAP

## FASE 1 — DATOS ✅

Estado: COMPLETADO

Incluye:

- limpieza de ingredientes
- matching de ingredientes
- precios PROFECO
- normalización de cantidades
- precios por kg/litro
- dataset final de recetas completas
- 889 recetas comparables

No rehacer.

---

## FASE 2 — RECOMENDADOR REAL ✅

Estado: COMPLETADO

Incluye:

- POST /recomendacion
- uso de dataset real
- ranking con TF-IDF
- selección de recetas
- presupuesto
- carrito
- costo total

Archivo principal:

api/services/recommendation.py

---

## FASE 3 — COMPARACIÓN DE SUPERMERCADOS ✅

Estado: COMPLETADO

Incluye:

- GET /comparar-precios/{id_receta}
- Walmart
- Soriana
- Chedraui
- cadena más barata
- cadena más cara
- ahorro

Archivo principal:

api/services/price_comparison.py

---

## FASE 4 — NÚMERO DE PERSONAS ✅

Estado: COMPLETADO

Incluye:

- 1 a 20 personas
- escalado de cantidades
- escalado de costos
- escalado del carrito
- impacto sobre presupuesto

Regla actual MVP:

factor = personas / 2

---

## FASE 5 — AUDITORÍA DE COSTOS ✅

Estado: IMPLEMENTADA

Objetivo:

Revisar receta por receta:

- costo individual
- costo escalado
- ingredientes
- cantidades
- total semanal

Motivo:

Validar si los costos bajos provienen del dataset o de la lógica del recomendador.

Reporte:

reports/cost_audit.txt

---

## FASE 6 — RESTRICCIONES ALIMENTARIAS ✅

Estado: IMPLEMENTADA EN MVP

Incluye:

- vegetariano
- vegano
- sin gluten
- aliases español/inglés
- combinación de restricciones

Importante:

Son filtros heurísticos basados en nombres de ingredientes.
No representan certificación para alergias, celiaquía
o contaminación cruzada.

---

## FASE 7 — DIVERSIDAD Y CALIDAD DEL MENÚ ✅

Estado: IMPLEMENTADA EN MVP

Incluye:

- filtro básico de nombres no alimentarios
- exclusión de términos como bleach/cleaner
- selección neutral alrededor del precio mediano
- prevención de recetas demasiado similares
- control de solapamiento de ingredientes
- clasificación heurística de plato principal
- exclusión de recetas tipo substitute/replacement
- exclusión de condimentos y preparaciones auxiliares evidentes
- categorías de proteínas/comidas
- el nombre de la receta tiene prioridad sobre ingredientes para clasificar categoría
- máximo 2 recetas de una categoría en el menú por defecto
- limpieza automática de entidades HTML
- mantenimiento del ranking TF-IDF cuando hay gustos

Siguiente mejora futura:

- clasificación semántica más avanzada de recetas
- categorías desayuno/comida/cena
- diversidad nutricional

---

## FASE 8 — FRONTEND 🚧

Estado: PREPARADO PARA INTEGRACIÓN

Backend disponible:

- POST /recomendacion
- GET /comparar-precios/{id_receta}
- GET /opciones

GET /opciones devuelve:

- cadenas válidas
- restricciones válidas
- personas_min
- personas_max

El frontend debe consumir estas opciones
en vez de duplicarlas manualmente.


Pendiente:

El frontend debe consumir:

POST /recomendacion

GET /comparar-precios/{id_receta}

No recalcular precios ni recomendaciones en frontend.

---

## FASE 9 — DEMO FINAL ⏳

Objetivo:

Mostrar flujo completo:

Usuario
→ gustos
→ presupuesto
→ número de personas
→ supermercado
→ menú semanal
→ carrito
→ comparación de precios
→ ahorro

---

## ESTADO DE TESTS

Tests actuales:

13 passed

Archivos:

tests/test_real_recommendation.py
tests/test_price_comparison.py
tests/test_people_scaling.py

---

## REGLA PRINCIPAL

Si una función aparece como COMPLETADA:

NO REHACERLA.

Primero:

1. entenderla
2. probarla
3. modificarla si hace falta

Nunca crear una implementación paralela sin una razón técnica clara.


### Contrato frontend/backend

Backend preparado para integración MVP:

- GET /opciones
- POST /recomendacion
- GET /comparar-precios/{id_receta}
- documentación en docs/FRONTEND_INTEGRATION.md
- smoke test en tests/test_frontend_contract.py


### Calidad con preferencias

Cuando el usuario escribe gustos:

- TF-IDF sigue siendo la señal principal
- se limita repetición de categorías
- se evita repetir títulos casi iguales
- existe fallback para completar 7 días
- Baby Food no se considera plato semanal


### Demo MVP

Estado: LISTA

Archivos:

- scripts/demo_mvp.py
- docs/DEMO_GUIDE.md
- tests/test_demo_mvp.py

La demo ejecuta el flujo:

1. opciones
2. recomendación
3. carrito
4. comparación de supermercados


## CIERRE BACKEND MVP ✅

Estado: LISTO PARA PR / MERGE

Validado:

- recomendación semanal
- presupuesto
- número de personas
- Walmart / Soriana / Chedraui
- comparación de precios
- restricciones alimentarias MVP
- diversidad de menú
- contrato frontend/backend
- demo end-to-end
- suite completa de tests

No rehacer el pipeline de precios ni datasets
sin una razón técnica nueva.


## STREAMLIT INTEGRATION ✅

Estado: IMPLEMENTADO EN FEATURE BRANCH

Incluye:

- selector de supermercado
- presupuesto
- número de personas
- gustos
- restricciones
- menú semanal
- carrito estimado
- comparación entre cadenas
- conservación del carrito manual existente

Branch:

feature/streamlit-integration

Documentación:

docs/STREAMLIT_INTEGRATION.md
