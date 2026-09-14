# ARMU — Integración Frontend / Backend

Este documento explica cómo consumir el backend de ARMU.

El frontend no debe inventar cadenas, restricciones ni límites
de personas.

Debe obtener esos valores desde:

GET /opciones

---

## 1. Obtener opciones disponibles

### Request

GET /opciones

### Response esperado

{
  "cadenas": [
    "Walmart",
    "Soriana",
    "Chedraui"
  ],
  "restricciones": [
    "vegetariano",
    "vegano",
    "sin_gluten"
  ],
  "personas_min": 1,
  "personas_max": 20
}

### Uso en frontend

Usar esta respuesta para construir:

- selector de supermercado
- checkboxes o multiselect de restricciones
- selector de número de personas

---

## 2. Generar recomendación semanal

### Request

POST /recomendacion

Content-Type: application/json

### Ejemplo

{
  "gustos": "rice vegetables",
  "presupuesto": 1000,
  "personas": 2,
  "cadena": "Walmart",
  "restricciones": [
    "vegetariano"
  ]
}

### Campos

gustos

Texto libre.

Ejemplos:

- chicken
- pasta
- rice vegetables

Puede enviarse vacío.

presupuesto

Presupuesto máximo estimado en MXN.

Puede ser null.

personas

Número de personas.

Actualmente:

- mínimo: 1
- máximo: 20

cadena

Debe ser una de las cadenas devueltas por:

GET /opciones

restricciones

Lista opcional.

Valores oficiales:

- vegetariano
- vegano
- sin_gluten

---

## 3. Response de recomendación

El response contiene:

- menu_semanal
- carrito_final
- mensaje

Cada receta contiene:

- id
- name
- servings
- ingredients
- steps
- tags
- is_vegan
- is_vegetarian
- is_gluten_free

### Importante sobre booleanos dietarios

Los campos:

- is_vegan
- is_vegetarian
- is_gluten_free

todavía no representan una clasificación certificada por receta.

Las restricciones se aplican mediante filtros heurísticos
antes de generar el menú.

El frontend no debe presentar estos booleanos como certificación
médica o nutricional.

---

## 4. Comparar precio de una receta

Después de recibir una receta desde POST /recomendacion,
usar su campo id.

Request:

GET /comparar-precios/{id_receta}

La respuesta contiene:

- id_receta
- nombre_receta
- comparacion
- cadena_mas_barata
- precio_mas_barato_mxn
- cadena_mas_cara
- precio_mas_caro_mxn
- ahorro_mxn

El frontend puede mostrar:

- supermercado más barato
- supermercado más caro
- ahorro
- comparación entre cadenas

---

## 5. Flujo recomendado del frontend

1. GET /opciones
2. El usuario selecciona sus preferencias
3. POST /recomendacion
4. Mostrar menú y carrito
5. Tomar id de una receta
6. GET /comparar-precios/{id_receta}
7. Mostrar comparación de precios

---

## 6. Errores esperados

### Personas fuera del rango

FastAPI devuelve HTTP 422.

### Cadena no válida

Usar únicamente cadenas devueltas por:

GET /opciones

### Restricción no válida

Actualmente no están soportadas:

- keto
- paleo
- low_carb

---

## 7. Nota sobre precios

El costo estimado utiliza el costo proporcional de los
ingredientes usados por la receta.

No significa necesariamente que el usuario pueda comprar
exactamente esa fracción de cada producto en tienda.

---

## 8. Endpoints disponibles para frontend

GET  /opciones
POST /recomendacion
GET  /comparar-precios/{id_receta}
GET  /health

---

## 9. Estado

Contrato backend listo para integración frontend MVP.

Antes de cambiar nombres de campos o endpoints,
coordinar el cambio con frontend para evitar romper
la integración.


## Calidad de resultados con gustos

Cuando el usuario envía texto en `gustos`, el backend:

1. prioriza similitud con TF-IDF;
2. evita repetir recetas casi iguales;
3. limita repetición excesiva de categorías;
4. intenta completar 7 días;
5. conserva las restricciones alimentarias y el presupuesto.

El frontend no necesita implementar esta lógica.
Solo debe enviar las preferencias del usuario.


## Demo del contrato

Para ejecutar el flujo backend completo sin frontend:

    python scripts/demo_mvp.py

La demo consume el mismo contrato documentado en este archivo.

También puede imprimirse como JSON:

    python scripts/demo_mvp.py --json

Guía completa:

docs/DEMO_GUIDE.md
