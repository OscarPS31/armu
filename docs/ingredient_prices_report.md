# Cobertura de precios de ingredientes con PROFECO

## Objetivo

Construir un dataset utilizable de precios de ingredientes mediante el
mapeo de ingredientes provenientes de `recipes_clean.csv` con productos
disponibles en el dataset de PROFECO Quién es Quién en los Precios.

El dataset final generado es:

`data/ingredient_prices.csv`

---

## Datos de origen

El dataset de recetas contiene:

- 500,436 recetas
- 3,932,699 apariciones totales de ingredientes
- 292,424 nombres únicos de ingredientes

El dataset más reciente de PROFECO fue limpiado y filtrado para conservar
únicamente categorías de alimentos y bebidas relevantes para las recetas.

Después del filtrado:

- 184,611 registros de alimentos y bebidas de PROFECO
- 31 categorías de alimentos y bebidas conservadas

Los registros con precios inválidos, nulos o iguales a cero fueron
excluidos del proceso de generación de precios.

---

## Cobertura del mapeo de ingredientes

Los nombres de ingredientes del dataset de recetas fueron normalizados y
mapeados a productos equivalentes o suficientemente cercanos disponibles
en PROFECO.

### Cobertura por apariciones

Apariciones de ingredientes mapeadas:

- 2,770,917 apariciones mapeadas
- 3,932,699 apariciones totales
- Cobertura: **70.46%**

Esta métrica mide qué porcentaje de las apariciones de ingredientes en
todas las recetas puede vincularse con un producto de PROFECO.

Fórmula:

`2,770,917 / 3,932,699 × 100 = 70.46%`

### Cobertura por nombres únicos

Nombres únicos de ingredientes mapeados:

- 169,317 nombres de ingredientes mapeados
- 292,424 nombres únicos totales
- Cobertura: **57.90%**

Fórmula:

`169,317 / 292,424 × 100 = 57.90%`

La cobertura por apariciones se utiliza como métrica principal porque los
ingredientes frecuentes tienen mayor impacto práctico en la estimación del
costo de las recetas que las variantes poco frecuentes de nombres.

---

## Metodología de mapeo

Los mappings se construyeron de manera conservadora utilizando los nombres
de ingredientes de las recetas y los productos disponibles en PROFECO.

Algunos ejemplos:

- `butter` → `Mantequilla`
- `olive oil` → `Aceite de Oliva`
- `rice` → `Arroz`
- `tomato` → `Jitomate`
- `chicken` → `Carne Pollo`
- `egg` → `Huevo`
- `jalapeno` → `Chile Fresco`
- `chickpeas` → `Garbanzo`
- `artichoke` → `Alcachofa`
- `rum` → `Ron`

Algunos mappings requieren filtros adicionales sobre la presentación del
producto para evitar utilizar precios correspondientes a otra variante.

Ejemplos:

- `cornstarch` → presentación que contiene `Fécula`
- `black beans` → presentación que contiene `Negro`
- `cider vinegar` → presentación que contiene `Manzana`
- `orange juice` → presentación que contiene `Naranja`
- `ground pork` → presentación que contiene `Molida`
- `pork tenderloin` → presentación que contiene `Lomo`
- `pork chops` → presentación que contiene `Chuleta`
- `italian sausage` → presentación que contiene `Longaniza`
- `jalapeno` → presentación que contiene `Jalapeño`
- `spaghetti` → presentación `Spaghetti` o `Espaguetti`

La cobertura reportada representa la cobertura producida por las reglas
actuales de mapeo. No debe interpretarse como una equivalencia comercial
exacta uno a uno para todos los ingredientes.

Los ingredientes que no tenían una equivalencia suficientemente defendible
en PROFECO se dejaron sin mapear en lugar de forzar una correspondencia.

Algunos ejemplos son:

- baking soda
- nutmeg
- paprika
- parmesan cheese
- ginger
- buttermilk
- cheddar cheese
- parsley
- basil

---

## Normalización de precios

PROFECO reporta precios de productos con diferentes tamaños y tipos de
presentación.

Para poder comparar los precios, las presentaciones fueron normalizadas
cuando fue posible interpretarlas de forma segura.

Conversiones utilizadas:

- gramos → precio por kilogramo
- kilogramos → precio por kilogramo
- mililitros → precio por litro
- litros → precio por litro
- paquetes con varias unidades → precio por pieza
- productos individuales → precio por pieza
- manojos → precio por manojo

Ejemplo:

Si un producto de 500 g cuesta MXN 60, se normaliza como:

`MXN 120 / kg`

en lugar de guardar incorrectamente MXN 60 como precio por kilogramo.

Para cada combinación de:

`ingrediente + producto PROFECO + unidad + tienda`

se utiliza la mediana de los precios disponibles.

La mediana permite reducir el efecto de observaciones repetidas y valores
atípicos.

---

## Dataset final

Archivo:

`data/ingredient_prices.csv`

Columnas:

1. `ingredient`
2. `profeco_category`
3. `price`
4. `unit`
5. `store`

Estadísticas finales:

- 3,505 filas
- 98 ingredientes canónicos con precios utilizables
- 80 productos de PROFECO
- 77 tiendas

Unidades normalizadas:

- `kg`
- `litro`
- `pieza`
- `manojo`

Tamaño final del archivo:

- aproximadamente **0.15 MB**

El archivo es suficientemente pequeño para compartirse y versionarse
dentro del proyecto.

---

## Validación final

El dataset final fue validado con los siguientes resultados:

- 0 valores nulos
- 0 precios menores o iguales a cero
- 0 filas duplicadas
- precio mínimo: MXN 1.65
- precio máximo: MXN 1,420.97
- columnas correctas
- tamaño final: aproximadamente 0.149 MB

---

## Limitaciones

PROFECO no contiene equivalentes directos para todos los ingredientes del
dataset de recetas.

Además, los nombres de ingredientes incluyen variantes ortográficas,
descripciones de preparación, términos regionales y productos muy
específicos que pueden no existir dentro del catálogo de PROFECO.

Por esta razón, se decidió no aumentar artificialmente la cobertura
mediante equivalencias débiles.

La cobertura actual de **70.46% por apariciones** prioriza mappings útiles
y defendibles sobre una cobertura numérica artificialmente más alta.
