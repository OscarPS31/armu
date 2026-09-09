# PROFECO Ingredient Price Coverage

## Objective

Build a usable ingredient-price dataset by matching ingredients from
`recipes_clean.csv` with food products available in the PROFECO
Quién es Quién en los Precios dataset.

The resulting dataset is:

`data/ingredient_prices.csv`

---

## Source data

The recipe dataset contains:

- 500,436 recipes
- 3,932,699 total ingredient occurrences
- 292,424 unique ingredient strings

The latest PROFECO dataset was cleaned and filtered to retain
food and beverage categories relevant to recipe ingredients.

After filtering:

- 184,611 PROFECO food/beverage rows
- 31 retained food/beverage categories

Rows with invalid, null, or zero prices were excluded from the
price-generation process.

---

## Ingredient mapping coverage

Ingredient names from the recipe dataset were normalized and mapped
to equivalent or sufficiently close PROFECO products.

### Occurrence coverage

Mapped ingredient occurrences:

- 2,770,917 mapped occurrences
- 3,932,699 total occurrences
- Coverage: **70.46%**

Occurrence coverage measures how often ingredients appearing across
all recipes can be linked to a PROFECO product.

Formula:

`2,770,917 / 3,932,699 × 100 = 70.46%`

### Unique-string coverage

Mapped unique ingredient strings:

- 169,317 mapped ingredient strings
- 292,424 total unique ingredient strings
- Coverage: **57.90%**

Formula:

`169,317 / 292,424 × 100 = 57.90%`

Occurrence coverage is the primary metric because frequent ingredients
have a larger practical impact on recipe cost estimation than rare
ingredient-name variations.

---

## Mapping methodology

Mappings were built conservatively using recipe ingredient names and
the products available in PROFECO.

Examples include:

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

Some mappings require presentation-level filtering to avoid using
prices for the wrong product variant.

Examples:

- `cornstarch` → presentation containing `Fécula`
- `black beans` → presentation containing `Negro`
- `cider vinegar` → presentation containing `Manzana`
- `orange juice` → presentation containing `Naranja`
- `ground pork` → presentation containing `Molida`
- `pork tenderloin` → presentation containing `Lomo`
- `pork chops` → presentation containing `Chuleta`
- `italian sausage` → presentation containing `Longaniza`
- `jalapeno` → presentation containing `Jalapeño`
- `spaghetti` → spaghetti/espaguetti presentation

The reported coverage therefore represents coverage produced by the
current mapping rules. It should not be interpreted as a claim that
every recipe ingredient has an exact one-to-one commercial equivalent.

Ingredients without a sufficiently defensible PROFECO equivalent were
left unmatched rather than forcing a mapping.

Examples include:

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

## Price normalization

PROFECO prices are originally reported for different package sizes.

To make prices comparable, package prices were normalized whenever
the presentation could be parsed safely.

Examples:

- grams → price per kilogram
- kilograms → price per kilogram
- milliliters → price per liter
- liters → price per liter
- multipacks → price per piece
- individual pieces → price per piece
- bunches → price per bunch (`manojo`)

For example:

A 500 g product costing MXN 60 becomes:

`MXN 120 / kg`

rather than incorrectly storing MXN 60 as the kilogram price.

Median price is used for each:

`ingredient + PROFECO product + unit + store`

This reduces the effect of repeated observations and price outliers.

---

## Final dataset

`data/ingredient_prices.csv`

Columns:

1. `ingredient`
2. `profeco_category`
3. `price`
4. `unit`
5. `store`

Final dataset statistics:

- 3,505 rows
- 98 canonical ingredients with usable prices
- 80 PROFECO products
- 77 stores

Normalized units:

- `kg`
- `litro`
- `pieza`
- `manojo`

Final file size:

- approximately **0.15 MB**

The file is therefore small enough to be safely shared and versioned
with the project.

---

## Limitations

PROFECO does not contain direct equivalents for every ingredient used
in the recipe dataset.

Recipe ingredient names also contain spelling variations,
preparation descriptions, regional terminology, and highly specific
products that may not exist in the PROFECO catalog.

For this reason, reaching higher numerical coverage by forcing weak
equivalences was intentionally avoided.

The current **70.46% occurrence coverage** prioritizes useful and
defensible mappings over artificially maximizing the coverage metric.
