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

## FASE 5 — AUDITORÍA DE COSTOS 🚧

Estado: SIGUIENTE

Objetivo:

Revisar receta por receta:

- costo individual
- costo escalado
- ingredientes
- cantidades
- total semanal

Motivo:

Algunos costos actuales parecen demasiado bajos y deben validarse antes de seguir construyendo.

---

## FASE 6 — RESTRICCIONES ALIMENTARIAS ⏳

Pendiente:

- vegetariano
- vegano
- gluten free
- otras restricciones si el dataset lo permite

---

## FASE 7 — DIVERSIDAD Y CALIDAD DEL MENÚ ⏳

Pendiente:

- evitar recetas repetitivas
- mejorar variedad semanal
- balancear relevancia y diversidad

---

## FASE 8 — FRONTEND ⏳

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
